"""
Bruce AI -- News Monitor Module

Aggregates news from free RSS feeds for financial, crypto, shipping, and market data.
Provides basic keyword-based sentiment analysis on headlines.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

import feedparser

logger = logging.getLogger("Bruce.NewsMonitor")

DEFAULT_TIMEOUT = 15
MAX_ARTICLES_PER_FEED = 15

# ---------------------------------------------------------------------------
# RSS Feed Sources
# ---------------------------------------------------------------------------

CRYPTO_FEEDS = [
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ("CoinTelegraph", "https://cointelegraph.com/rss"),
    ("Bitcoin Magazine", "https://bitcoinmagazine.com/.rss/full/"),
    ("Decrypt", "https://decrypt.co/feed"),
]

SHIPPING_FEEDS = [
    ("gCaptain", "https://gcaptain.com/feed/"),
    ("The Maritime Executive", "https://maritime-executive.com/rss"),
    ("Splash247", "https://splash247.com/feed/"),
    ("Seatrade Maritime", "https://www.seatrade-maritime.com/rss.xml"),
]

MARKET_FEEDS = [
    ("MarketWatch Top Stories", "https://feeds.marketwatch.com/marketwatch/topstories/"),
    ("MarketWatch Markets", "https://feeds.marketwatch.com/marketwatch/marketpulse/"),
    ("CNBC Business", "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001147"),
    ("Reuters Business", "https://www.reutersagency.com/feed/?best-topics=business-finance"),
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
]

# ---------------------------------------------------------------------------
# Sentiment Lexicon
# ---------------------------------------------------------------------------

POSITIVE_WORDS = {
    "surge", "surges", "surging", "rally", "rallies", "rallying", "gain", "gains",
    "rise", "rises", "rising", "jump", "jumps", "soar", "soars", "boom", "booms",
    "bullish", "upbeat", "optimistic", "profit", "profits", "profitable", "growth",
    "recover", "recovery", "breakthrough", "upgrade", "record high", "outperform",
    "strong", "strength", "beat", "beats", "exceed", "exceeds", "positive",
    "approval", "approved", "launch", "launches", "adopt", "adoption",
}

NEGATIVE_WORDS = {
    "crash", "crashes", "crashing", "plunge", "plunges", "plunging", "drop",
    "drops", "fall", "falls", "falling", "decline", "declines", "slump", "slumps",
    "bearish", "pessimistic", "loss", "losses", "losing", "recession", "downturn",
    "sell-off", "selloff", "dump", "dumps", "fear", "fears", "risk", "risks",
    "warning", "warn", "warns", "crisis", "bankrupt", "bankruptcy", "fraud",
    "hack", "hacked", "exploit", "vulnerability", "ban", "bans", "banned",
    "lawsuit", "sue", "sued", "fine", "fined", "penalty", "investigation",
    "weak", "weakness", "miss", "misses", "default", "collapse", "collapses",
}


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def parse_rss(url: str, source_name: str = "", timeout: int = DEFAULT_TIMEOUT) -> List[Dict]:
    """
    Parse an RSS feed and return a list of article dicts.

    Returns:
        list of dicts with keys: title, url, source, published, summary
    """
    logger.debug("Parsing RSS feed: %s (%s)", source_name or url, url)
    try:
        feed = feedparser.parse(url, request_headers={"User-Agent": "BruceAI/4.0"})

        if feed.bozo and not feed.entries:
            logger.warning("Feed parse error for %s: %s", url, feed.bozo_exception)
            return []

        articles = []
        for entry in feed.entries[:MAX_ARTICLES_PER_FEED]:
            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6],
                                         tzinfo=timezone.utc).isoformat()
                except Exception:
                    published = getattr(entry, "published", "")

            summary = ""
            if hasattr(entry, "summary"):
                # Strip HTML from summary
                summary = re.sub(r"<[^>]+>", "", entry.summary)
                summary = re.sub(r"\s+", " ", summary).strip()[:300]

            articles.append({
                "title": getattr(entry, "title", ""),
                "url": getattr(entry, "link", ""),
                "source": source_name or feed.feed.get("title", ""),
                "published": published,
                "summary": summary,
            })

        logger.debug("Parsed %d articles from %s", len(articles), source_name or url)
        return articles

    except Exception as exc:
        logger.error("RSS parse error for %s: %s", url, exc)
        return []


def _aggregate_feeds(feeds: List[tuple], max_total: int = 30) -> Dict:
    """Aggregate articles from multiple RSS feeds."""
    all_articles = []
    errors = []

    for name, url in feeds:
        articles = parse_rss(url, source_name=name)
        if articles:
            all_articles.extend(articles)
        else:
            errors.append(f"{name}: no articles or feed error")

    # Sort by published date (newest first), falling back to order
    def sort_key(a):
        try:
            return datetime.fromisoformat(a["published"])
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    all_articles.sort(key=sort_key, reverse=True)
    all_articles = all_articles[:max_total]

    return {
        "success": len(all_articles) > 0,
        "count": len(all_articles),
        "articles": all_articles,
        "errors": errors if errors else None,
    }


def get_crypto_news(max_total: int = 30) -> Dict:
    """
    Aggregate cryptocurrency news from multiple RSS feeds.

    Returns:
        dict with keys: success, count, articles, errors
    """
    logger.info("Fetching crypto news from %d feeds", len(CRYPTO_FEEDS))
    result = _aggregate_feeds(CRYPTO_FEEDS, max_total)
    result["category"] = "crypto"
    return result


def get_shipping_news(max_total: int = 30) -> Dict:
    """
    Aggregate shipping and maritime news from RSS feeds.

    Returns:
        dict with keys: success, count, articles, errors
    """
    logger.info("Fetching shipping news from %d feeds", len(SHIPPING_FEEDS))
    result = _aggregate_feeds(SHIPPING_FEEDS, max_total)
    result["category"] = "shipping"
    return result


def get_market_news(max_total: int = 30) -> Dict:
    """
    Aggregate financial market news from RSS feeds.

    Returns:
        dict with keys: success, count, articles, errors
    """
    logger.info("Fetching market news from %d feeds", len(MARKET_FEEDS))
    result = _aggregate_feeds(MARKET_FEEDS, max_total)
    result["category"] = "market"
    return result


def get_sentiment(headlines: List[str]) -> Dict:
    """
    Perform basic keyword-based sentiment analysis on a list of headlines.

    Returns:
        dict with keys:
            overall: "positive" | "negative" | "neutral"
            score: float between -1.0 and 1.0
            positive_count: int
            negative_count: int
            neutral_count: int
            details: list of {headline, sentiment, matched_words}
    """
    if not headlines:
        return {
            "overall": "neutral",
            "score": 0.0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "details": [],
        }

    details = []
    pos_total = 0
    neg_total = 0
    neu_total = 0

    for headline in headlines:
        lower = headline.lower()
        words = set(re.findall(r"\b\w+(?:-\w+)?\b", lower))

        pos_matches = words & POSITIVE_WORDS
        neg_matches = words & NEGATIVE_WORDS

        pos_score = len(pos_matches)
        neg_score = len(neg_matches)

        if pos_score > neg_score:
            sentiment = "positive"
            pos_total += 1
        elif neg_score > pos_score:
            sentiment = "negative"
            neg_total += 1
        else:
            sentiment = "neutral"
            neu_total += 1

        details.append({
            "headline": headline[:200],
            "sentiment": sentiment,
            "matched_words": list(pos_matches | neg_matches),
        })

    total = len(headlines)
    score = (pos_total - neg_total) / total if total > 0 else 0.0
    score = max(-1.0, min(1.0, score))

    if score > 0.15:
        overall = "positive"
    elif score < -0.15:
        overall = "negative"
    else:
        overall = "neutral"

    return {
        "overall": overall,
        "score": round(score, 3),
        "positive_count": pos_total,
        "negative_count": neg_total,
        "neutral_count": neu_total,
        "details": details,
    }
