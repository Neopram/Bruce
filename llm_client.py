"""
Bruce AI — Unified LLM Client

Tries multiple LLM backends in order:
1. Ollama (local, free, private)
2. OpenAI API (best quality)
3. Anthropic API (alternative)
4. Rule-based fallback (always available)

Bruce always has a brain — the quality depends on what's available.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger("Bruce.LLM")

BRAIN_CONFIG = Path("data/brain_config.json")


class UnifiedLLMClient:
    """Unified client that tries all available LLM backends."""

    def __init__(self):
        self.provider = "none"
        self.model = "none"
        self._detect_backend()

    def _detect_backend(self):
        """Auto-detect the best available LLM backend."""
        # 1. Check Ollama
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            if r.status_code == 200:
                models = [m["name"] for m in r.json().get("models", [])]
                if models:
                    # Prefer best reasoning models first
                    for preferred in ["qwen2.5", "deepseek-r1", "qwen", "mistral", "deepseek", "llama", "gemma", "phi"]:
                        match = next((m for m in models if preferred in m), None)
                        if match:
                            self.provider = "ollama"
                            self.model = match
                            logger.info(f"LLM: Ollama/{self.model}")
                            return
                    self.provider = "ollama"
                    self.model = models[0]
                    logger.info(f"LLM: Ollama/{self.model}")
                    return
        except Exception:
            pass

        # 2. Check OpenAI
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if openai_key and openai_key.startswith("sk-"):
            self.provider = "openai"
            self.model = "gpt-4o-mini"
            logger.info(f"LLM: OpenAI/{self.model}")
            return

        # 3. Check Anthropic
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if anthropic_key and anthropic_key.startswith("sk-ant-"):
            self.provider = "anthropic"
            self.model = "claude-3-5-sonnet-20241022"
            logger.info(f"LLM: Anthropic/{self.model}")
            return

        # 4. Check brain config file
        if BRAIN_CONFIG.exists():
            try:
                config = json.loads(BRAIN_CONFIG.read_text(encoding="utf-8"))
                if config.get("status") == "ready":
                    self.provider = config.get("provider", "none")
                    self.model = config.get("model", "none")
                    logger.info(f"LLM: {self.provider}/{self.model} (from config)")
                    return
            except Exception:
                pass

        logger.warning("No LLM backend available. Bruce will use rule-based responses.")

    def is_available(self) -> bool:
        return self.provider != "none"

    def generate(self, prompt: str, system: str = None,
                 temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Generate a response using the best available backend."""
        if self.provider == "ollama":
            return self._ollama_generate(prompt, system, temperature, max_tokens)
        elif self.provider == "openai":
            return self._openai_generate(prompt, system, temperature, max_tokens)
        elif self.provider == "anthropic":
            return self._anthropic_generate(prompt, system, temperature, max_tokens)
        else:
            return None

    def chat(self, messages: list, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """Chat with message history."""
        if self.provider == "ollama":
            return self._ollama_chat(messages, temperature, max_tokens)
        elif self.provider == "openai":
            return self._openai_chat(messages, temperature, max_tokens)
        elif self.provider == "anthropic":
            return self._anthropic_chat(messages, temperature, max_tokens)
        else:
            return None

    # === Ollama ===

    def _ollama_generate(self, prompt, system, temperature, max_tokens):
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
            if system:
                payload["system"] = system
            r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
            if r.status_code == 200:
                return r.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama error: {e}")
        return None

    def _ollama_chat(self, messages, temperature, max_tokens):
        try:
            r = requests.post("http://localhost:11434/api/chat", json={
                "model": self.model, "messages": messages, "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }, timeout=120)
            if r.status_code == 200:
                return r.json().get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
        return None

    # === OpenAI ===

    def _openai_generate(self, prompt, system, temperature, max_tokens):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self._openai_chat(messages, temperature, max_tokens)

    def _openai_chat(self, messages, temperature, max_tokens):
        try:
            key = os.environ.get("OPENAI_API_KEY", "")
            r = requests.post("https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": self.model, "messages": messages,
                      "temperature": temperature, "max_tokens": max_tokens},
                timeout=60)
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"].strip()
            else:
                logger.error(f"OpenAI error {r.status_code}: {r.text[:200]}")
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
        return None

    # === Anthropic ===

    def _anthropic_generate(self, prompt, system, temperature, max_tokens):
        messages = [{"role": "user", "content": prompt}]
        return self._anthropic_chat(messages, temperature, max_tokens, system)

    def _anthropic_chat(self, messages, temperature, max_tokens, system=None):
        try:
            key = os.environ.get("ANTHROPIC_API_KEY", "")
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if system:
                payload["system"] = system
            r = requests.post("https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload, timeout=60)
            if r.status_code == 200:
                content = r.json().get("content", [])
                if content:
                    return content[0].get("text", "").strip()
            else:
                logger.error(f"Anthropic error {r.status_code}: {r.text[:200]}")
        except Exception as e:
            logger.error(f"Anthropic error: {e}")
        return None

    def get_info(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "available": self.is_available(),
        }


# Singleton
_client = None


def get_llm() -> UnifiedLLMClient:
    """Get the global unified LLM client."""
    global _client
    if _client is None:
        _client = UnifiedLLMClient()
    return _client
