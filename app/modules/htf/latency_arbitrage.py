import logging
import asyncio
import numpy as np
import aiohttp
from app.config.settings import Config
from app.modules.execution.execution_engine import ExecutionEngine

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
MICROSECOND_LATENCY_THRESHOLD = 0.0005  # 0.05% threshold for arbitrage
MAX_RETRIES = 3

class LatencyArbitrage:
    """
    AI-Powered Latency Arbitrage System.
    """

    def __init__(self):
        """
        Initializes the Latency Arbitrage system.
        """
        self.execution_engine = ExecutionEngine()

    async def fetch_market_prices(self):
        """
        Retrieves real-time prices from multiple exchanges.

        Returns:
            dict: Price data from different venues.
        """
        okx_endpoint = f"https://www.okx.com/api/v5/market/ticker?instId={Config.TRADING_PAIR.replace('/', '-')}"
        binance_endpoint = f"https://api.binance.com/api/v3/ticker/price?symbol={Config.TRADING_PAIR.replace('/', '')}"

        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(okx_endpoint) as okx_response, session.get(binance_endpoint) as binance_response:
                        okx_price = await okx_response.json()
                        binance_price = await binance_response.json()

                        return {
                            "OKX": float(okx_price["data"][0]["last"]),
                            "Binance": float(binance_price["price"])
                        }
            except aiohttp.ClientError as e:
                logging.error(f"🚨 API Request Failed: {e} (Attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(2)

        return {}

    async def detect_latency_arbitrage_opportunity(self):
        """
        Identifies latency arbitrage opportunities by comparing price differences.

        Returns:
            bool: True if arbitrage exists, False otherwise.
        """
        prices = await self.fetch_market_prices()
        if not prices:
            return False

        price_diff = abs(prices["OKX"] - prices["Binance"])
        if price_diff / prices["OKX"] > MICROSECOND_LATENCY_THRESHOLD:
            logging.info(f"⚡ Latency Arbitrage Detected! OKX: {prices['OKX']} | Binance: {prices['Binance']}")
            return True

        return False

    async def execute_latency_arbitrage_trade(self):
        """
        Executes arbitrage trades when an opportunity arises.
        """
        if await self.detect_latency_arbitrage_opportunity():
            logging.info("🚀 Executing Latency Arbitrage Trade")
            self.execution_engine.execute_market_order("BUY", size=0.05)  # Arbitrage size


# Example Usage
if __name__ == "__main__":
    latency_arbitrage = LatencyArbitrage()
    asyncio.run(latency_arbitrage.execute_latency_arbitrage_trade())
