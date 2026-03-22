"""
On-Chain Data Module
====================
Free on-chain data from multiple sources (no API keys required):
  - Blockchain.com  — BTC stats, address info
  - Etherscan       — ETH price, gas price (basic free tier)
  - Mempool.space   — BTC fees, mempool stats
"""

import time
import logging
import requests

logger = logging.getLogger("Bruce.OnChainData")

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
#  HTTP helper
# ---------------------------------------------------------------------------
SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json", "User-Agent": "BruceAI/1.0"})
TIMEOUT = 15


def _get(url: str, params: dict = None):
    resp = SESSION.get(url, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ===================================================================
#  Blockchain.com — BTC on-chain stats
# ===================================================================

BLOCKCHAIN_BASE = "https://blockchain.info"


def get_btc_stats() -> dict:
    """Get BTC network stats: hashrate, difficulty, mempool size, block height, etc."""
    cached = _get_cached("btc_stats")
    if cached:
        return cached
    try:
        data = _get(f"{BLOCKCHAIN_BASE}/stats", params={"format": "json"})
        result = {
            "market_price_usd": data.get("market_price_usd"),
            "hash_rate_gh": round(data.get("hash_rate", 0), 2),
            "difficulty": data.get("difficulty"),
            "block_height": data.get("n_blocks_total"),
            "blocks_mined_24h": data.get("n_blocks_mined"),
            "minutes_between_blocks": round(data.get("minutes_between_blocks", 0), 2),
            "total_btc_sent_24h": data.get("total_btc_sent") / 1e8 if data.get("total_btc_sent") else None,
            "mempool_size": data.get("mempool_size"),
            "mempool_bytes": data.get("mempool_bytes"),
            "mempool_txs": data.get("mempool_count"),
            "unconfirmed_txs": data.get("n_tx"),
            "total_fees_btc_24h": data.get("total_fees_btc") / 1e8 if data.get("total_fees_btc") else None,
            "source": "blockchain.info",
        }
        _set_cache("btc_stats", result)
        return result
    except Exception as e:
        logger.error(f"get_btc_stats error: {e}")
        return {"error": str(e)}


def get_btc_address_info(address: str) -> dict:
    """Get BTC address balance and transaction count."""
    key = f"btc_addr_{address}"
    cached = _get_cached(key)
    if cached:
        return cached
    try:
        data = _get(f"{BLOCKCHAIN_BASE}/rawaddr/{address}", params={"limit": 0})
        result = {
            "address": address,
            "balance_btc": data.get("final_balance", 0) / 1e8,
            "total_received_btc": data.get("total_received", 0) / 1e8,
            "total_sent_btc": data.get("total_sent", 0) / 1e8,
            "tx_count": data.get("n_tx", 0),
            "source": "blockchain.info",
        }
        _set_cache(key, result)
        return result
    except Exception as e:
        logger.error(f"get_btc_address_info error: {e}")
        return {"error": str(e), "address": address}


# ===================================================================
#  Etherscan — ETH price & gas (free, no key needed for basic)
# ===================================================================

ETHERSCAN_BASE = "https://api.etherscan.io/api"


def get_eth_price() -> dict:
    """Get current ETH price in USD and BTC."""
    cached = _get_cached("eth_price")
    if cached:
        return cached
    try:
        data = _get(ETHERSCAN_BASE, params={"module": "stats", "action": "ethprice"})
        r = data.get("result", {})
        result = {
            "eth_usd": float(r.get("ethusd", 0)),
            "eth_btc": float(r.get("ethbtc", 0)),
            "timestamp": r.get("ethusd_timestamp", ""),
            "source": "etherscan",
        }
        _set_cache("eth_price", result)
        return result
    except Exception as e:
        logger.error(f"get_eth_price error: {e}")
        return {"error": str(e)}


def get_gas_price() -> dict:
    """Get current ETH gas price in gwei (safe, propose, fast)."""
    cached = _get_cached("eth_gas")
    if cached:
        return cached
    try:
        data = _get(ETHERSCAN_BASE, params={"module": "gastracker", "action": "gasoracle"})
        r = data.get("result", {})
        result = {
            "safe_gas_gwei": r.get("SafeGasPrice"),
            "propose_gas_gwei": r.get("ProposeGasPrice"),
            "fast_gas_gwei": r.get("FastGasPrice"),
            "suggested_base_fee": r.get("suggestBaseFee"),
            "source": "etherscan",
        }
        _set_cache("eth_gas", result)
        return result
    except Exception as e:
        logger.error(f"get_gas_price error: {e}")
        return {"error": str(e)}


# ===================================================================
#  Mempool.space — BTC fees & mempool
# ===================================================================

MEMPOOL_BASE = "https://mempool.space/api"


def get_btc_fees() -> dict:
    """Get recommended BTC transaction fees (sat/vB)."""
    cached = _get_cached("btc_fees")
    if cached:
        return cached
    try:
        data = _get(f"{MEMPOOL_BASE}/v1/fees/recommended")
        result = {
            "fastest_fee_sat_vb": data.get("fastestFee"),
            "half_hour_fee_sat_vb": data.get("halfHourFee"),
            "hour_fee_sat_vb": data.get("hourFee"),
            "economy_fee_sat_vb": data.get("economyFee"),
            "minimum_fee_sat_vb": data.get("minimumFee"),
            "source": "mempool.space",
        }
        _set_cache("btc_fees", result)
        return result
    except Exception as e:
        logger.error(f"get_btc_fees error: {e}")
        return {"error": str(e)}


def get_mempool_stats() -> dict:
    """Get BTC mempool statistics: size, tx count, fee histogram."""
    cached = _get_cached("mempool_stats")
    if cached:
        return cached
    try:
        data = _get(f"{MEMPOOL_BASE}/mempool")
        result = {
            "tx_count": data.get("count", 0),
            "total_vsize_bytes": data.get("vsize", 0),
            "total_fee_btc": data.get("total_fee", 0) / 1e8 if data.get("total_fee") else 0,
            "source": "mempool.space",
        }

        # Also grab fee histogram for richer data
        try:
            hist = _get(f"{MEMPOOL_BASE}/mempool/recent")
            if isinstance(hist, list):
                result["recent_txs_count"] = len(hist)
        except Exception:
            pass

        _set_cache("mempool_stats", result)
        return result
    except Exception as e:
        logger.error(f"get_mempool_stats error: {e}")
        return {"error": str(e)}


# ===================================================================
#  Convenience aggregator
# ===================================================================

def get_btc_onchain_summary() -> dict:
    """Aggregate BTC on-chain data from all sources."""
    stats = get_btc_stats()
    fees = get_btc_fees()
    mempool = get_mempool_stats()
    return {
        "network": stats,
        "fees": fees,
        "mempool": mempool,
        "source": "blockchain.info + mempool.space",
    }
