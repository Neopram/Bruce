
# macro_events.py

"""
Macro Events Analyzer for Bruce AI.
Tracks macroeconomic events, classifies their market impact,
and correlates events with market movements.
Uses simulated data as default with hooks for real data sources.
"""

import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("Bruce.MacroAnalyzer")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
#  Simulated macro event data
# ---------------------------------------------------------------------------

MACRO_CATEGORIES = [
    "monetary_policy",
    "fiscal_policy",
    "geopolitical",
    "employment",
    "inflation",
    "trade",
    "energy",
    "technology",
    "regulation",
]

# Simulated event templates for when no real data source is available
SIMULATED_EVENTS = {
    "monetary_policy": [
        {"title": "Federal Reserve holds interest rates steady", "impact": "medium", "sentiment": "neutral"},
        {"title": "ECB signals potential rate cut in next quarter", "impact": "high", "sentiment": "bullish"},
        {"title": "Bank of Japan adjusts yield curve control policy", "impact": "high", "sentiment": "bearish"},
        {"title": "Fed minutes reveal hawkish tone among members", "impact": "medium", "sentiment": "bearish"},
        {"title": "Central bank injects liquidity into banking system", "impact": "medium", "sentiment": "bullish"},
    ],
    "fiscal_policy": [
        {"title": "Government announces new infrastructure spending bill", "impact": "medium", "sentiment": "bullish"},
        {"title": "Tax reform proposal under congressional review", "impact": "medium", "sentiment": "neutral"},
        {"title": "Budget deficit reaches record levels", "impact": "high", "sentiment": "bearish"},
        {"title": "Stimulus package approved for small businesses", "impact": "low", "sentiment": "bullish"},
    ],
    "geopolitical": [
        {"title": "Trade tensions escalate between major economies", "impact": "high", "sentiment": "bearish"},
        {"title": "Diplomatic breakthrough in regional conflict", "impact": "medium", "sentiment": "bullish"},
        {"title": "Sanctions imposed on major commodity exporter", "impact": "high", "sentiment": "bearish"},
        {"title": "International summit concludes with cooperation agreement", "impact": "low", "sentiment": "bullish"},
    ],
    "employment": [
        {"title": "Non-farm payrolls exceed expectations", "impact": "high", "sentiment": "bullish"},
        {"title": "Unemployment rate ticks up slightly", "impact": "medium", "sentiment": "bearish"},
        {"title": "Weekly jobless claims fall to multi-year low", "impact": "medium", "sentiment": "bullish"},
        {"title": "Tech sector announces wave of layoffs", "impact": "medium", "sentiment": "bearish"},
    ],
    "inflation": [
        {"title": "CPI comes in above consensus estimates", "impact": "high", "sentiment": "bearish"},
        {"title": "Core inflation shows signs of cooling", "impact": "high", "sentiment": "bullish"},
        {"title": "PPI data suggests pipeline price pressures easing", "impact": "medium", "sentiment": "bullish"},
        {"title": "Consumer inflation expectations rise to multi-year high", "impact": "medium", "sentiment": "bearish"},
    ],
    "trade": [
        {"title": "Trade surplus widens on strong export demand", "impact": "medium", "sentiment": "bullish"},
        {"title": "New tariffs announced on imported goods", "impact": "high", "sentiment": "bearish"},
        {"title": "Free trade agreement signed between regional partners", "impact": "medium", "sentiment": "bullish"},
    ],
    "energy": [
        {"title": "Oil prices surge on supply disruption concerns", "impact": "high", "sentiment": "bearish"},
        {"title": "OPEC+ agrees to production increase", "impact": "high", "sentiment": "bullish"},
        {"title": "Natural gas inventories below seasonal average", "impact": "medium", "sentiment": "bearish"},
        {"title": "Renewable energy investment hits record levels", "impact": "low", "sentiment": "neutral"},
    ],
    "technology": [
        {"title": "Major tech earnings beat analyst expectations", "impact": "medium", "sentiment": "bullish"},
        {"title": "AI regulation framework proposed by lawmakers", "impact": "medium", "sentiment": "neutral"},
        {"title": "Crypto regulatory clarity emerging in key markets", "impact": "high", "sentiment": "bullish"},
    ],
    "regulation": [
        {"title": "SEC proposes new rules for digital asset exchanges", "impact": "high", "sentiment": "bearish"},
        {"title": "Banking regulators ease capital requirements", "impact": "medium", "sentiment": "bullish"},
        {"title": "Anti-trust action filed against major platform", "impact": "medium", "sentiment": "bearish"},
    ],
}

# Impact weights for correlation scoring
IMPACT_WEIGHTS = {"high": 3, "medium": 2, "low": 1}
SENTIMENT_SCORES = {"bullish": 1.0, "neutral": 0.0, "bearish": -1.0}


class MacroAnalyzer:
    def __init__(self):
        self._event_cache: List[dict] = []
        self._correlation_history: List[dict] = []
        # Generate initial simulated events
        self._generate_simulated_events()

    def _generate_simulated_events(self, days: int = 30):
        """Generate a set of simulated macro events for the recent period."""
        self._event_cache = []
        now = datetime.now(timezone.utc)

        for category, events in SIMULATED_EVENTS.items():
            for event_template in events:
                # Assign a random date within the period
                days_ago = random.randint(0, days)
                event_date = now - timedelta(days=days_ago)

                event = {
                    "title": event_template["title"],
                    "category": category,
                    "impact": event_template["impact"],
                    "sentiment": event_template["sentiment"],
                    "date": event_date.strftime("%Y-%m-%d"),
                    "timestamp": event_date.isoformat(),
                    "source": "simulated",
                }
                self._event_cache.append(event)

        # Sort by date descending
        self._event_cache.sort(key=lambda e: e["timestamp"], reverse=True)

    def summary(self) -> dict:
        """
        Return a summary of the current macro outlook.
        Aggregates recent events to determine overall market direction.
        """
        if not self._event_cache:
            self._generate_simulated_events()

        recent = self._event_cache[:15]  # last 15 events

        # Calculate aggregate sentiment
        total_score = 0.0
        total_weight = 0.0
        category_scores: Dict[str, float] = {}
        impact_counts = {"high": 0, "medium": 0, "low": 0}

        for event in recent:
            weight = IMPACT_WEIGHTS.get(event["impact"], 1)
            score = SENTIMENT_SCORES.get(event["sentiment"], 0.0) * weight
            total_score += score
            total_weight += weight

            cat = event["category"]
            category_scores[cat] = category_scores.get(cat, 0.0) + score
            impact_counts[event["impact"]] = impact_counts.get(event["impact"], 0) + 1

        avg_sentiment = total_score / total_weight if total_weight > 0 else 0.0

        # Determine outlook
        if avg_sentiment > 0.3:
            outlook = "bullish"
            description = "Macro environment is favorable. Multiple positive catalysts present."
        elif avg_sentiment < -0.3:
            outlook = "bearish"
            description = "Macro headwinds are significant. Risk-off positioning recommended."
        else:
            outlook = "neutral"
            description = "Mixed signals in the macro environment. Proceed with balanced positioning."

        # Key risks and opportunities
        risks = [e["title"] for e in recent if e["sentiment"] == "bearish" and e["impact"] == "high"]
        opportunities = [e["title"] for e in recent if e["sentiment"] == "bullish" and e["impact"] == "high"]

        return {
            "outlook": outlook,
            "description": description,
            "sentiment_score": round(avg_sentiment, 3),
            "impact_distribution": impact_counts,
            "category_scores": {k: round(v, 2) for k, v in category_scores.items()},
            "key_risks": risks[:3],
            "key_opportunities": opportunities[:3],
            "events_analyzed": len(recent),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_events(self, category: Optional[str] = None, days: int = 7) -> List[dict]:
        """
        Retrieve recent macro events, optionally filtered by category.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        events = self._event_cache
        if category:
            events = [e for e in events if e["category"] == category]

        return [e for e in events if e["date"] >= cutoff_str]

    def classify_impact(self, event: dict) -> dict:
        """
        Classify the market impact of an event.
        Considers the event's category, sentiment, and keywords to
        determine impact level and affected sectors.
        """
        title = event.get("title", "").lower()
        category = event.get("category", "unknown")

        # Keyword-based severity scoring
        high_impact_keywords = [
            "rate", "fed", "ecb", "tariff", "sanction", "war", "crisis",
            "cpi", "inflation", "crash", "default", "recession",
        ]
        medium_impact_keywords = [
            "earnings", "employment", "gdp", "trade", "policy", "regulation",
            "reform", "deficit", "surplus",
        ]

        keyword_score = 0
        matched_keywords = []
        for kw in high_impact_keywords:
            if kw in title:
                keyword_score += 3
                matched_keywords.append(kw)
        for kw in medium_impact_keywords:
            if kw in title:
                keyword_score += 1
                matched_keywords.append(kw)

        if keyword_score >= 5:
            impact = "high"
        elif keyword_score >= 2:
            impact = "medium"
        else:
            impact = "low"

        # Affected sectors based on category
        sector_map = {
            "monetary_policy": ["bonds", "forex", "equities", "crypto"],
            "fiscal_policy": ["equities", "bonds"],
            "geopolitical": ["commodities", "forex", "equities"],
            "employment": ["equities", "consumer"],
            "inflation": ["bonds", "commodities", "forex"],
            "trade": ["commodities", "forex", "equities"],
            "energy": ["commodities", "energy_stocks"],
            "technology": ["tech_equities", "crypto"],
            "regulation": ["crypto", "financials"],
        }

        return {
            "event_title": event.get("title", ""),
            "category": category,
            "impact_level": impact,
            "keyword_score": keyword_score,
            "matched_keywords": matched_keywords,
            "affected_sectors": sector_map.get(category, ["general"]),
            "sentiment": event.get("sentiment", "neutral"),
        }

    def correlate_with_market(self, event: dict, symbol: str = "BTC") -> dict:
        """
        Estimate the correlation between a macro event and market movement
        for a given symbol. Uses heuristic scoring since real market data
        would require an external API.
        """
        classification = self.classify_impact(event)
        impact_level = classification["impact_level"]
        sentiment = event.get("sentiment", "neutral")

        # Heuristic correlation strength
        base_correlation = IMPACT_WEIGHTS.get(impact_level, 1) / 3.0

        # Adjust for crypto-specific sensitivity
        crypto_sensitive_categories = {"monetary_policy", "regulation", "technology", "inflation"}
        if event.get("category") in crypto_sensitive_categories and symbol in ("BTC", "ETH", "SOL"):
            base_correlation *= 1.5

        # Direction estimate
        direction = SENTIMENT_SCORES.get(sentiment, 0.0)

        # Simulated expected price impact
        expected_impact_pct = round(direction * base_correlation * random.uniform(0.5, 2.0), 2)

        result = {
            "event_title": event.get("title", ""),
            "symbol": symbol,
            "correlation_strength": round(min(base_correlation, 1.0), 3),
            "expected_direction": "up" if direction > 0 else ("down" if direction < 0 else "flat"),
            "expected_impact_pct": expected_impact_pct,
            "confidence": round(base_correlation * 0.7, 3),
            "classification": classification,
            "note": "Correlation is estimated heuristically. Real-time market data improves accuracy.",
        }

        self._correlation_history.append(result)
        return result

    def get_categories(self) -> List[str]:
        """Return all available macro event categories."""
        return list(MACRO_CATEGORIES)

    def refresh_events(self, days: int = 30):
        """Regenerate simulated events (call when real data source is unavailable)."""
        self._generate_simulated_events(days)
        logger.info(f"[MacroAnalyzer] Refreshed {len(self._event_cache)} simulated events")
