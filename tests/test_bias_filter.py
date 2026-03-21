"""Tests for bias_filter.py - BiasFilter."""

import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bias_filter import BiasFilter, BIAS_PATTERNS


class TestBiasDetection:
    """Tests for cognitive bias detection."""

    @pytest.fixture(autouse=True)
    def _setup(self, temp_dir):
        """Create a BiasFilter with temp storage."""
        import bias_filter
        self._orig_log = bias_filter.BIAS_LOG
        bias_filter.BIAS_LOG = os.path.join(temp_dir, "bias_history.jsonl")
        self.bf = BiasFilter()
        yield
        bias_filter.BIAS_LOG = self._orig_log

    def test_detect_confirmation_bias(self):
        """Detects confirmation bias keywords."""
        text = "Obviously this proves my point, I knew it all along"
        biases = self.bf.detect_biases(text)
        bias_names = [b["bias"] for b in biases]
        assert "confirmation_bias" in bias_names

    def test_detect_fomo(self):
        """Detects FOMO bias keywords."""
        text = "Everyone is buying, don't miss out, it's going to the moon!"
        biases = self.bf.detect_biases(text)
        bias_names = [b["bias"] for b in biases]
        assert "fomo" in bias_names

    def test_detect_anchoring_bias(self):
        """Detects anchoring bias keywords."""
        text = "It was at $100 originally, so compared to the original price this is cheap"
        biases = self.bf.detect_biases(text)
        bias_names = [b["bias"] for b in biases]
        assert "anchoring_bias" in bias_names

    def test_detect_overconfidence(self):
        """Detects overconfidence bias."""
        text = "This is a guaranteed 100% sure thing, impossible to lose"
        biases = self.bf.detect_biases(text)
        bias_names = [b["bias"] for b in biases]
        assert "overconfidence_bias" in bias_names

    def test_detect_sunk_cost(self):
        """Detects sunk cost fallacy."""
        text = "I already invested too much to sell now, just average down"
        biases = self.bf.detect_biases(text)
        bias_names = [b["bias"] for b in biases]
        assert "sunk_cost_fallacy" in bias_names

    def test_no_bias_detected(self):
        """Clean text should not trigger any bias detection."""
        text = "The current market cap is approximately 500 million dollars"
        biases = self.bf.detect_biases(text)
        assert len(biases) == 0

    def test_clean_text_returns_structure(self):
        """clean() returns expected dict structure."""
        result = self.bf.clean("I knew it would happen, told you so", user_id="user1")
        assert "original_text" in result
        assert "cleaned_text" in result
        assert "biases_detected" in result
        assert "warnings" in result
        assert "bias_count" in result
        assert "has_high_severity" in result

    def test_clean_text_no_bias(self):
        """clean() with no biases returns zero count."""
        result = self.bf.clean("The weather is sunny today", user_id="user1")
        assert result["bias_count"] == 0
        assert result["has_high_severity"] is False
        assert len(result["biases_detected"]) == 0

    def test_clean_records_high_severity(self):
        """clean() correctly flags high severity biases."""
        result = self.bf.clean(
            "This is guaranteed, 100% can't go wrong, trust me",
            user_id="user1",
        )
        assert result["has_high_severity"] is True

    def test_bias_report_empty_user(self):
        """Bias report for user with no history returns empty state."""
        report = self.bf.get_bias_report("nobody")
        assert report["total_scans"] == 0
        assert report["most_common_bias"] is None

    def test_bias_report_with_data(self):
        """Bias report accumulates detection data."""
        self.bf.clean("I knew it, confirms what I thought", user_id="user1")
        self.bf.clean("FOMO don't miss out, everyone is buying", user_id="user1")
        self.bf.clean("Told you so, proves my point", user_id="user1")

        report = self.bf.get_bias_report("user1")
        assert report["total_scans"] >= 2
        assert "bias_frequency" in report
        assert len(report["recommendations"]) > 0

    def test_bias_detection_returns_suggestions(self):
        """Each detected bias should include a suggestion."""
        text = "Everyone is buying, last chance, FOMO!"
        biases = self.bf.detect_biases(text)
        for b in biases:
            assert "suggestion" in b
            assert len(b["suggestion"]) > 0

    def test_all_patterns_compile(self):
        """All regex patterns in BIAS_PATTERNS should compile without error."""
        import re
        for bias_name, info in BIAS_PATTERNS.items():
            for pattern in info["patterns"]:
                try:
                    re.compile(pattern)
                except re.error as e:
                    pytest.fail(f"Invalid regex in {bias_name}: {pattern} -> {e}")


class TestBiasPatterns:
    """Tests for the BIAS_PATTERNS configuration."""

    def test_all_biases_have_required_fields(self):
        """Each bias pattern should have description, patterns, severity, suggestion."""
        required = {"description", "patterns", "severity", "suggestion"}
        for name, info in BIAS_PATTERNS.items():
            for field in required:
                assert field in info, f"Bias '{name}' missing field '{field}'"

    def test_severity_values(self):
        """Severity should be one of high, medium, low."""
        valid = {"high", "medium", "low"}
        for name, info in BIAS_PATTERNS.items():
            assert info["severity"] in valid, \
                f"Bias '{name}' has invalid severity '{info['severity']}'"
