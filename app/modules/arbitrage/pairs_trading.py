import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from scipy.stats import pearsonr
from app.modules.execution.execution_engine import ExecutionEngine

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
CORRELATION_THRESHOLD = 0.8  # Minimum correlation required for pairs trading
SPREAD_THRESHOLD = 2.0  # Z-score threshold for trading signal

class PairsTrading:
    """
    AI-Enhanced Pairs Trading System.
    """

    def __init__(self, asset_pairs):
        """
        Initializes the Pairs Trading system.

        Args:
            asset_pairs (list of tuples): List of asset pairs to monitor.
        """
        self.asset_pairs = asset_pairs
        self.execution_engine = ExecutionEngine()
        self.price_data = {pair: [] for pair in asset_pairs}

    def update_price_data(self, pair, price1, price2):
        """
        Updates historical price data for a given asset pair.

        Args:
            pair (tuple): (Asset A, Asset B)
            price1 (float): Price of Asset A
            price2 (float): Price of Asset B
        """
        self.price_data[pair].append((price1, price2))
        if len(self.price_data[pair]) > 100:
            self.price_data[pair].pop(0)  # Keep only recent data

    def check_correlation(self, pair):
        """
        Computes the correlation between two assets.

        Args:
            pair (tuple): (Asset A, Asset B)

        Returns:
            float: Correlation coefficient.
        """
        if len(self.price_data[pair]) < 50:
            return 0  # Not enough data

        prices = np.array(self.price_data[pair])
        correlation, _ = pearsonr(prices[:, 0], prices[:, 1])
        return correlation

    def trade_pair(self, pair):
        """
        Executes a pairs trade if a statistical edge is detected.

        Args:
            pair (tuple): (Asset A, Asset B)
        """
        correlation = self.check_correlation(pair)
        if correlation < CORRELATION_THRESHOLD:
            return  # No strong correlation

        spread = np.array(self.price_data[pair])[:, 0] - np.array(self.price_data[pair])[:, 1]
        z_scores = (spread - np.mean(spread)) / np.std(spread)

        if z_scores[-1] > SPREAD_THRESHOLD:
            logging.info(f"📈 Pairs Trading Signal - Short {pair[0]}, Long {pair[1]}")
            self.execution_engine.execute_market_order(pair[0], "SELL", size=1)
            self.execution_engine.execute_market_order(pair[1], "BUY", size=1)
        elif z_scores[-1] < -SPREAD_THRESHOLD:
            logging.info(f"📉 Pairs Trading Signal - Long {pair[0]}, Short {pair[1]}")
            self.execution_engine.execute_market_order(pair[0], "BUY", size=1)
            self.execution_engine.execute_market_order(pair[1], "SELL", size=1)

# Example Usage
if __name__ == "__main__":
    pairs_trader = PairsTrading([("BTC/USDT", "ETH/USDT")])
    pairs_trader.update_price_data(("BTC/USDT", "ETH/USDT"), 50000, 4000)
    pairs_trader.trade_pair(("BTC/USDT", "ETH/USDT"))
