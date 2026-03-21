import numpy as np
import cvxpy as cp
import logging
import asyncio
from app.utils.database import DatabaseManager

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
RISK_FREE_RATE = 0.02  # Annual risk-free rate for Sharpe ratio calculation
MAX_ALLOCATION = 0.3  # Max allocation per asset
VOLATILITY_TARGET = 0.15  # Target portfolio volatility

class PortfolioOptimizer:
    """
    AI-Powered Portfolio Optimization Engine.
    """

    def __init__(self):
        """
        Initializes the portfolio optimizer.
        """
        self.db_manager = DatabaseManager()

    async def fetch_historical_data(self):
        """
        Retrieves historical price data for portfolio optimization.
        """
        assets = await self.db_manager.get_tradable_assets()
        historical_prices = await self.db_manager.get_historical_prices(assets)
        return historical_prices

    def optimize_portfolio(self, expected_returns, covariance_matrix):
        """
        Optimizes asset allocation using Mean-Variance Optimization (MVO).

        Args:
            expected_returns (np.array): Expected returns for each asset.
            covariance_matrix (np.array): Asset return covariance matrix.

        Returns:
            np.array: Optimized portfolio weights.
        """
        num_assets = len(expected_returns)
        weights = cp.Variable(num_assets)
        
        # Define risk function using covariance matrix
        risk = cp.quad_form(weights, covariance_matrix)
        
        # Objective: Maximize Sharpe Ratio (expected return - risk-free rate) / risk
        objective = cp.Maximize((expected_returns @ weights - RISK_FREE_RATE) / cp.sqrt(risk))
        
        # Constraints
        constraints = [
            cp.sum(weights) == 1,  # Sum of weights must be 1 (fully allocated)
            weights >= 0,  # No short selling
            weights <= MAX_ALLOCATION,  # Max allocation per asset
            risk <= VOLATILITY_TARGET  # Target volatility constraint
        ]
        
        # Solve optimization problem
        problem = cp.Problem(objective, constraints)
        problem.solve()
        
        return weights.value

    async def run_portfolio_optimization(self):
        """
        Executes AI-powered portfolio optimization process.
        """
        logging.info("🚀 Running AI-Powered Portfolio Optimization...")
        historical_prices = await self.fetch_historical_data()
        returns = np.log(historical_prices / historical_prices.shift(1)).dropna()
        
        expected_returns = returns.mean().values
        covariance_matrix = returns.cov().values
        
        optimal_weights = self.optimize_portfolio(expected_returns, covariance_matrix)
        logging.info(f"✅ Optimized Portfolio Weights: {optimal_weights}")

# Example Usage
if __name__ == "__main__":
    optimizer = PortfolioOptimizer()
    asyncio.run(optimizer.run_portfolio_optimization())
