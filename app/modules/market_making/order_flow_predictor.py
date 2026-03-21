import logging
import asyncio
import aiohttp
import numpy as np
from app.config.settings import Config
from app.modules.market_making.liquidity_forecaster import LiquidityForecaster

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
ORDER_FLOW_API = f"https://www.okx.com/api/v5/market/trades?instId={Config.TRADING_PAIR.replace('/', '-')}"

class OrderFlowPredictor:
    """
    AI-Powered Order Flow Prediction for Market Making.
    """

    def __init__(self):
        """
        Initializes order flow predictor.
        """
        self.liquidity_forecaster = LiquidityForecaster()

    async def fetch_order_flow(self):
        """
        Fetches real-time order flow data.

        Returns:
            list: List of recent trade transactions.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ORDER_FLOW_API) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"🚨 Failed to fetch order flow data: {e}")
            return {}

    async def analyze_order_flow(self):
        """
        Analyzes incoming buy/sell orders to predict market direction.

        Returns:
            dict: Predicted order flow trend.
        """
        order_data = await self.fetch_order_flow()
        if not order_data or "data" not in order_data:
            return {"error": "No order flow data available"}

        buy_volume = sum(float(trade["sz"]) for trade in order_data["data"] if trade["side"] == "buy")
        sell_volume = sum(float(trade["sz"]) for trade in order_data["data"] if trade["side"] == "sell")

        order_flow_trend = "Bullish" if buy_volume > sell_volume else "Bearish"

        return {
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "order_flow_trend": order_flow_trend
        }

    async def optimize_market_making(self):
        """
        Uses order flow analysis to optimize market-making strategies.
        """
        order_flow = await self.analyze_order_flow()
        if "error" in order_flow:
            logging.error("❌ Order flow analysis failed.")
            return

        trend = order_flow["order_flow_trend"]
        logging.info(f"📊 Order Flow Trend Detected: {trend}")

        await self.liquidity_forecaster.adjust_liquidity_positioning(trend)

# Example Usage
if __name__ == "__main__":
    predictor = OrderFlowPredictor()
    asyncio.run(predictor.optimize_market_making())
