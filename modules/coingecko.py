"""
Bruce AI - CoinGecko Data Connector
====================================
Free CoinGecko API (no key required).
Rate limit: 10-30 calls/min on free tier.
All responses cached for 60 seconds.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger("Bruce.CoinGecko")

BASE_URL = "https://api.coingecko.com/api/v3"
REQUEST_TIMEOUT = 15
CACHE_TTL = 60  # seconds


class _Cache:
    """Simple TTL cache for API responses."""

    def __init__(self, ttl: int = CACHE_TTL):
        self._store: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        ts = self._timestamps.get(key)
        if ts is not None and (time.time() - ts) < self._ttl:
            return self._store[key]
        # Expired — evict
        self._store.pop(key, None)
        self._timestamps.pop(key, None)
        return None

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value
        self._timestamps[key] = time.time()

    def clear(self) -> None:
        self._store.clear()
        self._timestamps.clear()


_cache = _Cache()

# Rate-limit tracking
_last_request_time: float = 0.0
_MIN_INTERVAL = 2.5  # seconds between requests (safe for free tier)


def _rate_limit() -> None:
    """Enforce minimum interval between requests."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)
    _last_request_time = time.time()


def _get(endpoint: str, params: Optional[dict] = None) -> Any:
    """Make a cached, rate-limited GET request to CoinGecko."""
    cache_key = f"{endpoint}|{json.dumps(params or {}, sort_keys=True)}"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    _rate_limit()
    url = f"{BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 429:
            logger.warning("CoinGecko rate limit hit, backing off 30s")
            time.sleep(30)
            resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        _cache.set(cache_key, data)
        return data
    except requests.exceptions.Timeout:
        logger.error(f"CoinGecko timeout: {endpoint}")
        return {"error": "Request timed out"}
    except requests.exceptions.HTTPError as e:
        logger.error(f"CoinGecko HTTP error: {e}")
        return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except requests.exceptions.RequestException as e:
        logger.error(f"CoinGecko request error: {e}")
        return {"error": str(e)}


# ===================================================================
#  Public API
# ===================================================================

def get_price(coin_id: str) -> Dict:
    """Get current price, market cap, volume, 24h change for a coin.

    Args:
        coin_id: CoinGecko coin id (e.g. 'bitcoin', 'ethereum', 'solana')

    Returns:
        Dict with price, market_cap, volume_24h, change_24h_pct, etc.
    """
    data = _get("/simple/price", {
        "ids": coin_id.lower(),
        "vs_currencies": "usd",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true",
        "include_last_updated_at": "true",
    })
    if "error" in data:
        return data

    coin_data = data.get(coin_id.lower())
    if not coin_data:
        return {"error": f"Coin '{coin_id}' not found. Use CoinGecko IDs (e.g. 'bitcoin', 'ethereum')."}

    return {
        "coin_id": coin_id.lower(),
        "price_usd": coin_data.get("usd"),
        "market_cap_usd": coin_data.get("usd_market_cap"),
        "volume_24h_usd": coin_data.get("usd_24h_vol"),
        "change_24h_pct": round(coin_data.get("usd_24h_change", 0) or 0, 2),
        "last_updated": coin_data.get("last_updated_at"),
    }


def get_prices(coin_ids: List[str]) -> Dict:
    """Get prices for multiple coins at once.

    Args:
        coin_ids: List of CoinGecko coin ids

    Returns:
        Dict mapping coin_id -> price data
    """
    ids_str = ",".join(c.lower() for c in coin_ids)
    data = _get("/simple/price", {
        "ids": ids_str,
        "vs_currencies": "usd",
        "include_market_cap": "true",
        "include_24hr_vol": "true",
        "include_24hr_change": "true",
    })
    if "error" in data:
        return data

    results = {}
    for coin_id in coin_ids:
        cid = coin_id.lower()
        coin_data = data.get(cid)
        if coin_data:
            results[cid] = {
                "price_usd": coin_data.get("usd"),
                "market_cap_usd": coin_data.get("usd_market_cap"),
                "volume_24h_usd": coin_data.get("usd_24h_vol"),
                "change_24h_pct": round(coin_data.get("usd_24h_change", 0) or 0, 2),
            }
        else:
            results[cid] = {"error": "not found"}
    return {"prices": results, "count": len(results)}


def get_historical(coin_id: str, days: int = 30) -> Dict:
    """Get historical price data for a coin.

    Args:
        coin_id: CoinGecko coin id
        days: Number of days of history (1, 7, 14, 30, 90, 180, 365, max)

    Returns:
        Dict with list of [timestamp, price] pairs
    """
    data = _get(f"/coins/{coin_id.lower()}/market_chart", {
        "vs_currency": "usd",
        "days": str(days),
    })
    if "error" in data:
        return data

    prices = data.get("prices", [])
    return {
        "coin_id": coin_id.lower(),
        "days": days,
        "data_points": len(prices),
        "prices": [
            {"timestamp": int(p[0] / 1000), "price": round(p[1], 2)}
            for p in prices
        ],
        "current": round(prices[-1][1], 2) if prices else None,
        "start": round(prices[0][1], 2) if prices else None,
        "change_pct": round(
            ((prices[-1][1] - prices[0][1]) / prices[0][1]) * 100, 2
        ) if prices and prices[0][1] else None,
    }


def get_trending() -> Dict:
    """Get trending coins on CoinGecko (based on search popularity).

    Returns:
        Dict with list of trending coins
    """
    data = _get("/search/trending")
    if "error" in data:
        return data

    coins = data.get("coins", [])
    trending = []
    for item in coins:
        coin = item.get("item", {})
        trending.append({
            "id": coin.get("id"),
            "name": coin.get("name"),
            "symbol": coin.get("symbol"),
            "market_cap_rank": coin.get("market_cap_rank"),
            "price_btc": coin.get("price_btc"),
            "score": coin.get("score"),
        })
    return {"trending": trending, "count": len(trending)}


def get_fear_greed_index() -> Dict:
    """Get the Crypto Fear & Greed Index from alternative.me.

    Returns:
        Dict with value (0-100), classification, and timestamp
    """
    cache_key = "fear_greed_index"
    cached = _cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.get(
            "https://api.alternative.me/fng/?limit=1&format=json",
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        entry = data.get("data", [{}])[0]
        result = {
            "value": int(entry.get("value", 0)),
            "classification": entry.get("value_classification", "Unknown"),
            "timestamp": entry.get("timestamp"),
            "time_until_update": entry.get("time_until_update"),
        }
        _cache.set(cache_key, result)
        return result
    except Exception as e:
        logger.error(f"Fear & Greed fetch error: {e}")
        return {"error": str(e)}


def get_top_coins(limit: int = 100) -> Dict:
    """Get top coins by market cap.

    Args:
        limit: Number of coins (max 250 per page)

    Returns:
        Dict with list of top coins and their data
    """
    limit = min(limit, 250)
    data = _get("/coins/markets", {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": str(limit),
        "page": "1",
        "sparkline": "false",
        "price_change_percentage": "24h,7d",
    })
    if "error" in data:
        return data
    if not isinstance(data, list):
        return {"error": "Unexpected response format", "raw": str(data)[:200]}

    coins = []
    for c in data:
        coins.append({
            "rank": c.get("market_cap_rank"),
            "id": c.get("id"),
            "symbol": c.get("symbol", "").upper(),
            "name": c.get("name"),
            "price_usd": c.get("current_price"),
            "market_cap": c.get("market_cap"),
            "volume_24h": c.get("total_volume"),
            "change_24h_pct": round(c.get("price_change_percentage_24h", 0) or 0, 2),
            "change_7d_pct": round(
                c.get("price_change_percentage_7d_in_currency", 0) or 0, 2
            ),
            "ath": c.get("ath"),
            "ath_change_pct": round(c.get("ath_change_percentage", 0) or 0, 2),
        })
    return {"coins": coins, "count": len(coins)}


def search_coin(query: str) -> Dict:
    """Search for a coin by name or symbol.

    Args:
        query: Search term (e.g. 'bitcoin', 'btc', 'sol')

    Returns:
        Dict with matching coins
    """
    data = _get("/search", {"query": query})
    if "error" in data:
        return data

    coins = data.get("coins", [])
    results = []
    for c in coins[:10]:
        results.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "symbol": c.get("symbol"),
            "market_cap_rank": c.get("market_cap_rank"),
            "thumb": c.get("thumb"),
        })
    return {"results": results, "count": len(results), "query": query}
