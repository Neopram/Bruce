import logging
import requests
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Sentiment Analyzer
nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()

# Constants
NEWS_API_URL = "https://newsapi.org/v2/everything?q=crypto&apiKey=YOUR_NEWSAPI_KEY"
TWITTER_API_URL = "https://api.twitter.com/2/tweets/search/recent?query=crypto&tweet.fields=created_at,lang&max_results=10"
TWITTER_BEARER_TOKEN = "YOUR_TWITTER_BEARER_TOKEN"

class SentimentAnalysisEngine:
    """
    AI-Powered Market Sentiment Analysis Engine.
    """

    def fetch_news_headlines(self):
        """
        Fetches latest crypto news headlines.

        Returns:
            list: List of news headlines.
        """
        response = requests.get(NEWS_API_URL)
        if response.status_code == 200:
            articles = response.json().get("articles", [])
            return [article["title"] for article in articles]
        return []

    def fetch_twitter_sentiment(self):
        """
        Fetches recent crypto-related tweets and analyzes sentiment.

        Returns:
            dict: Sentiment analysis results.
        """
        headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
        response = requests.get(TWITTER_API_URL, headers=headers)

        if response.status_code == 200:
            tweets = [tweet["text"] for tweet in response.json().get("data", [])]
            sentiments = [sia.polarity_scores(tweet)["compound"] for tweet in tweets]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
            return {"avg_sentiment": avg_sentiment, "tweets_analyzed": len(tweets)}

        return {"avg_sentiment": 0, "tweets_analyzed": 0}

    def analyze_sentiment(self):
        """
        Combines news & Twitter sentiment for market insights.

        Returns:
            float: Overall sentiment score.
        """
        headlines = self.fetch_news_headlines()
        news_sentiments = [sia.polarity_scores(headline)["compound"] for headline in headlines]
        news_sentiment_score = sum(news_sentiments) / len(news_sentiments) if news_sentiments else 0

        twitter_sentiment = self.fetch_twitter_sentiment()
        combined_score = (news_sentiment_score + twitter_sentiment["avg_sentiment"]) / 2

        logging.info(f"📊 Market Sentiment Score: {combined_score:.2f}")
        return combined_score

# Example Usage
if __name__ == "__main__":
    sentiment_engine = SentimentAnalysisEngine()
    sentiment_engine.analyze_sentiment()
