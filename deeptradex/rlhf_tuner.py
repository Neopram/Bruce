"""
RLHF (Reinforcement Learning from Human Feedback) tuner for trading.
Collects human feedback on trade decisions, adjusts reward functions,
and supports A/B comparison of model variants.
"""
import random
import hashlib
from datetime import datetime
from collections import defaultdict


class RLHFTuner:
    """Collects human feedback and tunes trading model reward functions."""

    def __init__(self):
        self.feedback_store = []
        self.reward_weights = {
            "profit": 1.0,
            "risk_management": 0.8,
            "timing": 0.6,
            "position_sizing": 0.5,
            "drawdown_control": 0.7,
        }
        self.model_variants = {}
        self.comparison_results = []
        self.feedback_batch_size = 10
        self.update_count = 0

    def register_model_variant(self, variant_name, description="", reward_overrides=None):
        """Register a model variant for A/B testing."""
        variant = {
            "name": variant_name,
            "description": description,
            "reward_weights": self.reward_weights.copy(),
            "created_at": datetime.utcnow().isoformat(),
            "total_feedback": 0,
            "avg_human_score": 0,
            "trades_evaluated": 0,
        }
        if reward_overrides:
            variant["reward_weights"].update(reward_overrides)

        self.model_variants[variant_name] = variant
        return {"registered": variant_name, "total_variants": len(self.model_variants)}

    def submit_feedback(self, trade_id, human_score, aspects=None, comment="", variant_name=None):
        """Submit human feedback on a specific trade decision.

        Args:
            trade_id: Identifier of the trade being evaluated
            human_score: Overall score from 1 (poor) to 10 (excellent)
            aspects: Dict of aspect scores, e.g. {"profit": 8, "timing": 6}
            comment: Optional text feedback
            variant_name: Model variant that made the decision
        """
        if not 1 <= human_score <= 10:
            return {"status": "error", "message": "Score must be between 1 and 10"}

        feedback = {
            "trade_id": trade_id,
            "human_score": human_score,
            "normalized_score": round((human_score - 1) / 9, 4),
            "aspects": aspects or {},
            "comment": comment,
            "variant_name": variant_name,
            "submitted_at": datetime.utcnow().isoformat(),
        }
        self.feedback_store.append(feedback)

        if variant_name and variant_name in self.model_variants:
            v = self.model_variants[variant_name]
            v["total_feedback"] += 1
            v["trades_evaluated"] += 1
            total = v["total_feedback"]
            v["avg_human_score"] = round(
                (v["avg_human_score"] * (total - 1) + human_score) / total, 3
            )

        if len(self.feedback_store) % self.feedback_batch_size == 0:
            self._update_reward_weights()

        return {"status": "recorded", "total_feedback": len(self.feedback_store)}

    def _update_reward_weights(self):
        """Update reward weights based on accumulated human feedback."""
        recent = self.feedback_store[-self.feedback_batch_size:]
        aspect_scores = defaultdict(list)

        for fb in recent:
            for aspect, score in fb.get("aspects", {}).items():
                if aspect in self.reward_weights:
                    aspect_scores[aspect].append(score)

        if not aspect_scores:
            return

        learning_rate = 0.05
        for aspect, scores in aspect_scores.items():
            avg_score = sum(scores) / len(scores)
            normalized = (avg_score - 5) / 5  # Map to [-1, 1]
            adjustment = learning_rate * normalized
            new_weight = max(0.1, min(2.0, self.reward_weights[aspect] + adjustment))
            self.reward_weights[aspect] = round(new_weight, 4)

        self.update_count += 1

    def compute_reward(self, trade_metrics, variant_name=None):
        """Compute the reward for a trade using current (or variant-specific) weights."""
        weights = self.reward_weights
        if variant_name and variant_name in self.model_variants:
            weights = self.model_variants[variant_name]["reward_weights"]

        total_reward = 0
        weighted_sum = 0
        weight_total = 0

        for aspect, weight in weights.items():
            metric_value = trade_metrics.get(aspect, 0)
            weighted_sum += weight * metric_value
            weight_total += weight

        if weight_total > 0:
            total_reward = round(weighted_sum / weight_total, 4)

        return {
            "reward": total_reward,
            "weights_used": weights,
            "metrics": trade_metrics,
        }

    def compare_variants(self, variant_a, variant_b, trade_metrics_list):
        """A/B comparison of two model variants on a set of trades."""
        if variant_a not in self.model_variants or variant_b not in self.model_variants:
            return {"status": "error", "message": "One or both variants not found"}

        a_rewards = []
        b_rewards = []

        for metrics in trade_metrics_list:
            r_a = self.compute_reward(metrics, variant_a)
            r_b = self.compute_reward(metrics, variant_b)
            a_rewards.append(r_a["reward"])
            b_rewards.append(r_b["reward"])

        avg_a = round(sum(a_rewards) / len(a_rewards), 4) if a_rewards else 0
        avg_b = round(sum(b_rewards) / len(b_rewards), 4) if b_rewards else 0

        winner = variant_a if avg_a > avg_b else variant_b if avg_b > avg_a else "tie"
        margin = round(abs(avg_a - avg_b), 4)

        result = {
            "variant_a": variant_a,
            "variant_b": variant_b,
            "avg_reward_a": avg_a,
            "avg_reward_b": avg_b,
            "winner": winner,
            "margin": margin,
            "trades_evaluated": len(trade_metrics_list),
            "human_score_a": self.model_variants[variant_a]["avg_human_score"],
            "human_score_b": self.model_variants[variant_b]["avg_human_score"],
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.comparison_results.append(result)
        return result

    def get_best_variant(self):
        """Return the variant with the highest average human score."""
        if not self.model_variants:
            return {"status": "error", "message": "No variants registered"}

        best = max(self.model_variants.values(), key=lambda v: v["avg_human_score"])
        return {"best_variant": best["name"], "avg_score": best["avg_human_score"],
                "total_feedback": best["total_feedback"]}

    def get_reward_weights(self):
        """Return current reward weights."""
        return {"weights": self.reward_weights, "update_count": self.update_count}

    def set_reward_weight(self, aspect, weight):
        """Manually set a reward weight."""
        if aspect not in self.reward_weights:
            return {"status": "error", "message": f"Unknown aspect: {aspect}"}
        self.reward_weights[aspect] = max(0.1, min(2.0, weight))
        return {"aspect": aspect, "weight": self.reward_weights[aspect]}

    def get_feedback_summary(self):
        """Return summary statistics of collected feedback."""
        if not self.feedback_store:
            return {"total_feedback": 0}

        scores = [f["human_score"] for f in self.feedback_store]
        return {
            "total_feedback": len(self.feedback_store),
            "avg_score": round(sum(scores) / len(scores), 2),
            "min_score": min(scores),
            "max_score": max(scores),
            "update_count": self.update_count,
            "model_variants": len(self.model_variants),
            "comparisons_run": len(self.comparison_results),
        }

    def get_comparison_results(self, limit=10):
        """Return recent A/B comparison results."""
        return self.comparison_results[-limit:]

    def get_feedback_log(self, limit=30):
        """Return recent feedback entries."""
        return self.feedback_store[-limit:]
