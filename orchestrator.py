"""Cognitive orchestrator for Bruce AI.

Central pipeline that ties together model routing, memory recall,
personality adjustment, and response logging into a single
`cognitive_infer` entry point.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("Bruce.Orchestrator")

# ---------------------------------------------------------------------------
# Lazy / optional imports -- the orchestrator must run even when some
# subsystems are missing or not yet installed.
# ---------------------------------------------------------------------------


def _try_import_router():
    try:
        from model_router import ModelRouter
        return ModelRouter
    except Exception as e:
        logger.warning("ModelRouter unavailable: %s", e)
        return None


def _try_import_memory():
    try:
        from app.core.memory import MemoryManager
        return MemoryManager
    except Exception as e:
        logger.debug("MemoryManager unavailable: %s", e)
        return None


def _try_import_personality():
    try:
        from ai_core.personality_engine import PersonalityEngine
        return PersonalityEngine
    except Exception as e:
        logger.debug("PersonalityEngine unavailable: %s", e)
        return None


def _try_import_vector_logger():
    try:
        from vector_logger import VectorLogger, VectorLogEntry
        return VectorLogger, VectorLogEntry
    except Exception as e:
        logger.debug("VectorLogger unavailable: %s", e)
        return None, None


def _try_import_device_info():
    try:
        from sync_monitor import get_device_info
        return get_device_info
    except Exception as e:
        logger.debug("sync_monitor unavailable: %s", e)
        return None


# ---------------------------------------------------------------------------
# Singleton instances (created on first use)
# ---------------------------------------------------------------------------

_router = None
_memory = None
_personality = None
_vector_logger = None
_device_fn = None


def _get_router():
    global _router
    if _router is None:
        cls = _try_import_router()
        if cls is not None:
            _router = cls()
    return _router


def _get_memory():
    global _memory
    if _memory is None:
        cls = _try_import_memory()
        if cls is not None:
            _memory = cls()
    return _memory


def _get_personality():
    global _personality
    if _personality is None:
        cls = _try_import_personality()
        if cls is not None:
            _personality = cls()
    return _personality


def _get_vector_logger():
    global _vector_logger
    if _vector_logger is None:
        VL, _ = _try_import_vector_logger()
        if VL is not None:
            _vector_logger = VL()
    return _vector_logger


def _get_device_info() -> Dict[str, Any]:
    global _device_fn
    if _device_fn is None:
        _device_fn = _try_import_device_info()
    if _device_fn is not None:
        try:
            return _device_fn()
        except Exception:
            pass
    return {"gpu_available": False}


# ---------------------------------------------------------------------------
# Context assembly
# ---------------------------------------------------------------------------

def _build_context(prompt: str, task: str, user_id: Optional[str]) -> str:
    """Assemble a context-enriched prompt from memory and personality."""
    parts: List[str] = []

    # 1. Personality preamble
    personality = _get_personality()
    if personality is not None:
        try:
            profile = personality.load_profile()
            tone = profile.get("tone", "neutral")
            style = profile.get("style", "precise")
            creativity = profile.get("creativity", 0.5)
            parts.append(
                f"[System] Respond in a {tone} tone, {style} style. "
                f"Creativity level: {creativity}."
            )
        except Exception as e:
            logger.debug("Personality context skipped: %s", e)

    # 2. Memory recall
    memory = _get_memory()
    if memory is not None and user_id:
        try:
            recent = memory.recall(user_id)
            if recent:
                history_lines = []
                for entry in recent:
                    if "prompt" in entry:
                        history_lines.append(f"- {entry['prompt']}")
                    elif "decision" in entry:
                        history_lines.append(f"- [decision] {entry['decision']}")
                if history_lines:
                    parts.append(
                        "[Context from recent interactions]\n"
                        + "\n".join(history_lines)
                    )
        except Exception as e:
            logger.debug("Memory recall skipped: %s", e)

    # 3. Task hint
    parts.append(f"[Task: {task}]")

    # 4. User prompt
    parts.append(prompt)

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Response logging
# ---------------------------------------------------------------------------

def _log_interaction(
    prompt: str,
    response: str,
    model_used: str,
    task: str,
    user_id: Optional[str],
    elapsed_ms: float,
):
    """Persist the interaction to vector logger and memory."""
    # Vector logger
    vl = _get_vector_logger()
    if vl is not None:
        try:
            _, VectorLogEntry = _try_import_vector_logger()
            if VectorLogEntry is not None:
                entry = VectorLogEntry(
                    role="user",
                    content=prompt,
                    context=task,
                    model=model_used,
                    tags=[task, f"user:{user_id or 'anon'}"],
                )
                vl.log(entry)

                entry_resp = VectorLogEntry(
                    role="assistant",
                    content=response,
                    context=task,
                    model=model_used,
                    tags=[task, f"elapsed_ms:{elapsed_ms}"],
                )
                vl.log(entry_resp)
        except Exception as e:
            logger.debug("Vector logging failed: %s", e)

    # Memory manager
    memory = _get_memory()
    if memory is not None and user_id:
        try:
            memory.log_interaction(prompt, user_id)
        except Exception as e:
            logger.debug("Memory logging failed: %s", e)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def cognitive_infer(
    prompt: str,
    task: str = "chat",
    user_id: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Main orchestrator entry point.

    Assembles context, routes to the best model, logs the interaction,
    and returns a result dict.

    Returns:
        {
            "response": str,
            "model": str,
            "elapsed_ms": float,
            "task": str,
            "user_id": str | None,
        }
    """
    start = time.perf_counter()

    # 1. Build enriched prompt
    enriched_prompt = _build_context(prompt, task, user_id)

    # 2. Route inference
    router = _get_router()
    if router is not None:
        device_info = _get_device_info()
        result = router.route(
            enriched_prompt,
            task=task,
            device_info=device_info,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        response = result["response"]
        model_used = result["model"]
    else:
        # Ultimate fallback -- no router available at all
        response = f"[Orchestrator-fallback] Router unavailable. Prompt: {prompt[:200]}"
        model_used = "none"

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

    # 3. Log the interaction
    try:
        _log_interaction(prompt, response, model_used, task, user_id, elapsed_ms)
    except Exception as e:
        logger.warning("Post-inference logging failed: %s", e)

    return {
        "response": response,
        "model": model_used,
        "elapsed_ms": elapsed_ms,
        "task": task,
        "user_id": user_id,
    }


async def cognitive_infer_async(
    prompt: str,
    task: str = "chat",
    user_id: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """Async wrapper around cognitive_infer for use in async web frameworks."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: cognitive_infer(prompt, task, user_id, max_tokens, temperature),
    )
