"""Tests for personality.py - TraderProfile personality engine."""

import os
import sys
import json
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from personality import TraderProfile, DEFAULT_PROFILES


class TestTraderProfile:
    """Tests for the TraderProfile class."""

    @pytest.fixture(autouse=True)
    def _setup(self, temp_dir):
        """Create a TraderProfile that does not touch the real personality file."""
        # Monkey-patch PERSONALITY_FILE to temp dir before creating instance
        import personality
        self._orig_file = personality.PERSONALITY_FILE
        personality.PERSONALITY_FILE = os.path.join(temp_dir, "personality_state.json")
        self.profile = TraderProfile()
        yield
        personality.PERSONALITY_FILE = self._orig_file

    def test_initial_persona_is_neutral(self):
        """New TraderProfile defaults to neutral persona."""
        assert self.profile.persona == "neutral"

    def test_list_profiles(self):
        """list_profiles returns all available profiles."""
        profiles = self.profile.list_profiles()
        assert "aggressive" in profiles
        assert "conservative" in profiles
        assert "neutral" in profiles
        assert "zen" in profiles
        assert "reactive" in profiles
        assert "analytical" in profiles
        assert "opportunistic" in profiles

    def test_set_persona_direct(self):
        """set_persona_direct switches the active personality."""
        result = self.profile.set_persona_direct("aggressive")
        assert result == "aggressive"
        assert self.profile.persona == "aggressive"

    def test_set_persona_unknown(self):
        """Setting an unknown persona does not change state."""
        original = self.profile.persona
        result = self.profile.set_persona_direct("nonexistent_persona")
        assert self.profile.persona == original
        assert result == original

    def test_personality_switch_records_transition(self):
        """Switching personalities records a transition in history."""
        self.profile.set_persona_direct("aggressive")
        self.profile.set_persona_direct("zen")
        history = self.profile.get_transition_history()
        assert len(history) >= 2
        assert history[-1]["from"] == "aggressive"
        assert history[-1]["to"] == "zen"

    def test_update_from_text_aggressive(self):
        """Text with aggressive triggers should switch to aggressive."""
        result = self.profile.update_from_text("Let's go yolo on this pump!")
        assert result == "aggressive"

    def test_update_from_text_conservative(self):
        """Text with conservative triggers should switch to conservative."""
        result = self.profile.update_from_text("We need to be safe and hedge")
        assert result == "conservative"

    def test_update_from_text_no_match(self):
        """Text without triggers should not change persona."""
        original = self.profile.persona
        result = self.profile.update_from_text("The weather is nice today")
        assert result == original

    def test_update_from_market_data_high_volatility(self):
        """High volatility should trigger reactive mode."""
        result = self.profile.update_from_market_data(0.85)
        assert result == "reactive"

    def test_update_from_market_data_low_volatility(self):
        """Low volatility should trigger zen mode."""
        result = self.profile.update_from_market_data(0.15)
        assert result == "zen"

    def test_personality_blending(self):
        """Blended params should interpolate during transition."""
        self.profile.set_persona_direct("aggressive")
        # Force a transition
        self.profile.set_persona_direct("zen")
        # Transition progress should start at 0
        assert self.profile._transition_progress == 0.0
        params = self.profile.get_blended_params()
        assert "transition_progress" in params
        assert params["transition_progress"] == 0.0

    def test_advance_transition(self):
        """advance_transition moves the progress toward 1.0."""
        self.profile.set_persona_direct("aggressive")
        self.profile.set_persona_direct("zen")
        self.profile.advance_transition(0.5)
        assert self.profile._transition_progress == pytest.approx(0.5)
        self.profile.advance_transition(0.5)
        assert self.profile._transition_progress == pytest.approx(1.0)

    def test_get_system_prompt_modifier(self):
        """System prompt modifier returns a non-empty string."""
        self.profile.set_persona_direct("analytical")
        self.profile._transition_progress = 1.0
        prompt = self.profile.get_system_prompt_modifier()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "quantitative" in prompt.lower() or "data" in prompt.lower()

    def test_get_temperature(self):
        """get_temperature returns a float for the current persona."""
        self.profile.set_persona_direct("aggressive")
        self.profile._transition_progress = 1.0
        temp = self.profile.get_temperature()
        assert 0.0 <= temp <= 1.0
        assert temp == DEFAULT_PROFILES["aggressive"]["temperature"]

    def test_current_profile_structure(self):
        """current_profile returns expected keys."""
        cp = self.profile.current_profile()
        assert "persona" in cp
        assert "updated_at" in cp
        assert "reason" in cp
        assert "params" in cp


class TestDefaultProfiles:
    """Tests for the DEFAULT_PROFILES configuration."""

    def test_all_profiles_have_required_keys(self):
        """Each profile should have triggers, description, and numeric params."""
        required_keys = {"triggers", "description", "risk_tolerance", "patience",
                         "creativity", "formality", "verbosity", "temperature",
                         "system_prompt_style"}
        for name, profile in DEFAULT_PROFILES.items():
            for key in required_keys:
                assert key in profile, f"Profile '{name}' missing key '{key}'"

    def test_numeric_params_in_range(self):
        """Numeric personality params should be between 0 and 1."""
        numeric_keys = ["risk_tolerance", "patience", "creativity",
                        "formality", "verbosity", "temperature"]
        for name, profile in DEFAULT_PROFILES.items():
            for key in numeric_keys:
                val = profile[key]
                assert 0.0 <= val <= 1.0, \
                    f"Profile '{name}' param '{key}' = {val} out of [0, 1]"
