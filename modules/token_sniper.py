"""
Token Sniper Module for Bruce AI
=================================
Production-grade token sniping intelligence system.

Detects new token launches, analyzes contract safety, evaluates snipe
opportunities, and tracks trending tokens across Solana and Ethereum.

All APIs are FREE (no keys required):
  - DexScreener    : https://api.dexscreener.com
  - GeckoTerminal  : https://api.geckoterminal.com/api/v2
  - GoPlus Security : https://api.gopluslabs.io

Inspired by how Banana Gun, Maestro Bot, and Unibot operate:
  - Real-time new pair detection via DEX factory monitoring
  - Multi-layer contract safety analysis (honeypot, mint, rug)
  - MEV-aware entry/exit evaluation
  - Paper mode by default (simulate, never execute without explicit approval)

Author: Bruce AI Training Module
"""

import time
import logging
import hashlib
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

import requests

logger = logging.getLogger("Bruce.TokenSniper")

# ---------------------------------------------------------------------------
#  Constants
# ---------------------------------------------------------------------------

DEXSCREENER_BASE = "https://api.dexscreener.com"
GECKOTERMINAL_BASE = "https://api.geckoterminal.com/api/v2"
GOPLUS_BASE = "https://api.gopluslabs.io/api/v1"

# GoPlus chain IDs for token security checks
GOPLUS_CHAIN_IDS = {
    "ethereum": "1",
    "eth": "1",
    "bsc": "56",
    "polygon": "137",
    "arbitrum": "42161",
    "base": "8453",
    "avalanche": "43114",
    "fantom": "250",
    "optimism": "10",
    "cronos": "25",
    "solana": "solana",
    "sol": "solana",
}

# GeckoTerminal network slugs
GECKO_NETWORKS = {
    "ethereum": "eth",
    "eth": "eth",
    "solana": "solana",
    "sol": "solana",
    "bsc": "bsc",
    "base": "base",
    "arbitrum": "arbitrum",
    "polygon": "polygon_pos",
    "avalanche": "avax",
    "optimism": "optimism",
}

# DexScreener chain slugs
DEXSCREENER_CHAINS = {
    "ethereum": "ethereum",
    "eth": "ethereum",
    "solana": "solana",
    "sol": "solana",
    "bsc": "bsc",
    "base": "base",
    "arbitrum": "arbitrum",
    "polygon": "polygon",
    "avalanche": "avalanche",
    "optimism": "optimism",
}

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sniper")
os.makedirs(DATA_DIR, exist_ok=True)


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TokenSafetyReport:
    """Full safety analysis for a token."""
    address: str
    chain: str
    name: str = ""
    symbol: str = ""
    # Contract checks
    is_verified: bool = False
    is_open_source: bool = False
    is_proxy: bool = False
    has_mint_function: bool = False
    can_owner_change_balance: bool = False
    owner_can_pause: bool = False
    has_blacklist: bool = False
    has_whitelist: bool = False
    is_honeypot: bool = False
    honeypot_reason: str = ""
    # Tax analysis
    buy_tax_pct: float = 0.0
    sell_tax_pct: float = 0.0
    # Liquidity
    total_liquidity_usd: float = 0.0
    lp_locked: bool = False
    lp_lock_pct: float = 0.0
    # Holder distribution
    holder_count: int = 0
    top_holder_pct: float = 0.0
    creator_pct: float = 0.0
    # Risk scoring
    rug_score: int = 50  # 0 = safe, 100 = certain rug
    risk_level: str = RiskLevel.MEDIUM
    red_flags: List[str] = field(default_factory=list)
    green_flags: List[str] = field(default_factory=list)
    # Metadata
    analyzed_at: str = ""
    source: str = "goplus"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SnipeOpportunity:
    """A potential sniping opportunity with entry/exit criteria."""
    token_address: str
    chain: str
    token_name: str = ""
    token_symbol: str = ""
    pair_address: str = ""
    dex: str = ""
    # Market data
    price_usd: float = 0.0
    liquidity_usd: float = 0.0
    volume_24h: float = 0.0
    market_cap: float = 0.0
    age_minutes: float = 0.0
    # Safety
    rug_score: int = 50
    risk_level: str = RiskLevel.MEDIUM
    # Decision
    action: str = "SKIP"  # SNIPE, WATCH, SKIP
    reason: str = ""
    confidence: float = 0.0  # 0.0 - 1.0
    # Position sizing (paper mode)
    suggested_entry_pct: float = 0.0  # % of portfolio
    take_profit_pct: float = 100.0
    stop_loss_pct: float = 50.0
    time_exit_minutes: int = 60
    # Metadata
    detected_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
#  HTTP Session (shared, cached)
# ---------------------------------------------------------------------------

_cache: Dict[str, dict] = {}
CACHE_TTL = 60  # 1 minute for sniper data (needs freshness)

SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/json",
    "User-Agent": "BruceAI-Sniper/1.0",
})
TIMEOUT = 15


def _get_cached(key: str, ttl: int = CACHE_TTL) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < ttl:
        return entry["data"]
    return None


def _set_cache(key: str, data: Any):
    _cache[key] = {"data": data, "ts": time.time()}


def _http_get(url: str, params: dict = None) -> Any:
    """HTTP GET with timeout and error handling."""
    try:
        resp = SESSION.get(url, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        logger.warning(f"Timeout fetching {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.warning(f"HTTP {e.response.status_code} from {url}")
        return None
    except Exception as e:
        logger.error(f"Request error for {url}: {e}")
        return None


# ===================================================================
#  1. NewTokenDetector
# ===================================================================

class NewTokenDetector:
    """
    Detect new token launches across chains using free APIs.

    Strategy (mirrors how Banana Gun / Maestro detect launches):
    1. Poll GeckoTerminal /new_pools endpoint for freshly created pairs
    2. Poll DexScreener token profiles for newly boosted tokens
    3. Cross-reference to find tokens that just received initial liquidity
    4. Filter by chain, liquidity floor, and age

    This does NOT monitor raw blockchain transactions (would need paid RPC).
    Instead, it uses aggregator APIs that index DEX factory events.
    """

    def __init__(self):
        self.seen_pairs: set = set()  # track already-seen pair addresses
        self._load_seen()

    def _load_seen(self):
        """Load previously seen pairs from disk to avoid duplicate alerts."""
        path = os.path.join(DATA_DIR, "seen_pairs.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    self.seen_pairs = set(json.load(f))
            except Exception:
                pass

    def _save_seen(self):
        """Persist seen pairs."""
        path = os.path.join(DATA_DIR, "seen_pairs.json")
        try:
            # Keep only last 5000 to prevent unbounded growth
            recent = list(self.seen_pairs)[-5000:]
            with open(path, "w") as f:
                json.dump(recent, f)
        except Exception as e:
            logger.warning(f"Could not save seen pairs: {e}")

    def scan_new_pairs_gecko(
        self,
        chain: str = "solana",
        max_results: int = 20,
    ) -> List[dict]:
        """
        Fetch newly created pools from GeckoTerminal.

        GeckoTerminal indexes DEX factory contract events
        (e.g., Raydium's initialize_market, Uniswap's PairCreated)
        and surfaces them via the /new_pools endpoint.

        Rate limit: 30 req/min (free tier).
        """
        network = GECKO_NETWORKS.get(chain.lower(), chain.lower())
        cache_key = f"gecko_new_{network}"
        cached = _get_cached(cache_key, ttl=30)
        if cached:
            return cached

        url = f"{GECKOTERMINAL_BASE}/networks/{network}/new_pools"
        data = _http_get(url, params={"page": 1})

        if not data or "data" not in data:
            return []

        results = []
        for pool in data["data"][:max_results]:
            attrs = pool.get("attributes", {})
            pool_addr = attrs.get("address", "")

            # Extract base token info
            base_token = attrs.get("base_token", {}) or {}
            quote_token = attrs.get("quote_token", {}) or {}

            # Calculate age
            created_at = attrs.get("pool_created_at", "")
            age_minutes = 0
            if created_at:
                try:
                    created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    age_minutes = (datetime.now(timezone.utc) - created_dt).total_seconds() / 60
                except Exception:
                    pass

            entry = {
                "pool_address": pool_addr,
                "chain": chain,
                "network": network,
                "dex": attrs.get("dex_id", ""),
                "base_token_name": base_token.get("name", attrs.get("name", "")),
                "base_token_symbol": base_token.get("symbol", attrs.get("symbol", "")),
                "base_token_address": base_token.get("address", ""),
                "quote_token_symbol": quote_token.get("symbol", ""),
                "price_usd": _safe_float(attrs.get("base_token_price_usd")),
                "volume_24h_usd": _safe_float(attrs.get("volume_usd", {}).get("h24", 0)),
                "liquidity_usd": _safe_float(
                    attrs.get("reserve_in_usd", 0)
                ),
                "price_change_1h_pct": _safe_float(
                    attrs.get("price_change_percentage", {}).get("h1", 0)
                ),
                "transactions_1h": attrs.get("transactions", {}).get("h1", {}),
                "age_minutes": round(age_minutes, 1),
                "created_at": created_at,
                "is_new": pool_addr not in self.seen_pairs,
                "source": "geckoterminal",
            }
            results.append(entry)

            # Track as seen
            if pool_addr:
                self.seen_pairs.add(pool_addr)

        self._save_seen()
        _set_cache(cache_key, results, )
        return results

    def scan_new_pairs_dexscreener(
        self,
        chain: str = "solana",
        max_results: int = 20,
    ) -> List[dict]:
        """
        Fetch latest token profiles from DexScreener.

        DexScreener monitors DEX factory contracts and indexes
        new pair creation events across all supported chains.

        Rate limit: 300 req/min (free, no key).
        """
        chain_slug = DEXSCREENER_CHAINS.get(chain.lower(), chain.lower())
        cache_key = f"dexs_profiles_{chain_slug}"
        cached = _get_cached(cache_key, ttl=30)
        if cached:
            return cached

        # DexScreener: get latest token profiles
        url = f"{DEXSCREENER_BASE}/token-profiles/latest/v1"
        data = _http_get(url)

        if not data or not isinstance(data, list):
            return []

        results = []
        for token in data:
            if token.get("chainId", "").lower() != chain_slug:
                continue
            if len(results) >= max_results:
                break

            addr = token.get("tokenAddress", "")
            entry = {
                "token_address": addr,
                "chain": chain,
                "description": token.get("description", ""),
                "icon": token.get("icon", ""),
                "links": token.get("links", []),
                "is_new": addr not in self.seen_pairs,
                "source": "dexscreener",
            }
            results.append(entry)
            if addr:
                self.seen_pairs.add(addr)

        self._save_seen()
        _set_cache(cache_key, results)
        return results

    def scan_all(self, chain: str = "solana", max_results: int = 20) -> dict:
        """
        Run all detection methods and merge results.

        This is the primary entry point, combining:
        1. GeckoTerminal new pools (has liquidity/volume data)
        2. DexScreener token profiles (has social/metadata)
        """
        gecko_pairs = self.scan_new_pairs_gecko(chain, max_results)
        dex_profiles = self.scan_new_pairs_dexscreener(chain, max_results)

        new_only = [p for p in gecko_pairs if p.get("is_new")]

        return {
            "chain": chain,
            "total_new_pools": len(gecko_pairs),
            "unseen_pools": len(new_only),
            "dexscreener_profiles": len(dex_profiles),
            "new_pools": gecko_pairs,
            "profiles": dex_profiles,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }


# ===================================================================
#  2. TokenAnalyzer
# ===================================================================

class TokenAnalyzer:
    """
    Analyze token safety using GoPlus Security API (free, no key).

    Checks performed (mirrors Banana Gun / Maestro anti-rug systems):
    1. Contract verification & open source status
    2. Honeypot detection (can you sell?)
    3. Mint function (can creator print infinite tokens?)
    4. Owner privileges (pause, blacklist, balance manipulation)
    5. Tax analysis (buy/sell fees)
    6. Liquidity lock status
    7. Holder distribution (whale concentration)
    8. Proxy/upgradeable contract detection

    Scoring: 0 = perfectly safe, 100 = certain rug pull.
    """

    def analyze_token(
        self,
        address: str,
        chain: str = "ethereum",
    ) -> TokenSafetyReport:
        """
        Run full safety analysis on a token via GoPlus Security API.

        GoPlus provides the same underlying data that Banana Gun and
        Maestro use for their anti-rug features:
        - Simulates buy/sell to detect honeypots
        - Decompiles bytecode to find mint/pause/blacklist functions
        - Checks LP lock status across known locker contracts
        - Analyzes holder distribution from on-chain data
        """
        report = TokenSafetyReport(
            address=address,
            chain=chain,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
        )

        # Resolve GoPlus chain ID
        chain_id = GOPLUS_CHAIN_IDS.get(chain.lower())
        if not chain_id:
            report.red_flags.append(f"Unsupported chain: {chain}")
            report.rug_score = 100
            report.risk_level = RiskLevel.CRITICAL
            return report

        # Handle Solana separately (different endpoint)
        if chain_id == "solana":
            return self._analyze_solana_token(address, report)

        # EVM chains: GoPlus Token Security API
        return self._analyze_evm_token(address, chain_id, report)

    def _analyze_evm_token(
        self,
        address: str,
        chain_id: str,
        report: TokenSafetyReport,
    ) -> TokenSafetyReport:
        """Analyze an EVM token (ETH, BSC, Base, etc.) via GoPlus."""
        cache_key = f"goplus_{chain_id}_{address.lower()}"
        cached = _get_cached(cache_key, ttl=120)

        if cached:
            data = cached
        else:
            url = f"{GOPLUS_BASE}/token_security/{chain_id}"
            data = _http_get(url, params={"contract_addresses": address.lower()})
            if data:
                _set_cache(cache_key, data)

        if not data or "result" not in data:
            report.red_flags.append("Could not fetch security data from GoPlus")
            report.rug_score = 75
            report.risk_level = RiskLevel.HIGH
            return report

        result = data["result"]
        token_data = result.get(address.lower(), {})

        if not token_data:
            report.red_flags.append("Token not found in GoPlus database")
            report.rug_score = 80
            report.risk_level = RiskLevel.HIGH
            return report

        # Parse token metadata
        report.name = token_data.get("token_name", "")
        report.symbol = token_data.get("token_symbol", "")

        # Contract checks
        report.is_open_source = _bool(token_data.get("is_open_source"))
        report.is_proxy = _bool(token_data.get("is_proxy"))
        report.has_mint_function = _bool(token_data.get("is_mintable"))
        report.can_owner_change_balance = _bool(token_data.get("can_take_back_ownership"))
        report.owner_can_pause = _bool(token_data.get("transfer_pausable"))
        report.has_blacklist = _bool(token_data.get("is_blacklisted"))
        report.has_whitelist = _bool(token_data.get("is_whitelisted"))

        # Honeypot
        report.is_honeypot = _bool(token_data.get("is_honeypot"))
        if report.is_honeypot:
            report.honeypot_reason = token_data.get("honeypot_with_same_creator", "Honeypot detected")

        # Taxes
        report.buy_tax_pct = _safe_float(token_data.get("buy_tax")) * 100
        report.sell_tax_pct = _safe_float(token_data.get("sell_tax")) * 100

        # Liquidity
        report.total_liquidity_usd = _safe_float(token_data.get("total_supply", 0))
        lp_holders = token_data.get("lp_holders", [])
        report.lp_locked = any(
            _bool(lp.get("is_locked")) for lp in lp_holders
        ) if lp_holders else False
        if lp_holders:
            locked_pct = sum(
                _safe_float(lp.get("percent", 0))
                for lp in lp_holders if _bool(lp.get("is_locked"))
            )
            report.lp_lock_pct = round(locked_pct * 100, 2)

        # Holders
        report.holder_count = int(token_data.get("holder_count", 0))
        holders = token_data.get("holders", [])
        if holders:
            report.top_holder_pct = _safe_float(holders[0].get("percent", 0)) * 100
        creator = token_data.get("creator_percent", "0")
        report.creator_pct = _safe_float(creator) * 100

        # Calculate rug score
        report = self._calculate_rug_score(report)
        return report

    def _analyze_solana_token(
        self,
        address: str,
        report: TokenSafetyReport,
    ) -> TokenSafetyReport:
        """
        Analyze a Solana token via GoPlus Solana endpoint.

        Solana tokens have different risk factors:
        - Mint authority (can create new tokens)
        - Freeze authority (can freeze your tokens)
        - Metadata mutability
        """
        cache_key = f"goplus_solana_{address}"
        cached = _get_cached(cache_key, ttl=120)

        if cached:
            data = cached
        else:
            url = f"{GOPLUS_BASE}/solana/token_security"
            data = _http_get(url, params={"contract_addresses": address})
            if data:
                _set_cache(cache_key, data)

        if not data or "result" not in data:
            # Fallback: try GeckoTerminal for basic data
            return self._analyze_via_geckoterminal(address, "solana", report)

        result = data["result"]
        token_data = result.get(address, {})

        if not token_data:
            return self._analyze_via_geckoterminal(address, "solana", report)

        report.name = token_data.get("token_name", "")
        report.symbol = token_data.get("token_symbol", "")

        # Solana-specific checks
        # Mint authority = can mint new tokens
        mint_auth = token_data.get("mintable", {})
        report.has_mint_function = _bool(mint_auth.get("status"))

        # Freeze authority = can freeze trading
        freeze_auth = token_data.get("freezeable", {})
        report.owner_can_pause = _bool(freeze_auth.get("status"))

        # Metadata
        metadata_mutable = token_data.get("metadata_mutable", {})
        if _bool(metadata_mutable.get("status")):
            report.red_flags.append("Metadata is mutable (can change token info)")

        # Holders and creator
        report.holder_count = int(token_data.get("holder_count", 0))
        report.creator_pct = _safe_float(token_data.get("creator_percent", 0)) * 100

        # Top holders
        holders = token_data.get("holders", [])
        if holders:
            report.top_holder_pct = _safe_float(holders[0].get("percent", 0)) * 100

        report = self._calculate_rug_score(report)
        return report

    def _analyze_via_geckoterminal(
        self,
        address: str,
        chain: str,
        report: TokenSafetyReport,
    ) -> TokenSafetyReport:
        """
        Fallback analysis using GeckoTerminal pool data.
        Less detailed than GoPlus but provides liquidity and volume data.
        """
        network = GECKO_NETWORKS.get(chain.lower(), chain.lower())
        url = f"{GECKOTERMINAL_BASE}/networks/{network}/tokens/{address}"
        data = _http_get(url)

        if not data or "data" not in data:
            report.red_flags.append("Token not found on GeckoTerminal")
            report.rug_score = 80
            report.risk_level = RiskLevel.HIGH
            return report

        attrs = data["data"].get("attributes", {})
        report.name = attrs.get("name", "")
        report.symbol = attrs.get("symbol", "")
        report.source = "geckoterminal"

        # Basic metrics only from GeckoTerminal
        report.red_flags.append("Limited analysis (GoPlus data unavailable, using GeckoTerminal)")

        # Still calculate a basic score
        report = self._calculate_rug_score(report)
        return report

    def _calculate_rug_score(self, report: TokenSafetyReport) -> TokenSafetyReport:
        """
        Calculate a rug pull risk score (0 = safe, 100 = certain rug).

        Scoring weights are calibrated based on common rug pull patterns
        documented by Banana Gun, Maestro, and security researchers:

        Critical (20 pts each):
          - Honeypot detected
          - Mint function exists

        High (15 pts each):
          - Owner can pause trading
          - Owner can change balances
          - Sell tax > 10%
          - Not open source / not verified

        Medium (10 pts each):
          - Proxy/upgradeable contract
          - Has blacklist function
          - LP not locked
          - Top holder > 20%

        Positive deductions (-5 to -15 pts):
          - Contract is open source
          - LP locked
          - Holder count > 100
          - Low buy/sell tax
        """
        score = 0
        red_flags = report.red_flags
        green_flags = report.green_flags

        # Critical risks
        if report.is_honeypot:
            score += 20
            red_flags.append("HONEYPOT: Cannot sell tokens")
        if report.has_mint_function:
            score += 20
            red_flags.append("MINT: Creator can print unlimited tokens")

        # High risks
        if report.owner_can_pause:
            score += 15
            red_flags.append("PAUSE: Owner can freeze trading")
        if report.can_owner_change_balance:
            score += 15
            red_flags.append("BALANCE: Owner can modify balances")
        if report.sell_tax_pct > 10:
            score += 15
            red_flags.append(f"HIGH TAX: {report.sell_tax_pct:.1f}% sell tax")
        if not report.is_open_source:
            score += 15
            red_flags.append("UNVERIFIED: Contract source not verified")

        # Medium risks
        if report.is_proxy:
            score += 10
            red_flags.append("PROXY: Upgradeable contract (logic can change)")
        if report.has_blacklist:
            score += 10
            red_flags.append("BLACKLIST: Contract has blacklist function")
        if not report.lp_locked:
            score += 10
            red_flags.append("LP UNLOCKED: Liquidity not locked")
        if report.top_holder_pct > 20:
            score += 10
            red_flags.append(f"WHALE: Top holder owns {report.top_holder_pct:.1f}%")
        if report.creator_pct > 10:
            score += 10
            red_flags.append(f"CREATOR: Creator holds {report.creator_pct:.1f}%")

        # Moderate risks
        if report.buy_tax_pct > 5:
            score += 5
            red_flags.append(f"BUY TAX: {report.buy_tax_pct:.1f}%")
        if report.has_whitelist:
            score += 5
            red_flags.append("WHITELIST: Selective trading access")

        # Positive signals (reduce score)
        if report.is_open_source:
            score -= 10
            green_flags.append("Verified open source contract")
        if report.lp_locked:
            score -= 10
            green_flags.append(f"LP locked ({report.lp_lock_pct:.1f}%)")
        if report.holder_count > 100:
            score -= 5
            green_flags.append(f"Good holder distribution ({report.holder_count} holders)")
        if report.sell_tax_pct <= 2 and report.buy_tax_pct <= 2:
            score -= 5
            green_flags.append("Low trading taxes")
        if report.holder_count > 1000:
            score -= 5
            green_flags.append("Strong community (1000+ holders)")

        # Clamp to 0-100
        report.rug_score = max(0, min(100, score))

        # Assign risk level
        if report.rug_score <= 20:
            report.risk_level = RiskLevel.LOW
        elif report.rug_score <= 45:
            report.risk_level = RiskLevel.MEDIUM
        elif report.rug_score <= 70:
            report.risk_level = RiskLevel.HIGH
        else:
            report.risk_level = RiskLevel.CRITICAL

        return report

    def quick_check(self, address: str, chain: str = "ethereum") -> dict:
        """
        Fast safety check returning just the essentials.
        Suitable for bulk scanning new tokens.
        """
        report = self.analyze_token(address, chain)
        return {
            "address": address,
            "chain": chain,
            "name": report.name,
            "symbol": report.symbol,
            "rug_score": report.rug_score,
            "risk_level": report.risk_level,
            "is_honeypot": report.is_honeypot,
            "has_mint": report.has_mint_function,
            "can_pause": report.owner_can_pause,
            "buy_tax": report.buy_tax_pct,
            "sell_tax": report.sell_tax_pct,
            "lp_locked": report.lp_locked,
            "red_flags": len(report.red_flags),
            "verdict": "SAFE" if report.rug_score <= 30 else (
                "CAUTION" if report.rug_score <= 60 else "DANGER"
            ),
        }


# ===================================================================
#  3. SniperEngine
# ===================================================================

class SniperEngine:
    """
    Evaluate and manage snipe opportunities.

    Mirrors the decision engine of bots like Banana Gun and Maestro:
    1. Detect new token via NewTokenDetector
    2. Run safety analysis via TokenAnalyzer
    3. Evaluate entry criteria (liquidity, holders, contract safety)
    4. Calculate position size based on risk score
    5. Set exit criteria (take profit, stop loss, time exit)

    PAPER MODE ONLY by default. Never executes real trades
    without explicit mode change and user confirmation.
    """

    def __init__(self):
        self.detector = NewTokenDetector()
        self.analyzer = TokenAnalyzer()

        # Engine configuration
        self.paper_mode = True  # ALWAYS paper mode by default
        self.active = False
        self.chain = "solana"

        # Entry criteria (configurable, conservative defaults)
        self.min_liquidity_usd = 5000
        self.max_rug_score = 45  # Reject tokens above this score
        self.min_holder_count = 10
        self.max_top_holder_pct = 30.0
        self.max_buy_tax_pct = 10.0
        self.max_sell_tax_pct = 10.0
        self.require_lp_locked = False  # Many new tokens don't lock yet
        self.require_verified = False  # Many Solana tokens aren't "verified"
        self.max_token_age_minutes = 60  # Only snipe tokens < 1 hour old

        # Exit criteria
        self.default_take_profit_pct = 100.0  # 2x
        self.default_stop_loss_pct = 50.0  # -50%
        self.default_time_exit_minutes = 60  # 1 hour max hold

        # Position sizing
        self.max_position_pct = 2.0  # Max 2% of portfolio per snipe
        self.base_position_pct = 1.0  # Default position size

        # State tracking
        self.opportunities: List[SnipeOpportunity] = []
        self.active_positions: List[dict] = []  # Paper positions
        self.history: List[dict] = []
        self._load_state()

    def _load_state(self):
        """Load engine state from disk."""
        path = os.path.join(DATA_DIR, "sniper_state.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    state = json.load(f)
                self.active_positions = state.get("active_positions", [])
                self.history = state.get("history", [])[-500:]
            except Exception:
                pass

    def _save_state(self):
        """Persist engine state."""
        path = os.path.join(DATA_DIR, "sniper_state.json")
        try:
            state = {
                "active_positions": self.active_positions,
                "history": self.history[-500:],
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
            with open(path, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save sniper state: {e}")

    def evaluate_opportunity(
        self,
        pool_data: dict,
        safety_report: Optional[TokenSafetyReport] = None,
    ) -> SnipeOpportunity:
        """
        Evaluate whether a new pool/token is worth sniping.

        Decision process mirrors professional sniper bots:
        1. Check minimum liquidity (avoid illiquid rugs)
        2. Run safety analysis (honeypot, mint, rug score)
        3. Evaluate holder distribution
        4. Check token age (fresh launches preferred)
        5. Calculate confidence and position size
        """
        opp = SnipeOpportunity(
            token_address=pool_data.get("base_token_address", pool_data.get("token_address", "")),
            chain=pool_data.get("chain", self.chain),
            token_name=pool_data.get("base_token_name", ""),
            token_symbol=pool_data.get("base_token_symbol", ""),
            pair_address=pool_data.get("pool_address", ""),
            dex=pool_data.get("dex", ""),
            price_usd=pool_data.get("price_usd", 0),
            liquidity_usd=pool_data.get("liquidity_usd", 0),
            volume_24h=pool_data.get("volume_24h_usd", 0),
            age_minutes=pool_data.get("age_minutes", 0),
            detected_at=datetime.now(timezone.utc).isoformat(),
        )

        # Run safety analysis if not provided
        if safety_report is None and opp.token_address:
            try:
                safety_report = self.analyzer.analyze_token(
                    opp.token_address, opp.chain
                )
            except Exception as e:
                logger.warning(f"Safety analysis failed: {e}")

        if safety_report:
            opp.rug_score = safety_report.rug_score
            opp.risk_level = safety_report.risk_level

        # Decision engine
        reasons = []
        confidence = 0.5

        # Check entry criteria
        if opp.liquidity_usd < self.min_liquidity_usd:
            reasons.append(f"Low liquidity: ${opp.liquidity_usd:,.0f} < ${self.min_liquidity_usd:,.0f}")
            confidence -= 0.3

        if opp.rug_score > self.max_rug_score:
            reasons.append(f"High rug score: {opp.rug_score} > {self.max_rug_score}")
            confidence -= 0.4

        if safety_report:
            if safety_report.is_honeypot:
                reasons.append("HONEYPOT detected - cannot sell")
                confidence = 0.0

            if safety_report.has_mint_function:
                reasons.append("Mint function exists")
                confidence -= 0.2

            if safety_report.sell_tax_pct > self.max_sell_tax_pct:
                reasons.append(f"Sell tax too high: {safety_report.sell_tax_pct:.1f}%")
                confidence -= 0.2

            if safety_report.top_holder_pct > self.max_top_holder_pct:
                reasons.append(f"Whale concentration: {safety_report.top_holder_pct:.1f}%")
                confidence -= 0.1

        if opp.age_minutes > self.max_token_age_minutes:
            reasons.append(f"Too old: {opp.age_minutes:.0f}min > {self.max_token_age_minutes}min")
            confidence -= 0.1

        # Positive signals
        if opp.liquidity_usd >= self.min_liquidity_usd * 2:
            confidence += 0.1

        if safety_report and safety_report.lp_locked:
            confidence += 0.1

        if safety_report and safety_report.holder_count > 100:
            confidence += 0.1

        if opp.volume_24h > opp.liquidity_usd * 2:
            confidence += 0.1  # High volume relative to liquidity = interest

        # Final decision
        confidence = max(0.0, min(1.0, confidence))
        opp.confidence = round(confidence, 2)

        if confidence <= 0.0 or (safety_report and safety_report.is_honeypot):
            opp.action = "SKIP"
            opp.reason = "REJECTED: " + "; ".join(reasons) if reasons else "Failed safety checks"
        elif confidence < 0.4:
            opp.action = "SKIP"
            opp.reason = "Low confidence: " + "; ".join(reasons)
        elif confidence < 0.6:
            opp.action = "WATCH"
            opp.reason = "Moderate opportunity: " + "; ".join(reasons) if reasons else "Watch for improvement"
        else:
            opp.action = "SNIPE"
            opp.reason = "Good opportunity" + (": " + "; ".join(reasons) if reasons else "")

        # Position sizing based on risk
        if opp.action == "SNIPE":
            risk_factor = max(0.2, 1.0 - (opp.rug_score / 100))
            opp.suggested_entry_pct = round(
                self.base_position_pct * risk_factor, 2
            )
            opp.suggested_entry_pct = min(opp.suggested_entry_pct, self.max_position_pct)

            # Tighter stops for riskier tokens
            if opp.rug_score > 30:
                opp.stop_loss_pct = 30.0
                opp.take_profit_pct = 150.0
                opp.time_exit_minutes = 30
            else:
                opp.stop_loss_pct = self.default_stop_loss_pct
                opp.take_profit_pct = self.default_take_profit_pct
                opp.time_exit_minutes = self.default_time_exit_minutes

        self.opportunities.append(opp)
        return opp

    def scan_and_evaluate(self, chain: str = "solana", max_tokens: int = 10) -> dict:
        """
        Full scan: detect new tokens, analyze safety, evaluate all.

        This is the main sniper loop, equivalent to what Banana Gun
        runs continuously in the background:
        1. Scan for new pairs across DEX aggregators
        2. Filter by basic criteria (liquidity, age)
        3. Run safety analysis on promising tokens
        4. Generate SNIPE / WATCH / SKIP decisions
        """
        scan = self.detector.scan_all(chain, max_results=max_tokens * 2)

        results = {
            "chain": chain,
            "scanned": len(scan.get("new_pools", [])),
            "opportunities": [],
            "snipe_count": 0,
            "watch_count": 0,
            "skip_count": 0,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "engine_mode": "paper" if self.paper_mode else "LIVE",
        }

        for pool in scan.get("new_pools", [])[:max_tokens]:
            # Quick pre-filter
            liq = pool.get("liquidity_usd", 0)
            if liq < self.min_liquidity_usd * 0.5:
                continue

            opp = self.evaluate_opportunity(pool)
            results["opportunities"].append(opp.to_dict())

            if opp.action == "SNIPE":
                results["snipe_count"] += 1
                if self.paper_mode:
                    self._paper_buy(opp)
            elif opp.action == "WATCH":
                results["watch_count"] += 1
            else:
                results["skip_count"] += 1

        return results

    def _paper_buy(self, opp: SnipeOpportunity):
        """Record a paper (simulated) buy."""
        position = {
            "token_address": opp.token_address,
            "chain": opp.chain,
            "token_name": opp.token_name,
            "token_symbol": opp.token_symbol,
            "entry_price": opp.price_usd,
            "position_pct": opp.suggested_entry_pct,
            "take_profit_pct": opp.take_profit_pct,
            "stop_loss_pct": opp.stop_loss_pct,
            "time_exit_minutes": opp.time_exit_minutes,
            "entered_at": datetime.now(timezone.utc).isoformat(),
            "status": "open",
            "mode": "paper",
            "rug_score": opp.rug_score,
            "confidence": opp.confidence,
        }
        self.active_positions.append(position)
        self._save_state()
        logger.info(
            f"[PAPER] Bought {opp.token_symbol} at ${opp.price_usd:.8f} "
            f"(rug_score={opp.rug_score}, confidence={opp.confidence})"
        )

    def get_status(self) -> dict:
        """Get current sniper engine status."""
        return {
            "active": self.active,
            "mode": "paper" if self.paper_mode else "LIVE",
            "chain": self.chain,
            "open_positions": len(self.active_positions),
            "total_history": len(self.history),
            "recent_opportunities": len(self.opportunities),
            "config": {
                "min_liquidity_usd": self.min_liquidity_usd,
                "max_rug_score": self.max_rug_score,
                "max_token_age_minutes": self.max_token_age_minutes,
                "take_profit_pct": self.default_take_profit_pct,
                "stop_loss_pct": self.default_stop_loss_pct,
                "max_position_pct": self.max_position_pct,
            },
            "positions": self.active_positions,
        }


# ===================================================================
#  4. TrendingMonitor
# ===================================================================

class TrendingMonitor:
    """
    Track trending tokens and volume spikes across chains.

    Uses DexScreener and GeckoTerminal trending endpoints to
    surface what the market is paying attention to RIGHT NOW.
    """

    def get_trending_gecko(self, chain: str = "solana", limit: int = 20) -> List[dict]:
        """
        Get trending pools from GeckoTerminal.

        GeckoTerminal ranks pools by a combination of
        web visits and on-chain activity (volume, transactions).
        """
        network = GECKO_NETWORKS.get(chain.lower(), chain.lower())
        cache_key = f"trending_gecko_{network}"
        cached = _get_cached(cache_key, ttl=60)
        if cached:
            return cached

        url = f"{GECKOTERMINAL_BASE}/networks/{network}/trending_pools"
        data = _http_get(url)

        if not data or "data" not in data:
            return []

        results = []
        for pool in data["data"][:limit]:
            attrs = pool.get("attributes", {})
            base_token = attrs.get("base_token", {}) or {}
            quote_token = attrs.get("quote_token", {}) or {}

            entry = {
                "pool_address": attrs.get("address", ""),
                "chain": chain,
                "dex": attrs.get("dex_id", ""),
                "name": attrs.get("name", ""),
                "base_token_name": base_token.get("name", ""),
                "base_token_symbol": base_token.get("symbol", ""),
                "base_token_address": base_token.get("address", ""),
                "quote_token_symbol": quote_token.get("symbol", ""),
                "price_usd": _safe_float(attrs.get("base_token_price_usd")),
                "volume_24h_usd": _safe_float(
                    attrs.get("volume_usd", {}).get("h24", 0)
                ),
                "volume_1h_usd": _safe_float(
                    attrs.get("volume_usd", {}).get("h1", 0)
                ),
                "liquidity_usd": _safe_float(attrs.get("reserve_in_usd", 0)),
                "price_change_1h_pct": _safe_float(
                    attrs.get("price_change_percentage", {}).get("h1", 0)
                ),
                "price_change_24h_pct": _safe_float(
                    attrs.get("price_change_percentage", {}).get("h24", 0)
                ),
                "transactions_1h": attrs.get("transactions", {}).get("h1", {}),
                "transactions_24h": attrs.get("transactions", {}).get("h24", {}),
                "source": "geckoterminal",
            }
            results.append(entry)

        _set_cache(cache_key, results)
        return results

    def get_trending_dexscreener(self, chain: str = "solana", limit: int = 20) -> List[dict]:
        """
        Get boosted/trending tokens from DexScreener.

        DexScreener's boosted tokens are those that projects
        have promoted, giving visibility into marketing activity.
        """
        cache_key = f"trending_dexs_{chain}"
        cached = _get_cached(cache_key, ttl=60)
        if cached:
            return cached

        url = f"{DEXSCREENER_BASE}/token-boosts/top/v1"
        data = _http_get(url)

        if not data or not isinstance(data, list):
            return []

        chain_slug = DEXSCREENER_CHAINS.get(chain.lower(), chain.lower())
        results = []

        for token in data:
            if token.get("chainId", "").lower() != chain_slug:
                continue
            if len(results) >= limit:
                break

            entry = {
                "token_address": token.get("tokenAddress", ""),
                "chain": chain,
                "description": token.get("description", ""),
                "total_boosts": token.get("totalAmount", 0),
                "icon": token.get("icon", ""),
                "links": token.get("links", []),
                "source": "dexscreener_boost",
            }
            results.append(entry)

        _set_cache(cache_key, results)
        return results

    def get_trending_all(self, chain: str = "solana", limit: int = 20) -> dict:
        """
        Aggregate trending data from all sources.
        """
        gecko = self.get_trending_gecko(chain, limit)
        dexscreener = self.get_trending_dexscreener(chain, limit)

        # Find volume spikes (tokens with 1h volume > 10% of 24h volume)
        volume_spikes = []
        for pool in gecko:
            vol_1h = pool.get("volume_1h_usd", 0)
            vol_24h = pool.get("volume_24h_usd", 0)
            if vol_24h > 0 and vol_1h > vol_24h * 0.1:
                pool["volume_spike_ratio"] = round(vol_1h / max(vol_24h, 1) * 24, 2)
                volume_spikes.append(pool)

        volume_spikes.sort(key=lambda x: x.get("volume_spike_ratio", 0), reverse=True)

        return {
            "chain": chain,
            "trending_pools": gecko,
            "boosted_tokens": dexscreener,
            "volume_spikes": volume_spikes[:10],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def detect_volume_anomalies(self, chain: str = "solana") -> List[dict]:
        """
        Find tokens with unusual volume activity.
        A sudden spike in volume relative to liquidity often
        precedes a major price movement.
        """
        trending = self.get_trending_gecko(chain, limit=30)
        anomalies = []

        for pool in trending:
            vol = pool.get("volume_1h_usd", 0)
            liq = pool.get("liquidity_usd", 1)

            if liq > 0 and vol > 0:
                # Volume-to-liquidity ratio (V/L)
                # V/L > 1 in 1 hour = very unusual activity
                vl_ratio = vol / liq
                if vl_ratio > 0.5:
                    pool["vl_ratio_1h"] = round(vl_ratio, 2)
                    pool["anomaly_type"] = (
                        "extreme" if vl_ratio > 2
                        else "high" if vl_ratio > 1
                        else "moderate"
                    )
                    anomalies.append(pool)

        anomalies.sort(key=lambda x: x.get("vl_ratio_1h", 0), reverse=True)
        return anomalies


# ===================================================================
#  Helper functions
# ===================================================================

def _safe_float(val) -> float:
    """Safely convert a value to float."""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _bool(val) -> bool:
    """Convert GoPlus-style string booleans to Python bool."""
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip() in ("1", "true", "True", "yes")
    if isinstance(val, (int, float)):
        return val == 1
    return False


# ===================================================================
#  Convenience functions (for MCP tools and CLI)
# ===================================================================

# Singleton instances
_detector: Optional[NewTokenDetector] = None
_analyzer: Optional[TokenAnalyzer] = None
_engine: Optional[SniperEngine] = None
_trending: Optional[TrendingMonitor] = None


def _get_detector() -> NewTokenDetector:
    global _detector
    if _detector is None:
        _detector = NewTokenDetector()
    return _detector


def _get_analyzer() -> TokenAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = TokenAnalyzer()
    return _analyzer


def _get_engine() -> SniperEngine:
    global _engine
    if _engine is None:
        _engine = SniperEngine()
    return _engine


def _get_trending() -> TrendingMonitor:
    global _trending
    if _trending is None:
        _trending = TrendingMonitor()
    return _trending


def scan_new_tokens(chain: str = "solana", max_results: int = 20) -> dict:
    """Scan for newly launched tokens on a chain."""
    return _get_detector().scan_all(chain, max_results)


def analyze_token(address: str, chain: str = "ethereum") -> dict:
    """Run full safety analysis on a token."""
    report = _get_analyzer().analyze_token(address, chain)
    return report.to_dict()


def quick_check_token(address: str, chain: str = "ethereum") -> dict:
    """Quick safety check on a token."""
    return _get_analyzer().quick_check(address, chain)


def trending_tokens(chain: str = "solana", limit: int = 20) -> dict:
    """Get trending tokens and pools."""
    return _get_trending().get_trending_all(chain, limit)


def volume_anomalies(chain: str = "solana") -> List[dict]:
    """Find tokens with unusual volume spikes."""
    return _get_trending().detect_volume_anomalies(chain)


def sniper_scan(chain: str = "solana", max_tokens: int = 10) -> dict:
    """Full sniper scan: detect, analyze, and evaluate new tokens."""
    return _get_engine().scan_and_evaluate(chain, max_tokens)


def sniper_status() -> dict:
    """Get sniper engine status and active positions."""
    return _get_engine().get_status()


# ===================================================================
#  Knowledge base content for training
# ===================================================================

SNIPER_TRAINING_DATA = """
# Token Sniping Intelligence - Training Module

## 1. How Token Sniping Works

Token sniping is the practice of buying newly launched cryptocurrency tokens
in the first moments after their liquidity pool goes live on a decentralized
exchange (DEX). The goal is to enter at the lowest possible price before
demand drives the price up.

### The Sniping Lifecycle
1. DETECTION: Monitor DEX factory contracts for new pair creation events
   - On Ethereum/EVM: Watch Uniswap/SushiSwap factory PairCreated events
   - On Solana: Watch Raydium initialize_market transactions
2. ANALYSIS: Run safety checks on the token contract within seconds
3. DECISION: Evaluate entry criteria (liquidity, safety, holder distribution)
4. EXECUTION: Submit buy transaction with optimal gas/priority fees
5. MANAGEMENT: Monitor position with take-profit, stop-loss, and time-based exits

### How Professional Bots Work
- Banana Gun: Telegram bot that detects liquidity additions and stealth launches.
  Uses First Bundle or Fail (FoF) to target block 0 placement. Charges a
  validator bribe (snipe tip) for priority ordering. Supports ETH, Solana, Base.
- Maestro Bot: Telegram bot with God Mode for instant liquidity sniping.
  Features dynamic deadblock detection, anti-rug frontrunning, and
  auto-adjusting max buy limits. Supports 10+ chains.
- Unibot: Specializes in Uniswap sniping with MEV protection via private
  mempools and limit order functionality.

## 2. Risk Management for Token Sniping

### Position Sizing Rules
- Never risk more than 1-2% of portfolio per snipe
- Scale position inversely with rug score (higher risk = smaller position)
- Use paper mode to validate strategy before committing real funds

### Exit Strategy (Critical)
- Take Profit: Set at 2x-5x depending on token type and risk
- Stop Loss: 30-50% maximum loss per position
- Time Exit: Close positions within 30-60 minutes (most new tokens lose
  80%+ of value within hours if they don't sustain momentum)
- Trailing Stop: Once up 50%+, trail with 25% stop to lock in gains

### Risk Categories
- LOW RISK (rug score 0-20): Verified contract, LP locked, distributed holders
- MEDIUM RISK (rug score 21-45): Some concerns but no critical red flags
- HIGH RISK (rug score 46-70): Multiple red flags, trade only with strict limits
- CRITICAL (rug score 71-100): Likely scam, do not trade

## 3. Anti-Rug Detection Methods

### Contract Red Flags (Automatic Checks)
1. HONEYPOT: Token allows buying but blocks selling. Detected by simulating
   a sell transaction. If sell fails or has >50% tax, it is a honeypot.
2. MINT FUNCTION: Creator can create unlimited new tokens and dump them.
   Check for mint(), _mint(), or similar functions in the contract.
3. PAUSE/FREEZE: Owner can stop all transfers. Check for pause(),
   freeze(), or similar admin functions.
4. BLACKLIST: Owner can block specific addresses from selling. Check for
   blacklist(), addToBlacklist(), or address mapping with transfer restrictions.
5. PROXY CONTRACT: Upgradeable logic means the contract can change to
   become malicious after launch.
6. HIDDEN OWNER: Even if ownership is "renounced," some contracts retain
   a hidden admin address that can still call restricted functions.

### Liquidity Analysis
- LP LOCKED: Check if liquidity provider tokens are locked in a known
  locker contract (Unicrypt, PinkSale, Team.Finance, etc.)
- LP BURN: Some projects burn LP tokens permanently (best case)
- LP AMOUNT: Minimum $5,000 liquidity to be worth considering
- LP RATIO: The ratio of LP to total supply indicates manipulation risk

### Holder Distribution
- TOP HOLDER: If one wallet holds >20% of supply, dump risk is extreme
- CREATOR HOLDING: Creator holding >10% is a red flag
- DISTRIBUTION: More holders = more organic demand = safer
- INSIDER CLUSTERS: Multiple wallets from same creator holding large portions

## 4. MEV Protection and Frontrunning

### What is MEV?
Maximal Extractable Value is profit extracted by reordering transactions
in a block. Affects snipers through:
- FRONTRUNNING: Bots see your buy and place their buy first
- SANDWICH ATTACKS: Bot buys before you and sells after you
- BACKRUNNING: Bots arbitrage price impact from your trade

### Protection Strategies
1. Private Mempools: Send transactions through Flashbots (ETH) or
   Jito (Solana) to hide them from public mempool
2. High Priority Fees: Outbid other bots for transaction ordering
3. Low Slippage: Limit price impact to reduce sandwich profitability
4. Intent-Based Trading: Use UniswapX or CoW Swap for MEV-resistant swaps
5. Bundled Transactions: Bundle buy with other txs to obscure intent

### Solana-Specific MEV
- Jito Block Engine: Submit bundles for priority inclusion
- Priority Fees: Set compute unit price for validator priority
- No Mempool: Solana doesn't have a traditional mempool, but validators
  can still reorder transactions within a block

## 5. Token Launch Detection Methods

### On-Chain Monitoring (What Bots Do)
- Subscribe to DEX factory contract events (PairCreated, PoolInitialized)
- Watch for large ETH/SOL transfers to known DEX router addresses
- Monitor token contract deployments followed by LP additions
- Track known deployer wallets for repeat launchers

### API-Based Detection (What We Use)
- DexScreener API: Aggregates new pairs across all DEXes
- GeckoTerminal API: New pools endpoint with real-time updates
- Both index DEX factory events and surface them via REST APIs
- Trade-off: Slightly slower than direct RPC but free and reliable

### Social Signal Detection
- Telegram groups announcing launches
- Twitter/X mentions of new contract addresses
- DexScreener token profile creation (projects register their token)

## 6. Liquidity Pool Analysis

### Key Metrics
- TOTAL VALUE LOCKED (TVL): Total USD value in the pool
- DEPTH: How much can be traded without significant price impact
- AGE: Newer pools are riskier; established pools are safer
- VOLUME/LIQUIDITY RATIO: High ratio = high interest = momentum
- FEE TIER: Higher fees can indicate MEV protection or low confidence

### Pool Types
- CPMM (Constant Product): Standard x*y=k pools (Uniswap V2, Raydium)
- Concentrated Liquidity: Capital-efficient pools (Uniswap V3, Orca)
- Weighted Pools: Different asset ratios (Balancer)
- Stable Pools: Low-slippage for similar assets (Curve)

### Red Flags in Pools
- One-sided liquidity (creator holds all LP)
- Very low initial liquidity (<$1,000)
- LP tokens not locked or burned
- Sudden large liquidity removal after launch
"""


def get_training_data() -> str:
    """Return the complete training data text for knowledge ingestion."""
    return SNIPER_TRAINING_DATA


def ingest_training_data() -> dict:
    """
    Ingest all sniping knowledge into the Bruce AI knowledge base.
    Uses the KnowledgeIngestor to chunk and store the training content.
    """
    try:
        from knowledge_ingestor import KnowledgeIngestor

        ingestor = KnowledgeIngestor()

        result = ingestor.ingest_text(
            text=SNIPER_TRAINING_DATA,
            source="token_sniper_training_module",
            metadata={
                "module": "token_sniper",
                "version": "1.0",
                "topics": [
                    "token_sniping",
                    "anti_rug_detection",
                    "mev_protection",
                    "liquidity_analysis",
                    "risk_management",
                    "banana_gun",
                    "maestro_bot",
                    "unibot",
                    "dex_trading",
                    "solana_sniping",
                    "ethereum_sniping",
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            chunk_size=600,
            overlap=80,
        )
        logger.info(f"[TokenSniper] Ingested training data: {result}")
        return result

    except ImportError:
        logger.warning("KnowledgeIngestor not available, saving training data to file")
        # Fallback: save to data directory
        path = os.path.join(DATA_DIR, "training_data.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(SNIPER_TRAINING_DATA)
        return {"status": "saved_to_file", "path": path}
    except Exception as e:
        logger.error(f"Failed to ingest training data: {e}")
        return {"error": str(e)}
