import logging
import numpy as np
import asyncio
from app.modules.market_analysis.market_microstructure import MarketMicrostructure
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
ORDER_FLOW_LOOKBACK = 100  # Number of recent trades to analyze
IMBALANCE_THRESHOLD = 0.02  # 2% order book imbalance triggers action
TRADE_SENTIMENT_THRESHOLD = 0.1  # Significant deviation in trade direction


class OrderFlowAnalyzer:
    """
    AI-Powered Order Flow Analysis & Prediction.
    """

    def __init__(self):
        self.market_microstructure = MarketMicrostructure()

    async def fetch_recent_trades(self):
        """
        Fetches real-time recent trade data.
        """
        return await self.market_microstructure.get_trade_history(limit=ORDER_FLOW_LOOKBACK)

    async def compute_order_imbalance(self):
        """
        Computes order book imbalance to detect liquidity shifts.
        
        Returns:
            float: Order imbalance percentage.
        """
        order_book = await self.market_microstructure.get_order_book()
        if not order_book:
            logging.warning("⚠️ No market data available.")
            return 0

        bid_volumes = sum([float(order["size"]) for order in order_book["bids"][:10]])
        ask_volumes = sum([float(order["size"]) for order in order_book["asks"][:10]])
        
        imbalance = (bid_volumes - ask_volumes) / (bid_volumes + ask_volumes)
        
        if abs(imbalance) > IMBALANCE_THRESHOLD:
            logging.warning(f"🚨 Order Book Imbalance Detected: {imbalance:.4f}")
        
        return imbalance

    async def analyze_trade_sentiment(self):
        """
        Analyzes recent trade direction to assess market sentiment.
        
        Returns:
            float: Trade sentiment score (-1 to 1).
        """
        trades = await self.fetch_recent_trades()
        if not trades:
            logging.warning("⚠️ No trade data available.")
            return 0

        buy_trades = sum([1 for trade in trades if trade["side"] == "BUY"])
        sell_trades = sum([1 for trade in trades if trade["side"] == "SELL"])
        
        sentiment_score = (buy_trades - sell_trades) / (buy_trades + sell_trades)
        
        if abs(sentiment_score) > TRADE_SENTIMENT_THRESHOLD:
            logging.info(f"📊 Trade Sentiment Score: {sentiment_score:.3f}")
        
        return sentiment_score

# Example Usage
if __name__ == "__main__":
    analyzer = OrderFlowAnalyzer()
    asyncio.run(analyzer.compute_order_imbalance())
