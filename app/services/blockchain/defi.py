"""
DeFi Service - Pool information, impermanent loss estimation,
yield farming opportunities, and gas estimates.
"""

import math
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


_SUPPORTED_PROTOCOLS = ["uniswap_v3", "aave_v3", "curve", "lido", "compound", "balancer"]

_CHAIN_GAS_PROFILES = {
    "ethereum": {"base_gwei": 25, "range": (10, 150), "currency": "ETH"},
    "polygon": {"base_gwei": 30, "range": (20, 200), "currency": "MATIC"},
    "arbitrum": {"base_gwei": 0.1, "range": (0.05, 0.5), "currency": "ETH"},
    "optimism": {"base_gwei": 0.01, "range": (0.005, 0.05), "currency": "ETH"},
    "bsc": {"base_gwei": 3, "range": (1, 10), "currency": "BNB"},
    "avalanche": {"base_gwei": 25, "range": (20, 50), "currency": "AVAX"},
}

_YIELD_POOL_TEMPLATES = [
    {"protocol": "Uniswap V3", "pair": "ETH/USDC", "chain": "ethereum", "type": "LP"},
    {"protocol": "Aave V3", "pair": "USDC", "chain": "ethereum", "type": "lending"},
    {"protocol": "Curve", "pair": "3pool", "chain": "ethereum", "type": "stable_LP"},
    {"protocol": "Lido", "pair": "stETH", "chain": "ethereum", "type": "staking"},
    {"protocol": "Compound", "pair": "ETH", "chain": "ethereum", "type": "lending"},
    {"protocol": "Aave V3", "pair": "WBTC", "chain": "arbitrum", "type": "lending"},
    {"protocol": "Balancer", "pair": "wstETH/ETH", "chain": "ethereum", "type": "LP"},
    {"protocol": "Uniswap V3", "pair": "WBTC/ETH", "chain": "arbitrum", "type": "LP"},
]


class DeFiService:
    """Provides DeFi pool data, yield analytics, and gas estimates."""

    def get_pool_info(self, protocol: str, pool_address: str) -> dict:
        """
        Return information about a specific DeFi pool.

        In production this would query on-chain data; here we return
        realistic simulated data.
        """
        if protocol.lower() not in [p.replace("_", " ").lower() for p in _SUPPORTED_PROTOCOLS]:
            protocol_label = protocol
        else:
            protocol_label = protocol

        tvl = round(random.uniform(1_000_000, 500_000_000), 2)
        apr = round(random.uniform(0.5, 35.0), 2)
        volume_24h = round(random.uniform(100_000, tvl * 0.3), 2)

        return {
            "protocol": protocol_label,
            "pool_address": pool_address,
            "tvl_usd": tvl,
            "apr_pct": apr,
            "volume_24h_usd": volume_24h,
            "fee_tier": random.choice([0.01, 0.05, 0.3, 1.0]),
            "token_0": {"symbol": "TOKEN_A", "reserve": round(random.uniform(1000, 1_000_000), 2)},
            "token_1": {"symbol": "TOKEN_B", "reserve": round(random.uniform(1000, 1_000_000), 2)},
            "utilization_pct": round(random.uniform(20, 95), 2),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def estimate_impermanent_loss(
        self,
        token_a: str,
        token_b: str,
        price_change_pct: float,
    ) -> dict:
        """
        Estimate impermanent loss for an AMM position given a price
        change between the two tokens.

        Parameters
        ----------
        token_a, token_b : str
            Token symbols.
        price_change_pct : float
            Percentage price change of token_a relative to token_b
            (e.g., 50 means token_a rose 50%).
        """
        ratio = 1 + (price_change_pct / 100)
        if ratio <= 0:
            return {
                "token_a": token_a,
                "token_b": token_b,
                "error": "Price change would result in non-positive ratio",
            }

        # IL formula: IL = 2*sqrt(r) / (1+r) - 1
        il = 2 * math.sqrt(ratio) / (1 + ratio) - 1
        il_pct = round(il * 100, 4)

        return {
            "token_a": token_a,
            "token_b": token_b,
            "price_change_pct": price_change_pct,
            "impermanent_loss_pct": il_pct,
            "value_retained_pct": round((1 + il) * 100, 4),
            "note": (
                "Negative IL means the LP position is worth less than holding. "
                "Fees earned may offset this loss."
            ),
        }

    def get_yield_opportunities(self, min_apr: float = 0.0, limit: int = 10) -> List[dict]:
        """
        Return a list of simulated yield farming opportunities
        sorted by APR descending.
        """
        opportunities = []
        for tmpl in _YIELD_POOL_TEMPLATES:
            apr = round(random.uniform(0.5, 40.0), 2)
            if apr < min_apr:
                continue
            tvl = round(random.uniform(500_000, 200_000_000), 2)
            opportunities.append(
                {
                    "protocol": tmpl["protocol"],
                    "pair": tmpl["pair"],
                    "chain": tmpl["chain"],
                    "type": tmpl["type"],
                    "apr_pct": apr,
                    "tvl_usd": tvl,
                    "risk_level": (
                        "low" if tmpl["type"] in ("staking", "lending") and apr < 10
                        else "medium" if apr < 20
                        else "high"
                    ),
                }
            )

        opportunities.sort(key=lambda x: x["apr_pct"], reverse=True)
        return opportunities[:limit]

    def get_gas_estimate(self, chain: str = "ethereum") -> dict:
        """
        Return current gas estimates for a given chain (simulated).
        """
        chain_key = chain.lower()
        profile = _CHAIN_GAS_PROFILES.get(chain_key)
        if not profile:
            return {"chain": chain, "error": f"Unsupported chain. Supported: {list(_CHAIN_GAS_PROFILES.keys())}"}

        low = round(random.uniform(profile["range"][0], profile["base_gwei"]), 4)
        standard = round(random.uniform(profile["base_gwei"], profile["base_gwei"] * 1.5), 4)
        fast = round(random.uniform(profile["base_gwei"] * 1.5, profile["range"][1]), 4)

        swap_gas = 150_000
        transfer_gas = 21_000

        return {
            "chain": chain_key,
            "currency": profile["currency"],
            "gas_prices_gwei": {"low": low, "standard": standard, "fast": fast},
            "estimated_costs": {
                "simple_transfer": {
                    "gas_units": transfer_gas,
                    "cost_low": round(low * transfer_gas / 1e9, 6),
                    "cost_standard": round(standard * transfer_gas / 1e9, 6),
                    "cost_fast": round(fast * transfer_gas / 1e9, 6),
                },
                "token_swap": {
                    "gas_units": swap_gas,
                    "cost_low": round(low * swap_gas / 1e9, 6),
                    "cost_standard": round(standard * swap_gas / 1e9, 6),
                    "cost_fast": round(fast * swap_gas / 1e9, 6),
                },
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Legacy function kept for backward compatibility
async def execute_trade(symbol: str, eth_amount: float) -> dict:
    """Simulated trade execution (legacy interface)."""
    return {
        "status": "simulated",
        "symbol": symbol,
        "eth_amount": eth_amount,
        "tx_hash": f"0x{'0' * 64}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
