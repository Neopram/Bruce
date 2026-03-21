from .emotion_state import EmotionState

# Instancia única del estado emocional
emotion = EmotionState()

def generate_emotional_response(base_response: str) -> str:
    mood = emotion.get_emotion()["mood"]
    tone_prefix = {
        "estresado": "😟 Te digo esto con preocupación: ",
        "relajado": "😌 Con calma te digo: ",
        "eufórico": "🚀 ¡Esto es emocionante!: ",
        "triste": "😢 Honestamente... ",
        "curioso": "🤔 Interesante... ",
        "enfocado": "🎯 Con claridad: "
    }
    prefix = tone_prefix.get(mood, "")
    return f"{prefix}{base_response}"