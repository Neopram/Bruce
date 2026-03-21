import logging
import aiohttp
import asyncio
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
ORDER_BOOK_API = f"https://www.okx.com/api/v5/market/books?instId={Config.TRADING_PAIR.replace('/', '-')}&sz=5"

class LiquidityForecaster:
    """
    AI-Powered Liquidity Forecasting & Market-Making Optimization.
    """

    async def fetch_order_book(self):
        """
        Fetches real-time order book data.

        Returns:
            dict: Order book data.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ORDER_BOOK_API) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"🚨 Failed to fetch order book data: {e}")
            return {}

    async def predict_liquidity_shift(self):
        """
        Predicts liquidity shifts by analyzing order book depth.

        Returns:
            dict: Liquidity shift analysis.
        """
        order_book = await self.fetch_order_book()
        if not order_book or "data" not in order_book:
            return {"error": "No order book data available"}

        bid_depth = sum(float(order[1]) for order in order_book["data"][0]["bids"])
        ask_depth = sum(float(order[1]) for order in order_book["data"][0]["asks"])

        liquidity_trend = "Increasing" if bid_depth > ask_depth else "Decreasing"

        return {
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
            "liquidity_trend": liquidity_trend
        }

    async def adjust_liquidity_positioning(self, order_flow_trend):
        """
        Adjusts market-making orders based on liquidity prediction.

        Args:
            order_flow_trend (str): Detected order flow trend ("Bullish" or "Bearish").
        """
        liquidity_shift = await self.predict_liquidity_shift()
        if "error" in liquidity_shift:
            logging.error("❌ Liquidity forecasting failed.")
            return

        trend = liquidity_shift["liquidity_trend"]
        logging.info(f"📊 Liquidity Shift Detected: {trend}")

        if order_flow_trend == "Bullish" and trend == "Increasing":
            logging.info("📈 Optimizing market-making: Adjusting bids higher.")
        elif order_flow_trend == "Bearish" and trend == "Decreasing":
            logging.info("📉 Optimizing market-making: Adjusting asks lower.")
        else:
            logging.info("⚖️ Market neutral: Maintaining liquidity positioning.")

# Example Usage
if __name__ == "__main__":
    forecaster = LiquidityForecaster()
    asyncio.run(forecaster.adjust_liquidity_positioning(order_flow_trend="Bullish"))
