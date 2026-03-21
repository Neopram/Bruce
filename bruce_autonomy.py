"""
Bruce AI — Advanced Autonomy System

This module gives Bruce true autonomous capabilities:
- Goal setting and pursuit
- Autonomous planning and execution
- Self-monitoring and correction
- Proactive intelligence gathering
- Decision chains with rollback
- Continuous self-improvement loop
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path
from enum import Enum

logger = logging.getLogger("Bruce.Autonomy")

AUTONOMY_DIR = Path("./data/autonomy")
AUTONOMY_DIR.mkdir(parents=True, exist_ok=True)


class GoalStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AutonomousPlanner:
    """Bruce's ability to set goals, plan, and execute autonomously."""

    def __init__(self):
        self._goals_file = AUTONOMY_DIR / "goals.json"
        self._plans_file = AUTONOMY_DIR / "plans.json"
        self._execution_log = AUTONOMY_DIR / "execution_log.json"
        self.goals = self._load("goals.json", [])
        self.plans = self._load("plans.json", [])
        self.execution_log = self._load("execution_log.json", [])

    def _load(self, fname, default):
        path = AUTONOMY_DIR / fname
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return default

    def _save(self, fname, data):
        (AUTONOMY_DIR / fname).write_text(
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

    # === Goals ===

    def set_goal(self, title: str, description: str, priority: str = "medium",
                 deadline: str = None) -> dict:
        """Bruce sets a goal for himself."""
        goal = {
            "id": f"goal-{len(self.goals)+1:03d}",
            "title": title,
            "description": description,
            "priority": priority,
            "status": GoalStatus.ACTIVE,
            "progress": 0,
            "steps": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "deadline": deadline,
            "outcome": None,
        }
        self.goals.append(goal)
        self._save("goals.json", self.goals)
        logger.info(f"New goal: {title} [{priority}]")
        return goal

    def update_goal_progress(self, goal_id: str, progress: int, note: str = ""):
        """Update progress on a goal."""
        for g in self.goals:
            if g["id"] == goal_id:
                g["progress"] = min(100, max(0, progress))
                if progress >= 100:
                    g["status"] = GoalStatus.COMPLETED
                if note:
                    g["steps"].append({
                        "note": note,
                        "progress": progress,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                self._save("goals.json", self.goals)
                return g
        return None

    def get_active_goals(self) -> List[dict]:
        return [g for g in self.goals if g["status"] == GoalStatus.ACTIVE]

    # === Planning ===

    def create_plan(self, goal_id: str, steps: List[str]) -> dict:
        """Create an execution plan for a goal."""
        plan = {
            "id": f"plan-{len(self.plans)+1:03d}",
            "goal_id": goal_id,
            "steps": [
                {"step": i + 1, "description": s, "status": "pending", "result": None}
                for i, s in enumerate(steps)
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "ready",
        }
        self.plans.append(plan)
        self._save("plans.json", self.plans)
        return plan

    def execute_plan(self, plan_id: str, execute_fn=None) -> dict:
        """Execute a plan step by step."""
        plan = next((p for p in self.plans if p["id"] == plan_id), None)
        if not plan:
            return {"error": "Plan not found"}

        plan["status"] = "executing"
        results = []

        for step in plan["steps"]:
            if step["status"] == "completed":
                continue

            step["status"] = "running"
            start = time.perf_counter()

            try:
                if execute_fn:
                    result = execute_fn(step["description"])
                else:
                    result = f"Executed: {step['description']}"

                step["status"] = "completed"
                step["result"] = str(result)[:500]
                elapsed = round((time.perf_counter() - start) * 1000, 1)

                self.execution_log.append({
                    "plan_id": plan_id,
                    "step": step["step"],
                    "description": step["description"],
                    "result": step["result"],
                    "elapsed_ms": elapsed,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                results.append({"step": step["step"], "status": "completed", "elapsed_ms": elapsed})

            except Exception as e:
                step["status"] = "failed"
                step["result"] = str(e)
                results.append({"step": step["step"], "status": "failed", "error": str(e)})
                plan["status"] = "failed"
                break

        if all(s["status"] == "completed" for s in plan["steps"]):
            plan["status"] = "completed"

        self._save("plans.json", self.plans)
        self._save("execution_log.json", self.execution_log[-200:])
        return {"plan_id": plan_id, "status": plan["status"], "results": results}


class SelfMonitor:
    """Bruce monitors his own performance and health."""

    def __init__(self):
        self._metrics_file = AUTONOMY_DIR / "metrics.json"
        self.metrics = self._load_metrics()

    def _load_metrics(self) -> dict:
        if self._metrics_file.exists():
            try:
                return json.loads(self._metrics_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "response_times": [],
            "error_count": 0,
            "success_count": 0,
            "uptime_start": datetime.now(timezone.utc).isoformat(),
            "anomalies_detected": [],
            "health_checks": [],
        }

    def _save_metrics(self):
        self._metrics_file.write_text(
            json.dumps(self.metrics, indent=2, default=str), encoding="utf-8"
        )

    def record_response(self, elapsed_ms: float, success: bool):
        """Record a response metric."""
        self.metrics["response_times"].append(elapsed_ms)
        self.metrics["response_times"] = self.metrics["response_times"][-1000:]
        if success:
            self.metrics["success_count"] += 1
        else:
            self.metrics["error_count"] += 1
        self._save_metrics()

    def detect_anomaly(self, metric_name: str, value: float) -> bool:
        """Detect if a metric value is anomalous."""
        times = self.metrics["response_times"]
        if len(times) < 10:
            return False
        avg = sum(times) / len(times)
        if value > avg * 3:  # 3x average = anomaly
            self.metrics["anomalies_detected"].append({
                "metric": metric_name,
                "value": value,
                "average": avg,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            self.metrics["anomalies_detected"] = self.metrics["anomalies_detected"][-50:]
            self._save_metrics()
            return True
        return False

    def health_check(self) -> dict:
        """Comprehensive health check."""
        times = self.metrics["response_times"]
        total = self.metrics["success_count"] + self.metrics["error_count"]
        health = {
            "status": "healthy",
            "uptime_since": self.metrics["uptime_start"],
            "total_requests": total,
            "success_rate": round(self.metrics["success_count"] / max(total, 1) * 100, 1),
            "avg_response_ms": round(sum(times) / max(len(times), 1), 1) if times else 0,
            "p95_response_ms": sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else 0,
            "anomalies": len(self.metrics["anomalies_detected"]),
            "error_count": self.metrics["error_count"],
        }

        # Determine health status
        if health["success_rate"] < 80:
            health["status"] = "degraded"
        if health["success_rate"] < 50:
            health["status"] = "critical"
        if health["error_count"] > 100:
            health["status"] = "degraded"

        self.metrics["health_checks"].append({
            **health, "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self.metrics["health_checks"] = self.metrics["health_checks"][-100:]
        self._save_metrics()
        return health


class SelfImprover:
    """Bruce's ability to analyze his own behavior and improve."""

    def __init__(self, learning_engine=None):
        self.learning = learning_engine
        self._improvements_file = AUTONOMY_DIR / "improvements.json"
        self.improvements = self._load()

    def _load(self) -> list:
        if self._improvements_file.exists():
            try:
                return json.loads(self._improvements_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def _save(self):
        self._improvements_file.write_text(
            json.dumps(self.improvements[-200:], indent=2, default=str), encoding="utf-8"
        )

    def analyze_performance(self, monitor: SelfMonitor) -> dict:
        """Analyze Bruce's performance and suggest improvements."""
        health = monitor.health_check()
        suggestions = []

        if health["avg_response_ms"] > 5000:
            suggestions.append({
                "area": "speed",
                "suggestion": "Response time too high. Consider lighter model or caching.",
                "priority": "high",
            })
        if health["success_rate"] < 90:
            suggestions.append({
                "area": "reliability",
                "suggestion": f"Success rate at {health['success_rate']}%. Investigate error patterns.",
                "priority": "critical",
            })
        if health["anomalies"] > 5:
            suggestions.append({
                "area": "stability",
                "suggestion": f"{health['anomalies']} anomalies detected. Review system load.",
                "priority": "high",
            })
        if not suggestions:
            suggestions.append({
                "area": "general",
                "suggestion": "System performing well. Continue monitoring.",
                "priority": "low",
            })

        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": health,
            "suggestions": suggestions,
        }
        self.improvements.append(analysis)
        self._save()
        return analysis

    def generate_evolution_report(self) -> dict:
        """Generate a report on how Bruce has evolved."""
        if not self.improvements:
            return {"message": "No improvement history yet."}

        areas = {}
        for imp in self.improvements:
            for s in imp.get("suggestions", []):
                area = s["area"]
                if area not in areas:
                    areas[area] = {"count": 0, "priorities": []}
                areas[area]["count"] += 1
                areas[area]["priorities"].append(s["priority"])

        return {
            "total_analyses": len(self.improvements),
            "focus_areas": {
                k: {
                    "occurrences": v["count"],
                    "critical_count": v["priorities"].count("critical"),
                }
                for k, v in areas.items()
            },
            "latest_health": self.improvements[-1].get("health", {}) if self.improvements else {},
        }


class ProactiveIntelligence:
    """Bruce proactively gathers intelligence and alerts Federico."""

    def __init__(self):
        self.alerts: List[dict] = []
        self.watchers: List[dict] = []

    def add_watcher(self, name: str, condition: str, action: str) -> dict:
        """Add a proactive watcher. Bruce monitors conditions and acts."""
        watcher = {
            "id": f"watch-{len(self.watchers)+1:03d}",
            "name": name,
            "condition": condition,
            "action": action,
            "active": True,
            "triggers": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.watchers.append(watcher)
        logger.info(f"Watcher added: {name} | {condition} → {action}")
        return watcher

    def check_watchers(self, current_state: dict) -> List[dict]:
        """Check all watchers against current state. Returns triggered alerts."""
        triggered = []
        for w in self.watchers:
            if not w["active"]:
                continue
            # Simple condition evaluation
            try:
                condition_met = self._evaluate_condition(w["condition"], current_state)
                if condition_met:
                    w["triggers"] += 1
                    alert = {
                        "watcher": w["name"],
                        "condition": w["condition"],
                        "action": w["action"],
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    self.alerts.append(alert)
                    triggered.append(alert)
                    logger.info(f"Watcher triggered: {w['name']}")
            except Exception:
                pass
        return triggered

    def _evaluate_condition(self, condition: str, state: dict) -> bool:
        """Evaluate a simple condition string against state."""
        # Support: "key > value", "key < value", "key == value", "key contains value"
        for op in [" > ", " < ", " == ", " contains "]:
            if op in condition:
                key, value = condition.split(op, 1)
                key = key.strip()
                value = value.strip()
                actual = state.get(key)
                if actual is None:
                    return False
                if op == " > ":
                    return float(actual) > float(value)
                elif op == " < ":
                    return float(actual) < float(value)
                elif op == " == ":
                    return str(actual) == value
                elif op == " contains ":
                    return value.lower() in str(actual).lower()
        return False

    def get_alerts(self, limit: int = 20) -> List[dict]:
        return self.alerts[-limit:]

    def list_watchers(self) -> List[dict]:
        return self.watchers
