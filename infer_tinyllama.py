"""TinyLlama inference engine for Bruce AI.

Handles loading and running the TinyLlama-1.1B model for fast, lightweight
responses -- ideal for quick queries, status checks, and low-latency tasks
where speed matters more than depth.
"""

import logging
import torch
from typing import Optional
from config.settings import get_settings

logger = logging.getLogger("Bruce.Inference.TinyLlama")


class TinyLLaMAInference:
    """TinyLlama-1.1B inference engine optimized for speed."""

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
        """Lazy load the TinyLlama model. Returns True if successful."""
        if self._loaded:
            return True

        settings = get_settings()
        model_path = settings.tinyllama_model_path
        self._device = self._detect_device()

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(
                f"Loading TinyLlama model from {model_path} on {self._device}"
            )

            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path, trust_remote_code=True
            )

            # TinyLlama is small enough to load in float32 on CPU without issue
            dtype = torch.float16 if self._device != "cpu" else torch.float32

            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                trust_remote_code=True,
                torch_dtype=dtype,
                device_map="auto" if self._device == "cuda" else None,
            )

            if self._device != "cuda":
                self._model = self._model.to(self._device)

            self._model.eval()
            self._loaded = True
            logger.info("TinyLlama model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load TinyLlama model: {e}")
            self._loaded = False
            return False

    def run(
        self, prompt: str, max_tokens: int = 256, temperature: float = 0.6
    ) -> str:
        """Run inference on the given prompt.

        Defaults to lower max_tokens (256) and temperature (0.6) for fast,
        focused responses.
        """
        if not self._loaded and not self.load():
            return f"[TinyLlama-fallback] Model not available. Prompt: {prompt[:100]}"

        try:
            inputs = self._tokenizer(
                prompt, return_tensors="pt", truncation=True, max_length=2048
            )
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    do_sample=temperature > 0,
                    temperature=temperature if temperature > 0 else 1.0,
                    top_p=0.9,
                    top_k=50,
                    repetition_penalty=1.15,
                    pad_token_id=self._tokenizer.eos_token_id,
                )

            input_length = inputs["input_ids"].shape[1]
            generated = outputs[0][input_length:]
            response = self._tokenizer.decode(generated, skip_special_tokens=True)
            return response.strip()
        except Exception as e:
            logger.error(f"TinyLlama inference error: {e}")
            return f"[TinyLlama-error] Inference failed: {e}"

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
            logger.info("TinyLlama model unloaded")
