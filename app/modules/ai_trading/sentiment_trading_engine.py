import logging
import asyncio
from app.modules.ai_trading.market_sentiment import MarketSentiment

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Trading Thresholds
BUY_THRESHOLD = 0.3
SELL_THRESHOLD = -0.3
FEAR_GREED_THRESHOLD = 20  # Extreme fear or greed triggers trade execution

class SentimentTradingEngine:
    """
    AI-Based Sentiment Trading Execution Engine.
    """

    def __init__(self):
        """
        Initializes the sentiment trading engine.
        """
        self.sentiment_analyzer = MarketSentiment()

    async def execute_trade_based_on_sentiment(self):
        """
        Executes buy/sell trades based on sentiment analysis.
        """
        sentiment_data = await self.sentiment_analyzer.analyze_market_sentiment()
        overall_sentiment = sentiment_data["overall_sentiment"]
        fear_greed_index = sentiment_data["fear_greed_index"]

        if overall_sentiment > BUY_THRESHOLD or fear_greed_index > 80:
            logging.info("🚀 Sentiment is bullish! Executing BUY order.")
        elif overall_sentiment < SELL_THRESHOLD or fear_greed_index < FEAR_GREED_THRESHOLD:
            logging.info("📉 Sentiment is bearish! Executing SELL order.")
        else:
            logging.info("⏳ Sentiment is neutral. No trade executed.")

    async def run_sentiment_trading(self):
        """
        Continuously executes sentiment-based trading.
        """
        logging.info("🚀 Starting AI Sentiment Trading System...")
        while True:
            await self.execute_trade_based_on_sentiment()
            await asyncio.sleep(5)


# Example Usage
if __name__ == "__main__":
    sentiment_trader = SentimentTradingEngine()
    asyncio.run(sentiment_trader.run_sentiment_trading())
