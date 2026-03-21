# Quantum-inspired optimizer (no pennylane/quantum dependency needed)
import math
import random
import time


class QuantumOptimizer:
    """Quantum-inspired optimization algorithms for portfolio and general optimization."""

    def __init__(self, seed=None):
        self._rng = random.Random(seed)
        self._history = []

    def optimize_portfolio(self, assets, constraints=None):
        """Quantum-inspired portfolio optimization using simulated annealing.

        Args:
            assets: List of dicts with 'symbol', 'expected_return', 'volatility'.
            constraints: Optional dict with 'max_weight', 'min_weight', 'target_return'.

        Returns:
            Dict with optimal weights and portfolio metrics.
        """
        if not assets:
            return {"error": "No assets provided"}

        constraints = constraints or {}
        n = len(assets)
        max_w = constraints.get("max_weight", 1.0)
        min_w = constraints.get("min_weight", 0.0)
        target_return = constraints.get("target_return")

        returns = [a.get("expected_return", 0.05) for a in assets]
        vols = [a.get("volatility", 0.2) for a in assets]

        def objective(weights):
            port_return = sum(w * r for w, r in zip(weights, returns))
            port_vol = math.sqrt(sum((w * v) ** 2 for w, v in zip(weights, vols)))
            sharpe = port_return / port_vol if port_vol > 0 else 0

            penalty = 0
            if target_return and port_return < target_return:
                penalty = (target_return - port_return) * 10

            return -(sharpe - penalty)  # Negative because SA minimizes

        def random_weights():
            raw = [self._rng.uniform(min_w, max_w) for _ in range(n)]
            total = sum(raw)
            return [w / total for w in raw] if total > 0 else [1.0 / n] * n

        bounds = [(min_w, max_w)] * n
        best_weights = random_weights()
        best_cost = objective(best_weights)

        result = self.simulated_annealing(
            objective=objective,
            bounds=bounds,
            iterations=1000,
            initial_solution=best_weights,
            normalize=True,
        )

        weights = result["best_solution"]
        port_return = sum(w * r for w, r in zip(weights, returns))
        port_vol = math.sqrt(sum((w * v) ** 2 for w, v in zip(weights, vols)))

        allocation = {}
        for i, asset in enumerate(assets):
            allocation[asset["symbol"]] = round(weights[i], 4)

        record = {
            "type": "portfolio_optimization",
            "assets": len(assets),
            "timestamp": time.time(),
        }
        self._history.append(record)

        return {
            "allocation": allocation,
            "expected_return": round(port_return, 4),
            "expected_volatility": round(port_vol, 4),
            "sharpe_ratio": round(port_return / port_vol, 4) if port_vol > 0 else 0,
            "iterations": result["iterations"],
        }

    def simulated_annealing(self, objective, bounds, iterations=1000,
                            initial_temp=1.0, cooling_rate=0.995,
                            initial_solution=None, normalize=False):
        """Simulated annealing optimizer.

        Args:
            objective: Callable that takes a solution list and returns cost (minimize).
            bounds: List of (min, max) tuples for each dimension.
            iterations: Number of iterations.
            initial_temp: Starting temperature.
            cooling_rate: Temperature decay per iteration.
            initial_solution: Optional starting point.
            normalize: If True, normalize solution to sum to 1 each step.

        Returns:
            Dict with best_solution, best_cost, iterations, and temperature history.
        """
        n = len(bounds)

        if initial_solution:
            current = list(initial_solution)
        else:
            current = [self._rng.uniform(lo, hi) for lo, hi in bounds]

        if normalize:
            total = sum(current)
            current = [c / total for c in current] if total > 0 else [1.0 / n] * n

        current_cost = objective(current)
        best = list(current)
        best_cost = current_cost
        temp = initial_temp
        temp_history = []

        for i in range(iterations):
            # Generate neighbor
            neighbor = list(current)
            idx = self._rng.randint(0, n - 1)
            lo, hi = bounds[idx]
            perturbation = self._rng.gauss(0, temp * (hi - lo) * 0.1)
            neighbor[idx] = max(lo, min(hi, neighbor[idx] + perturbation))

            if normalize:
                total = sum(neighbor)
                neighbor = [x / total for x in neighbor] if total > 0 else [1.0 / n] * n

            neighbor_cost = objective(neighbor)
            delta = neighbor_cost - current_cost

            if delta < 0 or self._rng.random() < math.exp(-delta / max(temp, 1e-10)):
                current = neighbor
                current_cost = neighbor_cost
                if current_cost < best_cost:
                    best = list(current)
                    best_cost = current_cost

            temp *= cooling_rate
            if i % 100 == 0:
                temp_history.append(round(temp, 6))

        record = {
            "type": "simulated_annealing",
            "iterations": iterations,
            "best_cost": round(best_cost, 6),
            "timestamp": time.time(),
        }
        self._history.append(record)

        return {
            "best_solution": [round(x, 6) for x in best],
            "best_cost": round(best_cost, 6),
            "iterations": iterations,
            "final_temperature": round(temp, 8),
            "temperature_history": temp_history,
        }

    def quantum_walk_search(self, graph, target):
        """Simulate a quantum walk search on a graph.

        Args:
            graph: Dict adjacency list, e.g. {'A': ['B', 'C'], 'B': ['A']}.
            target: Node to search for.

        Returns:
            Dict with path found, steps taken, and probability distribution.
        """
        if not graph:
            return {"error": "Empty graph"}
        if target not in graph:
            return {"found": False, "reason": "Target not in graph"}

        nodes = list(graph.keys())
        n = len(nodes)

        # Initialize uniform probability distribution (quantum superposition analog)
        prob = {node: 1.0 / n for node in nodes}
        visited = []
        steps = 0
        max_steps = n * 3

        current = self._rng.choice(nodes)
        path = [current]

        while steps < max_steps:
            steps += 1
            visited.append(current)

            if current == target:
                record = {
                    "type": "quantum_walk_search",
                    "steps": steps,
                    "found": True,
                    "timestamp": time.time(),
                }
                self._history.append(record)
                return {
                    "found": True,
                    "target": target,
                    "steps": steps,
                    "path": path,
                    "probability_distribution": {k: round(v, 4) for k, v in prob.items()},
                }

            # Quantum-inspired: update probabilities based on adjacency (Grover-like amplification)
            neighbors = graph.get(current, [])
            if not neighbors:
                current = self._rng.choice(nodes)
                path.append(current)
                continue

            # Amplify target probability if among neighbors
            for neighbor in neighbors:
                if neighbor == target:
                    prob[neighbor] = min(1.0, prob[neighbor] * 2)
                else:
                    prob[neighbor] = prob[neighbor] * 1.1

            # Normalize
            total_p = sum(prob.values())
            prob = {k: v / total_p for k, v in prob.items()}

            # Move based on probability
            r = self._rng.random()
            cumulative = 0
            for node in neighbors:
                cumulative += prob.get(node, 0)
                if r <= cumulative:
                    current = node
                    break
            else:
                current = self._rng.choice(neighbors)
            path.append(current)

        return {
            "found": False,
            "target": target,
            "steps": steps,
            "path": path[-20:],
            "probability_distribution": {k: round(v, 4) for k, v in prob.items()},
        }

    def get_optimization_history(self):
        """Return history of all optimization runs."""
        return {
            "total_runs": len(self._history),
            "history": self._history,
        }
