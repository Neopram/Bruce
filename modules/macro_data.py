"""
Bruce AI - Macro Economic Data Connector
==========================================
Free macro data from:
  - alternative.me (Crypto Fear & Greed)
  - Yahoo Finance via yfinance (VIX, DXY, Treasury yields)
  - FRED (if API key available)

All responses cached for 60 seconds.
"""

import logging
import time
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger("Bruce.MacroData")

REQUEST_TIMEOUT = 15
CACHE_TTL = 60


class _Cache:
    """Simple TTL cache."""

    def __init__(self, ttl: int = CACHE_TTL):
        self._store: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        ts = self._timestamps.get(key)
        if ts is not None and (time.time() - ts) < self._ttl:
            return self._store[key]
        self._store.pop(key, None)
        self._timestamps.pop(key, None)
        return None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value
        self._timestamps[key] = time.time()


_cache = _Cache()


def _yf_current(ticker_symbol: str) -> Optional[Dict]:
    """Fetch current data for a Yahoo Finance ticker using yfinance."""
    cache_key = f"yf|{ticker_symbol}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        import yfinance as yf

        ticker = yf.Ticker(ticker_symbol)
        info = ticker.fast_info
        # fast_info gives us lastPrice, previousClose, etc.
        result = {
            "last_price": getattr(info, "last_price", None),
            "previous_close": getattr(info, "previous_close", None),
            "open": getattr(info, "open", None),
            "day_high": getattr(info, "day_high", None),
            "day_low": getattr(info, "day_low", None),
        }
        # Calculate change
        if result["last_price"] and result["previous_close"]:
            change = result["last_price"] - result["previous_close"]
            change_pct = (change / result["previous_close"]) * 100
            result["change"] = round(change, 4)
            result["change_pct"] = round(change_pct, 2)

        _cache.set(cache_key, result)
        return result
    except ImportError:
        logger.error("yfinance not installed. Run: pip install yfinance")
        return None
    except Exception as e:
        logger.error(f"yfinance error for {ticker_symbol}: {e}")
        return None


def _yf_history(ticker_symbol: str, period: str = "5d") -> Optional[list]:
    """Fetch recent history for a ticker."""
    cache_key = f"yf_hist|{ticker_symbol}|{period}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        import yfinance as yf

        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return None
        records = []
        for date, row in hist.iterrows():
            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "close": round(row["Close"], 4),
                "open": round(row["Open"], 4),
                "high": round(row["High"], 4),
                "low": round(row["Low"], 4),
                "volume": int(row.get("Volume", 0)),
            })
        _cache.set(cache_key, records)
        return records
    except ImportError:
        return None
    except Exception as e:
        logger.error(f"yfinance history error for {ticker_symbol}: {e}")
        return None


# ===================================================================
#  Public API
# ===================================================================

def get_fear_greed() -> Dict:
    """Get the Crypto Fear & Greed Index from alternative.me.

    Returns:
        Dict with value (0-100), classification, timestamp
        0 = Extreme Fear, 100 = Extreme Greed
    """
    cache_key = "fear_greed"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            "https://api.alternative.me/fng/?limit=7&format=json",
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        entries = data.get("data", [])
        if not entries:
            return {"error": "No Fear & Greed data available"}

        current = entries[0]
        history = []
        for e in entries:
            history.append({
                "value": int(e.get("value", 0)),
                "classification": e.get("value_classification", ""),
                "timestamp": e.get("timestamp"),
            })

        result = {
            "current_value": int(current.get("value", 0)),
            "classification": current.get("value_classification", "Unknown"),
            "timestamp": current.get("timestamp"),
            "history_7d": history,
        }
        _cache.set(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"Fear & Greed fetch error: {e}")
        return {"error": str(e)}


def get_fed_rate() -> Dict:
    """Get the current Federal Funds Rate.

    Uses Yahoo Finance ticker ^IRX (13-week T-Bill) as a proxy,
    or FRED API if a key is available.

    Returns:
        Dict with rate value and metadata
    """
    cache_key = "fed_rate"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    # Try FRED API first if key is available
    import os
    fred_key = os.environ.get("FRED_API_KEY")
    if fred_key:
        try:
            resp = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": "FEDFUNDS",
                    "api_key": fred_key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 1,
                },
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            obs = data.get("observations", [])
            if obs:
                result = {
                    "rate": float(obs[0]["value"]),
                    "date": obs[0]["date"],
                    "source": "FRED",
                    "series": "FEDFUNDS",
                }
                _cache.set(cache_key, result)
                return result
        except Exception as e:
            logger.warning(f"FRED API failed, falling back to yfinance: {e}")

    # Fallback: use yfinance for 13-week T-Bill rate
    data = _yf_current("^IRX")
    if data and data.get("last_price") is not None:
        result = {
            "rate": round(data["last_price"], 2),
            "change": data.get("change"),
            "change_pct": data.get("change_pct"),
            "source": "Yahoo Finance (13-week T-Bill proxy)",
            "ticker": "^IRX",
            "note": "This is the 13-week T-Bill rate, a proxy for the Fed Funds rate.",
        }
        _cache.set(cache_key, result)
        return result

    return {"error": "Could not fetch Fed rate. Install yfinance or set FRED_API_KEY."}


def get_dxy() -> Dict:
    """Get the US Dollar Index (DXY).

    Returns:
        Dict with DXY value, change, and metadata
    """
    data = _yf_current("DX-Y.NYB")
    if data and data.get("last_price") is not None:
        return {
            "dxy": round(data["last_price"], 2),
            "previous_close": round(data.get("previous_close", 0) or 0, 2),
            "change": data.get("change"),
            "change_pct": data.get("change_pct"),
            "day_high": round(data.get("day_high", 0) or 0, 2),
            "day_low": round(data.get("day_low", 0) or 0, 2),
            "source": "Yahoo Finance",
            "ticker": "DX-Y.NYB",
        }
    return {"error": "Could not fetch DXY. Install yfinance: pip install yfinance"}


def get_treasury_yields() -> Dict:
    """Get current US Treasury yields (2Y, 5Y, 10Y, 30Y).

    Returns:
        Dict with yield values for each maturity
    """
    tickers = {
        "2Y": "^FVX",   # 5-year note yield (closest free proxy for 2Y is limited)
        "5Y": "^FVX",   # 5-year Treasury yield
        "10Y": "^TNX",  # 10-year Treasury yield
        "30Y": "^TYX",  # 30-year Treasury yield
    }

    # Better mapping using yfinance tickers
    yield_tickers = {
        "2Y": "2YY=F",   # 2-year yield futures
        "5Y": "^FVX",    # 5-year
        "10Y": "^TNX",   # 10-year
        "30Y": "^TYX",   # 30-year
    }

    results = {}
    for maturity, ticker in yield_tickers.items():
        data = _yf_current(ticker)
        if data and data.get("last_price") is not None:
            results[maturity] = {
                "yield_pct": round(data["last_price"], 3),
                "change": data.get("change"),
                "change_pct": data.get("change_pct"),
                "ticker": ticker,
            }
        else:
            results[maturity] = {"error": f"Could not fetch {maturity} yield"}

    # Calculate spread (10Y - 2Y)
    y10 = results.get("10Y", {}).get("yield_pct")
    y2 = results.get("2Y", {}).get("yield_pct")
    spread = None
    if y10 is not None and y2 is not None:
        spread = round(y10 - y2, 3)

    return {
        "yields": results,
        "spread_10y_2y": spread,
        "spread_signal": (
            "normal" if spread and spread > 0
            else "inverted (recession signal)" if spread and spread < 0
            else "flat"
        ) if spread is not None else "unknown",
        "source": "Yahoo Finance",
    }


def get_vix() -> Dict:
    """Get the CBOE Volatility Index (VIX).

    Returns:
        Dict with VIX value, change, and interpretation
    """
    data = _yf_current("^VIX")
    if data and data.get("last_price") is not None:
        vix = data["last_price"]
        # Interpretation
        if vix < 12:
            regime = "extremely_low"
            interpretation = "Market is extremely complacent. Historically low volatility."
        elif vix < 20:
            regime = "low"
            interpretation = "Market calm. Normal conditions."
        elif vix < 25:
            regime = "moderate"
            interpretation = "Elevated uncertainty. Market getting nervous."
        elif vix < 30:
            regime = "high"
            interpretation = "High fear. Significant market stress."
        else:
            regime = "extreme"
            interpretation = "Extreme fear/panic. Major market stress event."

        return {
            "vix": round(vix, 2),
            "previous_close": round(data.get("previous_close", 0) or 0, 2),
            "change": data.get("change"),
            "change_pct": data.get("change_pct"),
            "day_high": round(data.get("day_high", 0) or 0, 2),
            "day_low": round(data.get("day_low", 0) or 0, 2),
            "regime": regime,
            "interpretation": interpretation,
            "source": "Yahoo Finance",
            "ticker": "^VIX",
        }
    return {"error": "Could not fetch VIX. Install yfinance: pip install yfinance"}


def get_macro_summary() -> Dict:
    """Get a combined macro dashboard with all key indicators.

    Returns:
        Dict with fear_greed, vix, dxy, treasury_yields, and interpretation
    """
    fear_greed = get_fear_greed()
    vix = get_vix()
    dxy = get_dxy()
    yields = get_treasury_yields()
    fed_rate = get_fed_rate()

    # Build summary interpretation
    signals = []
    fg_val = fear_greed.get("current_value")
    vix_val = vix.get("vix")
    spread = yields.get("spread_10y_2y")

    if fg_val is not None:
        if fg_val < 25:
            signals.append("Crypto: EXTREME FEAR (potential buy zone)")
        elif fg_val > 75:
            signals.append("Crypto: EXTREME GREED (potential sell zone)")

    if vix_val is not None:
        if vix_val > 30:
            signals.append("Equities: EXTREME FEAR (VIX > 30)")
        elif vix_val < 15:
            signals.append("Equities: VERY CALM (VIX < 15)")

    if spread is not None and spread < 0:
        signals.append("Yield curve INVERTED: recession signal active")

    return {
        "fear_greed": fear_greed,
        "vix": vix,
        "dxy": dxy,
        "treasury_yields": yields,
        "fed_rate": fed_rate,
        "signals": signals if signals else ["No extreme signals detected"],
        "note": "Macro dashboard combining crypto, equity, and bond market indicators.",
    }
