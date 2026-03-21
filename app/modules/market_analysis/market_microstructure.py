import logging
import asyncio
import numpy as np
from app.config.settings import Config
from app.modules.market_analysis.trade_flow_analyzer import TradeFlowAnalyzer

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class MarketMicrostructure:
    """
    AI-Powered Market Microstructure Analysis for Trade Execution Optimization.
    """

    def __init__(self):
        """
        Initializes the market microstructure analysis system.
        """
        self.trade_flow_analyzer = TradeFlowAnalyzer()

    async def detect_order_flow_imbalance(self, order_book):
        """
        Detects order flow imbalance in the order book.

        Args:
            order_book (dict): Real-time order book data.

        Returns:
            float: Order imbalance ratio.
        """
        bid_volumes = np.array([order["size"] for order in order_book["bids"][:5]])
        ask_volumes = np.array([order["size"] for order in order_book["asks"][:5]])

        imbalance_ratio = np.sum(bid_volumes) / (np.sum(bid_volumes) + np.sum(ask_volumes))

        logging.info(f"📊 Order Flow Imbalance Ratio: {imbalance_ratio:.4f}")
        return imbalance_ratio

    async def detect_hidden_liquidity(self, order_book):
        """
        Detects iceberg orders or hidden liquidity in the order book.

        Args:
            order_book (dict): Real-time order book data.

        Returns:
            bool: True if iceberg orders are detected.
        """
        avg_trade_size = np.mean([order["size"] for order in order_book["bids"][:10]])
        iceberg_detected = avg_trade_size > np.percentile([order["size"] for order in order_book["bids"]], 95)

        if iceberg_detected:
            logging.warning("🚨 Hidden Liquidity Detected: Iceberg Order Identified.")

        return iceberg_detected

    async def analyze_market_structure(self, order_book):
        """
        Runs full market microstructure analysis.

        Args:
            order_book (dict): Live market data.
        """
        await self.detect_order_flow_imbalance(order_book)
        await self.detect_hidden_liquidity(order_book)
        await self.trade_flow_analyzer.analyze_trade_flow(order_book)

# Example Usage
if __name__ == "__main__":
    market_analyzer = MarketMicrostructure()
    sample_order_book = {
        "bids": [{"size": 5}, {"size": 10}, {"size": 15}],
        "asks": [{"size": 7}, {"size": 8}, {"size": 9}]
    }
    asyncio.run(market_analyzer.analyze_market_structure(sample_order_book))
