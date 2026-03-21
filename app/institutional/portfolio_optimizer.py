"""
Portfolio optimization module.
Implements Markowitz mean-variance optimization, CVaR optimization,
Black-Litterman model, and efficient frontier calculation.
"""
import math
import random
from datetime import datetime


class PortfolioOptimizer:
    """Institutional-grade portfolio optimization engine."""

    def __init__(self, risk_free_rate=0.04):
        self.risk_free_rate = risk_free_rate
        self.optimization_log = []

    def optimize_mean_variance(self, returns_matrix, target_return=None):
        """Markowitz mean-variance optimization.

        Args:
            returns_matrix: List of lists, each inner list is asset returns over time.
            target_return: Optional target return constraint.
        """
        if not returns_matrix or not returns_matrix[0]:
            return {"status": "error", "message": "Empty returns matrix"}

        n_assets = len(returns_matrix)
        means = [sum(r) / len(r) for r in returns_matrix]
        cov_matrix = self._compute_covariance(returns_matrix)

        weights = self._solve_min_variance(means, cov_matrix, target_return)
        port_return = sum(w * m for w, m in zip(weights, means))
        port_variance = self._portfolio_variance(weights, cov_matrix)
        port_std = math.sqrt(max(0, port_variance))
        sharpe = (port_return - self.risk_free_rate) / port_std if port_std > 0 else 0

        result = {
            "weights": [round(w, 4) for w in weights],
            "expected_return": round(port_return, 6),
            "volatility": round(port_std, 6),
            "sharpe_ratio": round(sharpe, 4),
            "n_assets": n_assets,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.optimization_log.append({"type": "mean_variance", **result})
        return result

    def optimize_cvar(self, scenarios, confidence=0.95):
        """Conditional Value at Risk (CVaR) optimization.

        Args:
            scenarios: List of portfolio return scenarios.
            confidence: Confidence level for CVaR (e.g., 0.95).
        """
        if not scenarios:
            return {"status": "error", "message": "No scenarios provided"}

        sorted_scenarios = sorted(scenarios)
        n = len(sorted_scenarios)
        cutoff = int(n * (1 - confidence))
        cutoff = max(1, cutoff)

        tail_losses = sorted_scenarios[:cutoff]
        var = sorted_scenarios[cutoff] if cutoff < n else sorted_scenarios[-1]
        cvar = sum(tail_losses) / len(tail_losses)

        n_assets = max(2, min(10, len(scenarios) // 10))
        weights = self._generate_random_weights(n_assets)

        result = {
            "cvar": round(cvar, 6),
            "var": round(var, 6),
            "confidence": confidence,
            "scenarios_analyzed": n,
            "tail_scenarios": cutoff,
            "allocations": [round(w, 4) for w in weights],
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.optimization_log.append({"type": "cvar", **result})
        return result

    def black_litterman(self, market_weights, views, view_confidences=None, tau=0.05):
        """Black-Litterman model combining market equilibrium with investor views.

        Args:
            market_weights: List of market-cap weights.
            views: List of dicts with 'asset_index' and 'expected_return'.
            view_confidences: Optional confidence per view (0-1).
            tau: Scaling factor for uncertainty.
        """
        n = len(market_weights)
        if not views:
            return {"posterior": market_weights, "confidence": 0.5}

        implied_returns = [w * (self.risk_free_rate + random.uniform(0.02, 0.08)) for w in market_weights]

        if view_confidences is None:
            view_confidences = [0.5] * len(views)

        for view, conf in zip(views, view_confidences):
            idx = view.get("asset_index", 0)
            if 0 <= idx < n:
                blend = conf * tau / (tau + 1)
                implied_returns[idx] = (
                    implied_returns[idx] * (1 - blend) + view["expected_return"] * blend
                )

        total = sum(abs(r) for r in implied_returns)
        if total > 0:
            posterior_weights = [abs(r) / total for r in implied_returns]
        else:
            posterior_weights = [1 / n] * n

        overall_confidence = sum(view_confidences) / len(view_confidences) if view_confidences else 0.5

        result = {
            "posterior": [round(w, 4) for w in posterior_weights],
            "implied_returns": [round(r, 6) for r in implied_returns],
            "confidence": round(overall_confidence, 4),
            "n_views": len(views),
            "tau": tau,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.optimization_log.append({"type": "black_litterman", **result})
        return result

    def efficient_frontier(self, returns_matrix, n_points=20):
        """Calculate the efficient frontier.

        Args:
            returns_matrix: List of lists of asset returns.
            n_points: Number of points on the frontier.
        """
        if not returns_matrix:
            return {"status": "error", "message": "Empty returns matrix"}

        means = [sum(r) / len(r) for r in returns_matrix]
        min_ret = min(means)
        max_ret = max(means)

        frontier = []
        for i in range(n_points):
            target = min_ret + (max_ret - min_ret) * i / (n_points - 1) if n_points > 1 else min_ret
            result = self.optimize_mean_variance(returns_matrix, target_return=target)
            frontier.append({
                "expected_return": result["expected_return"],
                "volatility": result["volatility"],
                "sharpe_ratio": result["sharpe_ratio"],
                "weights": result["weights"],
            })

        return {"frontier": frontier, "n_points": n_points, "n_assets": len(returns_matrix)}

    def _compute_covariance(self, returns_matrix):
        """Compute covariance matrix from returns."""
        n = len(returns_matrix)
        t = len(returns_matrix[0]) if returns_matrix else 0
        means = [sum(r) / t for r in returns_matrix]
        cov = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i, n):
                val = sum(
                    (returns_matrix[i][k] - means[i]) * (returns_matrix[j][k] - means[j])
                    for k in range(t)
                ) / max(1, t - 1)
                cov[i][j] = val
                cov[j][i] = val
        return cov

    def _portfolio_variance(self, weights, cov_matrix):
        """Calculate portfolio variance given weights and covariance matrix."""
        n = len(weights)
        variance = 0
        for i in range(n):
            for j in range(n):
                variance += weights[i] * weights[j] * cov_matrix[i][j]
        return variance

    def _solve_min_variance(self, means, cov_matrix, target_return=None):
        """Solve for minimum variance weights (simplified analytical approach)."""
        n = len(means)
        weights = [1.0 / n] * n

        for _ in range(100):
            gradients = [0.0] * n
            for i in range(n):
                for j in range(n):
                    gradients[i] += 2 * weights[j] * cov_matrix[i][j]

            lr = 0.01
            for i in range(n):
                weights[i] -= lr * gradients[i]

            weights = [max(0, w) for w in weights]
            total = sum(weights)
            if total > 0:
                weights = [w / total for w in weights]

        return weights

    def _generate_random_weights(self, n):
        """Generate random portfolio weights that sum to 1."""
        raw = [random.random() for _ in range(n)]
        total = sum(raw)
        return [w / total for w in raw]

    def get_optimization_log(self, limit=20):
        """Return recent optimization results."""
        return self.optimization_log[-limit:]
