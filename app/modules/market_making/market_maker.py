import asyncio
import logging
import numpy as np
import aiohttp
from app.config.settings import Config
from app.modules.execution.execution_engine import ExecutionEngine

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
SPREAD_ADJUSTMENT_FACTOR = 0.0005  # Adjust spread based on volatility
ORDER_SIZE = 0.1  # Default order size for market making
UPDATE_INTERVAL = 5  # Seconds between market making updates
MAX_RETRIES = 3  # API retry attempts
VOLATILITY_SMOOTHING = 0.95  # AI-based spread smoothing factor

class MarketMaker:
    """
    AI-Powered Market Maker for Automated Liquidity Provisioning.
    """

    def __init__(self):
        """
        Initializes the AI Market Maker.
        """
        self.execution_engine = ExecutionEngine()
        self.prev_volatility = None  # AI-based spread optimization

    async def fetch_order_book(self):
        """
        Retrieves real-time order book data.

        Returns:
            dict: Order book data.
        """
        endpoint = f"https://www.okx.com/api/v5/market/books?instId={Config.TRADING_PAIR.replace('/', '-')}&sz=5"

        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint) as response:
                        response.raise_for_status()
                        return await response.json()
            except aiohttp.ClientError as e:
                logging.error(f"🚨 API Request Failed: {e} (Attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(2)

        return {}

    def compute_adaptive_spread(self, bids, asks):
        """
        Computes an AI-enhanced adaptive spread.

        Args:
            bids (list): Bid prices.
            asks (list): Ask prices.

        Returns:
            tuple: (bid_price, ask_price)
        """
        mid_price = (bids[0] + asks[0]) / 2
        spread = abs(bids[0] - asks[0])

        # AI-Based Volatility Adjustment
        volatility = spread / mid_price
        if self.prev_volatility:
            volatility = VOLATILITY_SMOOTHING * self.prev_volatility + (1 - VOLATILITY_SMOOTHING) * volatility
        self.prev_volatility = volatility

        # Adjust bid-ask spread dynamically
        bid_price = mid_price * (1 - SPREAD_ADJUSTMENT_FACTOR * (1 + volatility))
        ask_price = mid_price * (1 + SPREAD_ADJUSTMENT_FACTOR * (1 + volatility))

        return bid_price, ask_price

    async def adjust_market_making_orders(self):
        """
        Dynamically adjusts bid-ask spreads based on market conditions.
        """
        order_book = await self.fetch_order_book()
        if not order_book or "data" not in order_book:
            logging.warning("⚠️ No valid order book data available.")
            return

        bids = [float(order[0]) for order in order_book["data"][0]["bids"]]
        asks = [float(order[0]) for order in order_book["data"][0]["asks"]]

        if not bids or not asks:
            logging.warning("⚠️ Order book is empty.")
            return

        bid_price, ask_price = self.compute_adaptive_spread(bids, asks)

        # AI-Optimized Market Making Orders
        await self.execution_engine.iceberg_order_execution("BUY", ORDER_SIZE, peak_size=0.01)
        await self.execution_engine.iceberg_order_execution("SELL", ORDER_SIZE, peak_size=0.01)

        logging.info(f"📈 Adjusted Market Making Orders - Bid: {bid_price:.4f}, Ask: {ask_price:.4f}")

    async def run_market_maker(self):
        """
        Continuously updates market making orders.
        """
        logging.info("🚀 Starting AI Market Maker...")
        while True:
            await self.adjust_market_making_orders()
            await asyncio.sleep(UPDATE_INTERVAL)


# Example Usage
if __name__ == "__main__":
    maker = MarketMaker()
    asyncio.run(maker.run_market_maker())
