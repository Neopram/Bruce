import time
import logging
import asyncio
import aiohttp
import numpy as np
from collections import deque
from app.config.settings import Config
from app.modules.machine_learning.reinforcement_learning import ReinforcementLearningAgent

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
MAX_RETRIES = 3
TRADE_ACTIONS = ["HOLD", "BUY", "SELL"]
ORDER_BOOK_DEPTH = 10  # How many levels of the order book to analyze
LATENCY_OPTIMIZATION_ENABLED = True  # Enables aggressive latency reduction techniques


class HighFrequencyTrader:
    """
    AI-powered High-Frequency Trading (HFT) system optimized for ultra-low latency execution.
    """

    def __init__(self):
        """
        Initializes the HFT trading system.
        """
        self.reinforcement_agent = ReinforcementLearningAgent()
        self.order_latency_tracker = deque(maxlen=100)  # Stores execution latencies
        self.spread_threshold = 0.01  # Min spread difference for arbitrage execution

    async def fetch_order_book(self):
        """
        Retrieves real-time order book data from OKX.

        Returns:
            dict: Processed order book with best bids/asks.
        """
        endpoint = f"https://www.okx.com/api/v5/market/books?instId={Config.TRADING_PAIR.replace('/', '-')}&sz={ORDER_BOOK_DEPTH}"
        return await self._fetch_market_data(endpoint)

    async def _fetch_market_data(self, endpoint):
        """
        Fetches real-time market data asynchronously.

        Args:
            endpoint (str): API endpoint.

        Returns:
            dict: API response.
        """
        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint) as response:
                        response.raise_for_status()
                        return await response.json()
            except aiohttp.ClientError as e:
                logging.error(f"🚨 API Request Failed: {e} (Attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(0.1)  # Retry quickly in case of failure

        return {}

    async def execute_trade(self, action, price, size):
        """
        Executes a market trade with ultra-low latency.

        Args:
            action (str): "BUY" or "SELL".
            price (float): Price to execute the order.
            size (float): Order size.

        Returns:
            dict: Order execution details.
        """
        start_time = time.time()

        order_payload = {
            "instId": Config.TRADING_PAIR.replace("/", "-"),
            "tdMode": "cash",
            "side": action.lower(),
            "ordType": "market",
            "sz": str(size),
            "px": str(price),
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://www.okx.com/api/v5/trade/order",
                json=order_payload,
                headers={"Authorization": f"Bearer {Config.OKX_API_KEY}"}
            ) as response:
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                self.order_latency_tracker.append(execution_time)
                response_data = await response.json()

                logging.info(f"⚡ Trade Executed ({action}): {size} @ {price}")
                logging.info(f"📊 Execution Latency: {execution_time:.2f}ms")

                return response_data

    async def predict_and_trade(self):
        """
        Uses AI to predict the next optimal trading action and executes it instantly.
        """
        action = await self.reinforcement_agent.predict_trade_action()
        if action in ["BUY", "SELL"]:
            order_book = await self.fetch_order_book()
            best_price = float(order_book["data"][0]["bids"][0][0]) if action == "BUY" else float(order_book["data"][0]["asks"][0][0])

            await self.execute_trade(action, best_price, size=0.1)  # Default size 0.1 BTC

    async def hft_loop(self):
        """
        Runs the high-frequency trading loop with AI-powered execution.
        """
        logging.info("🚀 High-Frequency Trading Engine Started!")
        while True:
            await self.predict_and_trade()
            await asyncio.sleep(0.05)  # 50ms loop for ultra-fast trading


# Example Usage
if __name__ == "__main__":
    hft_trader = HighFrequencyTrader()
    asyncio.run(hft_trader.hft_loop())
