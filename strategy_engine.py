"""
strategy_engine.py - Strategy evaluation, backtesting, and multi-strategy voting.
"""

from fastapi import APIRouter, HTTPException, Request
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import math
import logging

router = APIRouter()
logger = logging.getLogger("Bruce.StrategyEngine")


# ---------------------------------------------------------------------------
# Signal enum
# ---------------------------------------------------------------------------

class Signal(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


# ---------------------------------------------------------------------------
# Technical indicator helpers
# ---------------------------------------------------------------------------

def _sma(data: List[float], period: int) -> List[Optional[float]]:
    """Simple Moving Average."""
    result: List[Optional[float]] = [None] * len(data)
    for i in range(period - 1, len(data)):
        result[i] = sum(data[i - period + 1: i + 1]) / period
    return result


def _ema(data: List[float], period: int) -> List[float]:
    """Exponential Moving Average."""
    if not data:
        return []
    k = 2.0 / (period + 1)
    ema_vals = [data[0]]
    for i in range(1, len(data)):
        ema_vals.append(data[i] * k + ema_vals[-1] * (1 - k))
    return ema_vals


def _rsi(data: List[float], period: int = 14) -> List[Optional[float]]:
    """Relative Strength Index."""
    result: List[Optional[float]] = [None] * len(data)
    if len(data) < period + 1:
        return result

    gains, losses = [], []
    for i in range(1, period + 1):
        delta = data[i] - data[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))

    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period

    if avg_loss == 0:
        result[period] = 100.0
    else:
        rs = avg_gain / avg_loss
        result[period] = 100 - 100 / (1 + rs)

    for i in range(period + 1, len(data)):
        delta = data[i] - data[i - 1]
        gain = max(delta, 0)
        loss = max(-delta, 0)
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0:
            result[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            result[i] = 100 - 100 / (1 + rs)

    return result


def _macd(data: List[float], fast: int = 12, slow: int = 26, signal_period: int = 9
          ) -> Tuple[List[float], List[float], List[float]]:
    """MACD line, signal line, histogram."""
    ema_fast = _ema(data, fast)
    ema_slow = _ema(data, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = _ema(macd_line, signal_period)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, histogram


def _bollinger_bands(data: List[float], period: int = 20, num_std: float = 2.0
                     ) -> Tuple[List[Optional[float]], List[Optional[float]], List[Optional[float]]]:
    """Upper band, middle (SMA), lower band."""
    middle = _sma(data, period)
    upper: List[Optional[float]] = [None] * len(data)
    lower: List[Optional[float]] = [None] * len(data)
    for i in range(period - 1, len(data)):
        window = data[i - period + 1: i + 1]
        mean = middle[i]
        std = math.sqrt(sum((x - mean) ** 2 for x in window) / period)
        upper[i] = mean + num_std * std
        lower[i] = mean - num_std * std
    return upper, middle, lower


# ---------------------------------------------------------------------------
# Individual Strategy Evaluators
# ---------------------------------------------------------------------------

def _strategy_sma_crossover(data: List[float], short_period: int = 10, long_period: int = 30
                            ) -> Dict[str, Any]:
    if len(data) < long_period + 2:
        return {"signal": Signal.HOLD.value, "confidence": 0.0, "reason": "Insufficient data"}

    sma_short = _sma(data, short_period)
    sma_long = _sma(data, long_period)

    curr_short, prev_short = sma_short[-1], sma_short[-2]
    curr_long, prev_long = sma_long[-1], sma_long[-2]

    if curr_short is None or curr_long is None or prev_short is None or prev_long is None:
        return {"signal": Signal.HOLD.value, "confidence": 0.0, "reason": "Not enough computed SMA values"}

    # Crossover detection
    if prev_short <= prev_long and curr_short > curr_long:
        spread = (curr_short - curr_long) / curr_long
        confidence = min(0.5 + spread * 20, 1.0)
        return {"signal": Signal.BUY.value, "confidence": round(confidence, 3),
                "reason": f"SMA{short_period} crossed above SMA{long_period}"}
    elif prev_short >= prev_long and curr_short < curr_long:
        spread = (curr_long - curr_short) / curr_long
        confidence = min(0.5 + spread * 20, 1.0)
        return {"signal": Signal.SELL.value, "confidence": round(confidence, 3),
                "reason": f"SMA{short_period} crossed below SMA{long_period}"}

    return {"signal": Signal.HOLD.value, "confidence": 0.3, "reason": "No crossover detected"}


def _strategy_rsi(data: List[float], period: int = 14,
                  oversold: float = 30.0, overbought: float = 70.0) -> Dict[str, Any]:
    rsi_vals = _rsi(data, period)
    latest = rsi_vals[-1]
    if latest is None:
        return {"signal": Signal.HOLD.value, "confidence": 0.0, "reason": "Insufficient data for RSI"}

    if latest <= oversold:
        confidence = min(0.5 + (oversold - latest) / oversold, 1.0)
        return {"signal": Signal.BUY.value, "confidence": round(confidence, 3),
                "reason": f"RSI={latest:.1f} (oversold)"}
    elif latest >= overbought:
        confidence = min(0.5 + (latest - overbought) / (100 - overbought), 1.0)
        return {"signal": Signal.SELL.value, "confidence": round(confidence, 3),
                "reason": f"RSI={latest:.1f} (overbought)"}

    return {"signal": Signal.HOLD.value, "confidence": 0.4,
            "reason": f"RSI={latest:.1f} (neutral zone)"}


def _strategy_macd(data: List[float]) -> Dict[str, Any]:
    if len(data) < 35:
        return {"signal": Signal.HOLD.value, "confidence": 0.0, "reason": "Insufficient data for MACD"}

    macd_line, signal_line, histogram = _macd(data)
    curr_hist = histogram[-1]
    prev_hist = histogram[-2]

    if prev_hist <= 0 and curr_hist > 0:
        confidence = min(0.55 + abs(curr_hist) * 5, 1.0)
        return {"signal": Signal.BUY.value, "confidence": round(confidence, 3),
                "reason": "MACD histogram turned positive"}
    elif prev_hist >= 0 and curr_hist < 0:
        confidence = min(0.55 + abs(curr_hist) * 5, 1.0)
        return {"signal": Signal.SELL.value, "confidence": round(confidence, 3),
                "reason": "MACD histogram turned negative"}

    return {"signal": Signal.HOLD.value, "confidence": 0.35,
            "reason": f"MACD histogram={curr_hist:.4f} (no crossover)"}


def _strategy_bollinger(data: List[float], period: int = 20, num_std: float = 2.0
                        ) -> Dict[str, Any]:
    if len(data) < period + 1:
        return {"signal": Signal.HOLD.value, "confidence": 0.0, "reason": "Insufficient data for Bollinger"}

    upper, middle, lower = _bollinger_bands(data, period, num_std)
    price = data[-1]
    u, m, l_ = upper[-1], middle[-1], lower[-1]

    if u is None or l_ is None:
        return {"signal": Signal.HOLD.value, "confidence": 0.0, "reason": "Bollinger not computed"}

    band_width = u - l_
    if band_width == 0:
        return {"signal": Signal.HOLD.value, "confidence": 0.0, "reason": "Zero band width"}

    if price <= l_:
        penetration = (l_ - price) / band_width
        confidence = min(0.55 + penetration * 3, 1.0)
        return {"signal": Signal.BUY.value, "confidence": round(confidence, 3),
                "reason": f"Price ({price:.2f}) at/below lower band ({l_:.2f})"}
    elif price >= u:
        penetration = (price - u) / band_width
        confidence = min(0.55 + penetration * 3, 1.0)
        return {"signal": Signal.SELL.value, "confidence": round(confidence, 3),
                "reason": f"Price ({price:.2f}) at/above upper band ({u:.2f})"}

    position_in_band = (price - l_) / band_width
    return {"signal": Signal.HOLD.value, "confidence": 0.3,
            "reason": f"Price within bands (position={position_in_band:.2f})"}


# ---------------------------------------------------------------------------
# Strategy registry
# ---------------------------------------------------------------------------

STRATEGY_REGISTRY: Dict[str, Any] = {
    "sma_crossover": _strategy_sma_crossover,
    "rsi": _strategy_rsi,
    "macd": _strategy_macd,
    "bollinger": _strategy_bollinger,
}


# ---------------------------------------------------------------------------
# Strategy Engine
# ---------------------------------------------------------------------------

class StrategyEngine:
    """Evaluates, backtests and combines trading strategies."""

    def __init__(self):
        self.strategies = dict(STRATEGY_REGISTRY)

    def list_strategies(self) -> List[str]:
        return list(self.strategies.keys())

    # ------------------------------------------------------------------
    # Single strategy evaluation
    # ------------------------------------------------------------------

    def evaluate(self, strategy_name: str, data: List[float]) -> Dict[str, Any]:
        fn = self.strategies.get(strategy_name)
        if fn is None:
            return {"error": f"Unknown strategy: {strategy_name}",
                    "available": self.list_strategies()}
        try:
            result = fn(data)
            result["strategy"] = strategy_name
            result["data_points"] = len(data)
            result["evaluated_at"] = datetime.utcnow().isoformat()
            return result
        except Exception as exc:
            logger.error(f"Strategy evaluation error ({strategy_name}): {exc}")
            return {"error": str(exc), "strategy": strategy_name}

    # ------------------------------------------------------------------
    # Multi-strategy voting
    # ------------------------------------------------------------------

    def combine_strategies(self, strategy_names: List[str], data: List[float]) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        vote_scores: Dict[str, float] = {Signal.BUY.value: 0.0, Signal.SELL.value: 0.0, Signal.HOLD.value: 0.0}

        for name in strategy_names:
            res = self.evaluate(name, data)
            results.append(res)
            sig = res.get("signal", Signal.HOLD.value)
            conf = res.get("confidence", 0.0)
            vote_scores[sig] += conf

        # Determine winner
        winner = max(vote_scores, key=vote_scores.get)
        total_conf = sum(vote_scores.values())
        combined_confidence = vote_scores[winner] / total_conf if total_conf > 0 else 0.0

        return {
            "combined_signal": winner,
            "combined_confidence": round(combined_confidence, 3),
            "vote_scores": {k: round(v, 3) for k, v in vote_scores.items()},
            "individual_results": results,
            "strategies_used": strategy_names,
            "evaluated_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Backtesting
    # ------------------------------------------------------------------

    def backtest(self, strategy_name: str, historical_data: List[float],
                 initial_capital: float = 10000.0, position_size_pct: float = 1.0
                 ) -> Dict[str, Any]:
        fn = self.strategies.get(strategy_name)
        if fn is None:
            return {"error": f"Unknown strategy: {strategy_name}"}
        if len(historical_data) < 50:
            return {"error": "Need at least 50 data points for backtesting"}

        cash = initial_capital
        holdings = 0.0
        trades: List[Dict[str, Any]] = []
        equity_curve: List[float] = []
        peak = initial_capital

        window_size = 40  # rolling evaluation window

        for i in range(window_size, len(historical_data)):
            window = historical_data[:i + 1]
            price = historical_data[i]
            portfolio_val = cash + holdings * price

            equity_curve.append(portfolio_val)
            if portfolio_val > peak:
                peak = portfolio_val

            signal = fn(window)

            if signal["signal"] == Signal.BUY.value and signal.get("confidence", 0) >= 0.5 and holdings == 0.0:
                buy_amount = (cash * position_size_pct) / price
                cost = buy_amount * price
                cash -= cost
                holdings += buy_amount
                trades.append({"type": "BUY", "price": price, "amount": buy_amount, "index": i})

            elif signal["signal"] == Signal.SELL.value and signal.get("confidence", 0) >= 0.5 and holdings > 0:
                revenue = holdings * price
                cash += revenue
                trades.append({"type": "SELL", "price": price, "amount": holdings, "index": i})
                holdings = 0.0

        # Final liquidation
        final_price = historical_data[-1]
        final_value = cash + holdings * final_price

        # Metrics
        total_return = (final_value - initial_capital) / initial_capital
        max_drawdown = 0.0
        running_peak = 0.0
        for eq in equity_curve:
            if eq > running_peak:
                running_peak = eq
            dd = (running_peak - eq) / running_peak if running_peak else 0
            if dd > max_drawdown:
                max_drawdown = dd

        # Sharpe ratio (annualised, assuming daily data)
        if len(equity_curve) > 1:
            returns = [(equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1]
                       for i in range(1, len(equity_curve)) if equity_curve[i - 1] != 0]
            if returns:
                mean_ret = sum(returns) / len(returns)
                std_ret = math.sqrt(sum((r - mean_ret) ** 2 for r in returns) / len(returns)) if len(returns) > 1 else 1.0
                sharpe = (mean_ret / std_ret) * math.sqrt(252) if std_ret > 0 else 0.0
            else:
                sharpe = 0.0
        else:
            sharpe = 0.0

        win_trades = 0
        loss_trades = 0
        for j in range(0, len(trades) - 1, 2):
            if j + 1 < len(trades):
                if trades[j + 1]["price"] > trades[j]["price"]:
                    win_trades += 1
                else:
                    loss_trades += 1

        total_trades = win_trades + loss_trades
        win_rate = win_trades / total_trades if total_trades > 0 else 0.0

        return {
            "strategy": strategy_name,
            "initial_capital": initial_capital,
            "final_value": round(final_value, 2),
            "total_return_pct": round(total_return * 100, 2),
            "sharpe_ratio": round(sharpe, 3),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "total_trades": total_trades,
            "win_rate": round(win_rate * 100, 1),
            "data_points": len(historical_data),
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_engine = StrategyEngine()


def strategy_engine_evaluate(strategy_name: str = "sma_crossover", data: Optional[List[float]] = None) -> Dict[str, Any]:
    """Backwards-compatible convenience function."""
    if data is None:
        import random
        base = 100.0
        data = []
        for _ in range(200):
            base += random.gauss(0, 1)
            data.append(base)
    return _engine.evaluate(strategy_name, data)


# ---------------------------------------------------------------------------
# FastAPI endpoints
# ---------------------------------------------------------------------------

@router.get("/strategy-engine")
async def strategy_engine_endpoint():
    return {
        "msg": "Strategy engine active",
        "available_strategies": _engine.list_strategies(),
    }


@router.post("/strategy-engine/evaluate")
async def evaluate_endpoint(req: Request):
    data = await req.json()
    strategy = data.get("strategy", "sma_crossover")
    prices = data.get("data")
    if not prices or not isinstance(prices, list):
        raise HTTPException(status_code=400, detail="'data' must be a list of price floats")
    return _engine.evaluate(strategy, prices)


@router.post("/strategy-engine/combine")
async def combine_endpoint(req: Request):
    data = await req.json()
    strategies = data.get("strategies", list(STRATEGY_REGISTRY.keys()))
    prices = data.get("data")
    if not prices or not isinstance(prices, list):
        raise HTTPException(status_code=400, detail="'data' must be a list of price floats")
    return _engine.combine_strategies(strategies, prices)


@router.post("/strategy-engine/backtest")
async def backtest_endpoint(req: Request):
    data = await req.json()
    strategy = data.get("strategy", "sma_crossover")
    prices = data.get("data")
    if not prices or not isinstance(prices, list):
        raise HTTPException(status_code=400, detail="'data' must be a list of price floats")
    return _engine.backtest(strategy, prices,
                            data.get("initial_capital", 10000.0),
                            data.get("position_size_pct", 1.0))
