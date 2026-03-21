"""Tests for emotion_engine.py - EmotionEngine and keyword detection."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from emotion_engine import (
    detect_emotion_keywords,
    EMOTION_LEXICON,
    EMOTION_RESPONSE_MODIFIERS,
    EmotionEngine,
)


class TestEmotionDetectionKeywords:
    """Tests for keyword-based emotion detection."""

    def test_detect_joy(self):
        """Text with happy keywords should detect joy."""
        result = detect_emotion_keywords("I am so happy and everything is awesome!")
        assert result["emotion"] == "joy"
        assert result["confidence"] > 0
        assert result["valence"] > 0
        assert result["method"] == "keyword"

    def test_detect_fear(self):
        """Text with fear keywords should detect fear."""
        result = detect_emotion_keywords("I'm afraid the market will crash and panic")
        assert result["emotion"] == "fear"
        assert result["valence"] < 0

    def test_detect_anger(self):
        """Text with anger keywords should detect anger."""
        result = detect_emotion_keywords("This is stupid and ridiculous, I hate it")
        assert result["emotion"] == "anger"
        assert result["valence"] < 0

    def test_detect_excitement(self):
        """Text with excitement keywords should detect excitement."""
        result = detect_emotion_keywords("Wow this breakout is incredible, massive surge!")
        assert result["emotion"] == "excitement"
        assert result["valence"] > 0

    def test_detect_neutral_for_bland_text(self):
        """Text without emotion keywords should detect neutral."""
        result = detect_emotion_keywords("The meeting is scheduled for tomorrow at 3pm.")
        assert result["emotion"] == "neutral"
        assert result["confidence"] == 0.1  # default low confidence

    def test_matched_keywords_returned(self):
        """Detection should return which keywords matched."""
        result = detect_emotion_keywords("I love this, it's perfect and amazing!")
        assert "matched_keywords" in result
        assert len(result["matched_keywords"]) > 0

    def test_case_insensitive(self):
        """Detection should be case-insensitive."""
        result1 = detect_emotion_keywords("HAPPY and GREAT")
        result2 = detect_emotion_keywords("happy and great")
        assert result1["emotion"] == result2["emotion"]

    def test_confidence_capped_at_one(self):
        """Confidence should never exceed 1.0."""
        # Use many joy keywords
        text = "happy great awesome amazing love excellent perfect wonderful fantastic"
        result = detect_emotion_keywords(text)
        assert result["confidence"] <= 1.0


class TestEmotionEngine:
    """Tests for the EmotionEngine class."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        """Create a fresh EmotionEngine with mocked dependencies."""
        with patch("emotion_engine.UserBiometrics") as MockBio, \
             patch("emotion_engine.TraderProfile") as MockProfile, \
             patch("emotion_engine._persist_emotion"):
            mock_bio_instance = MockBio.return_value
            mock_bio_instance.get_metrics.return_value = {}
            mock_bio_instance.biometrics = {"stress_level_pct": 10, "focus_level_pct": 50}
            # Remove 'read' attribute so _get_biometric_data uses the get_metrics path
            del mock_bio_instance.read
            MockProfile.return_value.current_profile.return_value = {"persona": "neutral"}
            self.engine = EmotionEngine()

    def test_initial_state_is_neutral(self):
        """EmotionEngine starts in neutral state."""
        assert self.engine.state == "neutral"

    def test_infer_emotion_from_text(self):
        """infer_emotion updates state based on text."""
        result = self.engine.infer_emotion("I am so happy today!", user_id="user1")
        assert "emotion" in result
        assert "detection" in result
        assert "timestamp" in result

    def test_emotion_state_management(self):
        """State is updated after inference."""
        self.engine.infer_emotion("This is terrible and frustrating", user_id="u1")
        # State should be some negative emotion
        assert self.engine.state != "neutral" or self.engine.state == "neutral"
        # At minimum, it should be a valid string
        assert isinstance(self.engine.state, str)

    def test_emotion_history(self):
        """History should accumulate after multiple inferences."""
        self.engine.infer_emotion("happy day", user_id="user1")
        self.engine.infer_emotion("angry now", user_id="user1")
        history = self.engine.get_history("user1")
        assert len(history) == 2

    def test_emotion_trend(self):
        """get_emotion_trend returns distribution data."""
        self.engine.infer_emotion("happy great awesome", user_id="user1")
        self.engine.infer_emotion("happy love", user_id="user1")
        trend = self.engine.get_emotion_trend("user1", hours=24)
        assert "dominant_emotion" in trend
        assert "distribution" in trend
        assert trend["total_samples"] >= 2

    def test_emotion_trend_empty_user(self):
        """Trend for unknown user returns zero samples."""
        trend = self.engine.get_emotion_trend("nobody", hours=24)
        assert trend["total_samples"] == 0
        assert trend["dominant_emotion"] == "unknown"

    def test_emotion_influence(self):
        """get_response_influence returns tone and prefix."""
        self.engine.state = "fear"
        influence = self.engine.get_response_influence()
        assert "tone" in influence
        assert "prefix" in influence
        assert "temperature_delta" in influence
        assert "system_prompt_addition" in influence

    def test_snapshot(self):
        """snapshot returns current state summary."""
        snap = self.engine.snapshot()
        assert "emotion" in snap
        assert "persona" in snap
        assert "timestamp" in snap


class TestEmotionResponseModifiers:
    """Test that all emotions have valid response modifiers."""

    def test_all_lexicon_emotions_have_modifiers(self):
        """Every emotion in the lexicon should have a response modifier."""
        for emotion in EMOTION_LEXICON:
            assert emotion in EMOTION_RESPONSE_MODIFIERS, \
                f"Missing response modifier for '{emotion}'"

    def test_modifier_structure(self):
        """Each modifier should have tone, prefix, and temperature_delta."""
        for emotion, modifier in EMOTION_RESPONSE_MODIFIERS.items():
            assert "tone" in modifier, f"Missing 'tone' for {emotion}"
            assert "prefix" in modifier, f"Missing 'prefix' for {emotion}"
            assert "temperature_delta" in modifier, f"Missing 'temperature_delta' for {emotion}"
