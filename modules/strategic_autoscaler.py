"""
Auto-scaling module based on load and performance metrics.
Monitors system resources, scales workers up/down, and makes
load balancing decisions based on configurable thresholds.
"""
import time
import random
from datetime import datetime


class StrategicAutoscaler:
    """Analyzes strategy performance and decides scaling actions."""

    def __init__(self):
        self.metrics = {}
        self.workers = {}
        self.scaling_history = []
        self.config = {
            "scale_up_success_threshold": 0.8,
            "scale_up_latency_threshold": 1.0,
            "scale_down_success_threshold": 0.5,
            "min_workers": 1,
            "max_workers": 20,
            "cooldown_seconds": 60,
        }
        self.last_scale_time = {}

    def log_metric(self, strategy_name, success_rate, latency, quality_score):
        """Log performance metrics for a strategy."""
        entry = {
            "success_rate": success_rate,
            "latency": latency,
            "quality_score": quality_score,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if strategy_name not in self.metrics:
            self.metrics[strategy_name] = {"current": entry, "history": []}
        self.metrics[strategy_name]["current"] = entry
        self.metrics[strategy_name]["history"].append(entry)

        if len(self.metrics[strategy_name]["history"]) > 100:
            self.metrics[strategy_name]["history"] = self.metrics[strategy_name]["history"][-100:]

        return {"logged": strategy_name}

    def register_worker(self, strategy_name, worker_id, capacity=1.0):
        """Register a worker for a strategy."""
        if strategy_name not in self.workers:
            self.workers[strategy_name] = []
        self.workers[strategy_name].append({
            "worker_id": worker_id,
            "capacity": capacity,
            "status": "active",
            "registered_at": datetime.utcnow().isoformat(),
        })
        return {"strategy": strategy_name, "total_workers": len(self.workers[strategy_name])}

    def recommend(self):
        """Generate scaling recommendations for all strategies."""
        suggestions = {}
        for name, metric_data in self.metrics.items():
            metric = metric_data["current"]
            current_workers = len(self.workers.get(name, []))

            if (metric["success_rate"] > self.config["scale_up_success_threshold"]
                    and metric["latency"] < self.config["scale_up_latency_threshold"]):
                if current_workers < self.config["max_workers"]:
                    suggestions[name] = {"action": "scale_up", "reason": "high_performance",
                                         "current_workers": current_workers}
                else:
                    suggestions[name] = {"action": "maintain", "reason": "at_max_capacity",
                                         "current_workers": current_workers}
            elif metric["success_rate"] < self.config["scale_down_success_threshold"]:
                if current_workers > self.config["min_workers"]:
                    suggestions[name] = {"action": "scale_down", "reason": "low_success_rate",
                                         "current_workers": current_workers}
                else:
                    suggestions[name] = {"action": "maintain", "reason": "at_min_workers",
                                         "current_workers": current_workers}
            else:
                suggestions[name] = {"action": "maintain", "reason": "within_thresholds",
                                     "current_workers": current_workers}
        return suggestions

    def auto_scale(self):
        """Automatically apply scaling recommendations."""
        recommendations = self.recommend()
        actions_taken = []

        for strategy, rec in recommendations.items():
            now = time.time()
            last = self.last_scale_time.get(strategy, 0)
            if now - last < self.config["cooldown_seconds"]:
                continue

            if rec["action"] == "scale_up":
                new_worker = f"worker_{strategy}_{len(self.workers.get(strategy, []))}"
                self.register_worker(strategy, new_worker)
                self.last_scale_time[strategy] = now
                action = {"strategy": strategy, "action": "scaled_up", "new_worker": new_worker,
                          "timestamp": datetime.utcnow().isoformat()}
                actions_taken.append(action)
                self.scaling_history.append(action)

            elif rec["action"] == "scale_down":
                workers = self.workers.get(strategy, [])
                if len(workers) > self.config["min_workers"]:
                    removed = workers.pop()
                    self.last_scale_time[strategy] = now
                    action = {"strategy": strategy, "action": "scaled_down",
                              "removed_worker": removed["worker_id"],
                              "timestamp": datetime.utcnow().isoformat()}
                    actions_taken.append(action)
                    self.scaling_history.append(action)

        return actions_taken

    def get_system_resources(self):
        """Get simulated system resource metrics."""
        return {
            "cpu_usage_pct": round(random.uniform(10, 95), 1),
            "memory_usage_pct": round(random.uniform(20, 85), 1),
            "active_workers": sum(len(w) for w in self.workers.values()),
            "strategies_monitored": len(self.metrics),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_scaling_history(self, limit=20):
        """Return recent scaling actions."""
        return self.scaling_history[-limit:]

    def update_config(self, **kwargs):
        """Update scaler configuration."""
        for key, value in kwargs.items():
            if key in self.config:
                self.config[key] = value
        return {"config": self.config}

    def get_status(self):
        """Return current autoscaler status."""
        return {
            "strategies": len(self.metrics),
            "total_workers": sum(len(w) for w in self.workers.values()),
            "config": self.config,
            "scaling_actions_taken": len(self.scaling_history),
            "resources": self.get_system_resources(),
        }
