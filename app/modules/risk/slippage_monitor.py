import logging
import aiohttp
import asyncio
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
SLIPPAGE_THRESHOLD = 0.005  # 0.5% max acceptable slippage
SLIPPAGE_MONITOR_INTERVAL = 5  # Check slippage every 5 seconds

class SlippageMonitor:
    """
    AI-Powered Trade Slippage Monitoring System.
    """

    async def fetch_latest_trade_data(self):
        """
        Retrieves recent trade execution prices.

        Returns:
            float: Last executed trade price.
        """
        url = f"https://www.okx.com/api/v5/market/trades?instId={Config.TRADING_PAIR.replace('/', '-')}&limit=1"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    trade_data = await response.json()
                    return float(trade_data["data"][0]["px"])
        except Exception as e:
            logging.error(f"🚨 Failed to fetch trade data: {e}")
            return None

    async def fetch_order_book(self):
        """
        Retrieves real-time order book data.

        Returns:
            dict: Order book including bid-ask prices.
        """
        url = f"https://www.okx.com/api/v5/market/books?instId={Config.TRADING_PAIR.replace('/', '-')}&sz=5"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"🚨 Failed to fetch order book: {e}")
            return {}

    async def monitor_slippage(self):
        """
        Monitors trade slippage in real-time.
        """
        while True:
            trade_price = await self.fetch_latest_trade_data()
            order_book = await self.fetch_order_book()

            if trade_price and "data" in order_book:
                best_bid = float(order_book["data"][0]["bids"][0][0])
                best_ask = float(order_book["data"][0]["asks"][0][0])
                mid_price = (best_bid + best_ask) / 2

                slippage = abs(trade_price - mid_price) / mid_price
                if slippage > SLIPPAGE_THRESHOLD:
                    logging.warning(f"⚠️ High Slippage Detected: {slippage:.5f}")

            await asyncio.sleep(SLIPPAGE_MONITOR_INTERVAL)

# Example Usage
if __name__ == "__main__":
    slippage_monitor = SlippageMonitor()
    asyncio.run(slippage_monitor.monitor_slippage())
