import asyncio
from .brain import think

THINK_INTERVAL = 30  # segundos

async def launch_loop():
    print("[🤖 Bruce] Ciclo cognitivo iniciado.")
    while True:
        try:
            # En producción: usar triggers/eventos, no sólo bucle fijo
            prompt = "¿Hay algo que debería analizar o comunicar al usuario?"
            user_id = "auto_bruce"
            response = think(prompt, user_id)
            print("[🧠 Bruce Reflexión]:", response)
        except Exception as e:
            print("[⚠️ Bruce Error]:", e)
        await asyncio.sleep(THINK_INTERVAL)