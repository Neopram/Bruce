import logging
import aiohttp
import asyncio
import numpy as np
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
DEPTH_LOOKBACK_PERIOD = 100  # Number of past trades to analyze
SLIPPAGE_TOLERANCE = 0.003  # 0.3% maximum acceptable slippage

class MarketDepthAnalyzer:
    """
    AI-Powered Market Depth & Order Book Analysis System.
    """

    async def fetch_order_book(self):
        """
        Fetches real-time order book data.

        Returns:
            dict: Order book data.
        """
        url = f"https://www.okx.com/api/v5/market/books?instId={Config.TRADING_PAIR.replace('/', '-')}&sz=10"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"🚨 Failed to fetch order book: {e}")
            return {}

    async def analyze_market_depth(self):
        """
        Analyzes market depth and determines execution efficiency.

        Returns:
            dict: Depth analysis results.
        """
        order_book = await self.fetch_order_book()
        if not order_book or "data" not in order_book:
            return {"error": "No order book data available"}

        bids = [float(order[1]) for order in order_book["data"][0]["bids"][:5]]
        asks = [float(order[1]) for order in order_book["data"][0]["asks"][:5]]
        bid_liquidity = sum(bids)
        ask_liquidity = sum(asks)
        spread = abs(float(order_book["data"][0]["asks"][0][0]) - float(order_book["data"][0]["bids"][0][0]))

        execution_risk = spread > SLIPPAGE_TOLERANCE

        logging.info(f"📊 Market Depth Analysis: Bid Liquidity: {bid_liquidity}, Ask Liquidity: {ask_liquidity}, Execution Risk: {execution_risk}")

        return {
            "bid_liquidity": bid_liquidity,
            "ask_liquidity": ask_liquidity,
            "spread": spread,
            "execution_risk": execution_risk
        }

# Example Usage
if __name__ == "__main__":
    analyzer = MarketDepthAnalyzer()
    asyncio.run(analyzer.analyze_market_depth())
