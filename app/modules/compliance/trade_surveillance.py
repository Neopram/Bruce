import logging
import asyncio
from app.config.settings import Config
from app.modules.order_manager import OrderManager
from app.utils.database import DatabaseManager
from app.modules.alert_system import AlertSystem

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
INSIDER_TRADE_THRESHOLD = 0.10  # % deviation from normal trade volume
SPOOFING_THRESHOLD = 5  # Minimum spoofing attempts to trigger alert
WASH_TRADING_THRESHOLD = 10  # Minimum self-trade count before triggering alert
ORDER_IMBALANCE_THRESHOLD = 0.02  # Order book imbalance alert level
HFT_THRESHOLD = 500  # High-frequency trading alert level

class TradeSurveillance:
    """
    AI-Powered Market Manipulation & Trade Surveillance.
    """

    def __init__(self):
        """
        Initializes AI-driven trade surveillance with fraud detection capabilities.
        """
        self.db_manager = DatabaseManager()
        self.order_manager = OrderManager()
        self.alert_system = AlertSystem()

    async def detect_insider_trading(self):
        """
        Detects potential insider trading based on abnormal trade volume changes.
        """
        trade_data = await self.order_manager.get_recent_trades()
        volume_change = abs(trade_data["latest_trade_volume"] - trade_data["average_volume"]) / trade_data["average_volume"]
        
        if volume_change > INSIDER_TRADE_THRESHOLD:
            logging.warning("🚨 Potential Insider Trading Detected!")
            self.alert_system.send_alert("🚨 Insider Trading Alert!", alert_type="telegram")
            return True
        return False

    async def detect_spoofing(self):
        """
        Detects market spoofing attempts by tracking repeated fake orders.
        """
        spoofing_count = await self.order_manager.count_spoof_orders()
        
        if spoofing_count > SPOOFING_THRESHOLD:
            logging.warning("🚨 Market Spoofing Detected!")
            self.alert_system.send_alert("🚨 Market Spoofing Alert!", alert_type="telegram")
            return True
        return False

    async def detect_wash_trading(self):
        """
        Detects wash trading by analyzing self-trade frequency.
        """
        self_trade_count = await self.order_manager.count_self_trades()
        
        if self_trade_count > WASH_TRADING_THRESHOLD:
            logging.warning("🚨 Wash Trading Activity Detected!")
            self.alert_system.send_alert("🚨 Wash Trading Alert!", alert_type="telegram")
            return True
        return False

    async def detect_order_imbalance(self):
        """
        Identifies significant order book imbalances.
        """
        order_book = await self.db_manager.get_market_order_book()
        bid_volume = sum([order["size"] for order in order_book["bids"]])
        ask_volume = sum([order["size"] for order in order_book["asks"]])

        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        if abs(imbalance) > ORDER_IMBALANCE_THRESHOLD:
            logging.warning(f"⚠️ Order Flow Imbalance Detected! Imbalance: {imbalance:.4f}")
            self.alert_system.send_alert("⚠️ Order Imbalance Alert!", alert_type="telegram")
            return True

        return False

    async def detect_hft_abuse(self):
        """
        Detects high-frequency trading (HFT) abuse.
        """
        trade_data = await self.db_manager.get_trade_frequency()
        if trade_data["trades_per_second"] > HFT_THRESHOLD:
            logging.warning("⚠️ HFT Abuse Detected!")
            self.alert_system.send_alert("⚠️ High-Frequency Trading Alert!", alert_type="telegram")
            return True

        return False

    async def run_trade_surveillance(self):
        """
        Continuously monitors trade activities for fraud detection.
        """
        logging.info("🚀 Starting AI-Powered Trade Surveillance System...")
        while True:
            await self.detect_insider_trading()
            await self.detect_spoofing()
            await self.detect_wash_trading()
            await self.detect_order_imbalance()
            await self.detect_hft_abuse()
            await asyncio.sleep(5)  # Runs checks every 5 seconds

# Example Usage
if __name__ == "__main__":
    trade_surveillance = TradeSurveillance()
    asyncio.run(trade_surveillance.run_trade_surveillance())
