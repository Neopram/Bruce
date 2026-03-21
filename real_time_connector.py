"""
real_time_connector.py - Real-time market data connector with exchange and simulated fallback.
"""

from fastapi import APIRouter, WebSocket, Query
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime, timedelta
import asyncio
import random
import math
import logging

# Try ccxt for live exchange data
try:
    import ccxt
    CCXT_AVAILABLE = True
except ImportError:
    ccxt = None
    CCXT_AVAILABLE = False

router = APIRouter()
logger = logging.getLogger("Bruce.MarketDataConnector")


# ---------------------------------------------------------------------------
# Simulated Market Data Generator
# ---------------------------------------------------------------------------

class SimulatedMarket:
    """Generates realistic simulated market data when no exchange is configured."""

    _BASE: Dict[str, float] = {
        "BTC/USDT": 67500.0,
        "ETH/USDT": 3450.0,
        "SOL/USDT": 172.0,
        "BNB/USDT": 610.0,
        "XRP/USDT": 0.62,
        "ADA/USDT": 0.48,
        "DOGE/USDT": 0.165,
        "AVAX/USDT": 38.5,
        "DOT/USDT": 7.8,
        "MATIC/USDT": 0.72,
    }

    @classmethod
    def _base_price(cls, symbol: str) -> float:
        return cls._BASE.get(symbol, 100.0)

    @classmethod
    def ticker(cls, symbol: str) -> Dict[str, Any]:
        base = cls._base_price(symbol)
        noise = random.gauss(0, base * 0.003)
        last = round(base + noise, 6)
        spread = base * random.uniform(0.0001, 0.0005)
        return {
            "symbol": symbol,
            "last": last,
            "bid": round(last - spread / 2, 6),
            "ask": round(last + spread / 2, 6),
            "high_24h": round(base * (1 + random.uniform(0.01, 0.05)), 6),
            "low_24h": round(base * (1 - random.uniform(0.01, 0.05)), 6),
            "volume_24h": round(random.uniform(50_000, 500_000), 2),
            "change_24h_pct": round(random.uniform(-5, 5), 2),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "simulated",
        }

    @classmethod
    def orderbook(cls, symbol: str, depth: int = 10) -> Dict[str, Any]:
        base = cls._base_price(symbol)
        spread = base * 0.0003
        mid = base + random.gauss(0, base * 0.001)

        bids, asks = [], []
        for i in range(depth):
            offset = spread * (i + 1) * random.uniform(0.8, 1.2)
            bid_price = round(mid - offset, 6)
            ask_price = round(mid + offset, 6)
            bid_size = round(random.uniform(0.01, 5.0), 4)
            ask_size = round(random.uniform(0.01, 5.0), 4)
            bids.append([bid_price, bid_size])
            asks.append([ask_price, ask_size])

        return {
            "symbol": symbol,
            "bids": bids,
            "asks": asks,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "simulated",
        }

    @classmethod
    def ohlcv(cls, symbol: str, timeframe: str = "1h", limit: int = 100) -> List[List[Any]]:
        """Generate OHLCV candles. Each candle: [timestamp_ms, open, high, low, close, volume]."""
        tf_minutes = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}
        interval_min = tf_minutes.get(timeframe, 60)

        base = cls._base_price(symbol)
        price = base * random.uniform(0.9, 1.1)
        candles: List[List[Any]] = []
        now = datetime.utcnow()
        start = now - timedelta(minutes=interval_min * limit)

        volatility = base * 0.005

        for i in range(limit):
            ts = start + timedelta(minutes=interval_min * i)
            ts_ms = int(ts.timestamp() * 1000)
            open_ = price
            moves = [random.gauss(0, volatility) for _ in range(4)]
            close_ = open_ + sum(moves)
            high_ = max(open_, close_) + abs(random.gauss(0, volatility * 0.5))
            low_ = min(open_, close_) - abs(random.gauss(0, volatility * 0.5))
            volume = round(random.uniform(10, 1000), 2)
            candles.append([
                ts_ms,
                round(open_, 6),
                round(high_, 6),
                round(low_, 6),
                round(close_, 6),
                volume,
            ])
            price = close_

        return candles


# ---------------------------------------------------------------------------
# Market Data Connector
# ---------------------------------------------------------------------------

class MarketDataConnector:
    """
    Unified market data interface.  Attempts ccxt for live data;
    falls back to SimulatedMarket when unavailable.
    """

    def __init__(self, exchange_id: str = "binance", api_key: Optional[str] = None,
                 api_secret: Optional[str] = None):
        self.exchange_id = exchange_id
        self._exchange = None
        self._subscribers: Dict[str, List[Callable]] = {}

        if CCXT_AVAILABLE and api_key:
            try:
                exchange_class = getattr(ccxt, exchange_id, None)
                if exchange_class:
                    self._exchange = exchange_class({
                        "apiKey": api_key,
                        "secret": api_secret,
                        "enableRateLimit": True,
                    })
                    logger.info(f"Exchange connected: {exchange_id}")
            except Exception as exc:
                logger.warning(f"Failed to connect exchange: {exc}")

    @property
    def is_live(self) -> bool:
        return self._exchange is not None

    # ------------------------------------------------------------------
    # Ticker
    # ------------------------------------------------------------------

    def get_ticker(self, symbol: str, exchange: Optional[str] = None) -> Dict[str, Any]:
        if self._exchange:
            try:
                t = self._exchange.fetch_ticker(symbol)
                return {
                    "symbol": symbol,
                    "last": t.get("last"),
                    "bid": t.get("bid"),
                    "ask": t.get("ask"),
                    "high_24h": t.get("high"),
                    "low_24h": t.get("low"),
                    "volume_24h": t.get("baseVolume"),
                    "change_24h_pct": t.get("percentage"),
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": self.exchange_id,
                }
            except Exception as exc:
                logger.warning(f"Live ticker failed for {symbol}: {exc}")

        return SimulatedMarket.ticker(symbol)

    # ------------------------------------------------------------------
    # Orderbook
    # ------------------------------------------------------------------

    def get_orderbook(self, symbol: str, exchange: Optional[str] = None,
                      depth: int = 10) -> Dict[str, Any]:
        if self._exchange:
            try:
                ob = self._exchange.fetch_order_book(symbol, depth)
                return {
                    "symbol": symbol,
                    "bids": ob.get("bids", [])[:depth],
                    "asks": ob.get("asks", [])[:depth],
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": self.exchange_id,
                }
            except Exception as exc:
                logger.warning(f"Live orderbook failed for {symbol}: {exc}")

        return SimulatedMarket.orderbook(symbol, depth)

    # ------------------------------------------------------------------
    # OHLCV
    # ------------------------------------------------------------------

    def get_ohlcv(self, symbol: str, exchange: Optional[str] = None,
                  timeframe: str = "1h", limit: int = 100) -> Dict[str, Any]:
        if self._exchange:
            try:
                candles = self._exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                return {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "candles": candles,
                    "count": len(candles),
                    "source": self.exchange_id,
                }
            except Exception as exc:
                logger.warning(f"Live OHLCV failed for {symbol}: {exc}")

        candles = SimulatedMarket.ohlcv(symbol, timeframe, limit)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": candles,
            "count": len(candles),
            "source": "simulated",
        }

    # ------------------------------------------------------------------
    # WebSocket subscription (placeholder / simulated)
    # ------------------------------------------------------------------

    def subscribe_ticker(self, symbol: str, callback: Callable) -> str:
        sub_id = f"{symbol}_{id(callback)}"
        self._subscribers.setdefault(symbol, []).append(callback)
        logger.info(f"Subscribed to ticker for {symbol} (id={sub_id})")
        return sub_id

    def unsubscribe_ticker(self, symbol: str, callback: Callable):
        subs = self._subscribers.get(symbol, [])
        if callback in subs:
            subs.remove(callback)

    async def _simulated_ticker_loop(self, symbol: str, interval: float = 1.0):
        """Push simulated tickers to all subscribers for a symbol."""
        while True:
            callbacks = self._subscribers.get(symbol, [])
            if not callbacks:
                break
            ticker = SimulatedMarket.ticker(symbol)
            for cb in callbacks:
                try:
                    cb(ticker)
                except Exception as exc:
                    logger.error(f"Subscriber callback error: {exc}")
            await asyncio.sleep(interval)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_connector = MarketDataConnector()


def get_live_data(symbol: str = "BTC/USDT") -> Dict[str, Any]:
    """Backwards-compatible convenience function."""
    return _connector.get_ticker(symbol)


# ---------------------------------------------------------------------------
# FastAPI REST endpoints
# ---------------------------------------------------------------------------

@router.get("/market/ticker/{symbol}")
async def ticker_endpoint(symbol: str, exchange: Optional[str] = None):
    return _connector.get_ticker(symbol.upper(), exchange)


@router.get("/market/orderbook/{symbol}")
async def orderbook_endpoint(symbol: str, exchange: Optional[str] = None,
                             depth: int = Query(default=10, ge=1, le=50)):
    return _connector.get_orderbook(symbol.upper(), exchange, depth)


@router.get("/market/ohlcv/{symbol}")
async def ohlcv_endpoint(symbol: str, exchange: Optional[str] = None,
                         timeframe: str = Query(default="1h"),
                         limit: int = Query(default=100, ge=1, le=1000)):
    return _connector.get_ohlcv(symbol.upper(), exchange, timeframe, limit)


@router.get("/market/status")
async def market_status_endpoint():
    return {
        "ccxt_available": CCXT_AVAILABLE,
        "exchange_connected": _connector.is_live,
        "exchange_id": _connector.exchange_id,
        "supported_symbols": list(SimulatedMarket._BASE.keys()),
    }


# ---------------------------------------------------------------------------
# WebSocket endpoint (simulated streaming)
# ---------------------------------------------------------------------------

@router.websocket("/ws/market")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    symbol = "BTC/USDT"

    try:
        # Check for initial configuration message
        try:
            init_msg = await asyncio.wait_for(websocket.receive_json(), timeout=2.0)
            symbol = init_msg.get("symbol", symbol).upper()
        except (asyncio.TimeoutError, Exception):
            pass

        logger.info(f"WebSocket stream started for {symbol}")

        while True:
            ticker = SimulatedMarket.ticker(symbol)
            await websocket.send_json(ticker)
            await asyncio.sleep(1.0)

    except Exception as exc:
        logger.info(f"WebSocket closed: {exc}")
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
