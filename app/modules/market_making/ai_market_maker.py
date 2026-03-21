import logging
import asyncio
import numpy as np
import random
from datetime import datetime
from app.modules.execution.smart_order_router import SmartOrderRouter
from app.modules.risk.risk_manager import RiskManager
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
SPREAD_ADJUSTMENT_FACTOR = 0.02  # Dynamic spread adjustment based on volatility
LIQUIDITY_THRESHOLD = 10000  # Min available liquidity for aggressive market-making
VOLATILITY_LOOKBACK = 50  # Number of periods for volatility estimation


class AIMarketMaker:
    """
    AI-Powered Market Making Engine.
    """

    def __init__(self):
        self.smart_order_router = SmartOrderRouter()
        self.risk_manager = RiskManager()

    async def fetch_market_data(self):
        """
        Fetches real-time order book data for spread optimization.
        """
        return await self.smart_order_router.get_order_book()

    def compute_dynamic_spread(self, volatility):
        """
        Dynamically adjusts bid-ask spread based on market volatility.
        """
        base_spread = 0.001  # 0.1% default spread
        dynamic_spread = base_spread + (SPREAD_ADJUSTMENT_FACTOR * volatility)
        return round(dynamic_spread, 5)

    async def execute_market_making(self):
        """
        Runs continuous AI-driven market making.
        """
        logging.info("🚀 AI Market Maker Activated...")
        while True:
            market_data = await self.fetch_market_data()
            if not market_data:
                logging.warning("⚠️ No market data available. Skipping cycle.")
                await asyncio.sleep(1)
                continue

            best_bid = float(market_data["bids"][0]["price"])
            best_ask = float(market_data["asks"][0]["price"])
            mid_price = (best_bid + best_ask) / 2
            volatility = np.std([float(order["price"]) for order in market_data["bids"][:VOLATILITY_LOOKBACK]])

            spread = self.compute_dynamic_spread(volatility)
            bid_price = round(mid_price - (spread / 2), 5)
            ask_price = round(mid_price + (spread / 2), 5)

            if await self.risk_manager.enforce_risk_limits():
                logging.warning("🚨 Risk limits reached. Pausing market-making.")
                await asyncio.sleep(5)
                continue

            logging.info(f"📊 Market Making Orders | Bid: {bid_price} | Ask: {ask_price}")
            await self.smart_order_router.place_limit_order("BUY", bid_price, size=1)
            await self.smart_order_router.place_limit_order("SELL", ask_price, size=1)

            await asyncio.sleep(0.5)  # Microsecond-level delay to adapt to market

# Example Usage
if __name__ == "__main__":
    market_maker = AIMarketMaker()
    asyncio.run(market_maker.execute_market_making())
