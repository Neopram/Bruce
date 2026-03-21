import logging
import asyncio
from app.modules.alert_system import AlertSystem
from app.modules.transaction_monitor import TransactionMonitor
from app.modules.blockchain.aml_audit import AMLAudit

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Compliance Constants
AML_THRESHOLD = 10000  # USD value for suspicious transaction flagging
HIGH_RISK_COUNTRIES = {"North Korea", "Iran", "Syria", "Cuba", "Sudan"}
KYC_VERIFICATION_REQUIRED = True
ON_CHAIN_AUDIT_LOG = True

class RegulatoryComplianceEngine:
    """
    AI-Driven Compliance & AML Monitoring System.
    """

    def __init__(self):
        """
        Initializes the compliance engine with monitoring & auditing components.
        """
        self.alert_system = AlertSystem()
        self.transaction_monitor = TransactionMonitor()
        self.aml_audit = AMLAudit()

    async def detect_suspicious_transactions(self):
        """
        Monitors transactions and flags suspicious activities.
        """
        transactions = await self.transaction_monitor.get_recent_transactions()
        for txn in transactions:
            if txn["amount"] > AML_THRESHOLD or txn["country"] in HIGH_RISK_COUNTRIES:
                logging.warning(f"🚨 Suspicious Transaction Detected: {txn}")
                self.alert_system.send_alert("🚨 AML Alert! Suspicious Transaction Detected.", alert_type="email")
                if ON_CHAIN_AUDIT_LOG:
                    await self.aml_audit.log_transaction(txn)

    async def enforce_kyc_requirements(self):
        """
        Verifies user identity compliance with KYC regulations.
        """
        if KYC_VERIFICATION_REQUIRED:
            pending_kyc_users = await self.transaction_monitor.get_pending_kyc_users()
            for user in pending_kyc_users:
                logging.info(f"⚠️ KYC Pending for User: {user}")
                self.alert_system.send_alert(f"⚠️ KYC Pending: User {user}", alert_type="sms")

    async def run_compliance_checks(self):
        """
        Continuously runs compliance monitoring.
        """
        logging.info("🚀 Regulatory Compliance Engine Running...")
        while True:
            await self.detect_suspicious_transactions()
            await self.enforce_kyc_requirements()
            await asyncio.sleep(10)

# Example Usage
if __name__ == "__main__":
    compliance_engine = RegulatoryComplianceEngine()
    asyncio.run(compliance_engine.run_compliance_checks())
