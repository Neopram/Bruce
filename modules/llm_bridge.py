"""
Unified LLM interface module.
Routes requests to local models or external APIs (OpenAI, Anthropic, DeepSeek),
provides a unified response format, retry logic, and provider management.
"""
import requests
import time
from datetime import datetime


class LLMBridge:
    """Unified interface for communicating with multiple LLM providers."""

    PROVIDERS = {
        "openai": {
            "default_endpoint": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4",
            "format": "chat",
        },
        "anthropic": {
            "default_endpoint": "https://api.anthropic.com/v1/messages",
            "model": "claude-3-sonnet-20240229",
            "format": "messages",
        },
        "deepseek": {
            "default_endpoint": "https://api.deepseek.com/v1/chat/completions",
            "model": "deepseek-chat",
            "format": "chat",
        },
        "local": {
            "default_endpoint": "http://localhost:11434/api/generate",
            "model": "llama3",
            "format": "ollama",
        },
    }

    def __init__(self, endpoint=None, api_key=None, provider="openai"):
        self.provider = provider
        self.api_key = api_key
        provider_config = self.PROVIDERS.get(provider, self.PROVIDERS["openai"])
        self.endpoint = endpoint or provider_config["default_endpoint"]
        self.model = provider_config["model"]
        self.format = provider_config["format"]
        self.max_retries = 3
        self.timeout = 30
        self.request_log = []

    def query(self, prompt, max_tokens=150, temperature=0.7, system_prompt=None):
        """Send a query to the configured LLM provider."""
        payload = self._build_payload(prompt, max_tokens, temperature, system_prompt)
        headers = self._build_headers()

        for attempt in range(self.max_retries):
            try:
                start = time.time()
                response = requests.post(
                    self.endpoint, headers=headers, json=payload, timeout=self.timeout
                )
                latency = time.time() - start
                response.raise_for_status()
                result = self._parse_response(response.json())

                self.request_log.append({
                    "provider": self.provider,
                    "model": self.model,
                    "prompt_length": len(prompt),
                    "response_length": len(result),
                    "latency_s": round(latency, 3),
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat(),
                })
                return result

            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return self._error_response("Request timed out after retries")
            except requests.exceptions.HTTPError as e:
                status_code = e.response.status_code if e.response else 0
                if status_code == 429 and attempt < self.max_retries - 1:
                    time.sleep(2 ** (attempt + 1))
                    continue
                return self._error_response(f"HTTP {status_code}: {str(e)}")
            except Exception as e:
                return self._error_response(str(e))

    def _build_payload(self, prompt, max_tokens, temperature, system_prompt=None):
        """Build provider-specific request payload."""
        if self.format == "chat":
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
        elif self.format == "messages":
            payload = {
                "model": self.model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system_prompt:
                payload["system"] = system_prompt
            return payload
        elif self.format == "ollama":
            return {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": temperature},
            }
        return {"prompt": prompt, "max_tokens": max_tokens}

    def _build_headers(self):
        """Build provider-specific headers."""
        headers = {"Content-Type": "application/json"}
        if self.provider == "anthropic":
            headers["x-api-key"] = self.api_key or ""
            headers["anthropic-version"] = "2023-06-01"
        elif self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _parse_response(self, data):
        """Parse provider-specific response into unified format."""
        if self.format == "chat":
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
            return data.get("choices", [{}])[0].get("text", "").strip()
        elif self.format == "messages":
            content = data.get("content", [])
            if content:
                return content[0].get("text", "").strip()
            return ""
        elif self.format == "ollama":
            return data.get("response", "").strip()
        return str(data)

    def _error_response(self, message):
        """Create a standardized error response."""
        self.request_log.append({
            "provider": self.provider,
            "model": self.model,
            "status": "error",
            "error": message,
            "timestamp": datetime.utcnow().isoformat(),
        })
        return f"LLM error: {message}"

    def switch_provider(self, provider, api_key=None, endpoint=None):
        """Switch to a different LLM provider."""
        if provider not in self.PROVIDERS:
            return {"status": "error", "message": f"Unknown provider: {provider}"}
        config = self.PROVIDERS[provider]
        self.provider = provider
        self.endpoint = endpoint or config["default_endpoint"]
        self.model = config["model"]
        self.format = config["format"]
        if api_key:
            self.api_key = api_key
        return {"status": "switched", "provider": provider, "model": self.model}

    def set_model(self, model_name):
        """Override the model name for the current provider."""
        self.model = model_name
        return {"model": self.model, "provider": self.provider}

    def get_request_log(self, limit=20):
        """Return recent request history."""
        return self.request_log[-limit:]

    def get_status(self):
        """Return current bridge configuration."""
        return {
            "provider": self.provider,
            "model": self.model,
            "endpoint": self.endpoint,
            "format": self.format,
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "total_requests": len(self.request_log),
        }
