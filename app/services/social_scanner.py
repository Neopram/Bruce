"""
Social Sentiment Scanner - Analyzes social-media sentiment for crypto/finance
keywords, provides trending topics, and a simulated Fear & Greed index.
"""

import random
from datetime import datetime, timezone
from typing import Dict, List, Optional


_TRENDING_POOL = [
    "Bitcoin ETF inflows",
    "Ethereum staking yields",
    "Solana DeFi surge",
    "Federal Reserve rate decision",
    "Stablecoin regulation",
    "AI tokens rally",
    "Layer-2 scaling wars",
    "NFT market recovery",
    "Memecoin mania",
    "On-chain whale movements",
    "DePIN adoption",
    "Real-world asset tokenization",
]

_SENTIMENT_LABELS = {
    (0.6, 1.0): "very bullish",
    (0.2, 0.6): "bullish",
    (-0.2, 0.2): "neutral",
    (-0.6, -0.2): "bearish",
    (-1.0, -0.6): "very bearish",
}


def _label_for_score(score: float) -> str:
    for (lo, hi), label in _SENTIMENT_LABELS.items():
        if lo <= score <= hi:
            return label
    return "neutral"


class SocialSentimentScanner:
    """Scans and aggregates social sentiment for financial keywords."""

    def scan_sentiment(self, keyword: str) -> dict:
        """Analyze aggregated sentiment for a keyword across social sources."""
        twitter_score = round(random.uniform(-1.0, 1.0), 3)
        reddit_score = round(random.uniform(-1.0, 1.0), 3)
        news_score = round(random.uniform(-1.0, 1.0), 3)
        composite = round((twitter_score + reddit_score + news_score) / 3, 3)

        return {
            "keyword": keyword,
            "composite_score": composite,
            "label": _label_for_score(composite),
            "sources": {
                "twitter": {"score": twitter_score, "sample_size": random.randint(200, 5000)},
                "reddit": {"score": reddit_score, "sample_size": random.randint(50, 1500)},
                "news": {"score": news_score, "sample_size": random.randint(10, 300)},
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_trending_topics(self, limit: int = 5) -> List[dict]:
        """Return currently trending crypto/finance topics (simulated)."""
        selected = random.sample(_TRENDING_POOL, k=min(limit, len(_TRENDING_POOL)))
        topics = []
        for idx, topic in enumerate(selected, start=1):
            score = round(random.uniform(-1.0, 1.0), 3)
            topics.append(
                {
                    "rank": idx,
                    "topic": topic,
                    "sentiment_score": score,
                    "label": _label_for_score(score),
                    "mention_count": random.randint(500, 50000),
                }
            )
        return topics

    def get_fear_greed_index(self) -> dict:
        """Return a simulated crypto Fear & Greed index (0-100)."""
        value = random.randint(0, 100)
        if value <= 20:
            classification = "Extreme Fear"
        elif value <= 40:
            classification = "Fear"
        elif value <= 60:
            classification = "Neutral"
        elif value <= 80:
            classification = "Greed"
        else:
            classification = "Extreme Greed"

        return {
            "value": value,
            "classification": classification,
            "components": {
                "volatility": random.randint(0, 100),
                "market_momentum": random.randint(0, 100),
                "social_media": random.randint(0, 100),
                "dominance": random.randint(0, 100),
                "trends": random.randint(0, 100),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Backward-compatible alias
class SocialScanner(SocialSentimentScanner):
    """Legacy alias kept for backward compatibility."""

    def fetch_twitter_sentiment(self, symbol: str) -> dict:
        result = self.scan_sentiment(symbol)
        return {"symbol": symbol, "sentiment_score": result["sources"]["twitter"]["score"]}

    def scan_reddit_threads(self, keyword: str) -> List[str]:
        return [f"Post relacionado con {keyword}", f"Otro post sobre {keyword}"]

    def analyze_wallet_activity(self, wallet_address: str) -> dict:
        return {"tx_count": random.randint(100, 1000), "last_activity": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
