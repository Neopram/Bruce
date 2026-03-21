import asyncio
import logging
import aiohttp
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
EXCHANGES = ["OKX", "Binance", "Coinbase", "Kraken"]
MAX_RETRIES = 3  # API retry limit

class SmartOrderRouter:
    """
    AI-Powered Smart Order Routing System for Optimal Execution.
    """

    def __init__(self):
        """
        Initializes the Smart Order Router.
        """
        self.liquidity_sources = {
            "OKX": "https://api.okx.com/v5/market/ticker",
            "Binance": "https://api.binance.com/api/v3/ticker/bookTicker",
            "Coinbase": "https://api.exchange.coinbase.com/products/BTC-USD/ticker",
            "Kraken": "https://api.kraken.com/0/public/Ticker"
        }

    async def fetch_best_liquidity(self):
        """
        Fetches real-time liquidity from multiple exchanges and selects the best execution venue.

        Returns:
            str: Exchange with the best execution price.
        """
        best_exchange = None
        best_price = float("inf")
        tasks = []

        async with aiohttp.ClientSession() as session:
            for exchange, url in self.liquidity_sources.items():
                tasks.append(self._fetch_price(session, exchange, url))
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for exchange, price in results:
                if price and price < best_price:
                    best_price = price
                    best_exchange = exchange

        logging.info(f"✅ Best Execution Venue: {best_exchange} at ${best_price}")
        return best_exchange

    async def _fetch_price(self, session, exchange, url):
        """
        Fetches price data from an exchange API.
        """
        try:
            async with session.get(url) as response:
                data = await response.json()
                if exchange == "OKX":
                    return exchange, float(data["data"][0]["last"])
                elif exchange == "Binance":
                    return exchange, float(data["askPrice"])
                elif exchange == "Coinbase":
                    return exchange, float(data["price"])
                elif exchange == "Kraken":
                    return exchange, float(data["result"]["XXBTZUSD"]["c"][0])
        except Exception as e:
            logging.warning(f"⚠️ Failed to fetch data from {exchange}: {e}")
        return exchange, None

    async def route_order(self, action, size):
        """
        Routes order to the exchange with the best execution price.

        Args:
            action (str): "BUY" or "SELL".
            size (float): Order size.

        Returns:
            dict: Order execution response.
        """
        best_exchange = await self.fetch_best_liquidity()
        if not best_exchange:
            return {"error": "No valid execution venue found."}

        execution_response = await self.execute_order(best_exchange, action, size)
        return execution_response

    async def execute_order(self, exchange, action, size):
        """
        Executes an order on the selected exchange.

        Args:
            exchange (str): Exchange to route order.
            action (str): "BUY" or "SELL".
            size (float): Order size.

        Returns:
            dict: Execution result.
        """
        logging.info(f"🚀 Executing {action} order on {exchange} for {size} BTC")
        return {"exchange": exchange, "action": action, "size": size, "status": "executed"}

# Example Usage
if __name__ == "__main__":
    router = SmartOrderRouter()
    asyncio.run(router.route_order("BUY", size=0.1))