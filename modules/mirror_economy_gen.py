"""
Mirror economy generator module.
Simulates alternative economic scenarios, parallel universe modeling,
and comparative analysis between different economic trajectories.
"""
import random
from datetime import datetime


class MirrorEconomyGenerator:
    """Generates and manages simulated parallel economic universes."""

    SCENARIO_TEMPLATES = {
        "hyperinflation": {"inflation_rate": 50, "gdp_growth": -5, "unemployment": 20},
        "tech_boom": {"inflation_rate": 2, "gdp_growth": 8, "unemployment": 3},
        "recession": {"inflation_rate": 1, "gdp_growth": -3, "unemployment": 12},
        "stagflation": {"inflation_rate": 12, "gdp_growth": -1, "unemployment": 9},
        "golden_age": {"inflation_rate": 2.5, "gdp_growth": 5, "unemployment": 4},
        "war_economy": {"inflation_rate": 8, "gdp_growth": 2, "unemployment": 5},
    }

    def __init__(self):
        self.parallel_universes = {}
        self.comparison_log = []

    def simulate(self, scenario_name, steps=10, seed_params=None):
        """Simulate a parallel economic universe over multiple time steps."""
        template = self.SCENARIO_TEMPLATES.get(scenario_name)
        base_params = seed_params or template or {
            "inflation_rate": 3, "gdp_growth": 2, "unemployment": 6,
        }

        timeline = []
        state = {
            "assets": self._generate_assets(scenario_name),
            "liquidity": self._generate_liquidity(),
            "risk_index": self._calculate_risk_index(),
            "macro": base_params.copy(),
        }

        for step in range(steps):
            state = self._evolve_state(state, step)
            timeline.append({
                "step": step,
                "gdp_growth": state["macro"]["gdp_growth"],
                "inflation": state["macro"]["inflation_rate"],
                "unemployment": state["macro"]["unemployment"],
                "liquidity": state["liquidity"],
                "risk_index": state["risk_index"],
                "market_cap_usd": round(state["liquidity"] * random.uniform(5, 20), 2),
            })

        universe = {
            "scenario": scenario_name,
            "assets": state["assets"],
            "liquidity": state["liquidity"],
            "risk_index": state["risk_index"],
            "final_macro": state["macro"],
            "timeline": timeline,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.parallel_universes[scenario_name] = universe
        return universe

    def _evolve_state(self, state, step):
        """Evolve the economic state by one time step."""
        macro = state["macro"]
        macro["gdp_growth"] = round(macro["gdp_growth"] + random.uniform(-1, 1), 2)
        macro["inflation_rate"] = round(max(0, macro["inflation_rate"] + random.uniform(-0.5, 0.5)), 2)
        macro["unemployment"] = round(max(0, macro["unemployment"] + random.uniform(-1, 1)), 2)

        if macro["gdp_growth"] > 0:
            state["liquidity"] = round(state["liquidity"] * (1 + random.uniform(0, 0.05)), 2)
        else:
            state["liquidity"] = round(state["liquidity"] * (1 - random.uniform(0, 0.03)), 2)

        state["risk_index"] = round(max(0.01, min(0.99,
            state["risk_index"] + random.uniform(-0.05, 0.05))), 3)

        return state

    def compare_universes(self, scenario_a, scenario_b):
        """Compare two simulated universes."""
        a = self.parallel_universes.get(scenario_a)
        b = self.parallel_universes.get(scenario_b)
        if not a or not b:
            missing = []
            if not a:
                missing.append(scenario_a)
            if not b:
                missing.append(scenario_b)
            return {"status": "error", "message": f"Missing universes: {missing}"}

        comparison = {
            "scenarios": [scenario_a, scenario_b],
            "liquidity_diff": round(a["liquidity"] - b["liquidity"], 2),
            "risk_diff": round(a["risk_index"] - b["risk_index"], 3),
            "gdp_diff": round(a["final_macro"]["gdp_growth"] - b["final_macro"]["gdp_growth"], 2),
            "inflation_diff": round(a["final_macro"]["inflation_rate"] - b["final_macro"]["inflation_rate"], 2),
            "better_growth": scenario_a if a["final_macro"]["gdp_growth"] > b["final_macro"]["gdp_growth"] else scenario_b,
            "lower_risk": scenario_a if a["risk_index"] < b["risk_index"] else scenario_b,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.comparison_log.append(comparison)
        return comparison

    def _generate_assets(self, scenario_name=None):
        """Generate synthetic assets for a universe."""
        base_assets = ["QuantumCoin", "MirrorGold", "TimeBond"]
        if scenario_name:
            base_assets.append(f"{scenario_name.title()}Token")
        return base_assets

    def _generate_liquidity(self):
        """Generate initial liquidity pool value."""
        return round(random.uniform(1_000_000, 10_000_000), 2)

    def _calculate_risk_index(self):
        """Calculate initial risk index."""
        return round(random.uniform(0.1, 0.9), 3)

    def list_universes(self):
        """List all simulated universes."""
        return {
            name: {
                "assets": u["assets"],
                "liquidity": u["liquidity"],
                "risk_index": u["risk_index"],
                "created_at": u["created_at"],
            }
            for name, u in self.parallel_universes.items()
        }

    def get_available_templates(self):
        """Return available scenario templates."""
        return self.SCENARIO_TEMPLATES

    def delete_universe(self, scenario_name):
        """Delete a simulated universe."""
        if scenario_name in self.parallel_universes:
            del self.parallel_universes[scenario_name]
            return {"deleted": scenario_name}
        return {"status": "error", "message": f"Universe not found: {scenario_name}"}

    def get_comparison_log(self, limit=20):
        """Return recent comparisons."""
        return self.comparison_log[-limit:]
