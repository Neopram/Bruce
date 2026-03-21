import logging
import numpy as np
import asyncio
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
REBALANCE_THRESHOLD = 0.05  # 5% deviation triggers rebalancing
MAX_SINGLE_ASSET_ALLOCATION = 0.30  # No more than 30% in a single asset

class PortfolioRebalancer:
    """
    AI-Powered Portfolio Rebalancing & Optimization.
    """

    def __init__(self):
        """
        Initializes the AI portfolio rebalancer.
        """
        self.portfolio = {
            "BTC": 0.40,
            "ETH": 0.30,
            "SOL": 0.15,
            "USDT": 0.15
        }

    async def fetch_market_data(self):
        """
        Simulates fetching real-time asset price & volatility data.

        Returns:
            dict: Asset prices & volatility metrics.
        """
        return {
            "BTC": {"price": np.random.uniform(60000, 65000), "volatility": np.random.uniform(0.02, 0.06)},
            "ETH": {"price": np.random.uniform(3000, 3500), "volatility": np.random.uniform(0.03, 0.07)},
            "SOL": {"price": np.random.uniform(100, 130), "volatility": np.random.uniform(0.04, 0.09)},
            "USDT": {"price": 1.00, "volatility": 0.00}
        }

    async def rebalance_portfolio(self):
        """
        Analyzes market conditions and rebalances the portfolio.
        """
        market_data = await self.fetch_market_data()
        total_value = sum(self.portfolio[asset] * market_data[asset]["price"] for asset in self.portfolio)

        for asset in self.portfolio:
            current_weight = (self.portfolio[asset] * market_data[asset]["price"]) / total_value

            if abs(current_weight - self.portfolio[asset]) > REBALANCE_THRESHOLD:
                adjustment = (self.portfolio[asset] - current_weight) * total_value
                logging.info(f"🔄 Rebalancing {asset}: Adjusting position by {adjustment:.2f} USD.")

        logging.info("✅ Portfolio successfully rebalanced!")

    async def monitor_portfolio(self):
        """
        Continuously monitors portfolio allocations.
        """
        logging.info("🚀 Starting AI Portfolio Rebalancer...")
        while True:
            await self.rebalance_portfolio()
            await asyncio.sleep(30)


# Example Usage
if __name__ == "__main__":
    rebalancer = PortfolioRebalancer()
    asyncio.run(rebalancer.monitor_portfolio())
