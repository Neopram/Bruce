import logging
import asyncio
import numpy as np
from app.utils.database import DatabaseManager

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
ORDER_IMBALANCE_THRESHOLD = 0.02  # 2% imbalance triggers alert

class OrderFlowAnalyzer:
    """
    AI-Powered Order Flow & Market Microstructure Analyzer.
    """

    def __init__(self):
        """
        Initializes AI-driven order flow analytics.
        """
        self.db_manager = DatabaseManager()

    async def analyze_order_imbalance(self):
        """
        Detects buy/sell imbalances in order flow.
        """
        market_data = await self.db_manager.get_market_order_flow()
        bid_volume = sum([order["size"] for order in market_data["bids"]])
        ask_volume = sum([order["size"] for order in market_data["asks"]])

        imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume)
        logging.info(f"📊 Order Flow Imbalance: {imbalance:.4f}")

        if abs(imbalance) > ORDER_IMBALANCE_THRESHOLD:
            logging.warning("⚠️ Significant Order Flow Imbalance Detected!")
            return imbalance

        return 0

    async def detect_dark_pool_activity(self):
        """
        Identifies hidden liquidity & dark pool trades.
        """
        trade_data = await self.db_manager.get_recent_trades()
        dark_pool_trades = [trade for trade in trade_data if trade["source"] == "dark_pool"]

        logging.info(f"🕵️‍♂️ Detected {len(dark_pool_trades)} Dark Pool Trades")
        return dark_pool_trades

    async def analyze_market_maker_activity(self):
        """
        Tracks institutional market maker activity.
        """
        order_book = await self.db_manager.get_market_order_book()
        large_orders = [order for order in order_book["bids"] if order["size"] > 100] + \
                       [order for order in order_book["asks"] if order["size"] > 100]

        logging.info(f"🏦 Detected {len(large_orders)} Market Maker Orders")
        return large_orders

    async def run_order_flow_analysis(self):
        """
        Runs AI-powered order flow analytics continuously.
        """
        while True:
            await self.analyze_order_imbalance()
            await self.detect_dark_pool_activity()
            await self.analyze_market_maker_activity()
            await asyncio.sleep(5)  # Check every 5 seconds

# Example Usage
if __name__ == "__main__":
    order_flow_analyzer = OrderFlowAnalyzer()
    asyncio.run(order_flow_analyzer.run_order_flow_analysis())
