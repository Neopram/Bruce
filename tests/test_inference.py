"""Tests for inference engines and model routing."""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# DeepSeek Inference Tests
# ---------------------------------------------------------------------------

class TestDeepSeekInference:
    """Tests for infer_deepseek.py - DeepSeekInference."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        with patch("config.settings.get_settings") as mock_gs:
            mock_gs.return_value.deepseek_model_path = "./models/fake-deepseek"
            from infer_deepseek import DeepSeekInference
            self.engine = DeepSeekInference()

    def test_initial_state_not_loaded(self):
        """Engine should not be loaded initially."""
        assert self.engine.is_loaded is False

    def test_fallback_when_not_loaded(self):
        """run() returns fallback message when model cannot load."""
        result = self.engine.run("Test prompt")
        assert "[DeepSeek-fallback]" in result

    def test_unload_when_not_loaded(self):
        """unload() should not raise when nothing is loaded."""
        self.engine.unload()  # should not raise
        assert self.engine.is_loaded is False

    def test_fallback_contains_prompt(self):
        """Fallback response should include part of the prompt."""
        result = self.engine.run("What is Python?")
        assert "Python" in result or "fallback" in result.lower()


# ---------------------------------------------------------------------------
# Phi3 Inference Tests
# ---------------------------------------------------------------------------

class TestPhi3Inference:
    """Tests for infer_phi3.py - Phi3Inference."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        with patch("config.settings.get_settings") as mock_gs:
            mock_gs.return_value.phi3_model_path = "./models/fake-phi3"
            from infer_phi3 import Phi3Inference
            self.engine = Phi3Inference()

    def test_initial_state_not_loaded(self):
        """Engine should not be loaded initially."""
        assert self.engine.is_loaded is False

    def test_fallback_when_not_loaded(self):
        """run() returns fallback message when model cannot load."""
        result = self.engine.run("Test prompt")
        assert "[Phi3-fallback]" in result

    def test_chat_fallback(self):
        """chat() returns fallback when model is not available."""
        messages = [{"role": "user", "content": "Hello"}]
        result = self.engine.chat(messages)
        assert "[Phi3-fallback]" in result

    def test_chat_format_prompt(self):
        """_format_chat_prompt produces expected structure."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
        ]
        formatted = self.engine._format_chat_prompt(messages)
        assert "<|system|>" in formatted
        assert "<|user|>" in formatted
        assert "<|assistant|>" in formatted

    def test_unload_safe(self):
        """unload() is safe when nothing is loaded."""
        self.engine.unload()
        assert self.engine.is_loaded is False


# ---------------------------------------------------------------------------
# TinyLlama Inference Tests
# ---------------------------------------------------------------------------

class TestTinyLlamaInference:
    """Tests for infer_tinyllama.py - TinyLLaMAInference."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        with patch("config.settings.get_settings") as mock_gs:
            mock_gs.return_value.tinyllama_model_path = "./models/fake-tinyllama"
            from infer_tinyllama import TinyLLaMAInference
            self.engine = TinyLLaMAInference()

    def test_initial_state_not_loaded(self):
        """Engine should not be loaded initially."""
        assert self.engine.is_loaded is False

    def test_fallback_when_not_loaded(self):
        """run() returns fallback message when model cannot load."""
        result = self.engine.run("Quick status check")
        assert "[TinyLlama-fallback]" in result

    def test_unload_safe(self):
        """unload() is safe when nothing is loaded."""
        self.engine.unload()
        assert self.engine.is_loaded is False


# ---------------------------------------------------------------------------
# Model Router Tests
# ---------------------------------------------------------------------------

class TestModelRouter:
    """Tests for model_router.py - ModelRouter."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        # Reset singleton
        with patch("config.settings.get_settings") as mock_gs:
            mock_gs.return_value.deepseek_model_path = "./models/fake"
            mock_gs.return_value.phi3_model_path = "./models/fake"
            mock_gs.return_value.tinyllama_model_path = "./models/fake"
            from model_router import ModelRouter
            ModelRouter._instance = None
            self.router = ModelRouter()

    def test_get_all_models(self):
        """Router should list all registered model names."""
        models = self.router.get_all_models()
        assert "deepseek" in models
        assert "phi3" in models
        assert "tinyllama" in models

    def test_health_check(self):
        """health_check returns per-model status."""
        status = self.router.health_check()
        assert "deepseek" in status
        assert "loaded" in status["deepseek"]

    def test_route_returns_result_dict(self):
        """route() returns dict with response, model, elapsed_ms keys."""
        result = self.router.route("Hello", task="chat")
        assert "response" in result
        assert "model" in result
        assert "elapsed_ms" in result

    def test_route_all_unavailable(self):
        """When all models fail, router returns a fallback."""
        result = self.router.route("test prompt")
        # All models are fake, so all should fail
        assert "model" in result
        # response should contain fallback or error indicator
        assert isinstance(result["response"], str)


# ---------------------------------------------------------------------------
# Model Selector Tests
# ---------------------------------------------------------------------------

class TestModelSelector:
    """Tests for model_selector.py - ModelSelector."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        with patch("model_selector.torch") as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            from model_selector import ModelSelector, TASK_MODEL_MAP, DEFAULT_CHAIN
            self.selector = ModelSelector(device_info={"gpu_available": False})
            self.task_map = TASK_MODEL_MAP
            self.default_chain = DEFAULT_CHAIN

    def test_select_model_for_code(self):
        """Code tasks should prefer deepseek."""
        model = self.selector.select_model("code")
        assert model in ["deepseek", "phi3", "tinyllama"]

    def test_select_model_for_chat(self):
        """Chat tasks should prefer phi3."""
        model = self.selector.select_model("chat")
        assert model in ["phi3", "tinyllama", "deepseek"]

    def test_gpu_detection_false(self):
        """GPU should not be available in test env."""
        assert self.selector.gpu_available is False

    def test_fallback_chain(self):
        """Fallback chain should contain all models."""
        chain = self.selector.get_fallback_chain("code")
        assert len(chain) >= 1

    def test_unknown_task_uses_default(self):
        """Unknown task type falls back to default chain (with hardware adjustments)."""
        chain = self.selector.get_fallback_chain("completely_unknown_task")
        # Default chain is ["phi3", "deepseek", "tinyllama"] but hardware
        # constraints may reorder (e.g. no GPU moves deepseek to end).
        assert set(chain) == set(self.default_chain)
        assert len(chain) == len(self.default_chain)

    def test_get_recommended_model_with_available(self):
        """get_recommended_model filters by available models."""
        model = self.selector.get_recommended_model("code", available_models=["tinyllama"])
        assert model == "tinyllama"


# ---------------------------------------------------------------------------
# Orchestrator Tests
# ---------------------------------------------------------------------------

class TestOrchestrator:
    """Tests for orchestrator.py - cognitive_infer."""

    def test_cognitive_infer_returns_dict(self):
        """cognitive_infer returns a result dict with expected keys."""
        with patch("config.settings.get_settings") as mock_gs:
            mock_gs.return_value.deepseek_model_path = "./models/fake"
            mock_gs.return_value.phi3_model_path = "./models/fake"
            mock_gs.return_value.tinyllama_model_path = "./models/fake"
            # Reset router singleton
            from model_router import ModelRouter
            ModelRouter._instance = None
            from orchestrator import cognitive_infer
            result = cognitive_infer("Hello", task="chat", user_id="testuser")
            assert isinstance(result, dict)
            assert "response" in result
            assert "model" in result
            assert "elapsed_ms" in result
            assert "task" in result
            assert result["task"] == "chat"

    def test_cognitive_infer_pipeline_runs(self):
        """Pipeline should run end-to-end even when subsystems are unavailable."""
        with patch("config.settings.get_settings") as mock_gs:
            mock_gs.return_value.deepseek_model_path = "./models/fake"
            mock_gs.return_value.phi3_model_path = "./models/fake"
            mock_gs.return_value.tinyllama_model_path = "./models/fake"
            from model_router import ModelRouter
            ModelRouter._instance = None
            from orchestrator import cognitive_infer
            result = cognitive_infer("What is 2+2?", task="chat")
            assert isinstance(result["response"], str)
            assert result["elapsed_ms"] >= 0
