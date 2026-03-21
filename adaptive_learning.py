"""
Bruce AI — Adaptive Learning Engine

Bruce learns from EVERYTHING:
- Every conversation with Federico
- Every document ingested
- Every trade outcome
- Every mistake and success
- Federico's preferences, communication style, interests

This is Bruce's long-term memory and growth engine.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pathlib import Path

logger = logging.getLogger("Bruce.Learning")

LEARNING_DIR = Path("./data/learning")
LEARNING_DIR.mkdir(parents=True, exist_ok=True)


class AdaptiveLearningEngine:
    """Bruce's adaptive learning system. He grows smarter with every interaction."""

    def __init__(self):
        self.user_model = self._load_json("user_model.json", {
            "name": "Federico",
            "communication_style": "direct",
            "interests": [],
            "expertise_areas": [],
            "preferred_language": "es",
            "risk_profile": "moderate",
            "feedback_history": [],
            "interaction_count": 0,
            "first_interaction": None,
            "last_interaction": None,
        })
        self.domain_knowledge = self._load_json("domain_knowledge.json", {
            "domains": {},
            "total_facts": 0,
        })
        self.decision_log = self._load_json("decision_log.json", {
            "decisions": [],
            "success_rate": 0,
            "total_decisions": 0,
        })
        self.self_improvements = self._load_json("self_improvements.json", {
            "improvements": [],
            "lessons_learned": [],
            "version_history": [],
        })

    def _load_json(self, filename: str, default: dict) -> dict:
        path = LEARNING_DIR / filename
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return default.copy()

    def _save_json(self, filename: str, data: dict):
        path = LEARNING_DIR / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    # =========================================================================
    # User Adaptation — Learn Federico's preferences
    # =========================================================================

    def learn_from_interaction(self, user_message: str, bruce_response: str,
                                feedback: str = None):
        """Learn from every interaction with Federico."""
        now = datetime.now(timezone.utc).isoformat()
        self.user_model["interaction_count"] += 1
        self.user_model["last_interaction"] = now
        if not self.user_model["first_interaction"]:
            self.user_model["first_interaction"] = now

        # Detect language preference
        if any(w in user_message.lower() for w in ["que", "como", "para", "esto", "quiero"]):
            self.user_model["preferred_language"] = "es"
        elif any(w in user_message.lower() for w in ["what", "how", "the", "this", "want"]):
            self.user_model["preferred_language"] = "en"

        # Detect interests from keywords
        interest_keywords = {
            "shipping": ["shipping", "freight", "container", "route", "port", "vessel"],
            "crypto": ["bitcoin", "btc", "eth", "crypto", "defi", "token", "solana"],
            "trading": ["trade", "position", "order", "strategy", "pnl", "profit"],
            "macro": ["inflation", "gdp", "fed", "rates", "economy", "macro"],
            "ai": ["model", "llm", "train", "neural", "agent", "learning"],
            "code": ["code", "python", "api", "deploy", "docker", "build"],
        }
        msg_lower = user_message.lower()
        for interest, keywords in interest_keywords.items():
            if any(k in msg_lower for k in keywords):
                if interest not in self.user_model["interests"]:
                    self.user_model["interests"].append(interest)
                    logger.info(f"Learned new interest: {interest}")

        # Store feedback if provided
        if feedback:
            self.user_model["feedback_history"].append({
                "feedback": feedback,
                "context": user_message[:100],
                "timestamp": now,
            })
            # Keep last 100 feedbacks
            self.user_model["feedback_history"] = self.user_model["feedback_history"][-100:]

        self._save_json("user_model.json", self.user_model)

    def get_user_context(self) -> str:
        """Get a context string about Federico for LLM prompts."""
        m = self.user_model
        parts = [f"User: {m['name']}"]
        if m["interests"]:
            parts.append(f"Interests: {', '.join(m['interests'])}")
        if m["preferred_language"]:
            parts.append(f"Preferred language: {m['preferred_language']}")
        parts.append(f"Interactions: {m['interaction_count']}")
        if m["communication_style"]:
            parts.append(f"Style: {m['communication_style']}")
        return " | ".join(parts)

    # =========================================================================
    # Domain Learning — Learn ANY topic
    # =========================================================================

    def learn_domain(self, domain: str, facts: List[str], source: str = "unknown"):
        """Learn new facts about any domain."""
        if domain not in self.domain_knowledge["domains"]:
            self.domain_knowledge["domains"][domain] = {
                "facts": [],
                "sources": [],
                "learned_at": datetime.now(timezone.utc).isoformat(),
                "confidence": 0.5,
            }

        d = self.domain_knowledge["domains"][domain]
        for fact in facts:
            if fact not in d["facts"]:
                d["facts"].append(fact)
                self.domain_knowledge["total_facts"] += 1

        if source not in d["sources"]:
            d["sources"].append(source)

        # Confidence grows with more facts
        d["confidence"] = min(0.95, 0.3 + len(d["facts"]) * 0.01)

        self._save_json("domain_knowledge.json", self.domain_knowledge)
        logger.info(f"Learned {len(facts)} facts about '{domain}' (total: {len(d['facts'])})")

    def query_domain(self, domain: str, query: str) -> List[str]:
        """Query learned knowledge about a domain."""
        d = self.domain_knowledge["domains"].get(domain, {})
        facts = d.get("facts", [])
        if not facts:
            return []
        # Simple keyword matching
        query_words = set(query.lower().split())
        scored = []
        for fact in facts:
            fact_words = set(fact.lower().split())
            overlap = len(query_words & fact_words)
            if overlap > 0:
                scored.append((overlap, fact))
        scored.sort(reverse=True)
        return [f for _, f in scored[:10]]

    def get_known_domains(self) -> List[dict]:
        """List all domains Bruce has learned about."""
        return [
            {
                "domain": name,
                "facts_count": len(d["facts"]),
                "confidence": d["confidence"],
                "sources": len(d["sources"]),
            }
            for name, d in self.domain_knowledge["domains"].items()
        ]

    # =========================================================================
    # Decision Learning — Learn from outcomes
    # =========================================================================

    def log_decision(self, decision: str, context: str, outcome: str = None,
                     success: bool = None):
        """Log a decision and its outcome for future learning."""
        entry = {
            "decision": decision,
            "context": context,
            "outcome": outcome,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.decision_log["decisions"].append(entry)
        self.decision_log["total_decisions"] += 1

        # Update success rate
        decided = [d for d in self.decision_log["decisions"] if d["success"] is not None]
        if decided:
            self.decision_log["success_rate"] = sum(
                1 for d in decided if d["success"]
            ) / len(decided)

        # Keep last 500 decisions
        self.decision_log["decisions"] = self.decision_log["decisions"][-500:]
        self._save_json("decision_log.json", self.decision_log)

    def get_similar_decisions(self, context: str) -> List[dict]:
        """Find similar past decisions for better decision-making."""
        context_words = set(context.lower().split())
        scored = []
        for d in self.decision_log["decisions"]:
            d_words = set(d["context"].lower().split())
            overlap = len(context_words & d_words)
            if overlap > 1:
                scored.append((overlap, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for _, d in scored[:5]]

    # =========================================================================
    # Self-Improvement — Bruce gets better over time
    # =========================================================================

    def record_lesson(self, lesson: str, category: str = "general"):
        """Record a lesson Bruce has learned."""
        entry = {
            "lesson": lesson,
            "category": category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.self_improvements["lessons_learned"].append(entry)
        self._save_json("self_improvements.json", self.self_improvements)
        logger.info(f"Lesson learned: {lesson[:80]}")

    def get_lessons(self, category: str = None) -> List[dict]:
        """Get lessons Bruce has learned."""
        lessons = self.self_improvements["lessons_learned"]
        if category:
            lessons = [l for l in lessons if l.get("category") == category]
        return lessons[-20:]

    def get_growth_report(self) -> dict:
        """Generate a report on Bruce's growth and learning."""
        return {
            "user_model": {
                "name": self.user_model["name"],
                "interactions": self.user_model["interaction_count"],
                "known_interests": self.user_model["interests"],
                "preferred_language": self.user_model["preferred_language"],
            },
            "knowledge": {
                "domains_learned": len(self.domain_knowledge["domains"]),
                "total_facts": self.domain_knowledge["total_facts"],
                "top_domains": sorted(
                    self.get_known_domains(),
                    key=lambda x: x["facts_count"],
                    reverse=True,
                )[:5],
            },
            "decisions": {
                "total": self.decision_log["total_decisions"],
                "success_rate": round(self.decision_log["success_rate"] * 100, 1),
            },
            "lessons_learned": len(self.self_improvements["lessons_learned"]),
        }
