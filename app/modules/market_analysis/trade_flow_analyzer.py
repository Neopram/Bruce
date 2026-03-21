import logging
import numpy as np

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class TradeFlowAnalyzer:
    """
    AI-Driven Trade Flow Analysis for Market Impact Estimation.
    """

    def __init__(self):
        """
        Initializes the trade flow analysis module.
        """
        self.trade_history = []

    def analyze_trade_flow(self, order_book):
        """
        Analyzes trade flow trends to detect aggressive trading behavior.

        Args:
            order_book (dict): Real-time order book data.
        """
        trade_sizes = np.array([order["size"] for order in order_book["bids"][:5] + order_book["asks"][:5]])
        avg_trade_size = np.mean(trade_sizes)

        if avg_trade_size > np.percentile(trade_sizes, 90):
            logging.warning("🚨 Large Trade Flow Detected: Possible Institutional Activity.")

        logging.info(f"📊 Trade Flow Analysis: Avg Trade Size = {avg_trade_size:.2f}")

    def analyze_bid_ask_spread(self, order_book):
        """
        Analyzes bid-ask spread dynamics for optimal execution.

        Args:
            order_book (dict): Real-time order book data.

        Returns:
            float: Current bid-ask spread.
        """
        best_bid = order_book["bids"][0]["size"]
        best_ask = order_book["asks"][0]["size"]
        spread = abs(best_ask - best_bid)

        logging.info(f"📊 Bid-Ask Spread Analysis: Spread = {spread:.4f}")
        return spread

# Example Usage
if __name__ == "__main__":
    trade_analyzer = TradeFlowAnalyzer()
    sample_order_book = {
        "bids": [{"size": 5}, {"size": 10}, {"size": 15}],
        "asks": [{"size": 7}, {"size": 8}, {"size": 9}]
    }
    trade_analyzer.analyze_trade_flow(sample_order_book)
    trade_analyzer.analyze_bid_ask_spread(sample_order_book)
