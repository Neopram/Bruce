import logging
import numpy as np
from app.modules.order_manager import OrderManager

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
FOMO_THRESHOLD = 5  # Rapid buy orders within short time window
PANIC_SELLING_THRESHOLD = 3  # Consecutive loss trades triggering panic exit
OVERTRADING_ALERT_THRESHOLD = 20  # Too many trades in a short time
TRADE_STRESS_THRESHOLD = 15  # High trade volume with erratic behavior

class AITradingPsychology:
    """
    AI-Powered Trading Psychology Monitoring System.
    """

    def __init__(self):
        """
        Initializes AI trading psychology engine.
        """
        self.order_manager = OrderManager()

    def detect_fomo_trading(self, trade_data):
        """
        Detects FOMO (Fear of Missing Out) trading behavior.

        Args:
            trade_data (list): List of recent trades.

        Returns:
            bool: True if FOMO trading is detected.
        """
        fomo_trades = [trade for trade in trade_data if trade["type"] == "buy"]
        if len(fomo_trades) > FOMO_THRESHOLD:
            logging.warning("🚨 FOMO Trading Detected! Buyer frenzy alert.")
            return True
        return False

    def detect_panic_selling(self, trade_data):
        """
        Detects panic selling patterns.

        Args:
            trade_data (list): List of recent trades.

        Returns:
            bool: True if panic selling is detected.
        """
        loss_trades = [trade for trade in trade_data if trade["profit"] < 0]
        if len(loss_trades) > PANIC_SELLING_THRESHOLD:
            logging.warning("🚨 Panic Selling Detected! Traders exiting irrationally.")
            return True
        return False

    def detect_overtrading(self, trade_data):
        """
        Identifies excessive trading behavior.

        Args:
            trade_data (list): List of recent trades.

        Returns:
            bool: True if overtrading is detected.
        """
        if len(trade_data) > OVERTRADING_ALERT_THRESHOLD:
            logging.warning("🚨 Overtrading Alert! Trading volume abnormally high.")
            return True
        return False

    def detect_trade_stress(self, trade_data):
        """
        Detects stress-based irrational trading.

        Args:
            trade_data (list): List of recent trades.

        Returns:
            bool: True if trade stress is detected.
        """
        volatility = np.std([trade["price"] for trade in trade_data])
        if volatility > TRADE_STRESS_THRESHOLD:
            logging.warning("⚠️ Trading Stress Detected! Market instability risk.")
            return True
        return False

# Example Usage
if __name__ == "__main__":
    trade_psychology = AITradingPsychology()
    sample_trades = [{"type": "buy", "profit": 10, "price": 20000} for _ in range(10)]
    trade_psychology.detect_fomo_trading(sample_trades)
    trade_psychology.detect_panic_selling(sample_trades)
    trade_psychology.detect_overtrading(sample_trades)
    trade_psychology.detect_trade_stress(sample_trades)
