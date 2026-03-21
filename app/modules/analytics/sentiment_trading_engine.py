import logging
import asyncio
import requests
import numpy as np
from textblob import TextBlob
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
TWITTER_API_ENDPOINT = "https://api.twitter.com/2/tweets/search/recent"
NEWS_API_ENDPOINT = "https://newsapi.org/v2/top-headlines"
SENTIMENT_THRESHOLD = 0.3  # Minimum sentiment score required for execution

class SentimentTradingEngine:
    """
    AI-Powered Sentiment-Based Trading Engine.
    """

    def __init__(self, twitter_api_key, news_api_key):
        """
        Initializes sentiment trading engine.

        Args:
            twitter_api_key (str): API key for Twitter sentiment analysis.
            news_api_key (str): API key for news sentiment analysis.
        """
        self.twitter_api_key = twitter_api_key
        self.news_api_key = news_api_key

    def fetch_twitter_sentiment(self, keyword):
        """
        Fetches and analyzes Twitter sentiment for a given keyword.

        Args:
            keyword (str): Cryptocurrency name or symbol.

        Returns:
            float: Sentiment score (-1 to 1).
        """
        headers = {"Authorization": f"Bearer {self.twitter_api_key}"}
        params = {"query": keyword, "max_results": 50}
        response = requests.get(TWITTER_API_ENDPOINT, headers=headers, params=params)

        if response.status_code == 200:
            tweets = response.json().get("data", [])
            sentiment_scores = [TextBlob(tweet["text"]).sentiment.polarity for tweet in tweets]
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
            logging.info(f"🐦 Twitter Sentiment for {keyword}: {avg_sentiment:.2f}")
            return avg_sentiment

        logging.error("⚠️ Failed to fetch Twitter sentiment data.")
        return 0

    def fetch_news_sentiment(self, keyword):
        """
        Fetches and analyzes news sentiment for a given keyword.

        Args:
            keyword (str): Cryptocurrency name or symbol.

        Returns:
            float: Sentiment score (-1 to 1).
        """
        params = {"q": keyword, "apiKey": self.news_api_key, "language": "en"}
        response = requests.get(NEWS_API_ENDPOINT, params=params)

        if response.status_code == 200:
            articles = response.json().get("articles", [])
            sentiment_scores = [TextBlob(article["title"]).sentiment.polarity for article in articles]
            avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
            logging.info(f"📰 News Sentiment for {keyword}: {avg_sentiment:.2f}")
            return avg_sentiment

        logging.error("⚠️ Failed to fetch news sentiment data.")
        return 0

    async def execute_sentiment_trade(self, asset):
        """
        Executes a trade based on sentiment analysis.

        Args:
            asset (str): Cryptocurrency asset.
        """
        twitter_sentiment = self.fetch_twitter_sentiment(asset)
        news_sentiment = self.fetch_news_sentiment(asset)
        overall_sentiment = (twitter_sentiment + news_sentiment) / 2

        if overall_sentiment > SENTIMENT_THRESHOLD:
            logging.info(f"🚀 Buying {asset} due to positive sentiment ({overall_sentiment:.2f})")
        elif overall_sentiment < -SENTIMENT_THRESHOLD:
            logging.info(f"📉 Selling {asset} due to negative sentiment ({overall_sentiment:.2f})")
        else:
            logging.info(f"⚖️ No trade executed for {asset} (Sentiment: {overall_sentiment:.2f})")

    async def run_sentiment_trading(self):
        """
        Continuously analyzes sentiment and executes trades.
        """
        logging.info("🚀 Starting AI Sentiment Trading Engine...")
        while True:
            await self.execute_sentiment_trade("BTC")
            await asyncio.sleep(10)


# Example Usage
if __name__ == "__main__":
    sentiment_trader = SentimentTradingEngine("YOUR_TWITTER_API_KEY", "YOUR_NEWS_API_KEY")
    asyncio.run(sentiment_trader.run_sentiment_trading())
