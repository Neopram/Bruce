import logging
import asyncio
import requests
import tweepy
import numpy as np
from textblob import TextBlob
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Twitter API Credentials (Replace with actual credentials)
TWITTER_API_KEY = "your_twitter_api_key"
TWITTER_API_SECRET = "your_twitter_api_secret"
TWITTER_ACCESS_TOKEN = "your_twitter_access_token"
TWITTER_ACCESS_SECRET = "your_twitter_access_secret"

# News API Key (Replace with actual credentials)
NEWS_API_KEY = "your_news_api_key"

# Market Fear & Greed Index URL
FEAR_GREED_INDEX_URL = "https://api.alternative.me/fng/?limit=1"

class MarketSentiment:
    """
    AI-Powered Market Sentiment Analysis for Trading Decisions.
    """

    def __init__(self):
        """
        Initializes sentiment analysis system.
        """
        self.twitter_auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET)
        self.twitter_auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET)
        self.twitter_api = tweepy.API(self.twitter_auth)

    async def fetch_social_sentiment(self, keyword="Bitcoin"):
        """
        Fetches social media sentiment based on keyword.

        Args:
            keyword (str): Market keyword to track sentiment.

        Returns:
            float: Sentiment score (-1 to +1).
        """
        tweets = self.twitter_api.search_tweets(q=keyword, count=50, lang="en")
        sentiment_scores = [TextBlob(tweet.text).sentiment.polarity for tweet in tweets]

        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
        logging.info(f"📊 Social Media Sentiment ({keyword}): {avg_sentiment:.2f}")
        return avg_sentiment

    async def fetch_news_sentiment(self, keyword="crypto"):
        """
        Fetches financial news sentiment based on keyword.

        Args:
            keyword (str): Market keyword to track sentiment.

        Returns:
            float: Sentiment score (-1 to +1).
        """
        url = f"https://newsapi.org/v2/everything?q={keyword}&apiKey={NEWS_API_KEY}"
        response = requests.get(url).json()
        
        if "articles" not in response:
            return 0

        articles = response["articles"][:10]  # Analyze latest 10 articles
        sentiment_scores = [TextBlob(article["title"]).sentiment.polarity for article in articles]

        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
        logging.info(f"📰 News Sentiment ({keyword}): {avg_sentiment:.2f}")
        return avg_sentiment

    async def fetch_fear_greed_index(self):
        """
        Fetches the Fear & Greed Index.

        Returns:
            int: Fear & Greed score (0-100).
        """
        response = requests.get(FEAR_GREED_INDEX_URL).json()
        if "data" in response and len(response["data"]) > 0:
            index_value = int(response["data"][0]["value"])
            logging.info(f"😱 Fear & Greed Index: {index_value}")
            return index_value

        return 50  # Neutral default

    async def analyze_market_sentiment(self):
        """
        Performs a full sentiment analysis combining multiple sources.

        Returns:
            dict: Aggregated sentiment scores.
        """
        social_sentiment = await self.fetch_social_sentiment()
        news_sentiment = await self.fetch_news_sentiment()
        fear_greed_index = await self.fetch_fear_greed_index()

        overall_sentiment = (social_sentiment + news_sentiment) / 2
        return {
            "social_sentiment": social_sentiment,
            "news_sentiment": news_sentiment,
            "fear_greed_index": fear_greed_index,
            "overall_sentiment": overall_sentiment
        }


# Example Usage
if __name__ == "__main__":
    sentiment_analyzer = MarketSentiment()
    asyncio.run(sentiment_analyzer.analyze_market_sentiment())
