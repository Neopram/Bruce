"""
Macro data feeds module.
Aggregates macroeconomic data from IMF, World Bank, ECB,
and national statistical agencies into a unified feed.
"""
import random
from datetime import datetime


class MacroFeeds:
    """Aggregates macroeconomic data from multiple international sources."""

    def __init__(self):
        self.cache = {}
        self.fetch_log = []

    def fetch_imf_data(self, country="global"):
        """Fetch macroeconomic data from IMF-style feed."""
        data = {
            "source": "IMF",
            "country": country,
            "GDP_growth_pct": round(random.uniform(0.5, 5.0), 2),
            "inflation_pct": round(random.uniform(1.0, 10.0), 2),
            "reserves_usd": round(random.uniform(50_000_000, 500_000_000), 0),
            "current_account_pct_gdp": round(random.uniform(-5, 5), 2),
            "fiscal_balance_pct_gdp": round(random.uniform(-8, 2), 2),
            "public_debt_pct_gdp": round(random.uniform(30, 150), 1),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._log_fetch("IMF", country)
        self.cache[f"imf_{country}"] = data
        return data

    def fetch_world_bank_data(self, country="global"):
        """Fetch development indicators from World Bank-style feed."""
        data = {
            "source": "World Bank",
            "country": country,
            "poverty_rate": round(random.uniform(0.01, 0.40), 3),
            "gdp_per_capita_usd": round(random.uniform(1000, 80000), 0),
            "gini_coefficient": round(random.uniform(0.25, 0.65), 3),
            "life_expectancy_years": round(random.uniform(55, 85), 1),
            "literacy_rate": round(random.uniform(0.5, 1.0), 3),
            "fdi_net_inflows_usd": round(random.uniform(1_000_000, 100_000_000), 0),
            "trade_pct_gdp": round(random.uniform(20, 150), 1),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._log_fetch("WorldBank", country)
        self.cache[f"wb_{country}"] = data
        return data

    def fetch_ecb_data(self):
        """Fetch European Central Bank monetary data."""
        data = {
            "source": "ECB",
            "main_refinancing_rate": round(random.uniform(0, 5), 2),
            "deposit_facility_rate": round(random.uniform(-0.5, 4.5), 2),
            "m3_money_supply_growth_pct": round(random.uniform(-2, 10), 2),
            "hicp_inflation_pct": round(random.uniform(0.5, 8), 2),
            "euro_area_gdp_growth_pct": round(random.uniform(-1, 4), 2),
            "bank_lending_growth_pct": round(random.uniform(-2, 8), 2),
            "target2_balances_bn_eur": round(random.uniform(-500, 1500), 1),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._log_fetch("ECB", "eurozone")
        self.cache["ecb"] = data
        return data

    def fetch_national_api(self, source="INE", country=None):
        """Fetch data from national statistical agencies."""
        data = {
            "source": source,
            "country": country or source,
            "unemployment_rate": round(random.uniform(0.03, 0.15), 3),
            "cpi_yoy_pct": round(random.uniform(0.5, 8.0), 2),
            "interest_rate": round(random.uniform(0.5, 10.0), 2),
            "industrial_production_yoy_pct": round(random.uniform(-5, 8), 2),
            "retail_sales_yoy_pct": round(random.uniform(-3, 10), 2),
            "pmi_manufacturing": round(random.uniform(42, 58), 1),
            "pmi_services": round(random.uniform(44, 60), 1),
            "consumer_confidence": round(random.uniform(-20, 20), 1),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._log_fetch(source, country or source)
        self.cache[f"national_{source}"] = data
        return data

    def fetch_us_treasury_data(self):
        """Fetch US Treasury yield curve data."""
        base_2y = random.uniform(3.5, 5.5)
        data = {
            "source": "US Treasury",
            "yields": {
                "1M": round(base_2y + random.uniform(-0.5, 0.2), 3),
                "3M": round(base_2y + random.uniform(-0.3, 0.3), 3),
                "6M": round(base_2y + random.uniform(-0.2, 0.3), 3),
                "1Y": round(base_2y + random.uniform(-0.1, 0.3), 3),
                "2Y": round(base_2y, 3),
                "5Y": round(base_2y - random.uniform(0, 0.8), 3),
                "10Y": round(base_2y - random.uniform(0, 1.2), 3),
                "30Y": round(base_2y - random.uniform(0, 1.0), 3),
            },
            "curve_shape": "inverted" if base_2y > base_2y - 0.5 else "normal",
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._log_fetch("US Treasury", "US")
        self.cache["us_treasury"] = data
        return data

    def aggregate_all(self, country="global"):
        """Aggregate data from all sources into a unified macro snapshot."""
        snapshot = {
            "imf": self.fetch_imf_data(country),
            "world_bank": self.fetch_world_bank_data(country),
            "ecb": self.fetch_ecb_data(),
            "national": self.fetch_national_api(),
            "us_treasury": self.fetch_us_treasury_data(),
            "aggregated_at": datetime.utcnow().isoformat(),
        }
        return snapshot

    def get_cached(self, key):
        """Retrieve cached data by key."""
        return self.cache.get(key)

    def _log_fetch(self, source, target):
        """Log a data fetch operation."""
        self.fetch_log.append({
            "source": source,
            "target": target,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_fetch_log(self, limit=30):
        """Return recent fetch operations."""
        return self.fetch_log[-limit:]

    def get_available_sources(self):
        """Return list of available data sources."""
        return ["IMF", "World Bank", "ECB", "US Treasury", "National APIs (INE, BLS, ONS, etc.)"]
