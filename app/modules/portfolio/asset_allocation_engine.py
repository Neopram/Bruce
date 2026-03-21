import logging
import asyncio
import numpy as np
from app.utils.database import DatabaseManager

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
VOLATILITY_THRESHOLD = 0.05  # Volatility threshold for asset reallocation
MOMENTUM_LOOKBACK = 30  # Days for momentum calculation
ALLOCATION_REBALANCE_INTERVAL = 86400  # Rebalance every 24 hours

class AssetAllocationEngine:
    """
    AI-Powered Asset Allocation Engine.
    """

    def __init__(self):
        """
        Initializes the asset allocation engine.
        """
        self.db_manager = DatabaseManager()

    async def fetch_asset_data(self):
        """
        Retrieves historical asset performance data.
        """
        assets = await self.db_manager.get_tradable_assets()
        historical_prices = await self.db_manager.get_historical_prices(assets)
        return historical_prices

    def calculate_momentum(self, prices):
        """
        Computes asset momentum for allocation decisions.
        
        Args:
            prices (pd.DataFrame): Historical price data.

        Returns:
            np.array: Asset momentum scores.
        """
        momentum_scores = prices.pct_change(MOMENTUM_LOOKBACK).iloc[-1]
        return momentum_scores

    async def adjust_asset_allocations(self):
        """
        Dynamically reallocates assets based on AI-driven factors.
        """
        logging.info("🚀 Rebalancing Asset Allocations...")
        historical_prices = await self.fetch_asset_data()
        volatility = historical_prices.pct_change().std()
        momentum_scores = self.calculate_momentum(historical_prices)
        
        high_momentum_assets = momentum_scores[momentum_scores > 0]
        low_volatility_assets = volatility[volatility < VOLATILITY_THRESHOLD]

        selected_assets = high_momentum_assets.index.intersection(low_volatility_assets.index)
        
        logging.info(f"✅ Rebalanced Asset Allocations: {selected_assets.tolist()}")

    async def run_asset_allocation(self):
        """
        Runs the AI-powered asset allocation strategy continuously.
        """
        logging.info("🚀 Starting AI-Powered Asset Allocation Engine...")
        while True:
            await self.adjust_asset_allocations()
            await asyncio.sleep(ALLOCATION_REBALANCE_INTERVAL)

# Example Usage
if __name__ == "__main__":
    allocation_engine = AssetAllocationEngine()
    asyncio.run(allocation_engine.run_asset_allocation())
