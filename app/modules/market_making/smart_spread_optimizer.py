import logging
import asyncio
import numpy as np
from app.modules.market_analysis.market_microstructure import MarketMicrostructure
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
SPREAD_SCALING_FACTOR = 0.05  # Adjusts spread dynamically
MAX_SPREAD_WIDTH = 0.002  # Maximum allowable spread
VOLATILITY_LOOKBACK_PERIOD = 100  # Number of historical data points for spread calculations


class SmartSpreadOptimizer:
    """
    AI-Based Dynamic Spread Optimization.
    """

    def __init__(self):
        self.market_microstructure = MarketMicrostructure()

    async def fetch_market_volatility(self):
        """
        Retrieves real-time market volatility data.
        """
        volatility_data = await self.market_microstructure.get_market_volatility()
        return volatility_data["volatility"] if volatility_data else 0.01  # Default to 1% volatility

    def calculate_optimal_spread(self, volatility):
        """
        Computes the optimal bid-ask spread dynamically.
        """
        spread = SPREAD_SCALING_FACTOR * volatility
        spread = min(spread, MAX_SPREAD_WIDTH)  # Ensure spread does not exceed max limit
        return round(spread, 6)

    async def adjust_spread_dynamically(self):
        """
        Dynamically adjusts bid-ask spread based on real-time market conditions.
        """
        logging.info("🚀 Smart Spread Optimizer Activated...")
        while True:
            volatility = await self.fetch_market_volatility()
            optimal_spread = self.calculate_optimal_spread(volatility)

            logging.info(f"📊 Adjusted Spread: {optimal_spread:.6f} based on volatility: {volatility:.4f}")
            await asyncio.sleep(1)  # Recalculate every second

# Example Usage
if __name__ == "__main__":
    optimizer = SmartSpreadOptimizer()
    asyncio.run(optimizer.adjust_spread_dynamically())
