import requests
import os

DEEPSEEK_URL = os.getenv("DEEPSEEK_URL", "http://localhost:11434/api/generate")

def deepseek_call(prompt: str, system: str = "", temperature: float = 0.75, mode="socratic"):
    payload = {
        "model": "deepseek-coder",
        "prompt": prompt,
        "system": system,
        "temperature": temperature,
        "mode": mode,
        "max_tokens": 2048,
    }
    res = requests.post(DEEPSEEK_URL, json=payload)
    res.raise_for_status()
    return res.json().get("response", "")