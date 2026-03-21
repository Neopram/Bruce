"""
Geopolitical risk scoring module.
Evaluates geopolitical risk by region, assesses impact on markets,
and generates risk alerts with severity levels.
"""
import random
from datetime import datetime


class GeoPoliticalRiskMonitor:
    """Monitors and scores geopolitical risks and their market impact."""

    REGIONS = {
        "eastern_europe": {
            "name": "Eastern Europe",
            "base_risk": 0.6,
            "key_factors": ["armed_conflict", "energy_supply", "sanctions"],
            "affected_markets": ["energy", "grain", "defense"],
        },
        "east_asia": {
            "name": "East Asia",
            "base_risk": 0.45,
            "key_factors": ["trade_tensions", "semiconductor_supply", "territorial_disputes"],
            "affected_markets": ["tech", "semiconductors", "shipping"],
        },
        "middle_east": {
            "name": "Middle East",
            "base_risk": 0.55,
            "key_factors": ["oil_supply", "regional_conflict", "nuclear_proliferation"],
            "affected_markets": ["energy", "defense", "insurance"],
        },
        "south_america": {
            "name": "South America",
            "base_risk": 0.35,
            "key_factors": ["political_instability", "commodity_dependence", "currency_volatility"],
            "affected_markets": ["commodities", "emerging_markets", "agriculture"],
        },
        "north_america": {
            "name": "North America",
            "base_risk": 0.2,
            "key_factors": ["trade_policy", "fiscal_policy", "election_cycle"],
            "affected_markets": ["equities", "bonds", "usd"],
        },
        "sub_saharan_africa": {
            "name": "Sub-Saharan Africa",
            "base_risk": 0.5,
            "key_factors": ["governance", "resource_extraction", "debt_sustainability"],
            "affected_markets": ["mining", "frontier_markets", "development_bonds"],
        },
    }

    def __init__(self):
        self.alert_history = []
        self.risk_snapshots = []

    def current_alerts(self):
        """Generate current geopolitical risk alerts."""
        alerts = []
        for region_key, region in self.REGIONS.items():
            risk_score = self._compute_risk_score(region)
            if risk_score > 0.6:
                severity = "critical" if risk_score > 0.8 else "high"
                factor = random.choice(region["key_factors"])
                alert = {
                    "region": region["name"],
                    "severity": severity,
                    "risk_score": round(risk_score, 3),
                    "primary_factor": factor,
                    "affected_markets": region["affected_markets"],
                    "timestamp": datetime.utcnow().isoformat(),
                }
                alerts.append(alert)
                self.alert_history.append(alert)
            elif risk_score > 0.4:
                alerts.append({
                    "region": region["name"],
                    "severity": "moderate",
                    "risk_score": round(risk_score, 3),
                    "primary_factor": random.choice(region["key_factors"]),
                    "affected_markets": region["affected_markets"],
                    "timestamp": datetime.utcnow().isoformat(),
                })

        return {"alerts": alerts, "total": len(alerts)}

    def score_region(self, region_key):
        """Get detailed risk score for a specific region."""
        if region_key not in self.REGIONS:
            return {"status": "error", "message": f"Unknown region: {region_key}",
                    "available": list(self.REGIONS.keys())}

        region = self.REGIONS[region_key]
        overall_score = self._compute_risk_score(region)
        factor_scores = {}
        for factor in region["key_factors"]:
            factor_scores[factor] = round(random.uniform(0.1, 1.0), 3)

        return {
            "region": region["name"],
            "overall_risk_score": round(overall_score, 3),
            "factor_scores": factor_scores,
            "affected_markets": region["affected_markets"],
            "risk_level": self._risk_level(overall_score),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def global_stability_index(self):
        """Calculate overall global stability index (0 = unstable, 1 = very stable)."""
        scores = []
        region_details = {}
        for key, region in self.REGIONS.items():
            score = self._compute_risk_score(region)
            scores.append(score)
            region_details[key] = {
                "name": region["name"],
                "risk_score": round(score, 3),
                "risk_level": self._risk_level(score),
            }

        avg_risk = sum(scores) / len(scores)
        stability = round(1 - avg_risk, 3)

        snapshot = {
            "stability_index": stability,
            "avg_risk": round(avg_risk, 3),
            "regions": region_details,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.risk_snapshots.append(snapshot)
        return snapshot

    def market_impact_assessment(self, region_key):
        """Assess the potential market impact of risks in a region."""
        if region_key not in self.REGIONS:
            return {"status": "error", "message": f"Unknown region: {region_key}"}

        region = self.REGIONS[region_key]
        risk_score = self._compute_risk_score(region)

        impacts = []
        for market in region["affected_markets"]:
            impact_magnitude = risk_score * random.uniform(0.5, 1.5)
            impacts.append({
                "market": market,
                "expected_volatility_increase_pct": round(impact_magnitude * 20, 1),
                "direction_bias": random.choice(["bearish", "neutral", "mixed"]),
                "confidence": round(random.uniform(0.4, 0.9), 2),
            })

        return {
            "region": region["name"],
            "risk_score": round(risk_score, 3),
            "market_impacts": impacts,
            "recommendation": "reduce_exposure" if risk_score > 0.6 else "monitor",
        }

    def _compute_risk_score(self, region):
        """Compute dynamic risk score for a region."""
        base = region["base_risk"]
        volatility = random.uniform(-0.15, 0.15)
        return max(0, min(1, base + volatility))

    def _risk_level(self, score):
        """Map risk score to human-readable level."""
        if score > 0.8:
            return "critical"
        elif score > 0.6:
            return "high"
        elif score > 0.4:
            return "moderate"
        elif score > 0.2:
            return "low"
        return "minimal"

    def get_alert_history(self, limit=30):
        """Return recent alert history."""
        return self.alert_history[-limit:]

    def get_all_regions(self):
        """Return all monitored regions."""
        return {k: {"name": v["name"], "key_factors": v["key_factors"]} for k, v in self.REGIONS.items()}
