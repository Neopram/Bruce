from .memory_bridge import get_context_for_user
from .actions import execute_action
from .interfaces import deepseek_call
import json

def think(prompt: str, user_id: str):
    context = get_context_for_user(user_id)
    full_prompt = f"Contexto del usuario:\n{context}\n\nSituación:\n{prompt}\n\nRespuesta de Bruce:"
    response = deepseek_call(full_prompt)

    # Intentar deducir acción desde el razonamiento
    try:
        parsed = json.loads(response)
        if "action" in parsed:
            execute_action(parsed["action"], user_id)
    except Exception:
        pass  # En modo texto libre o no estructurado

    return response