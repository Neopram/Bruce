# Wallet activity tracker
import time
import uuid
from collections import defaultdict


class WalletTracker:
    """Web3 wallet tracker with simulated data and Web3 integration placeholder."""

    SUPPORTED_CHAINS = ["ethereum", "polygon", "bsc", "arbitrum", "solana", "avalanche"]

    def __init__(self):
        self._tracked_wallets = {}
        self._alerts = {}
        self._transaction_cache = defaultdict(list)
        self._balance_cache = {}

    def track_wallet(self, address, chain="ethereum"):
        """Start tracking a wallet address on a given chain.

        Args:
            address: Wallet address string.
            chain: Blockchain network (default 'ethereum').

        Returns:
            Dict with tracking status.
        """
        if chain not in self.SUPPORTED_CHAINS:
            return {"error": f"Unsupported chain '{chain}'. Supported: {self.SUPPORTED_CHAINS}"}

        key = f"{chain}:{address}"
        self._tracked_wallets[key] = {
            "address": address,
            "chain": chain,
            "tracked_since": time.time(),
            "last_checked": None,
            "label": None,
        }

        # Initialize simulated balance
        self._balance_cache[key] = self._generate_simulated_balance(chain)

        # Initialize simulated transactions
        self._transaction_cache[key] = self._generate_simulated_transactions(address, chain, count=5)

        return {
            "status": "tracking",
            "address": address,
            "chain": chain,
            "wallet_key": key,
        }

    def get_balance(self, address, chain="ethereum"):
        """Get wallet balance for an address on a chain.

        Args:
            address: Wallet address.
            chain: Blockchain network.

        Returns:
            Dict with balance details.
        """
        key = f"{chain}:{address}"

        if key not in self._balance_cache:
            self._balance_cache[key] = self._generate_simulated_balance(chain)

        balance = self._balance_cache[key]
        balance["last_updated"] = time.time()
        return {
            "address": address,
            "chain": chain,
            **balance,
        }

    def get_transactions(self, address, chain="ethereum", limit=10):
        """Get recent transactions for a wallet.

        Args:
            address: Wallet address.
            chain: Blockchain network.
            limit: Max transactions to return.

        Returns:
            Dict with transaction list.
        """
        key = f"{chain}:{address}"

        if key not in self._transaction_cache or not self._transaction_cache[key]:
            self._transaction_cache[key] = self._generate_simulated_transactions(address, chain, count=limit)

        txns = self._transaction_cache[key][-limit:]
        return {
            "address": address,
            "chain": chain,
            "transaction_count": len(txns),
            "transactions": txns,
        }

    def get_portfolio(self, address):
        """Get multi-chain portfolio for an address.

        Args:
            address: Wallet address to check across all supported chains.

        Returns:
            Dict with per-chain balances and total estimated USD value.
        """
        portfolio = {
            "address": address,
            "chains": {},
            "total_usd_estimate": 0.0,
        }

        for chain in self.SUPPORTED_CHAINS:
            key = f"{chain}:{address}"
            if key in self._tracked_wallets or key in self._balance_cache:
                balance = self.get_balance(address, chain)
                portfolio["chains"][chain] = balance
                portfolio["total_usd_estimate"] += balance.get("usd_value", 0)

        # If no chains tracked, check ethereum by default
        if not portfolio["chains"]:
            balance = self.get_balance(address, "ethereum")
            portfolio["chains"]["ethereum"] = balance
            portfolio["total_usd_estimate"] = balance.get("usd_value", 0)

        portfolio["total_usd_estimate"] = round(portfolio["total_usd_estimate"], 2)
        return portfolio

    def alert_on_movement(self, address, threshold, chain="ethereum"):
        """Set an alert for wallet movements above a USD threshold.

        Args:
            address: Wallet address to monitor.
            threshold: USD value threshold to trigger alert.
            chain: Blockchain network.

        Returns:
            Dict with alert configuration.
        """
        alert_id = str(uuid.uuid4())[:8]
        key = f"{chain}:{address}"

        self._alerts[alert_id] = {
            "alert_id": alert_id,
            "address": address,
            "chain": chain,
            "threshold_usd": threshold,
            "created_at": time.time(),
            "triggered": False,
            "trigger_count": 0,
        }

        # Ensure wallet is being tracked
        if key not in self._tracked_wallets:
            self.track_wallet(address, chain)

        return {
            "status": "alert_set",
            "alert_id": alert_id,
            "address": address,
            "chain": chain,
            "threshold_usd": threshold,
        }

    def check_alerts(self):
        """Check all alerts against recent transactions. Returns triggered alerts."""
        triggered = []
        for alert_id, alert in self._alerts.items():
            if alert["triggered"]:
                continue
            key = f"{alert['chain']}:{alert['address']}"
            txns = self._transaction_cache.get(key, [])
            for tx in txns:
                if abs(tx.get("usd_value", 0)) >= alert["threshold_usd"]:
                    alert["triggered"] = True
                    alert["trigger_count"] += 1
                    triggered.append({
                        "alert_id": alert_id,
                        "address": alert["address"],
                        "chain": alert["chain"],
                        "transaction": tx,
                        "threshold": alert["threshold_usd"],
                    })
                    break
        return triggered

    def list_tracked_wallets(self):
        """List all tracked wallets."""
        return [
            {
                "address": w["address"],
                "chain": w["chain"],
                "tracked_since": w["tracked_since"],
                "label": w["label"],
            }
            for w in self._tracked_wallets.values()
        ]

    def _generate_simulated_balance(self, chain):
        """Generate simulated balance data for a chain."""
        import random
        native_tokens = {
            "ethereum": ("ETH", 2500.0),
            "polygon": ("MATIC", 0.85),
            "bsc": ("BNB", 320.0),
            "arbitrum": ("ETH", 2500.0),
            "solana": ("SOL", 130.0),
            "avalanche": ("AVAX", 28.0),
        }
        token, price = native_tokens.get(chain, ("TOKEN", 1.0))
        amount = round(random.uniform(0.01, 10.0), 4)
        usd_value = round(amount * price, 2)

        return {
            "native_token": token,
            "native_balance": amount,
            "usd_value": usd_value,
            "token_price_usd": price,
            "tokens": [
                {"symbol": "USDC", "balance": round(random.uniform(100, 10000), 2), "usd_value": round(random.uniform(100, 10000), 2)},
                {"symbol": "USDT", "balance": round(random.uniform(50, 5000), 2), "usd_value": round(random.uniform(50, 5000), 2)},
            ],
        }

    def _generate_simulated_transactions(self, address, chain, count=5):
        """Generate simulated transaction data."""
        import random
        txns = []
        now = time.time()
        for i in range(count):
            tx_type = random.choice(["send", "receive", "swap", "approve"])
            value = round(random.uniform(0.001, 5.0), 4)
            usd_value = round(value * random.uniform(100, 3000), 2)

            txns.append({
                "tx_hash": f"0x{uuid.uuid4().hex[:64]}",
                "type": tx_type,
                "from": address if tx_type == "send" else f"0x{uuid.uuid4().hex[:40]}",
                "to": f"0x{uuid.uuid4().hex[:40]}" if tx_type == "send" else address,
                "value": value,
                "usd_value": usd_value,
                "chain": chain,
                "timestamp": now - (i * 3600),
                "status": "confirmed",
            })
        return txns
