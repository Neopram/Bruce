# Transformer-based sentiment analysis (keyword-based implementation, no ML deps)
import re
from collections import defaultdict


class SentimentAnalyzer:
    """NLP sentiment analyzer using keyword-based scoring (no ML dependencies)."""

    POSITIVE = {
        "bullish": 0.8, "buy": 0.6, "long": 0.5, "moon": 0.9, "pump": 0.7,
        "rally": 0.7, "surge": 0.8, "profit": 0.7, "gain": 0.6, "up": 0.4,
        "good": 0.5, "great": 0.6, "excellent": 0.8, "strong": 0.5, "growth": 0.6,
        "breakout": 0.7, "support": 0.4, "accumulate": 0.6, "undervalued": 0.7,
        "opportunity": 0.6, "promising": 0.6, "recovery": 0.5, "upgrade": 0.6,
    }
    NEGATIVE = {
        "bearish": -0.8, "sell": -0.6, "short": -0.5, "crash": -0.9, "dump": -0.7,
        "drop": -0.6, "loss": -0.7, "down": -0.4, "bad": -0.5, "terrible": -0.8,
        "weak": -0.5, "decline": -0.6, "fear": -0.6, "panic": -0.8, "risk": -0.4,
        "overvalued": -0.7, "resistance": -0.3, "bubble": -0.7, "scam": -0.9,
        "bankruptcy": -0.9, "default": -0.8, "downgrade": -0.6, "recession": -0.7,
    }

    INTENT_KEYWORDS = {
        "trade": ["buy", "sell", "trade", "long", "short", "swap", "exchange", "order", "execute"],
        "info": ["what", "how", "why", "explain", "tell", "show", "price", "chart", "analysis"],
        "alert": ["alert", "notify", "remind", "watch", "monitor", "track", "warning", "trigger"],
        "portfolio": ["portfolio", "balance", "holdings", "position", "allocation", "diversify"],
        "news": ["news", "report", "announcement", "update", "headline", "event", "earnings"],
    }

    TICKER_PATTERN = re.compile(r'\b[A-Z]{2,5}\b')
    AMOUNT_PATTERN = re.compile(r'\$[\d,]+(?:\.\d{1,2})?|\b\d+(?:,\d{3})*(?:\.\d{1,2})?\s*(?:USD|BTC|ETH|USDT)\b')
    DATE_PATTERN = re.compile(
        r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b|'
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2}(?:,?\s+\d{4})?\b',
        re.IGNORECASE,
    )

    # Common English words that look like tickers but aren't
    TICKER_STOPWORDS = {
        "THE", "FOR", "AND", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN", "HER",
        "WAS", "ONE", "OUR", "OUT", "HAS", "HIS", "HOW", "ITS", "MAY", "NEW",
        "NOW", "OLD", "SEE", "WAY", "WHO", "DID", "GET", "HIM", "LET", "SAY",
        "SHE", "TOO", "USE", "BUY", "USD", "BTC", "ETH",
    }

    def analyze(self, text):
        """Analyze sentiment of a single text, returning score and label.

        Args:
            text: Input text string.

        Returns:
            Dict with 'score' (-1 to 1), 'label', and matched words.
        """
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        total_score = 0.0
        matched = []

        for word in words:
            if word in self.POSITIVE:
                total_score += self.POSITIVE[word]
                matched.append((word, self.POSITIVE[word]))
            elif word in self.NEGATIVE:
                total_score += self.NEGATIVE[word]
                matched.append((word, self.NEGATIVE[word]))

        # Normalize to -1..1 range
        if matched:
            score = max(-1.0, min(1.0, total_score / len(matched)))
        else:
            score = 0.0

        if score > 0.2:
            label = "positive"
        elif score < -0.2:
            label = "negative"
        else:
            label = "neutral"

        return {
            "score": round(score, 4),
            "label": label,
            "matched_words": matched,
            "word_count": len(words),
        }

    def analyze_batch(self, texts):
        """Analyze sentiment for a batch of texts.

        Args:
            texts: List of text strings.

        Returns:
            Dict with individual results, summary statistics.
        """
        results = [self.analyze(t) for t in texts]
        scores = [r["score"] for r in results]

        if scores:
            avg = sum(scores) / len(scores)
            pos_count = sum(1 for s in scores if s > 0.2)
            neg_count = sum(1 for s in scores if s < -0.2)
            neu_count = len(scores) - pos_count - neg_count
        else:
            avg = 0.0
            pos_count = neg_count = neu_count = 0

        return {
            "results": results,
            "summary": {
                "average_score": round(avg, 4),
                "positive_count": pos_count,
                "negative_count": neg_count,
                "neutral_count": neu_count,
                "total": len(texts),
            },
        }

    def extract_entities(self, text):
        """Extract ticker symbols, monetary amounts, and dates from text.

        Args:
            text: Input text.

        Returns:
            Dict with 'tickers', 'amounts', and 'dates'.
        """
        # Tickers: uppercase 2-5 letter words, filtering stopwords
        raw_tickers = self.TICKER_PATTERN.findall(text)
        tickers = sorted(set(t for t in raw_tickers if t not in self.TICKER_STOPWORDS))

        amounts = self.AMOUNT_PATTERN.findall(text)
        dates = self.DATE_PATTERN.findall(text)

        return {
            "tickers": tickers,
            "amounts": amounts,
            "dates": dates,
        }

    def classify_intent(self, text):
        """Classify the user's intent from text.

        Args:
            text: User input text.

        Returns:
            Dict with primary intent, confidence, and all intent scores.
        """
        text_lower = text.lower()
        scores = {}

        for intent, keywords in self.INTENT_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in text_lower)
            scores[intent] = matches

        total = sum(scores.values())
        if total == 0:
            return {"intent": "unknown", "confidence": 0.0, "scores": scores}

        normalized = {k: round(v / total, 3) for k, v in scores.items()}
        primary = max(scores, key=scores.get)
        confidence = round(scores[primary] / total, 3)

        return {
            "intent": primary,
            "confidence": confidence,
            "scores": normalized,
        }
