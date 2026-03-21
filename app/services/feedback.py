"""
Feedback Service - Collects, stores, and analyzes user feedback on interactions.
Uses in-memory storage with optional JSONL file persistence.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional


FEEDBACK_LOG_PATH = os.path.abspath("logs/feedback.jsonl")


class FeedbackEntry:
    """Single feedback record."""

    def __init__(
        self,
        user_id: str,
        interaction_id: str,
        rating: int,
        comment: Optional[str] = None,
    ):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.interaction_id = interaction_id
        self.rating = max(1, min(5, rating))
        self.comment = comment
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "interaction_id": self.interaction_id,
            "rating": self.rating,
            "comment": self.comment,
            "timestamp": self.timestamp,
        }


class FeedbackService:
    """Service for storing and querying user feedback."""

    def __init__(self, persist_path: Optional[str] = None):
        self._store: List[dict] = []
        self._persist_path = persist_path or FEEDBACK_LOG_PATH
        self._load_from_disk()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load_from_disk(self) -> None:
        """Load previously persisted feedback from JSONL file."""
        if not os.path.exists(self._persist_path):
            return
        try:
            with open(self._persist_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        self._store.append(json.loads(line))
        except Exception:
            pass  # graceful degradation if file is corrupt

    def _append_to_disk(self, entry: dict) -> None:
        """Append a single entry to the JSONL file."""
        try:
            os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)
            with open(self._persist_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def store_feedback(
        self,
        user_id: str,
        interaction_id: str,
        rating: int,
        comment: Optional[str] = None,
    ) -> dict:
        """Store a new feedback entry. Returns the created record."""
        entry = FeedbackEntry(user_id, interaction_id, rating, comment)
        record = entry.to_dict()
        self._store.append(record)
        self._append_to_disk(record)
        return record

    def get_feedback_history(self, user_id: str) -> List[dict]:
        """Return all feedback entries for a given user, newest first."""
        return sorted(
            [fb for fb in self._store if fb["user_id"] == user_id],
            key=lambda x: x["timestamp"],
            reverse=True,
        )

    def get_aggregate_stats(self) -> dict:
        """Return aggregate statistics across all feedback."""
        if not self._store:
            return {
                "total_entries": 0,
                "average_rating": 0.0,
                "rating_distribution": {str(i): 0 for i in range(1, 6)},
                "unique_users": 0,
            }

        ratings = [fb["rating"] for fb in self._store]
        distribution = {str(i): 0 for i in range(1, 6)}
        for r in ratings:
            distribution[str(r)] = distribution.get(str(r), 0) + 1

        return {
            "total_entries": len(self._store),
            "average_rating": round(sum(ratings) / len(ratings), 2),
            "rating_distribution": distribution,
            "unique_users": len({fb["user_id"] for fb in self._store}),
        }


class FeedbackLearner:
    """Learns from human feedback to auto-adjust prompts."""

    def __init__(self, feedback_service: Optional[FeedbackService] = None):
        self._service = feedback_service or FeedbackService()

    def learn_from(self, prompt: str, response: str) -> dict:
        """Analyze prompt/response pair and suggest improvements."""
        stats = self._service.get_aggregate_stats()
        avg = stats.get("average_rating", 0)
        suggestion = (
            "Consider simplifying language"
            if avg < 3
            else "Current style is well-received"
        )
        return {
            "analyzed_prompt_length": len(prompt),
            "analyzed_response_length": len(response),
            "current_avg_rating": avg,
            "suggestion": suggestion,
        }
