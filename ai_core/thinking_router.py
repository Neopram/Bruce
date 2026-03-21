# ai_core/thinking_router.py

import os
from ai_core.phi3_kernel import Phi3HyperCore
from ai_core.deepseek_kernel import DeepSeekKernel
from ai_core.tinyllama_kernel import TinyLlamaKernel

class ThinkingRouter:
    def __init__(self):
        # Instancias precargadas
        self.models = {
            "phi3": Phi3HyperCore(),
            "tinyllama": TinyLlamaKernel(),
            "deepseek": DeepSeekKernel()
        }
        self.model_selector_path = "./models/active_model.txt"

    def _get_active_model(self) -> str:
        try:
            with open(self.model_selector_path, "r", encoding="utf-8") as f:
                model = f.read().strip().lower()
                if model in self.models:
                    return model
        except:
            pass
        return "phi3"  # Default fallback

    def _set_active_model(self, model_name: str):
        if model_name in self.models:
            with open(self.model_selector_path, "w", encoding="utf-8") as f:
                f.write(model_name)
            return f"✅ Active model changed to: {model_name}"
        return f"⚠️ Invalid model: {model_name}"

    def route(self, prompt: str) -> str:
        # Comandos de cambio dinámico
        prompt_lower = prompt.lower()
        if "cambia a deepseek" in prompt_lower:
            return self._set_active_model("deepseek")
        if "cambia a tinyllama" in prompt_lower:
            return self._set_active_model("tinyllama")
        if "cambia a phi3" in prompt_lower or "cambia a bruce" in prompt_lower:
            return self._set_active_model("phi3")

        active_model = self._get_active_model()
        model = self.models[active_model]
        
        # Compatibilidad entre modelos con `infer` o `hyper_run`
        if hasattr(model, "hyper_run"):
            return asyncio.run(model.hyper_run(prompt))
        elif hasattr(model, "infer"):
            return model.infer(prompt)
        elif hasattr(model, "run"):
            return asyncio.run(model.run(prompt))
        else:
            return f"❌ Modelo activo '{active_model}' no tiene método de ejecución válido."
