"""
Macro Analysis Service - Provides macroeconomic summaries, key indicators,
and regional outlooks using simulated data.
"""

import random
from datetime import datetime, timezone
from typing import Dict, List, Optional


_REGIONS = {
    "us": "United States",
    "eu": "European Union",
    "asia": "Asia-Pacific",
    "latam": "Latin America",
    "global": "Global",
}

_INDICATOR_DEFINITIONS = [
    {"name": "GDP Growth Rate", "unit": "%", "range": (-2.0, 6.0)},
    {"name": "CPI Inflation", "unit": "%", "range": (0.5, 10.0)},
    {"name": "Unemployment Rate", "unit": "%", "range": (2.0, 12.0)},
    {"name": "Federal Funds Rate", "unit": "%", "range": (0.0, 6.0)},
    {"name": "10Y Treasury Yield", "unit": "%", "range": (1.0, 5.5)},
    {"name": "Consumer Confidence", "unit": "index", "range": (60.0, 130.0)},
    {"name": "PMI Manufacturing", "unit": "index", "range": (40.0, 65.0)},
    {"name": "M2 Money Supply Growth", "unit": "%", "range": (-2.0, 20.0)},
]


class MacroService:
    """Provides macro-economic analysis and indicator data."""

    def __init__(self, provider: str = "openai"):
        self.provider = provider

    def get_macro_summary(self) -> dict:
        """Return a high-level summary of the current macro environment."""
        indicators = self.get_indicators()
        gdp = next(
            (i for i in indicators if i["name"] == "GDP Growth Rate"), None
        )
        cpi = next(
            (i for i in indicators if i["name"] == "CPI Inflation"), None
        )
        unemployment = next(
            (i for i in indicators if i["name"] == "Unemployment Rate"), None
        )

        if gdp and gdp["value"] > 3.0:
            growth_label = "expansionary"
        elif gdp and gdp["value"] > 0:
            growth_label = "moderate growth"
        else:
            growth_label = "contractionary"

        if cpi and cpi["value"] > 5.0:
            inflation_label = "elevated inflation"
        elif cpi and cpi["value"] > 2.5:
            inflation_label = "moderate inflation"
        else:
            inflation_label = "low inflation"

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": self.provider,
            "environment": growth_label,
            "inflation_regime": inflation_label,
            "unemployment_rate": unemployment["value"] if unemployment else None,
            "indicator_count": len(indicators),
            "narrative": (
                f"The macro environment is {growth_label} with {inflation_label}. "
                f"Unemployment stands at {unemployment['value'] if unemployment else 'N/A'}%."
            ),
        }

    def get_indicators(self) -> List[dict]:
        """Return key economic indicators with simulated current values."""
        results = []
        for defn in _INDICATOR_DEFINITIONS:
            value = round(random.uniform(*defn["range"]), 2)
            results.append(
                {
                    "name": defn["name"],
                    "value": value,
                    "unit": defn["unit"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        return results

    def get_outlook(self, region: str = "global") -> dict:
        """Return a regional macro outlook."""
        region_key = region.lower()
        region_name = _REGIONS.get(region_key, region)

        sentiment_score = round(random.uniform(-1.0, 1.0), 2)
        if sentiment_score > 0.3:
            outlook_label = "bullish"
        elif sentiment_score > -0.3:
            outlook_label = "neutral"
        else:
            outlook_label = "bearish"

        return {
            "region": region_name,
            "outlook": outlook_label,
            "sentiment_score": sentiment_score,
            "key_risks": random.sample(
                [
                    "Geopolitical tensions",
                    "Supply chain disruptions",
                    "Central bank policy shifts",
                    "Currency volatility",
                    "Commodity price swings",
                    "Debt sustainability concerns",
                ],
                k=3,
            ),
            "opportunities": random.sample(
                [
                    "Infrastructure spending",
                    "Technology adoption",
                    "Green energy transition",
                    "Emerging market growth",
                    "AI-driven productivity gains",
                ],
                k=2,
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Backward-compatible alias
class MacroAnalyzer(MacroService):
    """Legacy alias kept for backward compatibility."""

    def summary(self) -> str:
        data = self.get_macro_summary()
        return data["narrative"]
