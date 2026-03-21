from typing import List, Dict
import random

# Estrategias disponibles (mock inicial)
STRATEGIES = {
    "mean_reversion": {
        "description": "Compra en caídas, vende en recuperaciones",
        "risk_level": "medio",
        "type": "técnica"
    },
    "breakout": {
        "description": "Aprovecha rupturas de niveles clave",
        "risk_level": "alto",
        "type": "momentum"
    },
    "ppo_rl": {
        "description": "Aprendizaje por refuerzo PPO optimizado",
        "risk_level": "adaptativo",
        "type": "inteligencia artificial"
    }
}

def list_strategies() -> List[Dict]:
    return [{"name": name, **details} for name, details in STRATEGIES.items()]

def select_strategy(market_volatility: float, user_profile: str) -> Dict:
    if market_volatility > 0.6:
        return STRATEGIES["breakout"]
    elif user_profile == "conservador":
        return STRATEGIES["mean_reversion"]
    return STRATEGIES[random.choice(list(STRATEGIES.keys()))]