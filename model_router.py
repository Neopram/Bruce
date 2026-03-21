"""Model router for Bruce AI.

Maintains singleton instances of each inference engine, routes prompts
based on task type and model availability, and provides health-check
and discovery endpoints.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from infer_deepseek import DeepSeekInference
from infer_phi3 import Phi3Inference
from infer_tinyllama import TinyLLaMAInference
from model_selector import ModelSelector

logger = logging.getLogger("Bruce.Router")


class ModelRouter:
    """Singleton-based router that manages model lifecycle and inference dispatch."""

    _instance: Optional["ModelRouter"] = None

    def __new__(cls) -> "ModelRouter":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._engines: Dict[str, Any] = {
            "deepseek": DeepSeekInference(),
            "phi3": Phi3Inference(),
            "tinyllama": TinyLLaMAInference(),
        }
        self._selector = ModelSelector()
        self._initialized = True
        logger.info("ModelRouter initialized with engines: %s", list(self._engines.keys()))

    # ------------------------------------------------------------------
    # Discovery & health
    # ------------------------------------------------------------------

    def get_available_models(self) -> List[str]:
        """Return names of models whose weights loaded successfully."""
        available = []
        for name, engine in self._engines.items():
            if engine.is_loaded:
                available.append(name)
        return available

    def get_all_models(self) -> List[str]:
        """Return all registered model names regardless of load state."""
        return list(self._engines.keys())

    def health_check(self) -> Dict[str, Dict[str, Any]]:
        """Return per-model health status dict."""
        status: Dict[str, Dict[str, Any]] = {}
        for name, engine in self._engines.items():
            status[name] = {
                "loaded": engine.is_loaded,
                "device": getattr(engine, "_device", None),
            }
        return status

    # ------------------------------------------------------------------
    # Preloading
    # ------------------------------------------------------------------

    def preload(self, model_name: str) -> bool:
        """Eagerly load a specific model. Returns True on success."""
        engine = self._engines.get(model_name)
        if engine is None:
            logger.warning("Unknown model requested for preload: %s", model_name)
            return False
        return engine.load()

    def preload_all(self) -> Dict[str, bool]:
        """Attempt to load every registered model. Returns per-model success map."""
        results = {}
        for name in self._engines:
            results[name] = self.preload(name)
        return results

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def _run_on_engine(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Execute inference on a named engine, loading it first if needed."""
        engine = self._engines.get(model_name)
        if engine is None:
            return f"[Router-error] Unknown model: {model_name}"

        # Phi-3 chat mode when messages are provided
        if model_name == "phi3" and messages is not None:
            return engine.chat(messages, max_tokens=max_tokens, temperature=temperature)

        return engine.run(prompt, max_tokens=max_tokens, temperature=temperature)

    def route(
        self,
        prompt: str,
        task: str = "chat",
        device_info: Optional[Dict[str, Any]] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Select the best model for *task* and run inference.

        Returns a dict with keys: response, model, elapsed_ms.
        Falls back through the chain if the primary model fails.
        """
        device_info = device_info or {}
        available = self.get_available_models()

        # Get ordered candidate list from the selector
        candidates = self._selector.get_fallback_chain(task, available)

        # If nothing is loaded yet, try all candidates in order
        if not candidates:
            candidates = self._selector.get_fallback_chain(task, self.get_all_models())

        last_error = ""
        for model_name in candidates:
            start = time.perf_counter()
            response = self._run_on_engine(
                model_name, prompt, max_tokens, temperature, messages
            )
            elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

            # Treat fallback/error sentinel strings as failures
            is_fallback = response.startswith("[") and ("-fallback]" in response or "-error]" in response)
            if is_fallback:
                last_error = response
                logger.warning("Model %s failed, trying next. Response: %s", model_name, response[:120])
                continue

            return {
                "response": response,
                "model": model_name,
                "elapsed_ms": elapsed_ms,
            }

        # All candidates exhausted
        return {
            "response": last_error or "[Router] All models unavailable.",
            "model": "none",
            "elapsed_ms": 0,
        }

    # ------------------------------------------------------------------
    # Async wrapper
    # ------------------------------------------------------------------

    async def run_inference(
        self,
        prompt: str,
        task: str = "chat",
        device_info: Optional[Dict[str, Any]] = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Async-ready inference that offloads blocking model work to a thread."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.route(
                prompt, task, device_info, max_tokens, temperature, messages
            ),
        )

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def unload(self, model_name: str):
        """Unload a specific model to free memory."""
        engine = self._engines.get(model_name)
        if engine:
            engine.unload()

    def unload_all(self):
        """Unload every model."""
        for engine in self._engines.values():
            engine.unload()


# ---------------------------------------------------------------------------
# Module-level convenience function (backward-compatible with old API)
# ---------------------------------------------------------------------------

def route_inference(
    prompt: str,
    task: str = "chat",
    device_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Simple function interface -- returns the response string only."""
    router = ModelRouter()
    result = router.route(prompt, task, device_info)
    return result["response"]
