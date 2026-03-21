"""Model selector for Bruce AI.

Provides intelligent task-to-model mapping with GPU/CPU awareness,
memory checks, and fallback chains when preferred models are unavailable.
"""

import logging
import torch
from typing import Any, Dict, List, Optional

logger = logging.getLogger("Bruce.Selector")

# ---------------------------------------------------------------------------
# Task -> model mapping
# ---------------------------------------------------------------------------
# Each task maps to an ordered preference list.  The selector walks the list
# and picks the first model that is available.

TASK_MODEL_MAP: Dict[str, List[str]] = {
    # Code-centric tasks favour DeepSeek-coder
    "code": ["deepseek", "phi3", "tinyllama"],
    "code_generation": ["deepseek", "phi3", "tinyllama"],
    "code_review": ["deepseek", "phi3", "tinyllama"],
    "technical": ["deepseek", "phi3", "tinyllama"],
    "analysis": ["deepseek", "phi3", "tinyllama"],
    "debug": ["deepseek", "phi3", "tinyllama"],

    # Conversational / report tasks favour Phi-3
    "chat": ["phi3", "tinyllama", "deepseek"],
    "summarization": ["phi3", "tinyllama", "deepseek"],
    "report": ["phi3", "deepseek", "tinyllama"],
    "explanation": ["phi3", "tinyllama", "deepseek"],
    "translation": ["phi3", "tinyllama", "deepseek"],

    # Speed-critical tasks favour TinyLlama
    "fast": ["tinyllama", "phi3", "deepseek"],
    "status": ["tinyllama", "phi3", "deepseek"],
    "ping": ["tinyllama", "phi3", "deepseek"],
    "quick": ["tinyllama", "phi3", "deepseek"],
    "triage": ["tinyllama", "phi3", "deepseek"],
}

# Default fallback when task is unknown
DEFAULT_CHAIN: List[str] = ["phi3", "deepseek", "tinyllama"]


class ModelSelector:
    """Selects the best model for a task given hardware capabilities."""

    def __init__(self, device_info: Optional[Dict[str, Any]] = None):
        self.device_info = device_info or {}
        self._gpu_available: Optional[bool] = None
        self._vram_mb: Optional[float] = None

    # ------------------------------------------------------------------
    # Hardware detection
    # ------------------------------------------------------------------

    @property
    def gpu_available(self) -> bool:
        if self._gpu_available is None:
            # Prefer explicit device_info, fall back to torch detection
            if "gpu_available" in self.device_info:
                self._gpu_available = bool(self.device_info["gpu_available"])
            else:
                self._gpu_available = torch.cuda.is_available()
        return self._gpu_available

    @property
    def vram_mb(self) -> float:
        """Estimated free VRAM in megabytes (0 when no GPU)."""
        if self._vram_mb is None:
            if self.gpu_available and torch.cuda.is_available():
                try:
                    free, _ = torch.cuda.mem_get_info()
                    self._vram_mb = free / (1024 * 1024)
                except Exception:
                    self._vram_mb = 0.0
            else:
                self._vram_mb = 0.0
        return self._vram_mb

    def _ram_percent(self) -> float:
        return self.device_info.get("ram_percent", 50.0)

    # ------------------------------------------------------------------
    # Selection logic
    # ------------------------------------------------------------------

    def select_model(self, task: str) -> str:
        """Return the single best model name for *task*."""
        chain = self.get_fallback_chain(task)
        return chain[0] if chain else DEFAULT_CHAIN[0]

    def get_recommended_model(
        self, task: str, available_models: Optional[List[str]] = None
    ) -> str:
        """Return the best model given a task and which models are loaded.

        This is the primary public API for external callers.
        """
        chain = self.get_fallback_chain(task, available_models)
        return chain[0] if chain else DEFAULT_CHAIN[0]

    def get_fallback_chain(
        self, task: str, available_models: Optional[List[str]] = None
    ) -> List[str]:
        """Return an ordered list of model names to try for *task*.

        If *available_models* is given, only those names are included.
        Hardware constraints may reorder or filter the chain.
        """
        base_chain = TASK_MODEL_MAP.get(task, DEFAULT_CHAIN)

        # Apply hardware heuristics
        chain = self._apply_hardware_constraints(list(base_chain))

        if available_models is not None:
            chain = [m for m in chain if m in available_models]

        return chain if chain else list(DEFAULT_CHAIN)

    def _apply_hardware_constraints(self, chain: List[str]) -> List[str]:
        """Reorder / filter based on GPU availability and memory pressure."""
        # When RAM is critically high (>90%), prefer the lightest model first
        if self._ram_percent() > 90:
            if "tinyllama" in chain:
                chain.remove("tinyllama")
                chain.insert(0, "tinyllama")
            logger.warning("High RAM usage (%.1f%%), preferring TinyLlama", self._ram_percent())

        # Without GPU, deprioritise large models if VRAM is zero
        if not self.gpu_available:
            # Still usable on CPU, but move heavier models to the end
            for heavy in ("deepseek",):
                if heavy in chain:
                    chain.remove(heavy)
                    chain.append(heavy)

        # With GPU but limited VRAM (<2 GB free), prefer smaller models
        if self.gpu_available and 0 < self.vram_mb < 2048:
            if "tinyllama" in chain:
                chain.remove("tinyllama")
                chain.insert(0, "tinyllama")

        return chain
