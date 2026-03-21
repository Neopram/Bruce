import logging
import aiohttp
import asyncio
from transformers import pipeline

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
NEWS_SOURCES = {
    "coindesk": "https://www.coindesk.com/news/rss",
    "cointelegraph": "https://cointelegraph.com/rss"
}

class NewsFetcher:
    """
    AI-Powered News Sentiment Analyzer.
    """

    def __init__(self):
        """
        Initializes news sentiment analysis.
        """
        self.sentiment_pipeline = pipeline("sentiment-analysis")

    async def fetch_news(self, source_url):
        """
        Fetches news articles from RSS feeds.

        Args:
            source_url (str): RSS feed URL.

        Returns:
            list: Extracted news headlines.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(source_url) as response:
                    return await response.text()
        except Exception as e:
            logging.error(f"🚨 Failed to fetch news from {source_url}: {e}")
            return []

    async def fetch_news_sentiment(self):
        """
        Fetches news and analyzes sentiment.

        Returns:
            float: Aggregated news sentiment score.
        """
        sentiments = []
        for source, url in NEWS_SOURCES.items():
            headlines = await self.fetch_news(url)
            for headline in headlines.split("\n")[:5]:  # Analyze top 5 headlines
                sentiment = self.sentiment_pipeline(headline)[0]
                sentiments.append(sentiment["score"] if sentiment["label"] == "POSITIVE" else -sentiment["score"])

        return sum(sentiments) / len(sentiments) if sentiments else 0

# Example Usage
if __name__ == "__main__":
    news_fetcher = NewsFetcher()
    asyncio.run(news_fetcher.fetch_news_sentiment())
