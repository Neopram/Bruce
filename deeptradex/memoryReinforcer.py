"""
Memory reinforcement module for trading.
Reinforces successful trade patterns, decays failed ones,
provides pattern recognition in trade history, and adaptive learning rates.
"""
import math
import random
from datetime import datetime
from collections import defaultdict


class MemoryReinforcer:
    """Reinforcement-based memory system for trade pattern learning."""

    def __init__(self, learning_rate=0.1, decay_rate=0.05, min_strength=0.01):
        self.learning_rate = learning_rate
        self.decay_rate = decay_rate
        self.min_strength = min_strength
        self.patterns = {}
        self.trade_history = []
        self.reinforcement_log = []
        self.adaptive_lr = learning_rate

    def record_trade(self, trade):
        """Record a trade outcome for pattern extraction."""
        required_fields = {"asset", "action", "outcome"}
        if not required_fields.issubset(trade.keys()):
            return {"status": "error", "message": f"Trade must include: {required_fields}"}

        trade["recorded_at"] = datetime.utcnow().isoformat()
        self.trade_history.append(trade)

        pattern_key = self._extract_pattern(trade)
        self._reinforce_or_decay(pattern_key, trade)
        self._update_adaptive_lr()

        return {"pattern": pattern_key, "total_trades": len(self.trade_history)}

    def _extract_pattern(self, trade):
        """Extract a pattern key from a trade record."""
        asset = trade.get("asset", "unknown")
        action = trade.get("action", "unknown")
        context = trade.get("context", "default")
        return f"{asset}:{action}:{context}"

    def _reinforce_or_decay(self, pattern_key, trade):
        """Reinforce successful patterns, decay failed ones."""
        outcome = trade.get("outcome", "neutral")
        profit = trade.get("profit_pct", 0)

        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = {
                "strength": 0.5,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "avg_profit_pct": 0,
                "last_updated": None,
            }

        pattern = self.patterns[pattern_key]
        pattern["total_trades"] += 1

        if outcome == "win" or profit > 0:
            reward = self.adaptive_lr * (1 + abs(profit) / 100)
            pattern["strength"] = min(1.0, pattern["strength"] + reward)
            pattern["wins"] += 1
            action = "reinforced"
        elif outcome == "loss" or profit < 0:
            penalty = self.decay_rate * (1 + abs(profit) / 100)
            pattern["strength"] = max(self.min_strength, pattern["strength"] - penalty)
            pattern["losses"] += 1
            action = "decayed"
        else:
            slight_decay = self.decay_rate * 0.1
            pattern["strength"] = max(self.min_strength, pattern["strength"] - slight_decay)
            action = "slight_decay"

        total = pattern["wins"] + pattern["losses"]
        if total > 0:
            pattern["avg_profit_pct"] = round(
                (pattern["avg_profit_pct"] * (total - 1) + profit) / total, 4
            )
        pattern["last_updated"] = datetime.utcnow().isoformat()

        self.reinforcement_log.append({
            "pattern": pattern_key,
            "action": action,
            "new_strength": round(pattern["strength"], 4),
            "timestamp": pattern["last_updated"],
        })

    def _update_adaptive_lr(self):
        """Update learning rate based on recent performance."""
        recent = self.trade_history[-20:]
        if len(recent) < 5:
            return

        wins = sum(1 for t in recent if t.get("outcome") == "win" or t.get("profit_pct", 0) > 0)
        win_rate = wins / len(recent)

        if win_rate > 0.7:
            self.adaptive_lr = min(0.3, self.adaptive_lr * 1.1)
        elif win_rate < 0.3:
            self.adaptive_lr = max(0.01, self.adaptive_lr * 0.9)
        else:
            self.adaptive_lr = self.learning_rate

    def recognize_pattern(self, asset, action, context="default"):
        """Look up the strength and stats of a pattern."""
        key = f"{asset}:{action}:{context}"
        if key not in self.patterns:
            return {"pattern": key, "known": False, "recommendation": "no_data"}

        pattern = self.patterns[key]
        if pattern["strength"] > 0.7:
            recommendation = "strong_signal"
        elif pattern["strength"] > 0.4:
            recommendation = "moderate_signal"
        else:
            recommendation = "weak_signal"

        return {
            "pattern": key,
            "known": True,
            "strength": round(pattern["strength"], 4),
            "total_trades": pattern["total_trades"],
            "win_rate": round(pattern["wins"] / pattern["total_trades"], 3) if pattern["total_trades"] else 0,
            "avg_profit_pct": pattern["avg_profit_pct"],
            "recommendation": recommendation,
        }

    def get_top_patterns(self, n=10):
        """Return top N strongest patterns."""
        sorted_patterns = sorted(
            self.patterns.items(), key=lambda x: x[1]["strength"], reverse=True
        )
        return [
            {"pattern": k, "strength": round(v["strength"], 4),
             "total_trades": v["total_trades"],
             "win_rate": round(v["wins"] / v["total_trades"], 3) if v["total_trades"] else 0}
            for k, v in sorted_patterns[:n]
        ]

    def get_weak_patterns(self, threshold=0.3):
        """Return patterns below a strength threshold."""
        return [
            {"pattern": k, "strength": round(v["strength"], 4), "total_trades": v["total_trades"]}
            for k, v in self.patterns.items()
            if v["strength"] < threshold
        ]

    def decay_all(self, factor=None):
        """Apply time-based decay to all patterns."""
        decay = factor or self.decay_rate * 0.5
        for key, pattern in self.patterns.items():
            pattern["strength"] = max(self.min_strength, pattern["strength"] - decay)
            pattern["last_updated"] = datetime.utcnow().isoformat()
        return {"decayed_patterns": len(self.patterns), "decay_factor": decay}

    def get_stats(self):
        """Return memory reinforcer statistics."""
        total_trades = len(self.trade_history)
        wins = sum(1 for t in self.trade_history if t.get("outcome") == "win" or t.get("profit_pct", 0) > 0)
        return {
            "total_patterns": len(self.patterns),
            "total_trades": total_trades,
            "overall_win_rate": round(wins / total_trades, 3) if total_trades else 0,
            "adaptive_learning_rate": round(self.adaptive_lr, 4),
            "base_learning_rate": self.learning_rate,
            "decay_rate": self.decay_rate,
        }

    def get_reinforcement_log(self, limit=30):
        """Return recent reinforcement actions."""
        return self.reinforcement_log[-limit:]
