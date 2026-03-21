import logging
import aiohttp
import asyncio
import numpy as np
from textblob import TextBlob
from app.config.settings import Config

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
TWITTER_API_URL = "https://api.twitter.com/2/tweets/search/recent?query=bitcoin"
REDDIT_API_URL = "https://www.reddit.com/r/cryptocurrency/top.json"
ONCHAIN_API_URL = "https://api.coingecko.com/api/v3/exchanges/binance/volume_chart?days=7"

SENTIMENT_WEIGHTING = {"social": 0.5, "onchain": 0.3, "news": 0.2}

class SentimentAnalysis:
    """
    AI-Powered Crypto Market Sentiment Analyzer.
    """

    def __init__(self):
        """
        Initializes the Sentiment Analysis system.
        """
        self.sentiment_index = 50  # Neutral baseline

    async def fetch_json(self, url, headers=None):
        """
        Fetches JSON data from an API.

        Args:
            url (str): API URL.
            headers (dict, optional): Headers for the request.

        Returns:
            dict: API response.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"🚨 API Request Failed: {e}")
            return {}

    async def analyze_social_sentiment(self):
        """
        Analyzes social media sentiment from Twitter & Reddit.

        Returns:
            float: Sentiment score (-100 to +100).
        """
        headers = {"Authorization": f"Bearer {Config.TWITTER_BEARER_TOKEN}"}
        twitter_data = await self.fetch_json(TWITTER_API_URL, headers=headers)
        reddit_data = await self.fetch_json(REDDIT_API_URL)

        twitter_sentiments = []
        for tweet in twitter_data.get("data", []):
            analysis = TextBlob(tweet["text"]).sentiment.polarity
            twitter_sentiments.append(analysis)

        reddit_sentiments = []
        for post in reddit_data.get("data", {}).get("children", []):
            analysis = TextBlob(post["data"]["title"]).sentiment.polarity
            reddit_sentiments.append(analysis)

        avg_twitter = np.mean(twitter_sentiments) if twitter_sentiments else 0
        avg_reddit = np.mean(reddit_sentiments) if reddit_sentiments else 0

        return (avg_twitter + avg_reddit) * 50  # Scale sentiment score

    async def analyze_onchain_sentiment(self):
        """
        Analyzes on-chain sentiment based on exchange inflows/outflows.

        Returns:
            float: Sentiment score (-100 to +100).
        """
        onchain_data = await self.fetch_json(ONCHAIN_API_URL)
        if not onchain_data:
            return 0

        total_volume = sum([point[1] for point in onchain_data])
        inflows = sum([point[1] for point in onchain_data if point[1] > 0])
        outflows = total_volume - inflows

        sentiment_score = ((inflows - outflows) / total_volume) * 100
        return sentiment_score

    async def compute_sentiment_index(self):
        """
        Computes the overall AI-powered sentiment index.

        Returns:
            float: Sentiment index (0-100).
        """
        social_sentiment = await self.analyze_social_sentiment()
        onchain_sentiment = await self.analyze_onchain_sentiment()

        self.sentiment_index = (
            SENTIMENT_WEIGHTING["social"] * social_sentiment +
            SENTIMENT_WEIGHTING["onchain"] * onchain_sentiment
        )

        logging.info(f"📊 AI Sentiment Index: {self.sentiment_index:.2f}")
        return self.sentiment_index

# Example Usage
if __name__ == "__main__":
    sentiment_analyzer = SentimentAnalysis()
    asyncio.run(sentiment_analyzer.compute_sentiment_index())
