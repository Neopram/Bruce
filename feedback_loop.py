
# feedback_loop.py

"""
Feedback Loop module for Bruce AI.
Collects human feedback, ratings, and learns from interactions to
improve response quality and model selection over time.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger("Bruce.FeedbackLoop")
logger.setLevel(logging.INFO)

FEEDBACK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
FEEDBACK_FILE = os.path.join(FEEDBACK_DIR, "feedback.jsonl")
os.makedirs(FEEDBACK_DIR, exist_ok=True)


class FeedbackLearner:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or FEEDBACK_FILE
        self._interactions: List[dict] = []
        self._ratings: List[dict] = []
        self._model_weights: Dict[str, float] = {}
        self._load()

    # ------------------------------------------------------------------ #
    #  Persistence
    # ------------------------------------------------------------------ #

    def _load(self):
        """Load feedback history from disk."""
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                        rec_type = rec.get("type", "")
                        if rec_type == "interaction":
                            self._interactions.append(rec)
                        elif rec_type == "rating":
                            self._ratings.append(rec)
                        elif rec_type == "weight_adjustment":
                            model = rec.get("model")
                            if model:
                                self._model_weights[model] = rec.get("new_weight", 1.0)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.warning(f"[FeedbackLoop] Could not load history: {e}")

    def _persist(self, record: dict):
        """Append a record to the feedback log."""
        try:
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"[FeedbackLoop] Could not persist: {e}")

    # ------------------------------------------------------------------ #
    #  Core API
    # ------------------------------------------------------------------ #

    def learn_from(self, prompt: str, response: str, model: Optional[str] = None, user_id: str = "anonymous") -> dict:
        """
        Store an interaction for learning. Each interaction gets a unique ID
        that can be used for later rating.
        """
        interaction_id = str(uuid.uuid4())[:12]
        record = {
            "type": "interaction",
            "interaction_id": interaction_id,
            "prompt": prompt,
            "response": response,
            "model": model,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "rated": False,
        }
        self._interactions.append(record)
        self._persist(record)
        logger.info(f"[FeedbackLoop] Logged interaction {interaction_id}")
        return {"interaction_id": interaction_id, "status": "stored"}

    def rate(self, interaction_id: str, rating: float, comment: Optional[str] = None) -> dict:
        """
        Apply a human rating to a previous interaction.
        Rating: 0.0 (terrible) to 1.0 (perfect).
        """
        # Find the interaction
        target = None
        for i in self._interactions:
            if i.get("interaction_id") == interaction_id:
                target = i
                i["rated"] = True
                break

        if target is None:
            return {"error": f"Interaction {interaction_id} not found"}

        rating_record = {
            "type": "rating",
            "interaction_id": interaction_id,
            "rating": max(0.0, min(1.0, rating)),
            "comment": comment or "",
            "model": target.get("model"),
            "user_id": target.get("user_id", "anonymous"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._ratings.append(rating_record)
        self._persist(rating_record)

        # Auto-adjust model weights based on rating
        model = target.get("model")
        if model:
            direction = "up" if rating >= 0.6 else "down"
            self.adjust_weights(model, direction)

        logger.info(f"[FeedbackLoop] Rated interaction {interaction_id}: {rating}")
        return rating_record

    def get_ratings_summary(self) -> dict:
        """
        Return aggregated ratings summary across all interactions.
        """
        if not self._ratings:
            return {"total_ratings": 0, "average": 0.0, "by_model": {}}

        total = len(self._ratings)
        avg = sum(r["rating"] for r in self._ratings) / total

        # Per-model breakdown
        by_model: Dict[str, dict] = {}
        for r in self._ratings:
            model = r.get("model") or "unknown"
            if model not in by_model:
                by_model[model] = {"count": 0, "total_rating": 0.0, "ratings": []}
            by_model[model]["count"] += 1
            by_model[model]["total_rating"] += r["rating"]
            by_model[model]["ratings"].append(r["rating"])

        for model, data in by_model.items():
            data["average"] = round(data["total_rating"] / data["count"], 3)
            del data["total_rating"]
            # Keep only last 20 ratings for trend
            data["recent_trend"] = data.pop("ratings")[-20:]

        return {
            "total_ratings": total,
            "average": round(avg, 3),
            "by_model": by_model,
            "model_weights": dict(self._model_weights),
        }

    def get_improvement_areas(self) -> List[dict]:
        """
        Identify areas needing improvement based on low-rated interactions.
        Groups by common keywords in prompts that received low ratings.
        """
        low_rated_ids = {r["interaction_id"] for r in self._ratings if r["rating"] < 0.4}
        if not low_rated_ids:
            return [{"message": "No poorly rated interactions found. Performance is satisfactory."}]

        # Collect prompts from low-rated interactions
        low_prompts = []
        for i in self._interactions:
            if i.get("interaction_id") in low_rated_ids:
                low_prompts.append(i.get("prompt", ""))

        # Extract common themes
        import re
        word_freq: Dict[str, int] = {}
        for prompt in low_prompts:
            tokens = set(re.findall(r"\w{4,}", prompt.lower()))
            for token in tokens:
                word_freq[token] = word_freq.get(token, 0) + 1

        # Sort by frequency
        areas = []
        for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]:
            if count >= 2 or len(low_prompts) <= 3:
                areas.append({
                    "topic": word,
                    "occurrences_in_low_rated": count,
                    "suggestion": f"Review and improve handling of '{word}'-related queries.",
                })

        if not areas:
            areas.append({
                "topic": "general",
                "occurrences_in_low_rated": len(low_rated_ids),
                "suggestion": "Low-rated interactions are diverse. Consider overall response quality improvements.",
            })

        return areas

    def adjust_weights(self, model_name: str, direction: str) -> dict:
        """
        Adjust preference weight for a model.
        direction: 'up' to increase preference, 'down' to decrease.
        Weights are clamped to [0.1, 2.0].
        """
        current = self._model_weights.get(model_name, 1.0)
        delta = 0.05 if direction == "up" else -0.05
        new_weight = max(0.1, min(2.0, current + delta))
        self._model_weights[model_name] = round(new_weight, 3)

        record = {
            "type": "weight_adjustment",
            "model": model_name,
            "direction": direction,
            "old_weight": round(current, 3),
            "new_weight": round(new_weight, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._persist(record)
        logger.info(f"[FeedbackLoop] Adjusted {model_name} weight: {current:.3f} -> {new_weight:.3f}")
        return record

    def get_model_ranking(self) -> List[dict]:
        """Return models ranked by their current preference weight."""
        ranking = []
        for model, weight in sorted(self._model_weights.items(), key=lambda x: x[1], reverse=True):
            # Get rating stats for this model
            model_ratings = [r["rating"] for r in self._ratings if r.get("model") == model]
            avg_rating = sum(model_ratings) / len(model_ratings) if model_ratings else 0.0
            ranking.append({
                "model": model,
                "weight": weight,
                "total_ratings": len(model_ratings),
                "avg_rating": round(avg_rating, 3),
            })
        return ranking

    def get_stats(self) -> dict:
        """Return overall feedback system statistics."""
        rated_count = sum(1 for i in self._interactions if i.get("rated"))
        return {
            "total_interactions": len(self._interactions),
            "rated_interactions": rated_count,
            "unrated_interactions": len(self._interactions) - rated_count,
            "total_ratings": len(self._ratings),
            "tracked_models": len(self._model_weights),
            "model_weights": dict(self._model_weights),
        }
