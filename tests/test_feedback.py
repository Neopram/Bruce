"""Tests for feedback_loop.py - FeedbackLearner."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from feedback_loop import FeedbackLearner


class TestFeedbackLearner:
    """Tests for the FeedbackLearner class."""

    @pytest.fixture(autouse=True)
    def _setup(self, temp_dir):
        """Create a fresh FeedbackLearner with temp storage."""
        self.storage_path = os.path.join(temp_dir, "feedback.jsonl")
        self.fl = FeedbackLearner(storage_path=self.storage_path)

    def test_learn_from(self):
        """learn_from stores an interaction and returns an ID."""
        result = self.fl.learn_from(
            prompt="What is BTC price?",
            response="BTC is at $67,500",
            model="phi3",
            user_id="user1",
        )
        assert "interaction_id" in result
        assert result["status"] == "stored"
        assert len(result["interaction_id"]) > 0

    def test_learn_from_multiple(self):
        """Multiple interactions are tracked independently."""
        r1 = self.fl.learn_from("Prompt 1", "Response 1", model="phi3")
        r2 = self.fl.learn_from("Prompt 2", "Response 2", model="deepseek")
        assert r1["interaction_id"] != r2["interaction_id"]
        assert len(self.fl._interactions) == 2

    def test_rate_interaction(self):
        """rate() applies a rating to a known interaction."""
        stored = self.fl.learn_from("Test", "Reply", model="phi3")
        iid = stored["interaction_id"]
        result = self.fl.rate(iid, rating=0.9, comment="Great answer")
        assert result["interaction_id"] == iid
        assert result["rating"] == 0.9
        assert result["comment"] == "Great answer"

    def test_rate_unknown_interaction(self):
        """Rating a non-existent interaction returns an error."""
        result = self.fl.rate("nonexistent-id", rating=0.5)
        assert "error" in result

    def test_rate_clamps_values(self):
        """Ratings should be clamped to [0.0, 1.0]."""
        stored = self.fl.learn_from("Test", "Reply", model="phi3")
        iid = stored["interaction_id"]

        result_high = self.fl.rate(iid, rating=5.0)
        assert result_high["rating"] == 1.0

    def test_ratings_summary_empty(self):
        """Summary with no ratings returns zero values."""
        summary = self.fl.get_ratings_summary()
        assert summary["total_ratings"] == 0
        assert summary["average"] == 0.0

    def test_ratings_summary_with_data(self):
        """Summary computes correct averages."""
        r1 = self.fl.learn_from("P1", "R1", model="phi3")
        r2 = self.fl.learn_from("P2", "R2", model="deepseek")
        self.fl.rate(r1["interaction_id"], rating=0.8)
        self.fl.rate(r2["interaction_id"], rating=0.6)

        summary = self.fl.get_ratings_summary()
        assert summary["total_ratings"] == 2
        assert summary["average"] == pytest.approx(0.7, abs=0.01)
        assert "phi3" in summary["by_model"]
        assert "deepseek" in summary["by_model"]

    def test_improvement_areas_no_low_ratings(self):
        """No low-rated interactions returns satisfactory message."""
        r = self.fl.learn_from("Test", "Reply", model="phi3")
        self.fl.rate(r["interaction_id"], rating=0.9)
        areas = self.fl.get_improvement_areas()
        assert len(areas) == 1
        assert "satisfactory" in areas[0]["message"].lower() or "Performance" in areas[0]["message"]

    def test_improvement_areas_with_low_ratings(self):
        """Low-rated interactions produce improvement suggestions."""
        r1 = self.fl.learn_from("Explain trading strategy basics", "Bad response", model="phi3")
        r2 = self.fl.learn_from("Help with trading portfolio", "Bad again", model="phi3")
        self.fl.rate(r1["interaction_id"], rating=0.1)
        self.fl.rate(r2["interaction_id"], rating=0.2)

        areas = self.fl.get_improvement_areas()
        assert len(areas) >= 1
        # "trading" should appear as a common topic
        topics = [a["topic"] for a in areas]
        assert any("trading" in t for t in topics)

    def test_model_ranking(self):
        """get_model_ranking returns models sorted by weight."""
        self.fl._model_weights = {"phi3": 1.2, "deepseek": 0.8, "tinyllama": 1.0}
        ranking = self.fl.get_model_ranking()
        assert len(ranking) == 3
        assert ranking[0]["model"] == "phi3"
        assert ranking[-1]["model"] == "deepseek"

    def test_model_ranking_empty(self):
        """Empty model weights returns empty ranking."""
        ranking = self.fl.get_model_ranking()
        assert ranking == []

    def test_adjust_weights_up(self):
        """adjust_weights 'up' increases model preference."""
        self.fl._model_weights["phi3"] = 1.0
        result = self.fl.adjust_weights("phi3", "up")
        assert result["new_weight"] > 1.0

    def test_adjust_weights_down(self):
        """adjust_weights 'down' decreases model preference."""
        self.fl._model_weights["phi3"] = 1.0
        result = self.fl.adjust_weights("phi3", "down")
        assert result["new_weight"] < 1.0

    def test_adjust_weights_clamped(self):
        """Weights should be clamped between 0.1 and 2.0."""
        self.fl._model_weights["phi3"] = 0.1
        result = self.fl.adjust_weights("phi3", "down")
        assert result["new_weight"] >= 0.1

        self.fl._model_weights["phi3"] = 2.0
        result = self.fl.adjust_weights("phi3", "up")
        assert result["new_weight"] <= 2.0

    def test_get_stats(self):
        """get_stats returns comprehensive feedback statistics."""
        self.fl.learn_from("P1", "R1", model="phi3")
        stats = self.fl.get_stats()
        assert stats["total_interactions"] == 1
        assert stats["rated_interactions"] == 0
        assert stats["unrated_interactions"] == 1

    def test_persistence(self, temp_dir):
        """Data persists across FeedbackLearner instances."""
        path = os.path.join(temp_dir, "persist_feedback.jsonl")
        fl1 = FeedbackLearner(storage_path=path)
        fl1.learn_from("Persist test", "Reply", model="phi3")

        fl2 = FeedbackLearner(storage_path=path)
        assert len(fl2._interactions) == 1
        assert fl2._interactions[0]["prompt"] == "Persist test"
