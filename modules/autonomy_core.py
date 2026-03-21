"""
Autonomous decision system for Bruce.
Implements decision trees with confidence thresholds, human-in-the-loop
fallback when confidence is low, and action execution tracking.
"""
import random
import time
from datetime import datetime


class AutonomyCore:
    """Allows Bruce to operate autonomously with dynamic decision-making."""

    def __init__(self):
        self.planner = None  # Lazy-loaded to avoid circular imports
        self.confidence_threshold = 0.7
        self.human_in_loop_threshold = 0.4
        self.action_registry = {
            "analyze_logs": {"priority": 3, "estimated_time_s": 30, "risk": "low"},
            "generate_report": {"priority": 2, "estimated_time_s": 60, "risk": "low"},
            "optimize_code": {"priority": 4, "estimated_time_s": 120, "risk": "medium"},
            "train_model": {"priority": 5, "estimated_time_s": 300, "risk": "medium"},
            "execute_trade": {"priority": 1, "estimated_time_s": 5, "risk": "high"},
            "rebalance_portfolio": {"priority": 2, "estimated_time_s": 15, "risk": "high"},
        }
        self.execution_history = []
        self.pending_human_review = []
        self.autonomous_mode = True

    def _get_planner(self):
        """Lazy-load the planner to avoid circular import issues."""
        if self.planner is None:
            try:
                from modules.meta_bruce_planner import MetaBrucePlanner
                self.planner = MetaBrucePlanner()
            except ImportError:
                self.planner = None
        return self.planner

    def decide(self, context=None):
        """Make an autonomous decision based on context and confidence scoring."""
        options = list(self.action_registry.keys())
        scored_options = []
        for action in options:
            score = self._evaluate_action(action, context)
            scored_options.append((action, score))

        scored_options.sort(key=lambda x: x[1]["composite_score"], reverse=True)
        best_action, best_score = scored_options[0]

        if best_score["confidence"] < self.human_in_loop_threshold:
            self.pending_human_review.append({
                "action": best_action,
                "scores": best_score,
                "context": context,
                "requested_at": datetime.utcnow().isoformat(),
            })
            return {"action": None, "reason": "low_confidence", "pending_review": best_action}

        if best_score["confidence"] < self.confidence_threshold:
            return {"action": best_action, "mode": "cautious", "scores": best_score}

        return {"action": best_action, "mode": "autonomous", "scores": best_score}

    def _evaluate_action(self, action, context=None):
        """Evaluate an action and return confidence and priority scores."""
        info = self.action_registry.get(action, {})
        risk_penalties = {"low": 0, "medium": 0.1, "high": 0.25}
        base_confidence = random.uniform(0.3, 1.0)
        risk_penalty = risk_penalties.get(info.get("risk", "medium"), 0.1)

        if not self.autonomous_mode and info.get("risk") == "high":
            base_confidence *= 0.5

        confidence = max(0, min(1, base_confidence - risk_penalty))
        priority_score = info.get("priority", 3) / 5.0
        composite = confidence * 0.6 + priority_score * 0.4

        return {
            "confidence": round(confidence, 3),
            "priority_score": round(priority_score, 3),
            "composite_score": round(composite, 3),
            "risk": info.get("risk", "unknown"),
        }

    def execute(self, action=None, force=False):
        """Execute a decided action."""
        if action is None:
            decision = self.decide()
            action = decision.get("action")
            if action is None:
                return {"status": "blocked", "reason": "awaiting_human_review"}

        if not force and not self.autonomous_mode:
            info = self.action_registry.get(action, {})
            if info.get("risk") == "high":
                self.pending_human_review.append({
                    "action": action,
                    "requested_at": datetime.utcnow().isoformat(),
                })
                return {"status": "pending", "reason": "high_risk_requires_approval"}

        entry = {
            "action": action,
            "started_at": datetime.utcnow().isoformat(),
            "status": "executing",
        }

        try:
            result = self._run_action(action)
            entry["status"] = "completed"
            entry["result"] = result
            entry["completed_at"] = datetime.utcnow().isoformat()
        except Exception as e:
            entry["status"] = "failed"
            entry["error"] = str(e)

        self.execution_history.append(entry)
        return entry

    def _run_action(self, action):
        """Simulate running an action."""
        return {"action": action, "outcome": "success", "details": f"Action '{action}' completed"}

    def approve_pending(self, index=0):
        """Approve a pending human-review action."""
        if index >= len(self.pending_human_review):
            return {"status": "error", "message": "No pending action at that index"}
        pending = self.pending_human_review.pop(index)
        return self.execute(action=pending["action"], force=True)

    def set_autonomous_mode(self, enabled):
        """Enable or disable full autonomous mode."""
        self.autonomous_mode = enabled
        return {"autonomous_mode": self.autonomous_mode}

    def get_status(self):
        """Return current autonomy status."""
        return {
            "autonomous_mode": self.autonomous_mode,
            "confidence_threshold": self.confidence_threshold,
            "total_executions": len(self.execution_history),
            "pending_reviews": len(self.pending_human_review),
            "available_actions": list(self.action_registry.keys()),
        }

    def get_execution_history(self, limit=20):
        """Return recent execution history."""
        return self.execution_history[-limit:]
