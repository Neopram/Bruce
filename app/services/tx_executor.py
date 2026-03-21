"""
Transaction Executor - Builds, validates, signs, and sends blockchain
transactions. Maintains an execution history log.
"""

import uuid
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class Order:
    """Simple order representation."""

    def __init__(
        self,
        from_address: str,
        to_address: str,
        value: float,
        chain_id: int = 1,
        gas_limit: int = 21000,
        gas_price_gwei: float = 50.0,
        token: Optional[str] = None,
        side: str = "buy",
    ):
        self.id = str(uuid.uuid4())
        self.from_address = from_address
        self.to_address = to_address
        self.value = value
        self.chain_id = chain_id
        self.gas_limit = gas_limit
        self.gas_price_gwei = gas_price_gwei
        self.token = token
        self.side = side

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from_address": self.from_address,
            "to_address": self.to_address,
            "value": self.value,
            "chain_id": self.chain_id,
            "gas_limit": self.gas_limit,
            "gas_price_gwei": self.gas_price_gwei,
            "token": self.token,
            "side": self.side,
        }


class TransactionExecutor:
    """Executes and tracks blockchain transactions."""

    def __init__(self, web3=None, dry_run: bool = True):
        self.web3 = web3
        self.dry_run = dry_run
        self._history: List[dict] = []

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_order(self, order: Order) -> Dict[str, Any]:
        """Pre-execution validation of an order."""
        errors: List[str] = []

        if not order.from_address or len(order.from_address) != 42:
            errors.append("Invalid from_address (must be 42-char hex)")
        if not order.to_address or len(order.to_address) != 42:
            errors.append("Invalid to_address (must be 42-char hex)")
        if order.value <= 0:
            errors.append("Value must be positive")
        if order.gas_limit < 21000:
            errors.append("Gas limit too low (minimum 21000)")
        if order.gas_price_gwei <= 0:
            errors.append("Gas price must be positive")

        if self.web3 and not self.dry_run:
            try:
                balance = self.web3.eth.get_balance(order.from_address)
                required_wei = self.web3.to_wei(order.value, "ether") + (
                    order.gas_limit * self.web3.to_wei(order.gas_price_gwei, "gwei")
                )
                if balance < required_wei:
                    errors.append("Insufficient balance for value + gas")
            except Exception as exc:
                errors.append(f"Balance check failed: {exc}")

        return {"valid": len(errors) == 0, "errors": errors}

    # ------------------------------------------------------------------
    # Fee estimation
    # ------------------------------------------------------------------

    def estimate_fees(self, order: Order) -> dict:
        """Estimate transaction fees in ETH and USD (approximate)."""
        gas_cost_gwei = order.gas_limit * order.gas_price_gwei
        gas_cost_eth = gas_cost_gwei / 1e9
        eth_price_usd = 3500.0  # placeholder

        return {
            "gas_limit": order.gas_limit,
            "gas_price_gwei": order.gas_price_gwei,
            "estimated_fee_eth": round(gas_cost_eth, 8),
            "estimated_fee_usd": round(gas_cost_eth * eth_price_usd, 4),
            "eth_price_usd_estimate": eth_price_usd,
        }

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def build_tx(self, order: Order) -> dict:
        """Build a raw transaction dictionary."""
        nonce = 0
        if self.web3 and not self.dry_run:
            nonce = self.web3.eth.get_transaction_count(order.from_address)

        return {
            "to": order.to_address,
            "value": int(order.value * 1e18),
            "gas": order.gas_limit,
            "gasPrice": int(order.gas_price_gwei * 1e9),
            "nonce": nonce,
            "chainId": order.chain_id,
        }

    def execute_trade(self, order: Order) -> dict:
        """Execute a trade order (or simulate in dry-run mode)."""
        validation = self.validate_order(order)
        if not validation["valid"]:
            record = {
                "order_id": order.id,
                "status": "rejected",
                "errors": validation["errors"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._history.append(record)
            return record

        tx = self.build_tx(order)
        fees = self.estimate_fees(order)

        if self.dry_run or self.web3 is None:
            record = {
                "order_id": order.id,
                "status": "simulated",
                "tx": tx,
                "fees": fees,
                "tx_hash": f"0x{'0' * 64}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        else:
            try:
                signed = self.web3.eth.account.sign_transaction(tx, self.web3._private_key)
                tx_hash = self.web3.eth.send_raw_transaction(signed.rawTransaction)
                receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                record = {
                    "order_id": order.id,
                    "status": "confirmed" if receipt.status == 1 else "failed",
                    "tx_hash": tx_hash.hex(),
                    "block_number": receipt.blockNumber,
                    "gas_used": receipt.gasUsed,
                    "fees": fees,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            except Exception as exc:
                record = {
                    "order_id": order.id,
                    "status": "error",
                    "error": str(exc),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        self._history.append(record)
        return record

    # ------------------------------------------------------------------
    # History
    # ------------------------------------------------------------------

    def get_execution_history(self, limit: int = 50) -> List[dict]:
        """Return recent execution history, newest first."""
        return list(reversed(self._history[-limit:]))

    def sign_and_send(self, tx: dict, private_key: str):
        """Legacy helper: sign and send a pre-built tx dict."""
        if self.web3 is None:
            raise RuntimeError("web3 instance is required for live transactions")
        signed = self.web3.eth.account.sign_transaction(tx, private_key)
        return self.web3.eth.send_raw_transaction(signed.rawTransaction)
