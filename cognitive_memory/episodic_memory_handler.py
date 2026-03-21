# Ruta: C:\Users\feder\Desktop\OKK_Gorilla_Bot\cognitive_memory\episodic_memory_handler.py

import json
import os
from datetime import datetime
from typing import Dict, List

MEMORY_FILE = "cognitive_memory/episodic_memory.json"
os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)


def load_memory() -> List[Dict]:
    """
    Carga la memoria episódica completa.
    """
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return []


def append_episode(episode_data: Dict):
    """
    Añade un episodio a la memoria episódica.
    """
    memory = load_memory()
    memory.append(episode_data)
    with open(MEMORY_FILE, "w") as file:
        json.dump(memory, file, indent=2)


def summarize_memory(n: int = 10) -> List[Dict]:
    """
    Devuelve resumen de los últimos N episodios.
    """
    memory = load_memory()
    return memory[-n:] if len(memory) >= n else memory


def get_statistics() -> Dict:
    """
    Calcula estadísticas generales sobre la memoria.
    """
    memory = load_memory()
    if not memory:
        return {
            "total_episodes": 0,
            "average_reward": 0,
            "average_loss_signal": 0,
        }
    total_reward = sum(e["reward"] for e in memory)
    total_loss = sum(e["avg_loss_like_signal"] for e in memory)
    return {
        "total_episodes": len(memory),
        "average_reward": round(total_reward / len(memory), 2),
        "average_loss_signal": round(total_loss / len(memory), 4),
    }


if __name__ == "__main__":
    print("Últimos 5 episodios:")
    for e in summarize_memory(5):
        print(e)

    print("\nEstadísticas acumuladas:")
    print(get_statistics())
