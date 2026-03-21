"""Phi-3 inference engine for Bruce AI.

Handles loading and running the Phi-3-mini-4k-instruct model for chat,
summarization, report generation, and general conversational tasks.
Supports chat-template formatting and optional INT8 quantization.
"""

import logging
import torch
from typing import Dict, List, Optional
from config.settings import get_settings

logger = logging.getLogger("Bruce.Inference.Phi3")


class Phi3Inference:
    """Phi-3-mini-4k-instruct inference engine with chat template support."""

    def __init__(self, quantize_int8: bool = False):
        self._model = None
        self._tokenizer = None
        self._device = None
        self._loaded = False
        self._quantize_int8 = quantize_int8

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
        """Lazy load the Phi-3 model. Returns True if successful."""
        if self._loaded:
            return True

        settings = get_settings()
        model_path = settings.phi3_model_path
        self._device = self._detect_device()

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info(f"Loading Phi-3 model from {model_path} on {self._device}")

            self._tokenizer = AutoTokenizer.from_pretrained(
                model_path, trust_remote_code=True
            )

            load_kwargs = {
                "trust_remote_code": True,
            }

            # INT8 quantization requires bitsandbytes and CUDA
            if self._quantize_int8 and self._device == "cuda":
                try:
                    from transformers import BitsAndBytesConfig

                    quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                    load_kwargs["quantization_config"] = quantization_config
                    load_kwargs["device_map"] = "auto"
                    logger.info("Using INT8 quantization for Phi-3")
                except ImportError:
                    logger.warning(
                        "bitsandbytes not available, falling back to float16"
                    )
                    load_kwargs["torch_dtype"] = torch.float16
                    load_kwargs["device_map"] = "auto"
            elif self._device == "cuda":
                load_kwargs["torch_dtype"] = torch.float16
                load_kwargs["device_map"] = "auto"
            else:
                load_kwargs["torch_dtype"] = torch.float32

            self._model = AutoModelForCausalLM.from_pretrained(
                model_path, **load_kwargs
            )

            if self._device != "cuda":
                self._model = self._model.to(self._device)

            self._model.eval()
            self._loaded = True
            logger.info("Phi-3 model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load Phi-3 model: {e}")
            self._loaded = False
            return False

    def _format_chat_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Format messages into Phi-3 chat template.

        Phi-3 uses: <|system|>\\n{system}<|end|>\\n<|user|>\\n{user}<|end|>\\n<|assistant|>\\n
        """
        formatted = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                formatted += f"<|system|>\n{content}<|end|>\n"
            elif role == "user":
                formatted += f"<|user|>\n{content}<|end|>\n"
            elif role == "assistant":
                formatted += f"<|assistant|>\n{content}<|end|>\n"
        # Prompt the assistant to generate
        formatted += "<|assistant|>\n"
        return formatted

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        """Run chat inference with a list of messages [{role, content}].

        Args:
            messages: List of dicts with 'role' and 'content' keys.
            max_tokens: Maximum number of new tokens to generate.
            temperature: Sampling temperature (0 for greedy).

        Returns:
            Generated assistant response text.
        """
        if not self._loaded and not self.load():
            user_msg = next(
                (m["content"] for m in reversed(messages) if m["role"] == "user"),
                "N/A",
            )
            return f"[Phi3-fallback] Model not available. Last user message: {user_msg[:100]}"

        try:
            # Try using the tokenizer's built-in chat template first
            try:
                prompt = self._tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            except Exception:
                prompt = self._format_chat_prompt(messages)

            return self._generate(prompt, max_tokens, temperature)
        except Exception as e:
            logger.error(f"Phi-3 chat inference error: {e}")
            return f"[Phi3-error] Chat inference failed: {e}"

    def run(
        self, prompt: str, max_tokens: int = 512, temperature: float = 0.7
    ) -> str:
        """Run raw prompt inference (non-chat mode)."""
        if not self._loaded and not self.load():
            return f"[Phi3-fallback] Model not available. Prompt: {prompt[:100]}"

        try:
            return self._generate(prompt, max_tokens, temperature)
        except Exception as e:
            logger.error(f"Phi-3 inference error: {e}")
            return f"[Phi3-error] Inference failed: {e}"

    def _generate(
        self, prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """Core generation logic shared by run() and chat()."""
        inputs = self._tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=4096
        )
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=temperature > 0,
                temperature=temperature if temperature > 0 else 1.0,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self._tokenizer.eos_token_id,
            )

        input_length = inputs["input_ids"].shape[1]
        generated = outputs[0][input_length:]
        response = self._tokenizer.decode(generated, skip_special_tokens=True)

        # Strip any trailing end-of-turn tokens that leaked through
        for stop_token in ["<|end|>", "<|endoftext|>"]:
            if stop_token in response:
                response = response[: response.index(stop_token)]

        return response.strip()

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
            logger.info("Phi-3 model unloaded")
