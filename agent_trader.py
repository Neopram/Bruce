"""
agent_trader.py - Complete Trading Agent with paper/live mode support.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from enum import Enum
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta, timezone
import uuid
import logging
import random
import math

# Try to import ccxt for live exchange connectivity
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    ccxt = None
    CCXT_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger("Bruce.AgentTrader")


# ---------------------------------------------------------------------------
# Enums & Models
# ---------------------------------------------------------------------------

class TradingMode(str, Enum):
    PAPER = "paper"
    LIVE = "live"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"


class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class OrderRequest(BaseModel):
    symbol: str
    side: OrderSide
    amount: float
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = None
    stop_price: Optional[float] = None


# ---------------------------------------------------------------------------
# Risk Manager
# ---------------------------------------------------------------------------

class RiskManager:
    """Enforces position-level and portfolio-level risk limits."""

    def __init__(
        self,
        max_position_pct: float = 0.20,
        max_drawdown_pct: float = 0.15,
        max_open_orders: int = 20,
        max_daily_loss_pct: float = 0.05,
    ):
        self.max_position_pct = max_position_pct
        self.max_drawdown_pct = max_drawdown_pct
        self.max_open_orders = max_open_orders
        self.max_daily_loss_pct = max_daily_loss_pct

    def check_risk_limits(self, portfolio_value: float, position_value: float,
                          open_orders: int, daily_pnl: float, peak_value: float) -> Dict[str, Any]:
        violations: List[str] = []

        # Position concentration
        if portfolio_value > 0 and (position_value / portfolio_value) > self.max_position_pct:
            violations.append(
                f"Position exceeds {self.max_position_pct*100:.0f}% of portfolio "
                f"({position_value/portfolio_value*100:.1f}%)"
            )

        # Max drawdown
        if peak_value > 0:
            drawdown = (peak_value - portfolio_value) / peak_value
            if drawdown > self.max_drawdown_pct:
                violations.append(
                    f"Drawdown {drawdown*100:.1f}% exceeds limit {self.max_drawdown_pct*100:.0f}%"
                )

        # Open order count
        if open_orders > self.max_open_orders:
            violations.append(f"Open orders ({open_orders}) exceeds limit ({self.max_open_orders})")

        # Daily loss
        if portfolio_value > 0 and daily_pnl < 0:
            daily_loss_pct = abs(daily_pnl) / portfolio_value
            if daily_loss_pct > self.max_daily_loss_pct:
                violations.append(
                    f"Daily loss {daily_loss_pct*100:.1f}% exceeds limit {self.max_daily_loss_pct*100:.0f}%"
                )

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def position_size_calculator(
        self, portfolio_value: float, risk_per_trade_pct: float,
        entry_price: float, stop_loss_price: float
    ) -> Dict[str, Any]:
        """Kelly-inspired position sizing based on risk budget and stop distance."""
        if entry_price <= 0 or stop_loss_price <= 0:
            return {"error": "Prices must be positive", "suggested_size": 0}

        risk_amount = portfolio_value * risk_per_trade_pct
        price_risk = abs(entry_price - stop_loss_price)
        if price_risk == 0:
            return {"error": "Entry and stop-loss are identical", "suggested_size": 0}

        raw_size = risk_amount / price_risk
        position_value = raw_size * entry_price

        # Cap at max position concentration
        max_value = portfolio_value * self.max_position_pct
        if position_value > max_value:
            raw_size = max_value / entry_price

        return {
            "suggested_size": round(raw_size, 8),
            "position_value": round(raw_size * entry_price, 2),
            "risk_amount": round(risk_amount, 2),
            "risk_reward_info": {
                "entry": entry_price,
                "stop_loss": stop_loss_price,
                "distance_pct": round(price_risk / entry_price * 100, 2),
            },
        }


# ---------------------------------------------------------------------------
# Simulated Price Feed (used when ccxt is unavailable or in paper mode)
# ---------------------------------------------------------------------------

class SimulatedPriceFeed:
    """Generates deterministic-ish simulated prices for paper trading."""

    _base_prices: Dict[str, float] = {
        "BTC/USDT": 67500.0,
        "ETH/USDT": 3450.0,
        "SOL/USDT": 172.0,
        "BNB/USDT": 610.0,
        "XRP/USDT": 0.62,
        "ADA/USDT": 0.48,
        "DOGE/USDT": 0.165,
    }

    @classmethod
    def get_price(cls, symbol: str) -> float:
        base = cls._base_prices.get(symbol, 100.0)
        noise = random.gauss(0, base * 0.002)
        return round(base + noise, 6)


# ---------------------------------------------------------------------------
# Trading Agent
# ---------------------------------------------------------------------------

class TradingAgent:
    """
    Core trading agent supporting paper (simulated) and live modes.

    In paper mode every order is filled instantly at the simulated market price.
    In live mode the agent delegates to ccxt (if available).
    """

    def __init__(
        self,
        mode: TradingMode = TradingMode.PAPER,
        initial_balance: float = 100_000.0,
        exchange_id: str = "binance",
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ):
        self.mode = mode
        self.exchange_id = exchange_id

        # Paper-trading state
        self.cash_balance: float = initial_balance
        self.initial_balance: float = initial_balance
        self.peak_value: float = initial_balance
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.orders: Dict[str, Dict[str, Any]] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.daily_pnl: float = 0.0
        self.daily_pnl_reset: Optional[datetime] = None

        # Risk manager
        self.risk_manager = RiskManager()

        # ccxt exchange (live mode)
        self._exchange = None
        if mode == TradingMode.LIVE and CCXT_AVAILABLE and api_key:
            try:
                exchange_class = getattr(ccxt, exchange_id, None)
                if exchange_class:
                    self._exchange = exchange_class({
                        "apiKey": api_key,
                        "secret": api_secret,
                        "enableRateLimit": True,
                    })
                    logger.info(f"Live exchange connection initialised: {exchange_id}")
            except Exception as exc:
                logger.error(f"Failed to initialise live exchange: {exc}")

    # ------------------------------------------------------------------
    # Portfolio helpers
    # ------------------------------------------------------------------

    def _get_simulated_price(self, symbol: str) -> float:
        return SimulatedPriceFeed.get_price(symbol)

    def _portfolio_value(self) -> float:
        total = self.cash_balance
        for sym, pos in self.positions.items():
            price = self._get_simulated_price(sym)
            total += pos["amount"] * price
        return total

    def _reset_daily_pnl_if_needed(self):
        now = datetime.now(timezone.utc)
        if self.daily_pnl_reset is None or (now - self.daily_pnl_reset) > timedelta(hours=24):
            self.daily_pnl = 0.0
            self.daily_pnl_reset = now

    # ------------------------------------------------------------------
    # Order management
    # ------------------------------------------------------------------

    def create_order(
        self, symbol: str, side: OrderSide, amount: float,
        order_type: OrderType = OrderType.MARKET, price: Optional[float] = None,
    ) -> Dict[str, Any]:
        self._reset_daily_pnl_if_needed()
        order_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # ------ Live mode ------
        if self.mode == TradingMode.LIVE and self._exchange:
            try:
                ccxt_order = self._exchange.create_order(
                    symbol, order_type.value, side.value, amount, price
                )
                record = {
                    "order_id": order_id,
                    "exchange_order_id": ccxt_order.get("id"),
                    "symbol": symbol,
                    "side": side.value,
                    "amount": amount,
                    "order_type": order_type.value,
                    "price": ccxt_order.get("price"),
                    "status": OrderStatus.FILLED.value,
                    "created_at": timestamp,
                    "mode": "live",
                }
                self.orders[order_id] = record
                self.trade_history.append(record)
                logger.info(f"[LIVE] Order placed: {record}")
                return record
            except Exception as exc:
                logger.error(f"[LIVE] Order failed: {exc}")
                raise ValueError(f"Live order failed: {exc}")

        # ------ Paper mode ------
        # Normalise enum-or-string arguments so .value never fails on a plain str
        if isinstance(side, str):
            side = OrderSide(side)
        if isinstance(order_type, str):
            order_type = OrderType(order_type)

        sim_price = self._get_simulated_price(symbol) if price is None else price

        # Risk pre-check
        position_value = amount * sim_price
        portfolio_val = self._portfolio_value()
        open_count = sum(1 for o in self.orders.values() if o["status"] == OrderStatus.PENDING.value)
        risk_check = self.risk_manager.check_risk_limits(
            portfolio_val, position_value, open_count, self.daily_pnl, self.peak_value
        )
        if not risk_check["passed"]:
            return {
                "order_id": order_id,
                "status": OrderStatus.REJECTED.value,
                "reason": risk_check["violations"],
                "created_at": timestamp,
            }

        # Balance check for buys
        if side == OrderSide.BUY:
            cost = amount * sim_price
            if cost > self.cash_balance:
                return {
                    "order_id": order_id,
                    "status": OrderStatus.REJECTED.value,
                    "reason": f"Insufficient cash: need {cost:.2f}, have {self.cash_balance:.2f}",
                    "created_at": timestamp,
                }
            self.cash_balance -= cost
            pos = self.positions.setdefault(symbol, {"amount": 0.0, "avg_entry": 0.0})
            old_cost = pos["amount"] * pos["avg_entry"]
            pos["amount"] += amount
            pos["avg_entry"] = (old_cost + cost) / pos["amount"] if pos["amount"] else 0.0

        elif side == OrderSide.SELL:
            pos = self.positions.get(symbol)
            if not pos or pos["amount"] < amount:
                return {
                    "order_id": order_id,
                    "status": OrderStatus.REJECTED.value,
                    "reason": f"Insufficient position to sell {amount} {symbol}",
                    "created_at": timestamp,
                }
            revenue = amount * sim_price
            cost_basis = amount * pos["avg_entry"]
            realised_pnl = revenue - cost_basis
            self.cash_balance += revenue
            pos["amount"] -= amount
            self.daily_pnl += realised_pnl
            if pos["amount"] == 0:
                del self.positions[symbol]

        # Track peak for drawdown
        current_val = self._portfolio_value()
        if current_val > self.peak_value:
            self.peak_value = current_val

        record = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side.value,
            "amount": amount,
            "order_type": order_type.value,
            "price": sim_price,
            "status": OrderStatus.FILLED.value,
            "created_at": timestamp,
            "mode": "paper",
        }
        self.orders[order_id] = record
        self.trade_history.append(record)
        logger.info(f"[PAPER] Order filled: {record}")
        return record

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        order = self.orders.get(order_id)
        if not order:
            return {"error": f"Order {order_id} not found"}
        if order["status"] != OrderStatus.PENDING.value:
            return {"error": f"Order {order_id} cannot be cancelled (status={order['status']})"}
        order["status"] = OrderStatus.CANCELLED.value
        logger.info(f"Order cancelled: {order_id}")
        return order

    # ------------------------------------------------------------------
    # Portfolio & positions
    # ------------------------------------------------------------------

    def get_portfolio(self) -> Dict[str, Any]:
        positions_detail: List[Dict[str, Any]] = []
        total_position_value = 0.0
        total_unrealised_pnl = 0.0

        for sym, pos in self.positions.items():
            price = self._get_simulated_price(sym)
            market_value = pos["amount"] * price
            unrealised = (price - pos["avg_entry"]) * pos["amount"]
            total_position_value += market_value
            total_unrealised_pnl += unrealised
            positions_detail.append({
                "symbol": sym,
                "amount": pos["amount"],
                "avg_entry": round(pos["avg_entry"], 6),
                "current_price": price,
                "market_value": round(market_value, 2),
                "unrealised_pnl": round(unrealised, 2),
            })

        portfolio_value = self.cash_balance + total_position_value
        drawdown = (self.peak_value - portfolio_value) / self.peak_value if self.peak_value else 0.0

        return {
            "mode": self.mode.value,
            "cash_balance": round(self.cash_balance, 2),
            "total_position_value": round(total_position_value, 2),
            "portfolio_value": round(portfolio_value, 2),
            "unrealised_pnl": round(total_unrealised_pnl, 2),
            "peak_value": round(self.peak_value, 2),
            "drawdown_pct": round(drawdown * 100, 2),
            "positions": positions_detail,
        }

    def get_position(self, symbol: str) -> Dict[str, Any]:
        pos = self.positions.get(symbol)
        if not pos:
            return {"symbol": symbol, "amount": 0.0, "status": "no_position"}
        price = self._get_simulated_price(symbol)
        return {
            "symbol": symbol,
            "amount": pos["amount"],
            "avg_entry": round(pos["avg_entry"], 6),
            "current_price": price,
            "market_value": round(pos["amount"] * price, 2),
            "unrealised_pnl": round((price - pos["avg_entry"]) * pos["amount"], 2),
        }

    # ------------------------------------------------------------------
    # Risk
    # ------------------------------------------------------------------

    def check_risk_limits(self) -> Dict[str, Any]:
        self._reset_daily_pnl_if_needed()
        portfolio_val = self._portfolio_value()
        max_pos_val = max(
            (p["amount"] * self._get_simulated_price(s) for s, p in self.positions.items()),
            default=0.0,
        )
        open_count = sum(1 for o in self.orders.values() if o["status"] == OrderStatus.PENDING.value)
        return self.risk_manager.check_risk_limits(
            portfolio_val, max_pos_val, open_count, self.daily_pnl, self.peak_value,
        )

    def position_size_calculator(
        self, risk_per_trade_pct: float, entry_price: float, stop_loss_price: float
    ) -> Dict[str, Any]:
        return self.risk_manager.position_size_calculator(
            self._portfolio_value(), risk_per_trade_pct, entry_price, stop_loss_price,
        )

    # ------------------------------------------------------------------
    # Strategy execution (delegates to strategy_engine)
    # ------------------------------------------------------------------

    def execute_strategy(self, strategy_name: str, symbol: str, data: Optional[List[float]] = None) -> Dict[str, Any]:
        try:
            from strategy_engine import StrategyEngine
            engine = StrategyEngine()
            if data is None:
                data = [self._get_simulated_price(symbol) for _ in range(100)]
            signal = engine.evaluate(strategy_name, data)

            action_taken = None
            if signal["signal"] == "BUY" and signal["confidence"] >= 0.6:
                sizing = self.position_size_calculator(0.02, data[-1], data[-1] * 0.95)
                size = sizing.get("suggested_size", 0)
                if size > 0:
                    action_taken = self.create_order(symbol, OrderSide.BUY, size)
            elif signal["signal"] == "SELL" and signal["confidence"] >= 0.6:
                pos = self.positions.get(symbol)
                if pos and pos["amount"] > 0:
                    action_taken = self.create_order(symbol, OrderSide.SELL, pos["amount"])

            return {
                "strategy": strategy_name,
                "symbol": symbol,
                "signal": signal,
                "action_taken": action_taken,
            }
        except Exception as exc:
            logger.error(f"Strategy execution error: {exc}")
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # History / PnL
    # ------------------------------------------------------------------

    def get_trade_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self.trade_history[-limit:]

    def get_pnl(self) -> Dict[str, Any]:
        portfolio_val = self._portfolio_value()
        total_pnl = portfolio_val - self.initial_balance
        total_return_pct = (total_pnl / self.initial_balance * 100) if self.initial_balance else 0.0
        drawdown = (self.peak_value - portfolio_val) / self.peak_value if self.peak_value else 0.0
        return {
            "initial_balance": self.initial_balance,
            "current_value": round(portfolio_val, 2),
            "total_pnl": round(total_pnl, 2),
            "total_return_pct": round(total_return_pct, 2),
            "peak_value": round(self.peak_value, 2),
            "max_drawdown_pct": round(drawdown * 100, 2),
            "total_trades": len(self.trade_history),
            "daily_pnl": round(self.daily_pnl, 2),
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_agent = TradingAgent(mode=TradingMode.PAPER)


def execute_trading_agent() -> Dict[str, Any]:
    """Backwards-compatible convenience function."""
    return _agent.get_portfolio()


# ---------------------------------------------------------------------------
# FastAPI endpoints
# ---------------------------------------------------------------------------

@router.get("/agent-trader")
async def agent_trader_endpoint():
    return _agent.get_portfolio()


@router.post("/agent-trader/order")
async def create_order_endpoint(req: Request):
    try:
        data = await req.json()
        order_req = OrderRequest(**data)
        result = _agent.create_order(
            symbol=order_req.symbol,
            side=order_req.side,
            amount=order_req.amount,
            order_type=order_req.order_type,
            price=order_req.price,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/agent-trader/order/{order_id}")
async def cancel_order_endpoint(order_id: str):
    return _agent.cancel_order(order_id)


@router.get("/agent-trader/portfolio")
async def portfolio_endpoint():
    return _agent.get_portfolio()


@router.get("/agent-trader/position/{symbol}")
async def position_endpoint(symbol: str):
    return _agent.get_position(symbol)


@router.get("/agent-trader/risk")
async def risk_endpoint():
    return _agent.check_risk_limits()


@router.post("/agent-trader/position-size")
async def position_size_endpoint(req: Request):
    data = await req.json()
    return _agent.position_size_calculator(
        data.get("risk_per_trade_pct", 0.02),
        data["entry_price"],
        data["stop_loss_price"],
    )


@router.post("/agent-trader/execute-strategy")
async def execute_strategy_endpoint(req: Request):
    data = await req.json()
    return _agent.execute_strategy(
        data["strategy_name"],
        data["symbol"],
        data.get("data"),
    )


@router.get("/agent-trader/history")
async def history_endpoint():
    return _agent.get_trade_history()


@router.get("/agent-trader/pnl")
async def pnl_endpoint():
    return _agent.get_pnl()
