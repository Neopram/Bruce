import logging
import numpy as np
import asyncio
from app.modules.market_analysis.market_microstructure import MarketMicrostructure
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
SLIPPAGE_THRESHOLD = 0.002  # 0.2% price movement as threshold
LIQUIDITY_IMPACT_SENSITIVITY = 0.01  # Minimum change in liquidity to trigger alerts
ORDER_FLOW_LOOKBACK = 50  # Number of trades to analyze


class MarketImpactAnalyzer:
    """
    AI-Powered Market Impact Prediction Engine.
    """

    def __init__(self):
        self.market_microstructure = MarketMicrostructure()

    async def fetch_order_book_data(self):
        """
        Retrieves real-time order book data.
        """
        return await self.market_microstructure.get_order_book()

    async def compute_market_impact(self, order_size):
        """
        Predicts market impact based on order book depth.

        Args:
            order_size (float): The size of the order.

        Returns:
            float: Estimated price impact.
        """
        order_book = await self.fetch_order_book_data()
        if not order_book:
            logging.warning("⚠️ No market data available.")
            return 0

        best_bid = float(order_book["bids"][0]["price"])
        best_ask = float(order_book["asks"][0]["price"])
        mid_price = (best_bid + best_ask) / 2
        market_depth = sum([float(order["size"]) for order in order_book["bids"][:10]])

        impact = (order_size / market_depth) * LIQUIDITY_IMPACT_SENSITIVITY
        estimated_slippage = impact * mid_price

        logging.info(f"📊 Estimated Market Impact: {estimated_slippage:.6f} USDT")
        return estimated_slippage

    async def detect_abnormal_liquidity_drops(self):
        """
        Monitors order book liquidity to detect sudden drops.
        """
        order_book = await self.fetch_order_book_data()
        if not order_book:
            return False

        liquidity_levels = [float(order["size"]) for order in order_book["bids"][:10]]
        avg_liquidity = np.mean(liquidity_levels)

        if avg_liquidity < LIQUIDITY_IMPACT_SENSITIVITY:
            logging.warning("🚨 Abnormal Liquidity Drop Detected!")
            return True
        return False

# Example Usage
if __name__ == "__main__":
    analyzer = MarketImpactAnalyzer()
    asyncio.run(analyzer.compute_market_impact(order_size=100))
