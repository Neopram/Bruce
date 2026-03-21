"""
Stress testing module.
Applies shock scenarios to portfolios, measures impact on positions,
and generates comprehensive risk reports.
"""
import math
import random
from datetime import datetime


class StressTester:
    """Applies stress scenarios to portfolios and reports impact."""

    SCENARIOS = {
        "2008": {
            "name": "2008 Financial Crisis",
            "equity_shock_pct": -55,
            "bond_shock_pct": -5,
            "credit_spread_bps": 600,
            "volatility_multiplier": 4.0,
            "duration_months": 18,
            "description": "Banking crisis triggered by mortgage default contagion",
        },
        "covid": {
            "name": "COVID-19 Crash",
            "equity_shock_pct": -34,
            "bond_shock_pct": 5,
            "credit_spread_bps": 400,
            "volatility_multiplier": 5.0,
            "duration_months": 3,
            "description": "Pandemic-driven market crash with rapid recovery",
        },
        "dotcom": {
            "name": "Dot-com Bubble Burst",
            "equity_shock_pct": -49,
            "bond_shock_pct": 10,
            "credit_spread_bps": 300,
            "volatility_multiplier": 2.5,
            "duration_months": 30,
            "description": "Technology sector collapse after speculative bubble",
        },
        "rate_shock": {
            "name": "Interest Rate Shock",
            "equity_shock_pct": -20,
            "bond_shock_pct": -15,
            "credit_spread_bps": 200,
            "volatility_multiplier": 2.0,
            "duration_months": 12,
            "description": "Rapid rate hikes causing bond and equity selloff",
        },
        "geopolitical": {
            "name": "Geopolitical Crisis",
            "equity_shock_pct": -25,
            "bond_shock_pct": 3,
            "credit_spread_bps": 250,
            "volatility_multiplier": 3.0,
            "duration_months": 6,
            "description": "Major geopolitical conflict disrupting global trade",
        },
        "hyperinflation": {
            "name": "Hyperinflation Shock",
            "equity_shock_pct": -15,
            "bond_shock_pct": -30,
            "credit_spread_bps": 500,
            "volatility_multiplier": 3.5,
            "duration_months": 24,
            "description": "Extreme inflation eroding real asset values",
        },
    }

    def __init__(self):
        self.test_results = []

    def simulate_crisis(self, scenario="2008", portfolio=None):
        """Simulate a historical crisis scenario on a portfolio.

        Args:
            scenario: Scenario key or custom scenario dict.
            portfolio: Optional dict of {asset: {"value": float, "asset_class": str}}.
        """
        if isinstance(scenario, str):
            if scenario not in self.SCENARIOS:
                return {"status": "error", "message": f"Unknown scenario: {scenario}",
                        "available": list(self.SCENARIOS.keys())}
            scenario_config = self.SCENARIOS[scenario]
        else:
            scenario_config = scenario

        if portfolio is None:
            portfolio = self._default_portfolio()

        impacts = {}
        total_before = 0
        total_after = 0

        for asset, details in portfolio.items():
            value = details.get("value", 0)
            asset_class = details.get("asset_class", "equity")
            total_before += value

            shock = self._get_shock_for_class(asset_class, scenario_config)
            noise = random.uniform(-0.05, 0.05)
            total_shock = shock + noise
            stressed_value = value * (1 + total_shock)
            stressed_value = max(0, stressed_value)
            total_after += stressed_value

            impacts[asset] = {
                "original_value": round(value, 2),
                "stressed_value": round(stressed_value, 2),
                "shock_pct": round(total_shock * 100, 2),
                "loss_usd": round(value - stressed_value, 2),
                "asset_class": asset_class,
            }

        total_loss = total_before - total_after
        drawdown_pct = (total_loss / total_before * 100) if total_before > 0 else 0

        result = {
            "scenario": scenario_config["name"],
            "description": scenario_config.get("description", ""),
            "portfolio_before": round(total_before, 2),
            "portfolio_after": round(total_after, 2),
            "total_loss": round(total_loss, 2),
            "drawdown_pct": round(drawdown_pct, 2),
            "recovery_months": scenario_config.get("duration_months", 12),
            "volatility_multiplier": scenario_config.get("volatility_multiplier", 2.0),
            "impacts": impacts,
            "risk_metrics": self._compute_risk_metrics(impacts, total_before),
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.test_results.append(result)
        return result

    def run_multi_scenario(self, portfolio=None):
        """Run all predefined scenarios against a portfolio."""
        results = {}
        for scenario_key in self.SCENARIOS:
            results[scenario_key] = self.simulate_crisis(scenario_key, portfolio)

        worst = max(results.values(), key=lambda r: r["drawdown_pct"])
        best = min(results.values(), key=lambda r: r["drawdown_pct"])

        return {
            "scenarios_run": len(results),
            "results": results,
            "worst_case": {"scenario": worst["scenario"], "drawdown_pct": worst["drawdown_pct"]},
            "best_case": {"scenario": best["scenario"], "drawdown_pct": best["drawdown_pct"]},
            "avg_drawdown_pct": round(sum(r["drawdown_pct"] for r in results.values()) / len(results), 2),
        }

    def custom_shock(self, portfolio, shocks):
        """Apply custom shocks to a portfolio.

        Args:
            portfolio: Dict of {asset: {"value": float, "asset_class": str}}.
            shocks: Dict of {asset: shock_pct} where shock_pct is percentage change.
        """
        impacts = {}
        total_before = 0
        total_after = 0

        for asset, details in portfolio.items():
            value = details.get("value", 0)
            total_before += value
            shock_pct = shocks.get(asset, 0) / 100
            stressed_value = max(0, value * (1 + shock_pct))
            total_after += stressed_value
            impacts[asset] = {
                "original_value": round(value, 2),
                "stressed_value": round(stressed_value, 2),
                "shock_pct": round(shock_pct * 100, 2),
                "loss_usd": round(value - stressed_value, 2),
            }

        return {
            "scenario": "custom",
            "portfolio_before": round(total_before, 2),
            "portfolio_after": round(total_after, 2),
            "total_loss": round(total_before - total_after, 2),
            "drawdown_pct": round((total_before - total_after) / total_before * 100, 2) if total_before > 0 else 0,
            "impacts": impacts,
        }

    def _get_shock_for_class(self, asset_class, scenario):
        """Get the appropriate shock percentage for an asset class."""
        shocks = {
            "equity": scenario.get("equity_shock_pct", -30) / 100,
            "bond": scenario.get("bond_shock_pct", -5) / 100,
            "credit": scenario.get("equity_shock_pct", -30) / 100 * 0.7,
            "commodity": scenario.get("equity_shock_pct", -30) / 100 * 0.5,
            "real_estate": scenario.get("equity_shock_pct", -30) / 100 * 0.6,
            "cash": 0,
            "crypto": scenario.get("equity_shock_pct", -30) / 100 * 1.5,
        }
        return shocks.get(asset_class, scenario.get("equity_shock_pct", -30) / 100)

    def _compute_risk_metrics(self, impacts, total_before):
        """Compute risk metrics from stress test impacts."""
        losses = [imp["loss_usd"] for imp in impacts.values()]
        if not losses or total_before == 0:
            return {}

        max_single_loss = max(losses)
        concentration = max_single_loss / sum(losses) if sum(losses) > 0 else 0

        return {
            "max_single_asset_loss": round(max_single_loss, 2),
            "concentration_risk": round(concentration, 4),
            "assets_with_loss": sum(1 for l in losses if l > 0),
            "assets_total": len(losses),
        }

    def _default_portfolio(self):
        """Generate a default diversified portfolio for testing."""
        return {
            "US_Equities": {"value": 40000, "asset_class": "equity"},
            "Intl_Equities": {"value": 15000, "asset_class": "equity"},
            "US_Bonds": {"value": 25000, "asset_class": "bond"},
            "Corporate_Bonds": {"value": 10000, "asset_class": "credit"},
            "Real_Estate": {"value": 5000, "asset_class": "real_estate"},
            "Cash": {"value": 5000, "asset_class": "cash"},
        }

    def get_available_scenarios(self):
        """Return all available stress test scenarios."""
        return {k: {"name": v["name"], "description": v["description"]} for k, v in self.SCENARIOS.items()}

    def get_test_results(self, limit=10):
        """Return recent test results."""
        return self.test_results[-limit:]
