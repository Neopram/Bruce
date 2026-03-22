"""
Yahoo Finance Module
====================
Wraps yfinance for stocks, forex, commodities, indices, and historical data.
100% free, no API key required.
"""

import time
import logging
from typing import Optional

logger = logging.getLogger("Bruce.YahooFinance")

# ---------------------------------------------------------------------------
#  Cache
# ---------------------------------------------------------------------------
_cache: dict = {}
CACHE_TTL = 300  # 5 minutes


def _get_cached(key: str):
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None


def _set_cache(key: str, data):
    _cache[key] = {"data": data, "ts": time.time()}


# ---------------------------------------------------------------------------
#  Ticker aliases
# ---------------------------------------------------------------------------
COMMON_TICKERS = {
    # Indices
    "sp500": "^GSPC", "s&p500": "^GSPC", "s&p": "^GSPC",
    "dow": "^DJI", "dji": "^DJI", "dowjones": "^DJI",
    "nasdaq": "^IXIC", "ixic": "^IXIC",
    "russell": "^RUT", "russell2000": "^RUT",
    "vix": "^VIX",
    # Commodities
    "gold": "GC=F", "silver": "SI=F", "oil": "CL=F",
    "crude": "CL=F", "wti": "CL=F", "brent": "BZ=F",
    "natgas": "NG=F", "naturalgas": "NG=F",
    "copper": "HG=F", "platinum": "PL=F",
    # Forex
    "eurusd": "EURUSD=X", "gbpusd": "GBPUSD=X",
    "usdjpy": "USDJPY=X", "audusd": "AUDUSD=X",
    "usdcad": "USDCAD=X", "usdchf": "USDCHF=X",
    "dxy": "DX-Y.NYB",
    # Crypto
    "btc": "BTC-USD", "eth": "ETH-USD", "sol": "SOL-USD",
}


def _resolve_ticker(ticker: str) -> str:
    """Resolve common names to Yahoo Finance tickers."""
    cleaned = ticker.strip().lower().replace(" ", "").replace("/", "")
    if cleaned in COMMON_TICKERS:
        return COMMON_TICKERS[cleaned]
    # If it looks like a forex pair without =X suffix (e.g. EURUSD)
    if len(cleaned) == 6 and cleaned.isalpha() and "=" not in ticker:
        return f"{ticker.upper()}=X"
    return ticker.upper()


# ---------------------------------------------------------------------------
#  Core fetch helper
# ---------------------------------------------------------------------------

def _fetch_ticker_info(ticker: str) -> dict:
    """Fetch ticker data via yfinance."""
    import yfinance as yf
    resolved = _resolve_ticker(ticker)
    key = f"yf_{resolved}"
    cached = _get_cached(key)
    if cached:
        return cached

    t = yf.Ticker(resolved)
    info = t.info or {}

    result = {
        "ticker": resolved,
        "name": info.get("shortName") or info.get("longName", resolved),
        "price": info.get("regularMarketPrice") or info.get("currentPrice"),
        "previous_close": info.get("regularMarketPreviousClose") or info.get("previousClose"),
        "open": info.get("regularMarketOpen") or info.get("open"),
        "day_high": info.get("regularMarketDayHigh") or info.get("dayHigh"),
        "day_low": info.get("regularMarketDayLow") or info.get("dayLow"),
        "volume": info.get("regularMarketVolume") or info.get("volume"),
        "market_cap": info.get("marketCap"),
        "currency": info.get("currency", "USD"),
        "exchange": info.get("exchange", ""),
        "quote_type": info.get("quoteType", ""),
    }

    # Calculate change
    price = result["price"]
    prev = result["previous_close"]
    if price and prev and prev != 0:
        result["change"] = round(price - prev, 4)
        result["change_pct"] = round(((price - prev) / prev) * 100, 2)

    _set_cache(key, result)
    return result


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

def get_stock_price(ticker: str) -> dict:
    """Get current price for any stock, ETF, or index."""
    try:
        return _fetch_ticker_info(ticker)
    except Exception as e:
        logger.error(f"get_stock_price error for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


def get_forex_rate(pair: str) -> dict:
    """Get forex rate. Accepts: 'EURUSD', 'EUR/USD', 'eurusd', etc."""
    try:
        data = _fetch_ticker_info(pair)
        data["type"] = "forex"
        return data
    except Exception as e:
        logger.error(f"get_forex_rate error for {pair}: {e}")
        return {"error": str(e), "pair": pair}


def get_commodity_price(commodity: str) -> dict:
    """Get commodity price. Accepts: 'gold', 'oil', 'silver', 'natgas', 'copper', or futures ticker."""
    try:
        data = _fetch_ticker_info(commodity)
        data["type"] = "commodity"
        return data
    except Exception as e:
        logger.error(f"get_commodity_price error for {commodity}: {e}")
        return {"error": str(e), "commodity": commodity}


def get_index(index: str) -> dict:
    """Get market index value. Accepts: 'sp500', 'dow', 'nasdaq', 'vix', 'russell', or ticker."""
    try:
        data = _fetch_ticker_info(index)
        data["type"] = "index"
        return data
    except Exception as e:
        logger.error(f"get_index error for {index}: {e}")
        return {"error": str(e), "index": index}


def get_historical(ticker: str, period: str = "1mo") -> dict:
    """Get historical price data.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    """
    try:
        import yfinance as yf
        resolved = _resolve_ticker(ticker)
        t = yf.Ticker(resolved)
        hist = t.history(period=period)

        if hist.empty:
            return {"error": "No data returned", "ticker": resolved, "period": period}

        records = []
        for date, row in hist.iterrows():
            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 4),
                "high": round(row["High"], 4),
                "low": round(row["Low"], 4),
                "close": round(row["Close"], 4),
                "volume": int(row["Volume"]) if row["Volume"] else 0,
            })

        first_close = records[0]["close"] if records else 0
        last_close = records[-1]["close"] if records else 0
        change_pct = round(((last_close - first_close) / first_close) * 100, 2) if first_close else 0

        return {
            "ticker": resolved,
            "period": period,
            "data_points": len(records),
            "start_price": first_close,
            "end_price": last_close,
            "change_pct": change_pct,
            "high": round(hist["High"].max(), 4),
            "low": round(hist["Low"].min(), 4),
            "data": records[-30:] if len(records) > 30 else records,  # limit to last 30 for readability
        }
    except Exception as e:
        logger.error(f"get_historical error for {ticker}: {e}")
        return {"error": str(e), "ticker": ticker}


def get_earnings_calendar() -> dict:
    """Get upcoming earnings from major tickers."""
    try:
        import yfinance as yf
        # Check earnings for popular stocks
        watchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "JPM", "BAC", "WMT"]
        upcoming = []
        for sym in watchlist:
            try:
                t = yf.Ticker(sym)
                cal = t.calendar
                if cal is not None and not (hasattr(cal, 'empty') and cal.empty):
                    if isinstance(cal, dict):
                        upcoming.append({
                            "ticker": sym,
                            "earnings_date": str(cal.get("Earnings Date", [""])[0]) if isinstance(cal.get("Earnings Date"), list) else str(cal.get("Earnings Date", "")),
                            "eps_estimate": cal.get("EPS Estimate"),
                            "revenue_estimate": cal.get("Revenue Estimate"),
                        })
            except Exception:
                continue

        return {
            "earnings": upcoming,
            "count": len(upcoming),
            "watchlist": watchlist,
            "source": "Yahoo Finance",
        }
    except Exception as e:
        logger.error(f"get_earnings_calendar error: {e}")
        return {"error": str(e)}


def get_market_overview() -> dict:
    """Get a full market overview: major indices, VIX, gold, oil, BTC, ETH."""
    overview = {}
    targets = {
        "sp500": "^GSPC",
        "dow": "^DJI",
        "nasdaq": "^IXIC",
        "vix": "^VIX",
        "gold": "GC=F",
        "oil": "CL=F",
        "btc": "BTC-USD",
        "eth": "ETH-USD",
    }
    for label, ticker in targets.items():
        try:
            data = _fetch_ticker_info(ticker)
            overview[label] = {
                "price": data.get("price"),
                "change_pct": data.get("change_pct"),
                "name": data.get("name", label),
            }
        except Exception as e:
            overview[label] = {"error": str(e)}

    return {"market_overview": overview, "source": "Yahoo Finance"}
