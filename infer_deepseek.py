"""DeepSeek inference engine for Bruce AI.

Handles loading and running the DeepSeek-coder-1.3b model for code generation,
technical analysis, and complex reasoning tasks.
"""

import logging
import torch
from typing import Optional
from config.settings import get_settings

logger = logging.getLogger("Bruce.Inference.DeepSeek")


class DeepSeekInference:
    """DeepSeek model inference engine with lazy loading and GPU support."""

    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._device = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def _detect_device(self) -> str:
        if torch.cuda.is_available():
            return "cuda"
        try:
            if torch.backends.mps.is_available():
                return "mps"
        except AttributeError:
            pass
        return "cpu"

    def load(self) -> bool:
        """Lazy load the DeepSeek model. Returns True if successful."""
        if self._loaded:
            return True

        settings = get_settings()
        model_path = settings.deepseek_model_path
        self._device = self._detect_device()

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(f"Loading DeepSeek model from {model_path} on {self._device}")
            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path, trust_remote_code=True
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=torch.float16 if self._device != "cpu" else torch.float32,
                device_map="auto" if self._device == "cuda" else None,
            )
            if self._device != "cuda":
                self._model = self._model.to(self._device)
            self._model.eval()
            self._loaded = True
            logger.info("DeepSeek model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load DeepSeek model: {e}")
            self._loaded = False
            return False

    def run(self, prompt: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Run inference on the given prompt."""
        if not self._loaded and not self.load():
            return f"[DeepSeek-fallback] Model not available. Prompt: {prompt[:100]}"

        try:
            inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    do_sample=temperature > 0,
                    temperature=temperature if temperature > 0 else 1.0,
                    top_p=0.95,
                    repetition_penalty=1.1,
                    pad_token_id=self._tokenizer.eos_token_id,
                )

            input_length = inputs["input_ids"].shape[1]
            generated = outputs[0][input_length:]
            response = self._tokenizer.decode(generated, skip_special_tokens=True)
            return response.strip()
        except Exception as e:
            logger.error(f"DeepSeek inference error: {e}")
            return f"[DeepSeek-error] Inference failed: {e}"

    def unload(self):
        """Free model from memory."""
        if self._model is not None:
            del self._model
            del self._tokenizer
            self._model = None
            self._tokenizer = None
            self._loaded = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("DeepSeek model unloaded")
