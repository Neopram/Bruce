"""Tests for crisis_simulator.py - CrisisSimulator."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from crisis_simulator import (
    CrisisSimulator,
    CRISIS_SCENARIOS,
    _monte_carlo_paths,
    _compute_path_stats,
    simulate_crisis_response,
)


class TestCrisisScenarios:
    """Tests for predefined crisis scenarios."""

    def test_scenarios_exist(self):
        """Key scenarios should be defined."""
        assert "crash_2008" in CRISIS_SCENARIOS
        assert "flash_crash_2010" in CRISIS_SCENARIOS
        assert "covid_2020" in CRISIS_SCENARIOS
        assert "black_swan" in CRISIS_SCENARIOS

    def test_scenario_structure(self):
        """Each scenario should have required fields."""
        required = {"name", "description", "peak_drawdown_pct", "duration_days",
                    "recovery_days", "volatility_multiplier", "correlation_spike",
                    "asset_impacts"}
        for sid, scenario in CRISIS_SCENARIOS.items():
            for field in required:
                assert field in scenario, f"Scenario '{sid}' missing '{field}'"

    def test_drawdowns_are_negative(self):
        """Peak drawdowns should be negative percentages."""
        for sid, scenario in CRISIS_SCENARIOS.items():
            assert scenario["peak_drawdown_pct"] < 0, \
                f"Scenario '{sid}' drawdown should be negative"


class TestMonteCarloHelpers:
    """Tests for Monte Carlo simulation utilities."""

    def test_monte_carlo_paths_shape(self):
        """Generated paths should have correct dimensions."""
        paths = _monte_carlo_paths(
            initial_value=10000,
            mean_daily_return=-0.001,
            daily_volatility=0.02,
            days=30,
            num_simulations=50,
        )
        assert len(paths) == 50
        assert len(paths[0]) == 31  # initial + 30 days

    def test_monte_carlo_paths_start_at_initial(self):
        """All paths should start at the initial value."""
        paths = _monte_carlo_paths(100, -0.001, 0.02, 10, 20)
        for path in paths:
            assert path[0] == 100

    def test_monte_carlo_values_non_negative(self):
        """Path values should never go negative."""
        paths = _monte_carlo_paths(100, -0.05, 0.1, 50, 100)
        for path in paths:
            for v in path:
                assert v >= 0

    def test_compute_path_stats_structure(self):
        """Path stats should have expected keys."""
        paths = _monte_carlo_paths(10000, -0.001, 0.02, 30, 50)
        stats = _compute_path_stats(paths, 10000)
        expected_keys = {
            "mean_final_value", "median_final_value", "percentile_5",
            "percentile_95", "worst_case", "best_case",
            "mean_max_drawdown_pct", "worst_drawdown_pct",
            "prob_loss", "prob_loss_gt_50pct", "num_simulations",
        }
        for key in expected_keys:
            assert key in stats, f"Missing key '{key}' in path stats"


class TestCrisisSimulator:
    """Tests for the CrisisSimulator class."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.sim = CrisisSimulator()

    def test_list_scenarios(self):
        """list_scenarios returns all registered scenarios."""
        scenarios = self.sim.list_scenarios()
        assert len(scenarios) >= 4
        for s in scenarios:
            assert "id" in s
            assert "name" in s

    def test_simulate_crash_2008(self, sample_portfolio):
        """Simulate 2008 crash returns valid results."""
        result = self.sim.simulate("crash_2008", sample_portfolio, num_simulations=50)
        assert "error" not in result
        assert "scenario" in result
        assert result["scenario"]["id"] == "crash_2008"
        assert "portfolio_stats" in result
        assert "asset_results" in result
        assert result["portfolio_initial_value"] == sum(sample_portfolio.values())

    def test_simulate_flash_crash(self, sample_portfolio):
        """Simulate flash crash returns valid results."""
        result = self.sim.simulate("flash_crash_2010", sample_portfolio, num_simulations=50)
        assert "error" not in result
        assert result["scenario"]["name"] == "2010 Flash Crash"

    def test_simulate_unknown_scenario(self, sample_portfolio):
        """Unknown scenario returns error."""
        result = self.sim.simulate("nonexistent_crisis", sample_portfolio)
        assert "error" in result

    def test_simulate_empty_portfolio(self):
        """Empty portfolio returns error."""
        result = self.sim.simulate("crash_2008", {})
        assert "error" in result

    def test_stress_test_portfolio(self, sample_portfolio):
        """Stress test runs across all scenarios."""
        result = self.sim.stress_test(sample_portfolio, num_simulations=30)
        assert "worst_scenario" in result
        assert "scenarios_tested" in result
        assert len(result["scenarios_tested"]) >= 4
        assert "results" in result

    def test_stress_test_selected_scenarios(self, sample_portfolio):
        """Stress test with specific scenarios."""
        result = self.sim.stress_test(
            sample_portfolio,
            scenario_ids=["crash_2008", "covid_2020"],
            num_simulations=30,
        )
        assert len(result["scenarios_tested"]) == 2

    def test_hedging_recommendations(self, sample_portfolio):
        """Hedging recommendations return actionable advice."""
        result = self.sim.get_hedging_recommendations(sample_portfolio, "crash_2008")
        assert "error" not in result
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
        assert "expected_loss" in result
        for rec in result["recommendations"]:
            assert "action" in rec
            assert "priority" in rec

    def test_hedging_unknown_scenario(self, sample_portfolio):
        """Hedging for unknown scenario returns error."""
        result = self.sim.get_hedging_recommendations(sample_portfolio, "fake_crisis")
        assert "error" in result

    def test_hedging_empty_portfolio(self):
        """Hedging with empty portfolio returns error."""
        result = self.sim.get_hedging_recommendations({}, "crash_2008")
        assert "error" in result

    def test_simulate_crisis_response_convenience(self):
        """Module-level convenience function runs without error."""
        result = simulate_crisis_response()
        assert isinstance(result, dict)
        assert "worst_scenario" in result
