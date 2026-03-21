import logging
import asyncio
import aiohttp
import numpy as np
from transformers import pipeline
from app.config.settings import Config
from app.modules.market_analysis.news_fetcher import NewsFetcher

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
SOCIAL_MEDIA_APIS = {
    "twitter": "https://api.twitter.com/2/tweets/search/recent",
    "reddit": "https://www.reddit.com/r/cryptocurrency/top.json"
}
ON_CHAIN_APIS = {
    "whale_alert": "https://api.whale-alert.io/v1/transactions",
    "liquidations": "https://api.coinglass.com/api/futures/liquidations"
}

SENTIMENT_THRESHOLD = 0.6  # Confidence score threshold for bullish/bearish signals

class SentimentAnalyzer:
    """
    AI-Powered Sentiment Analysis & Market Prediction System.
    """

    def __init__(self):
        """
        Initializes sentiment analysis models.
        """
        self.news_fetcher = NewsFetcher()
        self.sentiment_pipeline = pipeline("sentiment-analysis")

    async def fetch_social_media_sentiment(self):
        """
        Fetches and analyzes sentiment from Twitter & Reddit.

        Returns:
            float: Aggregated sentiment score.
        """
        sentiments = []
        for platform, api_url in SOCIAL_MEDIA_APIS.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url) as response:
                        data = await response.json()
                        posts = data.get("data", [])[:5]  # Analyze top 5 posts
                        for post in posts:
                            sentiment = self.sentiment_pipeline(post["text"])[0]
                            sentiments.append(sentiment["score"] if sentiment["label"] == "POSITIVE" else -sentiment["score"])
            except Exception as e:
                logging.error(f"🚨 Failed to fetch {platform} sentiment: {e}")

        return np.mean(sentiments) if sentiments else 0

    async def fetch_on_chain_sentiment(self):
        """
        Analyzes whale activity and liquidation data for market sentiment.

        Returns:
            float: Aggregated on-chain sentiment score.
        """
        whale_activity = []
        for api_name, api_url in ON_CHAIN_APIS.items():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(api_url) as response:
                        data = await response.json()
                        tx_count = len(data.get("transactions", []))
                        whale_activity.append(tx_count)
            except Exception as e:
                logging.error(f"🚨 Failed to fetch {api_name} data: {e}")

        whale_score = np.mean(whale_activity) if whale_activity else 0
        return 0.5 + (whale_score / 1000)  # Normalized score

    async def compute_sentiment_score(self):
        """
        Computes overall sentiment score combining news, social media, and on-chain data.

        Returns:
            float: Final sentiment score.
        """
        news_sentiment = await self.news_fetcher.fetch_news_sentiment()
        social_sentiment = await self.fetch_social_media_sentiment()
        on_chain_sentiment = await self.fetch_on_chain_sentiment()

        final_score = (news_sentiment + social_sentiment + on_chain_sentiment) / 3
        return final_score

    async def predict_market_trend(self):
        """
        Predicts whether the market trend is bullish or bearish based on sentiment analysis.

        Returns:
            str: "Bullish" or "Bearish"
        """
        sentiment_score = await self.compute_sentiment_score()
        trend = "Bullish" if sentiment_score > SENTIMENT_THRESHOLD else "Bearish"

        logging.info(f"📊 Market Sentiment Score: {sentiment_score:.2f} | Prediction: {trend}")
        return trend

# Example Usage
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    asyncio.run(analyzer.predict_market_trend())
