
# archetypes.py
"""
Arquetipos Cognitivos de Trader
Permite cambiar el estilo de decisión y riesgo de DeepSeek dinámicamente
"""

ARCHETYPES = {
    "warren_buffett": {
        "estilo": "value",
        "riesgo": "bajo",
        "duracion": "larga",
        "preferencia": "fundamentales",
    },
    "scalper_ninja": {
        "estilo": "scalping",
        "riesgo": "alto",
        "duracion": "segundos-minutos",
        "preferencia": "técnica pura",
    },
    "wall_street_wolf": {
        "estilo": "agresivo",
        "riesgo": "alto",
        "duracion": "media",
        "preferencia": "momentum + noticias",
    },
    "sociotrader": {
        "estilo": "sentimiento social",
        "riesgo": "medio",
        "duracion": "variable",
        "preferencia": "datos de redes",
    }
}

def get_arquetipo(nombre: str) -> dict:
    return ARCHETYPES.get(nombre.lower(), {"error": "Arquetipo no reconocido"})
