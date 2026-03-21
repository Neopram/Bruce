import random

def detect_emotion_from_voice(audio_bytes: bytes) -> dict:
    # TODO: analizar prosodia real, tono, ritmo, etc.
    return {
        "mood": random.choice(["estresado", "relajado", "curioso"]),
        "valence": round(random.uniform(-1, 1), 2),
        "arousal": round(random.uniform(0, 1), 2),
    }

def detect_emotion_from_text(text: str) -> dict:
    # TODO: usar modelo NLP para clasificación emocional real
    keywords = {
        "estresado": -0.8,
        "feliz": 0.8,
        "cansado": -0.5,
        "tranquilo": 0.2,
        "ansioso": -0.7
    }
    valence = sum(v for k, v in keywords.items() if k in text.lower())
    return {
        "mood": "estresado" if valence < -0.6 else "relajado" if valence > 0.4 else "curioso",
        "valence": max(-1, min(1, valence)),
        "arousal": 0.5  # Default temporal
    }

def detect_emotion_from_image(image_bytes: bytes) -> dict:
    # TODO: integración con visión computacional para microexpresiones
    return {
        "mood": random.choice(["feliz", "triste", "enfocado"]),
        "valence": round(random.uniform(-1, 1), 2),
        "arousal": round(random.uniform(0, 1), 2)
    }