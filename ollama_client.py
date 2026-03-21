"""Ollama LLM client for Bruce AI.

Provides a simple interface to Ollama for local LLM inference.
Supports Mistral 7B as primary model with fallbacks.
"""

import logging
import time
from typing import Optional

import requests

logger = logging.getLogger("Bruce.Ollama")

OLLAMA_BASE_URL = "http://localhost:11434"


class OllamaClient:
    """Client for Ollama local LLM inference."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = "mistral:7b-instruct-v0.3-q4_K_M"):
        self.base_url = base_url
        self.model = model
        self._available = None

    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            self._available = r.status_code == 200
            return self._available
        except Exception:
            self._available = False
            return False

    def list_models(self) -> list:
        """List available models in Ollama."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return []

    def has_model(self, model_name: str = None) -> bool:
        """Check if a specific model is pulled."""
        models = self.list_models()
        name = model_name or self.model
        return any(name in m for m in models)

    def generate(
        self,
        prompt: str,
        system: str = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> str:
        """Generate a response from the model."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system

        try:
            start = time.time()
            r = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120,
            )
            elapsed = time.time() - start

            if r.status_code == 200:
                data = r.json()
                response = data.get("response", "").strip()
                tokens = data.get("eval_count", 0)
                logger.info(
                    f"Ollama [{self.model}] {tokens} tokens in {elapsed:.1f}s "
                    f"({tokens/elapsed:.0f} tok/s)" if elapsed > 0 else ""
                )
                return response
            else:
                logger.error(f"Ollama error {r.status_code}: {r.text[:200]}")
                return f"[Ollama error] {r.status_code}"
        except requests.Timeout:
            logger.error("Ollama request timed out (120s)")
            return "[Ollama timeout] Request took too long"
        except requests.ConnectionError:
            logger.error("Ollama not running on localhost:11434")
            return "[Ollama offline] Server not available"
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"[Ollama error] {e}"

    def chat(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Chat-style inference with message history."""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            start = time.time()
            r = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120,
            )
            elapsed = time.time() - start

            if r.status_code == 200:
                data = r.json()
                response = data.get("message", {}).get("content", "").strip()
                tokens = data.get("eval_count", 0)
                logger.info(f"Ollama chat [{self.model}] {elapsed:.1f}s")
                return response
            else:
                logger.error(f"Ollama chat error {r.status_code}")
                return f"[Ollama error] {r.status_code}"
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            return f"[Ollama error] {e}"

    def pull_model(self, model_name: str = None) -> bool:
        """Pull a model from Ollama registry."""
        name = model_name or self.model
        logger.info(f"Pulling model {name}...")
        try:
            r = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": name, "stream": False},
                timeout=1800,  # 30 min for large models
            )
            return r.status_code == 200
        except Exception as e:
            logger.error(f"Failed to pull {name}: {e}")
            return False


# Singleton instance
_client = None


def get_ollama() -> OllamaClient:
    """Get the global Ollama client instance."""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
