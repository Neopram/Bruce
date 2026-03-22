"""
DeFi Data Module — DeFiLlama API
=================================
100% free, no API key required.
Provides TVL, protocol data, stablecoin stats, and yield farming opportunities.
"""

import time
import logging
import requests
from typing import Optional

logger = logging.getLogger("Bruce.DeFiData")

# ---------------------------------------------------------------------------
#  Simple in-memory cache
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
#  HTTP helper
# ---------------------------------------------------------------------------
BASE_URL = "https://api.llama.fi"
YIELDS_URL = "https://yields.llama.fi"
SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json", "User-Agent": "BruceAI/1.0"})
TIMEOUT = 15


def _get(url: str, params: dict = None) -> dict | list:
    """GET with timeout and error handling."""
    resp = SESSION.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------

def get_tvl_all() -> dict:
    """Get total TVL across all chains."""
    cached = _get_cached("tvl_all")
    if cached:
        return cached
    try:
        data = _get(f"{BASE_URL}/v2/historicalChainTvl")
        # Latest entry
        if isinstance(data, list) and data:
            latest = data[-1]
            result = {
                "total_tvl_usd": latest.get("tvl", 0),
                "date": latest.get("date", ""),
                "source": "DeFiLlama",
            }
        else:
            result = {"total_tvl_usd": data, "source": "DeFiLlama"}
        _set_cache("tvl_all", result)
        return result
    except Exception as e:
        logger.error(f"get_tvl_all error: {e}")
        return {"error": str(e)}


def get_protocol_tvl(protocol: str) -> dict:
    """Get TVL and details for a specific protocol (e.g. 'aave', 'uniswap', 'lido')."""
    key = f"proto_{protocol.lower()}"
    cached = _get_cached(key)
    if cached:
        return cached
    try:
        data = _get(f"{BASE_URL}/protocol/{protocol.lower()}")
        result = {
            "name": data.get("name", protocol),
            "symbol": data.get("symbol", ""),
            "tvl_usd": data.get("currentChainTvls", {}),
            "total_tvl": data.get("tvl", [{}])[-1].get("totalLiquidityUSD", 0) if data.get("tvl") else 0,
            "category": data.get("category", ""),
            "chains": data.get("chains", []),
            "url": data.get("url", ""),
            "description": data.get("description", "")[:200],
            "source": "DeFiLlama",
        }
        _set_cache(key, result)
        return result
    except Exception as e:
        logger.error(f"get_protocol_tvl error: {e}")
        return {"error": str(e), "protocol": protocol}


def get_chain_tvl(chain: str) -> dict:
    """Get TVL for a specific chain (e.g. 'ethereum', 'solana', 'arbitrum')."""
    key = f"chain_{chain.lower()}"
    cached = _get_cached(key)
    if cached:
        return cached
    try:
        data = _get(f"{BASE_URL}/v2/historicalChainTvl/{chain}")
        if isinstance(data, list) and data:
            latest = data[-1]
            result = {
                "chain": chain,
                "tvl_usd": latest.get("tvl", 0),
                "date": latest.get("date", ""),
                "source": "DeFiLlama",
            }
        else:
            result = {"chain": chain, "data": data, "source": "DeFiLlama"}
        _set_cache(key, result)
        return result
    except Exception as e:
        logger.error(f"get_chain_tvl error: {e}")
        return {"error": str(e), "chain": chain}


def get_top_protocols(limit: int = 20) -> dict:
    """Get top DeFi protocols by TVL."""
    cached = _get_cached("top_protocols")
    if cached:
        # Slice after cache hit in case limit differs
        cached["protocols"] = cached["protocols"][:limit]
        return cached
    try:
        data = _get(f"{BASE_URL}/protocols")
        if not isinstance(data, list):
            return {"error": "Unexpected response format", "source": "DeFiLlama"}

        # Sort by TVL descending
        sorted_protos = sorted(data, key=lambda p: p.get("tvl", 0) or 0, reverse=True)

        protocols = []
        for p in sorted_protos[:max(limit, 50)]:  # cache more than requested
            protocols.append({
                "name": p.get("name", ""),
                "symbol": p.get("symbol", ""),
                "tvl_usd": round(p.get("tvl", 0) or 0, 2),
                "category": p.get("category", ""),
                "chains": p.get("chains", []),
                "change_1d": p.get("change_1d"),
                "change_7d": p.get("change_7d"),
            })

        result = {"protocols": protocols, "count": len(protocols), "source": "DeFiLlama"}
        _set_cache("top_protocols", result)
        result["protocols"] = result["protocols"][:limit]
        return result
    except Exception as e:
        logger.error(f"get_top_protocols error: {e}")
        return {"error": str(e)}


def get_stablecoin_mcap() -> dict:
    """Get stablecoin market caps."""
    cached = _get_cached("stablecoin_mcap")
    if cached:
        return cached
    try:
        data = _get(f"{BASE_URL}/stablecoins?includePrices=true")
        stables = data.get("peggedAssets", [])
        result_list = []
        for s in stables[:20]:
            circulating = s.get("circulating", {})
            peg_usd = circulating.get("peggedUSD", 0) if isinstance(circulating, dict) else 0
            result_list.append({
                "name": s.get("name", ""),
                "symbol": s.get("symbol", ""),
                "mcap_usd": peg_usd,
                "peg_type": s.get("pegType", ""),
                "chains": s.get("chains", []),
            })
        result_list.sort(key=lambda x: x.get("mcap_usd", 0) or 0, reverse=True)
        result = {"stablecoins": result_list, "count": len(result_list), "source": "DeFiLlama"}
        _set_cache("stablecoin_mcap", result)
        return result
    except Exception as e:
        logger.error(f"get_stablecoin_mcap error: {e}")
        return {"error": str(e)}


def get_yields(pool_type: str = "stable") -> dict:
    """Get yield farming opportunities. pool_type: 'stable', 'all', or a specific project name."""
    key = f"yields_{pool_type}"
    cached = _get_cached(key)
    if cached:
        return cached
    try:
        data = _get(f"{YIELDS_URL}/pools")
        pools = data.get("data", [])

        # Filter
        if pool_type == "stable":
            pools = [p for p in pools if p.get("stablecoin", False)]
        elif pool_type != "all":
            pools = [p for p in pools if pool_type.lower() in (p.get("project", "") or "").lower()]

        # Sort by APY descending, take top 25
        pools.sort(key=lambda p: p.get("apy", 0) or 0, reverse=True)
        top = pools[:25]

        result_list = []
        for p in top:
            result_list.append({
                "pool": p.get("symbol", ""),
                "project": p.get("project", ""),
                "chain": p.get("chain", ""),
                "apy": round(p.get("apy", 0) or 0, 2),
                "tvl_usd": round(p.get("tvlUsd", 0) or 0, 2),
                "stablecoin": p.get("stablecoin", False),
            })

        result = {"yields": result_list, "count": len(result_list), "filter": pool_type, "source": "DeFiLlama"}
        _set_cache(key, result)
        return result
    except Exception as e:
        logger.error(f"get_yields error: {e}")
        return {"error": str(e)}
