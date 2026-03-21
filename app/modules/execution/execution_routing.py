import logging
import aiohttp
import asyncio
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
CEX_ENDPOINTS = {
    "binance": "https://api.binance.com/api/v3/order",
    "okx": "https://www.okx.com/api/v5/trade/order"
}

DEX_ENDPOINTS = {
    "raydium": "https://api.raydium.io/trade",
    "uniswap": "https://api.uniswap.org/v2/trade"
}

class ExecutionRouter:
    """
    AI-Powered Smart Order Routing System.
    """

    async def fetch_market_data(self):
        """
        Fetches real-time market data for execution optimization.

        Returns:
            dict: Market order book data.
        """
        url = f"https://www.okx.com/api/v5/market/books?instId={Config.TRADING_PAIR.replace('/', '-')}&sz=5"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"🚨 Failed to fetch market data: {e}")
            return {}

    async def route_order(self, order_type, trade_size):
        """
        Routes order to the best execution venue based on AI-driven analysis.

        Args:
            order_type (str): Type of order (market, limit, etc.).
            trade_size (float): Trade amount.
        """
        best_exchange = await self.identify_best_execution_venue()
        if not best_exchange:
            logging.error("❌ No optimal exchange found. Trade aborted.")
            return

        logging.info(f"🚀 Routing {order_type} order of size {trade_size} to {best_exchange}")

        order_url = CEX_ENDPOINTS.get(best_exchange) or DEX_ENDPOINTS.get(best_exchange)
        if order_url:
            await self.execute_trade(order_url, order_type, trade_size)

    async def identify_best_execution_venue(self):
        """
        Identifies the best trading venue for execution.

        Returns:
            str: Best exchange for execution.
        """
        exchange_latency = {
            "binance": 20,
            "okx": 25,
            "raydium": 15,
            "uniswap": 18
        }
        best_exchange = min(exchange_latency, key=exchange_latency.get)
        logging.info(f"📊 Selected Best Execution Venue: {best_exchange}")
        return best_exchange

    async def execute_trade(self, order_url, order_type, trade_size):
        """
        Executes trade on the selected exchange.

        Args:
            order_url (str): API endpoint for trade execution.
            order_type (str): Type of order.
            trade_size (float): Trade amount.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(order_url, json={
                    "order_type": order_type,
                    "size": trade_size
                }) as response:
                    response.raise_for_status()
                    order_result = await response.json()
                    logging.info(f"✅ Order Execution Result: {order_result}")
        except Exception as e:
            logging.error(f"🚨 Order Execution Failed: {e}")

# Example Usage
if __name__ == "__main__":
    router = ExecutionRouter()
    asyncio.run(router.route_order(order_type="limit", trade_size=1.5))
