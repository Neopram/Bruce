# self_reflection.py

"""
Bruce - Cognitive Self-Assessment Module
Maps knowledge domains, tracks confidence, identifies growth areas,
generates learning plans, and maintains a reflective journal.
"""

from datetime import datetime, timezone
import logging
import json
import os
from typing import Dict, List, Optional

logger = logging.getLogger("Bruce.SelfReflection")
logger.setLevel(logging.INFO)

REFLECTION_LOG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs", "reflections.jsonl"
)
os.makedirs(os.path.dirname(REFLECTION_LOG), exist_ok=True)


class SelfReflection:
    def __init__(self):
        self.domains: Dict[str, dict] = {
            "trading": {"level": 0.9, "confidence": "high", "last_updated": None},
            "macroeconomics": {"level": 0.85, "confidence": "high", "last_updated": None},
            "ai agents": {"level": 0.8, "confidence": "medium", "last_updated": None},
            "blockchain": {"level": 0.75, "confidence": "medium", "last_updated": None},
            "latam crypto taxation": {"level": 0.2, "confidence": "low", "last_updated": None},
            "decentralized governance": {"level": 0.4, "confidence": "low", "last_updated": None},
        }
        self.last_review = datetime.now(timezone.utc).isoformat()
        self._journal: List[dict] = []
        self._goals: List[dict] = []
        self._load_state()
        logger.info(f"[SelfReflection] Initialized with {len(self.domains)} domains")

    # ------------------------------------------------------------------ #
    #  Persistence
    # ------------------------------------------------------------------ #

    def _load_state(self):
        """Load saved reflection state from disk."""
        state_file = REFLECTION_LOG.replace(".jsonl", "_state.json")
        if not os.path.exists(state_file):
            return
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "domains" in data:
                self.domains = data["domains"]
            self._journal = data.get("journal", [])
            self._goals = data.get("goals", [])
            self.last_review = data.get("last_review", self.last_review)
        except Exception as e:
            logger.warning(f"[SelfReflection] Could not load state: {e}")

    def _save_state(self):
        """Persist current state to disk."""
        state_file = REFLECTION_LOG.replace(".jsonl", "_state.json")
        try:
            data = {
                "domains": self.domains,
                "journal": self._journal[-100:],  # keep last 100
                "goals": self._goals,
                "last_review": self.last_review,
            }
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"[SelfReflection] Could not save state: {e}")

    def _persist_entry(self, entry: dict):
        """Append a journal entry to the JSONL log."""
        try:
            with open(REFLECTION_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    #  Domain knowledge management
    # ------------------------------------------------------------------ #

    def evaluate(self) -> dict:
        """
        Evaluate current knowledge state across all domains.
        Returns a structured report with strengths, weaknesses, and growth areas.
        """
        known = []
        growing = []
        unknown = []
        for domain, info in self.domains.items():
            lvl = info["level"]
            if lvl >= 0.7:
                known.append(domain)
            elif lvl >= 0.4:
                growing.append(domain)
            else:
                unknown.append(domain)

        # Calculate overall knowledge score
        levels = [info["level"] for info in self.domains.values()]
        avg_level = sum(levels) / len(levels) if levels else 0

        report = {
            "known_domains": known,
            "growing_domains": growing,
            "unknown_domains": unknown,
            "total": len(self.domains),
            "average_level": round(avg_level, 3),
            "last_reviewed": self.last_review,
            "confidence_map": {d: info["confidence"] for d, info in self.domains.items()},
            "reflection_summary": (
                f"Strong in {len(known)} domains, growing in {len(growing)}, "
                f"need improvement in {len(unknown)}. Average level: {avg_level:.1%}."
            ),
        }

        self.last_review = datetime.now(timezone.utc).isoformat()
        logger.info(f"[SelfReflection] Evaluation complete: {report['reflection_summary']}")
        return report

    def update_knowledge(self, domain: str, delta: float, reason: Optional[str] = None):
        """
        Update knowledge level for a domain by delta.
        Automatically adjusts confidence tier.
        """
        if domain not in self.domains:
            self.domains[domain] = {"level": 0.1, "confidence": "low", "last_updated": None}

        old_level = self.domains[domain]["level"]
        new_level = min(max(old_level + delta, 0.0), 1.0)
        self.domains[domain]["level"] = round(new_level, 3)
        self.domains[domain]["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Update confidence tier
        if new_level >= 0.8:
            self.domains[domain]["confidence"] = "high"
        elif new_level >= 0.5:
            self.domains[domain]["confidence"] = "medium"
        else:
            self.domains[domain]["confidence"] = "low"

        self.last_review = datetime.now(timezone.utc).isoformat()

        # Record in journal
        entry = {
            "type": "knowledge_update",
            "domain": domain,
            "old_level": round(old_level, 3),
            "new_level": round(new_level, 3),
            "delta": delta,
            "reason": reason or "no reason provided",
            "timestamp": self.last_review,
        }
        self._journal.append(entry)
        self._persist_entry(entry)
        self._save_state()

        logger.info(f"[SelfReflection] Updated {domain}: {old_level:.2f} -> {new_level:.2f}")

    def add_new_domain(self, domain: str, initial_level: float = 0.1) -> dict:
        """Register a new knowledge domain."""
        if domain not in self.domains:
            confidence = "high" if initial_level >= 0.8 else ("medium" if initial_level >= 0.5 else "low")
            self.domains[domain] = {
                "level": initial_level,
                "confidence": confidence,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
            self._save_state()
            logger.info(f"[SelfReflection] New domain added: {domain}")
        return self.domains[domain]

    # ------------------------------------------------------------------ #
    #  Reflective journal
    # ------------------------------------------------------------------ #

    def reflect(self, topic: str, insight: str, sentiment: str = "neutral") -> dict:
        """
        Add a reflective journal entry about a topic.
        """
        entry = {
            "type": "reflection",
            "topic": topic,
            "insight": insight,
            "sentiment": sentiment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._journal.append(entry)
        self._persist_entry(entry)
        self._save_state()
        logger.info(f"[SelfReflection] Reflection on '{topic}': {insight[:60]}")
        return entry

    def get_journal(self, limit: int = 20, topic: Optional[str] = None) -> List[dict]:
        """Return recent journal entries, optionally filtered by topic."""
        entries = self._journal
        if topic:
            entries = [e for e in entries if topic.lower() in e.get("topic", "").lower()]
        return entries[-limit:]

    # ------------------------------------------------------------------ #
    #  Learning goals
    # ------------------------------------------------------------------ #

    def set_goal(self, domain: str, target_level: float, deadline: Optional[str] = None) -> dict:
        """Set a learning goal for a domain."""
        goal = {
            "domain": domain,
            "target_level": target_level,
            "current_level": self.domains.get(domain, {}).get("level", 0.0),
            "deadline": deadline,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._goals.append(goal)
        self._save_state()
        logger.info(f"[SelfReflection] Goal set: {domain} -> {target_level}")
        return goal

    def check_goals(self) -> List[dict]:
        """Check progress on all active goals."""
        results = []
        for goal in self._goals:
            if goal["status"] != "active":
                continue
            domain = goal["domain"]
            current = self.domains.get(domain, {}).get("level", 0.0)
            target = goal["target_level"]
            progress = current / target if target > 0 else 0.0

            status = "active"
            if current >= target:
                status = "achieved"
                goal["status"] = "achieved"

            results.append({
                "domain": domain,
                "current": round(current, 3),
                "target": target,
                "progress": round(min(progress, 1.0), 3),
                "status": status,
            })
        self._save_state()
        return results

    # ------------------------------------------------------------------ #
    #  Comprehensive self-report
    # ------------------------------------------------------------------ #

    def full_report(self) -> dict:
        """
        Generate a comprehensive self-reflection report covering
        domains, journal, goals, and growth trajectory.
        """
        evaluation = self.evaluate()
        goals = self.check_goals()
        recent_journal = self.get_journal(limit=5)

        # Growth trajectory: domains that have been updated recently
        recently_updated = []
        for domain, info in self.domains.items():
            if info.get("last_updated"):
                recently_updated.append({
                    "domain": domain,
                    "level": info["level"],
                    "last_updated": info["last_updated"],
                })
        recently_updated.sort(key=lambda x: x["last_updated"] or "", reverse=True)

        return {
            "evaluation": evaluation,
            "active_goals": [g for g in goals if g["status"] == "active"],
            "achieved_goals": [g for g in goals if g["status"] == "achieved"],
            "recent_reflections": recent_journal,
            "recently_updated_domains": recently_updated[:5],
            "total_journal_entries": len(self._journal),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# Test local
if __name__ == "__main__":
    brain = SelfReflection()
    print(json.dumps(brain.evaluate(), indent=2))
    brain.update_knowledge("latam crypto taxation", 0.3, reason="Studied local regulations")
    brain.add_new_domain("quantum finance")
    brain.reflect("trading", "Need to improve stop-loss discipline")
    brain.set_goal("quantum finance", 0.6, deadline="2026-06-01")
    print(json.dumps(brain.full_report(), indent=2))
