import logging
import asyncio
import requests
from textblob import TextBlob
from app.utils.database import DatabaseManager
from app.modules.order_manager import OrderManager

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# API Sources
NEWS_API = "https://newsapi.org/v2/everything?q=crypto&apiKey=YOUR_NEWS_API_KEY"
TWITTER_API = "https://api.twitter.com/2/tweets/search/recent"

class SentimentTradingEngine:
    """
    AI-Powered Sentiment Trading Engine.
    """

    def __init__(self):
        """
        Initializes sentiment-based trading strategies.
        """
        self.db_manager = DatabaseManager()
        self.order_manager = OrderManager()

    async def fetch_news_sentiment(self):
        """
        Fetches recent crypto news and analyzes sentiment.
        """
        response = requests.get(NEWS_API)
        if response.status_code == 200:
            articles = response.json().get("articles", [])
            sentiments = [TextBlob(article["title"]).sentiment.polarity for article in articles]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            logging.info(f"📰 News Sentiment Score: {avg_sentiment:.2f}")
            return avg_sentiment
        logging.error("❌ Failed to fetch news data")
        return 0

    async def fetch_social_media_sentiment(self):
        """
        Fetches and analyzes social media sentiment from Twitter.
        """
        headers = {"Authorization": f"Bearer YOUR_TWITTER_BEARER_TOKEN"}
        response = requests.get(TWITTER_API, headers=headers)
        if response.status_code == 200:
            tweets = response.json().get("data", [])
            sentiments = [TextBlob(tweet["text"]).sentiment.polarity for tweet in tweets]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            logging.info(f"🐦 Social Media Sentiment Score: {avg_sentiment:.2f}")
            return avg_sentiment
        logging.error("❌ Failed to fetch Twitter data")
        return 0

    async def execute_sentiment_trade(self):
        """
        Uses AI-generated sentiment scores to execute trades.
        """
        news_sentiment = await self.fetch_news_sentiment()
        social_sentiment = await self.fetch_social_media_sentiment()

        total_sentiment = (news_sentiment + social_sentiment) / 2

        if total_sentiment > 0.3:
            logging.info("🚀 Bullish Sentiment Detected - Placing BUY Order")
            return await self.order_manager.create_market_order("BTC-USD", "buy", size=0.5)

        if total_sentiment < -0.3:
            logging.info("📉 Bearish Sentiment Detected - Placing SELL Order")
            return await self.order_manager.create_market_order("BTC-USD", "sell", size=0.5)

        logging.info("📊 Neutral Sentiment - No Trade Executed")
        return "No trade executed"

# Example Usage
if __name__ == "__main__":
    sentiment_engine = SentimentTradingEngine()
    asyncio.run(sentiment_engine.execute_sentiment_trade())
