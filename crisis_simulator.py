"""
crisis_simulator.py - Portfolio crisis simulation, stress testing, and hedging recommendations.
"""

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import random
import math
import logging

router = APIRouter()
logger = logging.getLogger("Bruce.CrisisSimulator")


# ---------------------------------------------------------------------------
# Predefined crisis scenarios
# ---------------------------------------------------------------------------

CRISIS_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "crash_2008": {
        "name": "2008 Financial Crisis",
        "description": "Global financial meltdown triggered by subprime mortgage collapse",
        "peak_drawdown_pct": -56.8,
        "duration_days": 517,
        "recovery_days": 1480,
        "volatility_multiplier": 4.5,
        "correlation_spike": 0.90,
        "asset_impacts": {
            "BTC/USDT": -0.65,   # hypothetical (BTC didn't exist yet)
            "ETH/USDT": -0.72,
            "SOL/USDT": -0.80,
            "BNB/USDT": -0.70,
            "stocks": -0.568,
            "bonds": 0.05,
            "gold": 0.25,
        },
    },
    "flash_crash_2010": {
        "name": "2010 Flash Crash",
        "description": "Dow Jones dropped ~9% in minutes before partial recovery",
        "peak_drawdown_pct": -9.2,
        "duration_days": 1,
        "recovery_days": 4,
        "volatility_multiplier": 8.0,
        "correlation_spike": 0.95,
        "asset_impacts": {
            "BTC/USDT": -0.15,
            "ETH/USDT": -0.20,
            "SOL/USDT": -0.25,
            "BNB/USDT": -0.18,
            "stocks": -0.092,
            "bonds": 0.02,
            "gold": 0.01,
        },
    },
    "covid_2020": {
        "name": "COVID-19 Crash (March 2020)",
        "description": "Pandemic-driven market crash with rapid recovery",
        "peak_drawdown_pct": -33.9,
        "duration_days": 33,
        "recovery_days": 148,
        "volatility_multiplier": 5.0,
        "correlation_spike": 0.85,
        "asset_impacts": {
            "BTC/USDT": -0.50,
            "ETH/USDT": -0.55,
            "SOL/USDT": -0.60,
            "BNB/USDT": -0.52,
            "stocks": -0.339,
            "bonds": 0.08,
            "gold": -0.03,
        },
    },
    "black_swan": {
        "name": "Black Swan Event",
        "description": "Hypothetical extreme tail-risk event (99.9th percentile)",
        "peak_drawdown_pct": -75.0,
        "duration_days": 90,
        "recovery_days": 730,
        "volatility_multiplier": 10.0,
        "correlation_spike": 0.98,
        "asset_impacts": {
            "BTC/USDT": -0.85,
            "ETH/USDT": -0.90,
            "SOL/USDT": -0.92,
            "BNB/USDT": -0.88,
            "stocks": -0.75,
            "bonds": -0.10,
            "gold": 0.15,
        },
    },
}


# ---------------------------------------------------------------------------
# Monte Carlo helpers
# ---------------------------------------------------------------------------

def _monte_carlo_paths(
    initial_value: float,
    mean_daily_return: float,
    daily_volatility: float,
    days: int,
    num_simulations: int = 1000,
) -> List[List[float]]:
    """Generate Monte Carlo price paths using geometric Brownian motion."""
    paths: List[List[float]] = []
    for _ in range(num_simulations):
        path = [initial_value]
        value = initial_value
        for _ in range(days):
            shock = random.gauss(mean_daily_return, daily_volatility)
            value *= (1 + shock)
            value = max(value, 0.0)
            path.append(value)
        paths.append(path)
    return paths


def _compute_path_stats(paths: List[List[float]], initial_value: float) -> Dict[str, Any]:
    """Compute statistics from Monte Carlo paths."""
    final_values = [p[-1] for p in paths]
    min_values = [min(p) for p in paths]

    max_drawdowns = []
    for p in paths:
        peak = p[0]
        max_dd = 0.0
        for v in p:
            if v > peak:
                peak = v
            dd = (peak - v) / peak if peak > 0 else 0.0
            if dd > max_dd:
                max_dd = dd
        max_drawdowns.append(max_dd)

    sorted_finals = sorted(final_values)
    n = len(sorted_finals)

    return {
        "mean_final_value": round(sum(final_values) / n, 2),
        "median_final_value": round(sorted_finals[n // 2], 2),
        "percentile_5": round(sorted_finals[int(n * 0.05)], 2),
        "percentile_95": round(sorted_finals[int(n * 0.95)], 2),
        "worst_case": round(sorted_finals[0], 2),
        "best_case": round(sorted_finals[-1], 2),
        "mean_max_drawdown_pct": round(sum(max_drawdowns) / n * 100, 2),
        "worst_drawdown_pct": round(max(max_drawdowns) * 100, 2),
        "prob_loss": round(sum(1 for v in final_values if v < initial_value) / n * 100, 1),
        "prob_loss_gt_50pct": round(sum(1 for v in final_values if v < initial_value * 0.5) / n * 100, 1),
        "num_simulations": n,
    }


# ---------------------------------------------------------------------------
# Crisis Simulator
# ---------------------------------------------------------------------------

class CrisisSimulator:
    """Simulates portfolio behaviour under various crisis scenarios."""

    def __init__(self):
        self.scenarios = dict(CRISIS_SCENARIOS)

    def list_scenarios(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": k,
                "name": v["name"],
                "description": v["description"],
                "peak_drawdown_pct": v["peak_drawdown_pct"],
                "duration_days": v["duration_days"],
            }
            for k, v in self.scenarios.items()
        ]

    # ------------------------------------------------------------------
    # Single scenario simulation
    # ------------------------------------------------------------------

    def simulate(
        self,
        scenario_id: str,
        portfolio: Dict[str, float],
        num_simulations: int = 500,
    ) -> Dict[str, Any]:
        """
        Run a Monte Carlo simulation of *portfolio* under *scenario_id*.

        portfolio: mapping of asset symbol -> current value in USD
            e.g. {"BTC/USDT": 40000, "ETH/USDT": 20000, "cash": 10000}
        """
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            return {"error": f"Unknown scenario: {scenario_id}",
                    "available": list(self.scenarios.keys())}

        total_value = sum(portfolio.values())
        if total_value <= 0:
            return {"error": "Portfolio value must be positive"}

        impacts = scenario["asset_impacts"]
        vol_mult = scenario["volatility_multiplier"]
        duration = scenario["duration_days"]

        # Per-asset simulation
        asset_results: Dict[str, Any] = {}
        portfolio_paths: Optional[List[List[float]]] = None

        for asset, value in portfolio.items():
            if value <= 0:
                continue
            impact = impacts.get(asset, impacts.get("stocks", -0.30))
            daily_return = impact / max(duration, 1)
            daily_vol = abs(impact) / math.sqrt(max(duration, 1)) * vol_mult * 0.3

            paths = _monte_carlo_paths(value, daily_return, daily_vol, duration, num_simulations)
            stats = _compute_path_stats(paths, value)
            asset_results[asset] = {
                "initial_value": value,
                "expected_impact_pct": round(impact * 100, 1),
                **stats,
            }

            # Aggregate portfolio paths
            if portfolio_paths is None:
                portfolio_paths = paths
            else:
                for i in range(len(paths)):
                    for j in range(len(paths[i])):
                        portfolio_paths[i][j] += paths[i][j]

        # Portfolio-level stats
        portfolio_stats = _compute_path_stats(portfolio_paths, total_value) if portfolio_paths else {}

        # Compute portfolio-level impact percentage
        mean_final = portfolio_stats.get("mean_final_value", total_value)
        portfolio_impact_pct = round((mean_final - total_value) / total_value * 100, 2) if total_value else 0.0

        return {
            "scenario": {
                "id": scenario_id,
                "name": scenario["name"],
                "description": scenario["description"],
                "peak_drawdown_pct": scenario["peak_drawdown_pct"],
                "duration_days": duration,
                "recovery_days": scenario["recovery_days"],
            },
            "portfolio_initial_value": round(total_value, 2),
            "portfolio_impact_pct": portfolio_impact_pct,
            "portfolio_stats": portfolio_stats,
            "asset_results": asset_results,
            "simulated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Stress test across all scenarios
    # ------------------------------------------------------------------

    def stress_test(
        self,
        portfolio: Dict[str, float],
        scenario_ids: Optional[List[str]] = None,
        num_simulations: int = 300,
    ) -> Dict[str, Any]:
        ids = scenario_ids or list(self.scenarios.keys())
        results: Dict[str, Any] = {}
        worst_scenario = None
        worst_loss = 0.0

        for sid in ids:
            sim = self.simulate(sid, portfolio, num_simulations)
            if "error" in sim:
                results[sid] = sim
                continue
            results[sid] = sim
            mean_final = sim["portfolio_stats"].get("mean_final_value", sim["portfolio_initial_value"])
            loss = sim["portfolio_initial_value"] - mean_final
            if loss > worst_loss:
                worst_loss = loss
                worst_scenario = sid

        total_value = sum(portfolio.values())
        return {
            "portfolio_value": round(total_value, 2),
            "scenarios_tested": ids,
            "worst_scenario": worst_scenario,
            "worst_expected_loss": round(worst_loss, 2),
            "worst_expected_loss_pct": round(worst_loss / total_value * 100, 2) if total_value else 0,
            "results": results,
            "tested_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # Hedging recommendations
    # ------------------------------------------------------------------

    def get_hedging_recommendations(
        self,
        portfolio: Dict[str, float],
        scenario_id: str,
    ) -> Dict[str, Any]:
        scenario = self.scenarios.get(scenario_id)
        if not scenario:
            return {"error": f"Unknown scenario: {scenario_id}"}

        total_value = sum(portfolio.values())
        if total_value <= 0:
            return {"error": "Portfolio value must be positive"}

        impacts = scenario["asset_impacts"]
        recommendations: List[Dict[str, Any]] = []

        # Compute expected loss
        expected_loss = 0.0
        for asset, value in portfolio.items():
            impact = impacts.get(asset, impacts.get("stocks", -0.30))
            expected_loss += value * abs(min(impact, 0))

        # Generate recommendations based on portfolio composition
        crypto_exposure = sum(
            v for k, v in portfolio.items() if "/" in k
        )
        crypto_pct = crypto_exposure / total_value * 100 if total_value else 0

        if crypto_pct > 50:
            recommendations.append({
                "action": "Reduce crypto concentration",
                "priority": "HIGH",
                "detail": f"Crypto is {crypto_pct:.0f}% of portfolio. Consider reducing to < 40% "
                          f"to limit drawdown in a {scenario['name']} event.",
                "estimated_risk_reduction_pct": round(min((crypto_pct - 40) * 0.5, 25), 1),
            })

        # Stablecoin / cash buffer
        cash = portfolio.get("cash", 0) + portfolio.get("USDT", 0) + portfolio.get("USDC", 0)
        cash_pct = cash / total_value * 100 if total_value else 0
        if cash_pct < 15:
            recommendations.append({
                "action": "Increase cash / stablecoin buffer",
                "priority": "HIGH",
                "detail": f"Cash/stablecoins are only {cash_pct:.0f}% of portfolio. "
                          f"Target at least 15-20% for liquidity during a crisis.",
                "estimated_risk_reduction_pct": round((15 - cash_pct) * 0.3, 1),
            })

        # Diversification into uncorrelated assets
        if "gold" not in portfolio and "GLD" not in portfolio:
            recommendations.append({
                "action": "Add gold or gold-backed assets",
                "priority": "MEDIUM",
                "detail": "Gold historically acts as a safe haven during market crises. "
                          "Consider allocating 5-10% of portfolio.",
                "estimated_risk_reduction_pct": 8.0,
            })

        # Options / hedging instruments
        if expected_loss > total_value * 0.15:
            recommendations.append({
                "action": "Consider put options or inverse ETFs",
                "priority": "MEDIUM",
                "detail": f"Expected loss under {scenario['name']} is "
                          f"${expected_loss:,.0f} ({expected_loss/total_value*100:.1f}%). "
                          f"Protective puts can cap downside at a defined level.",
                "estimated_risk_reduction_pct": 15.0,
            })

        # Stop-loss orders
        high_impact_assets = [
            (asset, impacts.get(asset, impacts.get("stocks", -0.30)))
            for asset, val in portfolio.items()
            if val > total_value * 0.10 and "/" in asset
        ]
        for asset, impact in high_impact_assets:
            if impact < -0.40:
                recommendations.append({
                    "action": f"Set stop-loss for {asset}",
                    "priority": "HIGH",
                    "detail": f"{asset} has an expected impact of {impact*100:.0f}% under this scenario. "
                              f"A trailing stop-loss at 15-20% can limit realised losses.",
                    "estimated_risk_reduction_pct": round(abs(impact) * 30, 1),
                })

        # Correlation-aware note
        if scenario["correlation_spike"] > 0.85:
            recommendations.append({
                "action": "Be aware of correlation spike",
                "priority": "INFO",
                "detail": f"During {scenario['name']}, asset correlations spike to "
                          f"{scenario['correlation_spike']:.2f}. Normal diversification benefits "
                          f"are significantly reduced.",
                "estimated_risk_reduction_pct": 0.0,
            })

        return {
            "scenario": scenario_id,
            "scenario_name": scenario["name"],
            "portfolio_value": round(total_value, 2),
            "expected_loss": round(expected_loss, 2),
            "expected_loss_pct": round(expected_loss / total_value * 100, 2) if total_value else 0,
            "recommendations": recommendations,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_simulator = CrisisSimulator()


def simulate_crisis_response() -> Dict[str, Any]:
    """Backwards-compatible convenience function."""
    demo_portfolio = {
        "BTC/USDT": 40000,
        "ETH/USDT": 20000,
        "SOL/USDT": 10000,
        "cash": 30000,
    }
    return _simulator.stress_test(demo_portfolio)


# ---------------------------------------------------------------------------
# FastAPI endpoints
# ---------------------------------------------------------------------------

@router.get("/crisis")
async def crisis_endpoint():
    return {
        "msg": "Crisis simulator active",
        "available_scenarios": _simulator.list_scenarios(),
    }


@router.get("/crisis/scenarios")
async def scenarios_endpoint():
    return _simulator.list_scenarios()


@router.post("/crisis/simulate")
async def simulate_endpoint(req: Request):
    data = await req.json()
    scenario_id = data.get("scenario")
    portfolio = data.get("portfolio")
    if not scenario_id or not portfolio:
        raise HTTPException(status_code=400, detail="'scenario' and 'portfolio' are required")
    num_sims = data.get("num_simulations", 500)
    return _simulator.simulate(scenario_id, portfolio, num_sims)


@router.post("/crisis/stress-test")
async def stress_test_endpoint(req: Request):
    data = await req.json()
    portfolio = data.get("portfolio")
    if not portfolio:
        raise HTTPException(status_code=400, detail="'portfolio' is required")
    scenarios = data.get("scenarios")
    num_sims = data.get("num_simulations", 300)
    return _simulator.stress_test(portfolio, scenarios, num_sims)


@router.post("/crisis/hedging")
async def hedging_endpoint(req: Request):
    data = await req.json()
    scenario_id = data.get("scenario")
    portfolio = data.get("portfolio")
    if not scenario_id or not portfolio:
        raise HTTPException(status_code=400, detail="'scenario' and 'portfolio' are required")
    return _simulator.get_hedging_recommendations(portfolio, scenario_id)


@router.get("/crisis/demo")
async def demo_endpoint():
    return simulate_crisis_response()
