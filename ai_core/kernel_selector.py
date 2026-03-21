# ai_core/kernel_selector.py

import os

from ai_core.phi3_kernel import Phi3HyperCore
from ai_core.tinyllama_kernel import TinyLlamaKernel
from ai_core.deepseek_kernel import DeepSeekMiniKernel, DeepSeekBaseKernel

# Puedes definir esto en tu .env o config.yaml
MODEL_NAME = os.getenv("BRUCE_MODEL", "phi3").lower()

def get_active_kernel():
    if MODEL_NAME == "tinyllama":
        print("🧠 Loading TinyLlama Kernel...")
        return TinyLlamaKernel()
    
    elif MODEL_NAME == "deepseek-mini":
        print("🧠 Loading DeepSeek Coder MINI Kernel...")
        return DeepSeekMiniKernel()
    
    elif MODEL_NAME == "deepseek-base":
        print("🧠 Loading DeepSeek Coder BASE Kernel...")
        return DeepSeekBaseKernel()
    
    else:
        print("🧠 Defaulting to Phi3 HyperCore...")
        return Phi3HyperCore()

# Instancia única accesible por el sistema
active_kernel = get_active_kernel()
