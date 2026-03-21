import logging
import asyncio
import numpy as np
import aiohttp
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
ORDER_BOOK_DEPTH = 10
IMBALANCE_THRESHOLD = 0.05  # 5% imbalance triggers execution strategy change
MAX_RETRIES = 3

class MarketMicrostructure:
    """
    AI-Driven Market Microstructure Analysis System.
    """

    def __init__(self):
        """
        Initializes the Market Microstructure analyzer.
        """
        self.order_book_history = []

    async def fetch_order_book(self):
        """
        Retrieves real-time order book data from OKX.

        Returns:
            dict: Order book data.
        """
        endpoint = f"https://www.okx.com/api/v5/market/books?instId={Config.TRADING_PAIR.replace('/', '-')}&sz={ORDER_BOOK_DEPTH}"
        
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

    def analyze_order_book_imbalance(self, order_book):
        """
        Computes the order book imbalance to detect liquidity shifts.

        Args:
            order_book (dict): Order book data.

        Returns:
            float: Order book imbalance ratio.
        """
        if "data" not in order_book:
            return None

        bids = np.array([float(order[1]) for order in order_book["data"][0]["bids"]])
        asks = np.array([float(order[1]) for order in order_book["data"][0]["asks"]])

        total_bids = np.sum(bids)
        total_asks = np.sum(asks)

        imbalance = (total_bids - total_asks) / (total_bids + total_asks)

        logging.info(f"📊 Order Book Imbalance: {imbalance:.4f}")
        return imbalance

    async def detect_hidden_liquidity(self):
        """
        Detects hidden liquidity by analyzing order flow dynamics.

        Returns:
            bool: True if hidden liquidity is detected.
        """
        order_book = await self.fetch_order_book()
        if not order_book:
            return False

        imbalance = self.analyze_order_book_imbalance(order_book)

        if abs(imbalance) > IMBALANCE_THRESHOLD:
            logging.warning(f"⚠️ Hidden Liquidity Detected - Imbalance: {imbalance:.2f}")
            return True

        return False

    async def monitor_microstructure(self):
        """
        Continuously analyzes market microstructure.
        """
        while True:
            await self.detect_hidden_liquidity()
            await asyncio.sleep(5)  # Monitor every 5 seconds


# Example Usage
if __name__ == "__main__":
    microstructure = MarketMicrostructure()
    asyncio.run(microstructure.monitor_microstructure())
