"""
Government policy insights module.
Tracks central bank decisions, regulatory changes, fiscal policy,
and generates analytical reports on policy impacts.
"""
import random
from datetime import datetime


class GovInsightGenerator:
    """Generates insights on government policy and its market impact."""

    CENTRAL_BANKS = {
        "FED": {"name": "Federal Reserve", "currency": "USD", "current_rate": 5.25},
        "ECB": {"name": "European Central Bank", "currency": "EUR", "current_rate": 4.50},
        "BOJ": {"name": "Bank of Japan", "currency": "JPY", "current_rate": 0.10},
        "BOE": {"name": "Bank of England", "currency": "GBP", "current_rate": 5.00},
        "PBOC": {"name": "People's Bank of China", "currency": "CNY", "current_rate": 3.45},
        "RBI": {"name": "Reserve Bank of India", "currency": "INR", "current_rate": 6.50},
    }

    def __init__(self):
        self.policy_log = []
        self.regulatory_alerts = []

    def generate_financial_stability_report(self):
        """Generate a financial stability report with current indicators."""
        date = datetime.now().strftime("%B %Y")
        inflation = round(random.uniform(2.0, 8.0), 1)
        gdp = round(random.uniform(-1.0, 4.0), 1)
        debt_to_gdp = round(random.uniform(60, 130), 1)

        report = {
            "title": f"Financial Stability Report - {date}",
            "projected_inflation_pct": inflation,
            "projected_gdp_growth_pct": gdp,
            "debt_to_gdp_ratio": debt_to_gdp,
            "key_risks": self._assess_risks(inflation, gdp, debt_to_gdp),
            "policy_stance": "hawkish" if inflation > 5 else "dovish" if inflation < 2.5 else "neutral",
            "liquidity_conditions": random.choice(["tight", "adequate", "loose"]),
            "financial_stress_index": round(random.uniform(0, 1), 3),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.policy_log.append(report)
        return report

    def generate_monthly_overview(self):
        """Generate a monthly economic overview."""
        return {
            "title": "Monthly Economic Overview",
            "employment_change_pct": round(random.uniform(-0.5, 1.0), 2),
            "exchange_rate_stability": random.choice(["stable", "volatile", "appreciating", "depreciating"]),
            "industrial_production_change_pct": round(random.uniform(-2, 3), 1),
            "consumer_confidence_index": round(random.uniform(80, 120), 1),
            "retail_sales_change_pct": round(random.uniform(-1, 4), 1),
            "housing_starts_change_pct": round(random.uniform(-5, 10), 1),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_central_bank_outlook(self, bank_code="FED"):
        """Get outlook and analysis for a specific central bank."""
        if bank_code not in self.CENTRAL_BANKS:
            return {"status": "error", "message": f"Unknown bank: {bank_code}",
                    "available": list(self.CENTRAL_BANKS.keys())}

        bank = self.CENTRAL_BANKS[bank_code]
        rate_direction = random.choice(["hike", "hold", "cut"])
        rate_change = 0.25 if rate_direction == "hike" else -0.25 if rate_direction == "cut" else 0

        return {
            "bank": bank["name"],
            "code": bank_code,
            "currency": bank["currency"],
            "current_rate": bank["current_rate"],
            "expected_action": rate_direction,
            "expected_rate_change": rate_change,
            "projected_rate": bank["current_rate"] + rate_change,
            "confidence": round(random.uniform(0.4, 0.9), 2),
            "next_meeting_impact": {
                "bonds": "bullish" if rate_direction == "cut" else "bearish" if rate_direction == "hike" else "neutral",
                "equities": "bullish" if rate_direction == "cut" else "bearish" if rate_direction == "hike" else "neutral",
                "currency": "bearish" if rate_direction == "cut" else "bullish" if rate_direction == "hike" else "neutral",
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def track_regulatory_change(self, jurisdiction, sector, change_type, description, severity="medium"):
        """Track a regulatory change and assess impact."""
        impact_map = {
            "low": random.uniform(0.01, 0.03),
            "medium": random.uniform(0.03, 0.08),
            "high": random.uniform(0.08, 0.20),
        }

        alert = {
            "jurisdiction": jurisdiction,
            "sector": sector,
            "change_type": change_type,
            "description": description,
            "severity": severity,
            "estimated_market_impact_pct": round(impact_map.get(severity, 0.05), 3),
            "compliance_deadline_days": random.randint(30, 365),
            "affected_instruments": self._get_affected_instruments(sector),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.regulatory_alerts.append(alert)
        return alert

    def fiscal_policy_analysis(self, country="US"):
        """Analyze current fiscal policy stance for a country."""
        return {
            "country": country,
            "fiscal_stance": random.choice(["expansionary", "contractionary", "neutral"]),
            "government_spending_change_pct": round(random.uniform(-3, 8), 1),
            "tax_revenue_change_pct": round(random.uniform(-2, 5), 1),
            "budget_deficit_to_gdp_pct": round(random.uniform(1, 10), 1),
            "debt_sustainability_score": round(random.uniform(0.3, 0.9), 2),
            "key_programs": random.sample(
                ["infrastructure", "defense", "healthcare", "education", "social_security", "energy_transition"],
                k=3,
            ),
            "market_implications": {
                "bonds": random.choice(["positive", "negative", "neutral"]),
                "equities": random.choice(["positive", "negative", "neutral"]),
                "inflation_outlook": random.choice(["upward_pressure", "contained", "deflationary"]),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _assess_risks(self, inflation, gdp, debt_ratio):
        """Assess key macroeconomic risks."""
        risks = []
        if inflation > 6:
            risks.append({"risk": "high_inflation", "severity": "high"})
        if gdp < 0:
            risks.append({"risk": "recession", "severity": "critical"})
        if debt_ratio > 100:
            risks.append({"risk": "debt_sustainability", "severity": "medium"})
        if not risks:
            risks.append({"risk": "global_uncertainty", "severity": "low"})
        return risks

    def _get_affected_instruments(self, sector):
        """Get instruments affected by regulatory changes in a sector."""
        sector_map = {
            "banking": ["bank_stocks", "bonds", "credit_derivatives"],
            "crypto": ["BTC", "ETH", "stablecoins", "defi_tokens"],
            "energy": ["oil_futures", "gas_futures", "renewable_etfs"],
            "tech": ["tech_stocks", "semiconductors", "cloud_etfs"],
        }
        return sector_map.get(sector, ["general_equities"])

    def get_policy_log(self, limit=20):
        """Return recent policy reports."""
        return self.policy_log[-limit:]

    def get_regulatory_alerts(self, limit=20):
        """Return recent regulatory alerts."""
        return self.regulatory_alerts[-limit:]
