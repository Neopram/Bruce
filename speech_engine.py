# speech_engine.py

"""
🗣️ Módulo de Síntesis de Voz – Bruce AI
Permite generar audio con distintas voces, configuraciones emocionales y soporte para voz del usuario (Federico).
Compatible con TTS locales (pyttsx3), motores cloud (gTTS, ElevenLabs), y simulaciones internas.
"""

import logging
import os
import uuid
from datetime import datetime

try:
    import pyttsx3  # TTS local
except ImportError:
    pyttsx3 = None

try:
    from gtts import gTTS  # TTS cloud
except ImportError:
    gTTS = None

# Logger
logger = logging.getLogger("Bruce.SpeechEngine")
logger.setLevel(logging.INFO)

# Voces disponibles
AVAILABLE_VOICES = {
    "creator": "Federico",
    "bruce": "Bruce_AI",
    "docu": "Narrator",
    "soft": "Emotional_Tone",
    "alert": "Critical_Alert"
}

VOICE_LANGUAGES = {
    "creator": "en",
    "bruce": "en",
    "docu": "en",
    "soft": "en",
    "alert": "en",
    "es": "es",
    "en": "en",
    "fr": "fr",
    "de": "de",
    "default": "en",
}

TEMP_AUDIO_DIR = "temp/speech"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)


class SpeechEngine:
    def __init__(self, mode="local"):
        self.mode = mode
        if pyttsx3 and self.mode == "local":
            self.engine = pyttsx3.init()
        logger.info(f"[SpeechEngine] Iniciado en modo '{self.mode}'")

    def synthesize_speech(self, text: str, voice: str = "bruce", pitch: float = 1.0, speed: float = 1.0):
        """
        🧠 Método principal para síntesis de voz.
        En modo 'local' usa pyttsx3.
        En modo 'simulate' devuelve texto simulado.
        En modo 'external' usa gTTS y retorna path del archivo MP3.
        """
        voice_label = AVAILABLE_VOICES.get(voice, "Generic")
        timestamp = datetime.utcnow().isoformat()

        # Registro
        log_message = f"[{timestamp}] 🎤 [{voice_label}] {text}"
        logger.info(log_message)

        if self.mode == "simulate":
            return f"[Simulación {voice_label}]: {text}"

        elif self.mode == "local" and pyttsx3:
            self.engine.setProperty('rate', int(200 * speed))
            self.engine.setProperty('volume', 1.0)
            self.engine.say(text)
            self.engine.runAndWait()
            return f"[Local TTS] {voice_label}: {text}"

        elif self.mode == "external" and gTTS:
            try:
                lang = VOICE_LANGUAGES.get(voice, "en")
                filename = f"{uuid.uuid4()}.mp3"
                output_path = os.path.join(TEMP_AUDIO_DIR, filename)
                tts = gTTS(text=text, lang=lang)
                tts.save(output_path)
                logger.info(f"[gTTS] Audio guardado en: {output_path}")
                return output_path
            except Exception as e:
                logger.error(f"[ERROR gTTS] {str(e)}")
                return f"[ERROR] No se pudo sintetizar con gTTS: {str(e)}"

        elif self.mode == "federico":
            return f"[🎙️ Federico Voice Synth] {text}"

        else:
            return f"[Fallback Voice] {text}"

    def list_voices(self):
        return AVAILABLE_VOICES

    def simulate_audio_feedback(self, text: str):
        return f"[🔊 Feedback Simulado] {text}"


# 🔓 Función global accesible para main.py
_speech_engine = SpeechEngine(mode="external")  # puedes cambiar a 'local' o 'simulate' si prefieres
def synthesize_speech(text: str, voice: str = "creator"):
    return _speech_engine.synthesize_speech(text, voice)

# 🎯 Modo CLI para pruebas rápidas
if __name__ == "__main__":
    engine = SpeechEngine(mode="simulate")
    print(engine.synthesize_speech("Hola, Federico. Estoy listo para actuar.", voice="bruce"))
    print(engine.synthesize_speech("Este es un resumen estratégico.", voice="docu"))
    print(engine.synthesize_speech("Activa el modo de alerta máxima.", voice="alert"))
