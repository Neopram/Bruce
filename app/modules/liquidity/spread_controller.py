import logging
import numpy as np

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
SPREAD_ADJUSTMENT_FACTOR = 0.001  # Minimum adjustment per volatility shift
VOLATILITY_LOOKBACK = 20  # Number of trades to consider for volatility
DEFAULT_SPREAD = 0.0005  # Default bid-ask spread

class SpreadController:
    """
    AI-Powered Spread Optimization for Market Making.
    """

    def __init__(self):
        """
        Initializes the spread optimization module.
        """
        self.current_spread = DEFAULT_SPREAD
        self.trade_history = []

    def calculate_volatility(self):
        """
        Calculates short-term market volatility based on trade history.

        Returns:
            float: Volatility percentage.
        """
        if len(self.trade_history) < VOLATILITY_LOOKBACK:
            return np.std(self.trade_history) if self.trade_history else 0.01

        recent_prices = self.trade_history[-VOLATILITY_LOOKBACK:]
        return np.std(recent_prices)

    def adjust_spread(self):
        """
        Dynamically adjusts the bid-ask spread based on volatility.
        """
        volatility = self.calculate_volatility()
        new_spread = DEFAULT_SPREAD + (volatility * SPREAD_ADJUSTMENT_FACTOR)

        if new_spread != self.current_spread:
            logging.info(f"📈 Adjusting Spread: {self.current_spread:.5f} → {new_spread:.5f}")
            self.current_spread = new_spread

        return self.current_spread

    def update_trade_history(self, price):
        """
        Updates trade history for spread optimization.

        Args:
            price (float): Executed trade price.
        """
        self.trade_history.append(price)
        if len(self.trade_history) > VOLATILITY_LOOKBACK:
            self.trade_history.pop(0)

        self.adjust_spread()

# Example Usage
if __name__ == "__main__":
    spread_optimizer = SpreadController()

    sample_prices = [100 + np.random.uniform(-1, 1) for _ in range(30)]
    for price in sample_prices:
        spread_optimizer.update_trade_history(price)

    logging.info(f"📊 Final Optimized Spread: {spread_optimizer.current_spread:.5f}")
