#!/usr/bin/env python3
"""
Bruce AI — Voice Engine

Text-to-Speech (TTS) and Speech-to-Text (STT) capabilities.
Provides voice chat mode where Bruce speaks and listens.

Dependencies:
  pip install pyttsx3 SpeechRecognition pyaudio

  If pyaudio fails on Windows:
    pip install pipwin && pipwin install pyaudio

  STT is optional — TTS works without a microphone.
"""

import os
import sys
import time
import threading
import logging
from typing import Optional, Callable, List, Dict, Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Availability flags — graceful degradation if libraries are missing
# ---------------------------------------------------------------------------

TTS_AVAILABLE = False
STT_AVAILABLE = False
PYAUDIO_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None

try:
    import speech_recognition as sr
    STT_AVAILABLE = True
except ImportError:
    sr = None

try:
    import pyaudio  # noqa: F401
    PYAUDIO_AVAILABLE = True
except ImportError:
    pass


def voice_status() -> Dict[str, Any]:
    """Return a dict describing which voice features are available."""
    return {
        "tts_available": TTS_AVAILABLE,
        "stt_available": STT_AVAILABLE,
        "pyaudio_available": PYAUDIO_AVAILABLE,
        "missing": _missing_packages(),
    }


def _missing_packages() -> List[str]:
    missing = []
    if not TTS_AVAILABLE:
        missing.append("pyttsx3  (pip install pyttsx3)")
    if not STT_AVAILABLE:
        missing.append("SpeechRecognition  (pip install SpeechRecognition)")
    if not PYAUDIO_AVAILABLE:
        missing.append("PyAudio  (pip install pyaudio — or: pip install pipwin && pipwin install pyaudio)")
    return missing


# ===================================================================
# Text-to-Speech Engine
# ===================================================================

class TextToSpeech:
    """Offline TTS powered by pyttsx3 (uses SAPI5 on Windows, espeak on Linux)."""

    def __init__(self):
        if not TTS_AVAILABLE:
            raise RuntimeError(
                "pyttsx3 is not installed. Install it with:  pip install pyttsx3"
            )
        self._engine = pyttsx3.init()
        self._lock = threading.Lock()
        self._speaking = False

    # -- Core methods --------------------------------------------------

    def speak(self, text: str) -> None:
        """Speak *text* aloud (blocking until finished)."""
        with self._lock:
            self._speaking = True
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            finally:
                self._speaking = False

    def speak_async(self, text: str) -> threading.Thread:
        """Speak *text* in a background thread. Returns the Thread object."""
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()
        return t

    def stop(self) -> None:
        """Stop any speech currently in progress."""
        try:
            self._engine.stop()
        except Exception:
            pass
        self._speaking = False

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    # -- Voice configuration -------------------------------------------

    def list_voices(self) -> List[Dict[str, str]]:
        """Return a list of available system voices."""
        voices = self._engine.getProperty("voices") or []
        result = []
        for v in voices:
            result.append({
                "id": v.id,
                "name": v.name,
                "languages": getattr(v, "languages", []),
                "gender": getattr(v, "gender", "unknown"),
            })
        return result

    def set_voice(self, voice_id: str) -> None:
        """Set the active voice by its ID (use list_voices() to discover IDs)."""
        self._engine.setProperty("voice", voice_id)

    def set_rate(self, rate: int = 175) -> None:
        """Set speech rate in words-per-minute (default ~175)."""
        self._engine.setProperty("rate", rate)

    def get_rate(self) -> int:
        return self._engine.getProperty("rate")

    def set_volume(self, volume: float = 1.0) -> None:
        """Set volume from 0.0 (silent) to 1.0 (max)."""
        self._engine.setProperty("volume", max(0.0, min(1.0, volume)))

    def get_volume(self) -> float:
        return self._engine.getProperty("volume")

    def save_to_file(self, text: str, filename: str) -> str:
        """Save spoken text to a WAV file. Returns the absolute path."""
        abs_path = os.path.abspath(filename)
        with self._lock:
            self._engine.save_to_file(text, abs_path)
            self._engine.runAndWait()
        return abs_path


# ===================================================================
# Speech-to-Text Engine
# ===================================================================

class SpeechToText:
    """
    STT using the SpeechRecognition library.

    Backends:
      - Google Speech Recognition (free, online, default)
      - CMU Sphinx (offline, needs pocketsphinx installed)
    """

    BACKEND_GOOGLE = "google"
    BACKEND_SPHINX = "sphinx"

    def __init__(self, backend: str = BACKEND_GOOGLE, language: str = "en-US"):
        if not STT_AVAILABLE:
            raise RuntimeError(
                "SpeechRecognition is not installed. Install it with:  pip install SpeechRecognition"
            )
        if not PYAUDIO_AVAILABLE:
            raise RuntimeError(
                "PyAudio is not installed (required for microphone input).\n"
                "Install with:  pip install pyaudio\n"
                "On Windows if that fails:  pip install pipwin && pipwin install pyaudio"
            )
        self._recognizer = sr.Recognizer()
        self._microphone = sr.Microphone()
        self._backend = backend
        self._language = language
        self._listening = False
        self._stop_continuous = threading.Event()

        # Calibrate for ambient noise once
        try:
            with self._microphone as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
        except Exception as e:
            logger.warning("Could not calibrate microphone: %s", e)

    # -- Configuration -------------------------------------------------

    def set_language(self, lang: str) -> None:
        """Set recognition language (e.g. 'en-US', 'es-ES')."""
        self._language = lang

    def set_backend(self, backend: str) -> None:
        """Switch backend: 'google' (online) or 'sphinx' (offline)."""
        if backend not in (self.BACKEND_GOOGLE, self.BACKEND_SPHINX):
            raise ValueError(f"Unknown backend '{backend}'. Use 'google' or 'sphinx'.")
        self._backend = backend

    # -- Listening -----------------------------------------------------

    def listen(self, timeout: float = 10.0, phrase_limit: float = 30.0) -> Optional[str]:
        """
        Listen for a single utterance from the microphone.

        Returns recognised text, or None on failure / silence.
        """
        self._listening = True
        try:
            with self._microphone as source:
                audio = self._recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
            return self._recognise(audio)
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            logger.warning("Listen error: %s", e)
            return None
        finally:
            self._listening = False

    def listen_continuous(self, callback: Callable[[str], None],
                          stop_event: Optional[threading.Event] = None) -> None:
        """
        Listen continuously, calling *callback(text)* for each recognised phrase.

        Blocks until *stop_event* is set or KeyboardInterrupt.
        """
        stop = stop_event or self._stop_continuous
        stop.clear()
        self._listening = True
        try:
            while not stop.is_set():
                text = self.listen(timeout=5.0)
                if text:
                    callback(text)
        except KeyboardInterrupt:
            pass
        finally:
            self._listening = False

    def stop_listening(self) -> None:
        """Signal continuous listening to stop."""
        self._stop_continuous.set()

    @property
    def is_listening(self) -> bool:
        return self._listening

    # -- Internal recognition ------------------------------------------

    def _recognise(self, audio) -> Optional[str]:
        """Run recognition on captured audio using the configured backend."""
        try:
            if self._backend == self.BACKEND_GOOGLE:
                return self._recognizer.recognize_google(audio, language=self._language)
            elif self._backend == self.BACKEND_SPHINX:
                return self._recognizer.recognize_sphinx(audio, language=self._language)
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger.warning("Recognition service error (%s): %s", self._backend, e)
            return None
        return None


# ===================================================================
# Voice Chat — combines TTS + STT for conversational interaction
# ===================================================================

class VoiceChat:
    """
    Interactive voice conversation with Bruce AI.

    Flow:
      1. Bruce greets the user with TTS.
      2. Listens for speech (STT).
      3. If the wake-word "Bruce" is detected, processes the command.
      4. Bruce responds via TTS.
      5. Loop until "stop" or "exit" is spoken.
    """

    WAKE_WORD = "bruce"
    EXIT_WORDS = {"stop", "exit", "quit", "goodbye", "bye"}

    def __init__(self, bruce_agent=None, tts: Optional[TextToSpeech] = None,
                 stt: Optional[SpeechToText] = None, require_wake_word: bool = False):
        """
        Parameters
        ----------
        bruce_agent : optional
            A Bruce agent instance with a .chat(text) method.
            If None, voice chat will echo back what it hears (demo mode).
        tts : TextToSpeech, optional
            Pre-configured TTS instance.  Created automatically if omitted.
        stt : SpeechToText, optional
            Pre-configured STT instance.  Created automatically if omitted.
        require_wake_word : bool
            If True, only process speech that starts with the wake word "Bruce".
            If False (default), process all speech immediately.
        """
        self.bruce = bruce_agent
        self.require_wake_word = require_wake_word
        self._running = False
        self._stop_event = threading.Event()

        # TTS — required
        if tts is not None:
            self.tts = tts
        else:
            if not TTS_AVAILABLE:
                raise RuntimeError(
                    "Cannot start voice chat: pyttsx3 is not installed.\n"
                    "Install with:  pip install pyttsx3"
                )
            self.tts = TextToSpeech()

        # STT — required for voice input
        if stt is not None:
            self.stt = stt
        else:
            if not STT_AVAILABLE or not PYAUDIO_AVAILABLE:
                raise RuntimeError(
                    "Cannot start voice chat: SpeechRecognition and/or PyAudio not installed.\n"
                    "Install with:  pip install SpeechRecognition pyaudio"
                )
            self.stt = SpeechToText()

    # -- Public API ----------------------------------------------------

    def start(self) -> None:
        """Begin the interactive voice conversation loop (blocking)."""
        self._running = True
        self._stop_event.clear()

        greeting = "Voice mode activated. I'm listening."
        print(f"\033[36mBruce (voice):\033[0m {greeting}")
        self.tts.speak(greeting)

        if self.require_wake_word:
            print(f"\033[90m  Say 'Bruce' followed by your command. Say 'stop' or 'exit' to end.\033[0m")
        else:
            print(f"\033[90m  Speak freely. Say 'stop' or 'exit' to end voice chat.\033[0m")

        try:
            while self._running and not self._stop_event.is_set():
                self._voice_loop_iteration()
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False
            farewell = "Voice mode deactivated."
            print(f"\n\033[36mBruce (voice):\033[0m {farewell}")
            self.tts.speak(farewell)

    def stop(self) -> None:
        """Signal the voice loop to stop."""
        self._running = False
        self._stop_event.set()

    @property
    def is_running(self) -> bool:
        return self._running

    # -- Internal loop -------------------------------------------------

    def _voice_loop_iteration(self) -> None:
        """One listen-respond cycle."""
        print("\033[90m  [listening...]\033[0m", end="\r", flush=True)
        text = self.stt.listen(timeout=8.0, phrase_limit=30.0)

        if not text:
            return  # silence or unrecognised

        text_lower = text.lower().strip()
        print(f"\033[32mYou (voice):\033[0m {text}")

        # Check for exit words
        if any(word in text_lower.split() for word in self.EXIT_WORDS):
            self.stop()
            return

        # Wake-word check (if required)
        if self.require_wake_word:
            if not text_lower.startswith(self.WAKE_WORD):
                # Heard something but no wake word — ignore
                return
            # Strip the wake word from the command
            text = text[len(self.WAKE_WORD):].strip().lstrip(",").strip()
            if not text:
                self.tts.speak("Yes?")
                print(f"\033[36mBruce (voice):\033[0m Yes?")
                return

        # Get Bruce's response
        response = self._get_response(text)
        print(f"\033[36mBruce (voice):\033[0m {response}")
        self.tts.speak(response)

    def _get_response(self, text: str) -> str:
        """Get a response from Bruce or fall back to echo mode."""
        if self.bruce is not None:
            try:
                return self.bruce.chat(text)
            except Exception as e:
                logger.warning("Bruce chat error: %s", e)
                return f"I had trouble processing that: {e}"
        else:
            return f"[Echo mode] You said: {text}"


# ===================================================================
# Convenience helpers
# ===================================================================

def quick_speak(text: str) -> None:
    """One-liner: speak text aloud, then return."""
    if not TTS_AVAILABLE:
        print(f"[TTS unavailable] {text}")
        return
    tts = TextToSpeech()
    tts.speak(text)


def start_voice_chat(bruce_agent=None, require_wake_word: bool = False) -> None:
    """
    High-level entry point to start a voice chat session.

    Prints friendly error messages if dependencies are missing.
    """
    status = voice_status()

    if not status["tts_available"]:
        print("\033[31m[Voice] Text-to-Speech is not available.\033[0m")
        print("  Install with:  pip install pyttsx3")
        return

    if not status["stt_available"] or not status["pyaudio_available"]:
        print("\033[33m[Voice] Speech-to-Text is not fully available.\033[0m")
        for pkg in status["missing"]:
            print(f"  Missing: {pkg}")
        print("\n\033[33m  Falling back to TTS-only mode (type text, Bruce speaks).\033[0m\n")
        _tts_only_mode(bruce_agent)
        return

    try:
        vc = VoiceChat(bruce_agent=bruce_agent, require_wake_word=require_wake_word)
        vc.start()
    except Exception as e:
        print(f"\033[31m[Voice] Error starting voice chat: {e}\033[0m")
        print("\033[33m  Falling back to TTS-only mode.\033[0m\n")
        _tts_only_mode(bruce_agent)


def _tts_only_mode(bruce_agent=None) -> None:
    """Fallback mode: user types, Bruce speaks the response."""
    if not TTS_AVAILABLE:
        print("\033[31m[Voice] TTS not available either. Install pyttsx3.\033[0m")
        return

    tts = TextToSpeech()
    greeting = "Voice output mode. Type your messages and I will speak the responses. Type 'exit' to stop."
    print(f"\033[36mBruce (voice):\033[0m {greeting}")
    tts.speak(greeting)

    while True:
        try:
            user_input = input("\033[32mFederico:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input or user_input.lower() in ("exit", "stop", "quit"):
            break

        if bruce_agent is not None:
            try:
                response = bruce_agent.chat(user_input)
            except Exception as e:
                response = f"Error: {e}"
        else:
            response = f"[Echo] {user_input}"

        print(f"\033[36mBruce (voice):\033[0m {response}")
        tts.speak(response)

    farewell = "Voice mode ended."
    print(f"\033[36mBruce (voice):\033[0m {farewell}")
    tts.speak(farewell)


# ===================================================================
# CLI self-test
# ===================================================================

if __name__ == "__main__":
    print("=== Bruce AI Voice Engine — Status ===")
    status = voice_status()
    print(f"  TTS available:     {status['tts_available']}")
    print(f"  STT available:     {status['stt_available']}")
    print(f"  PyAudio available: {status['pyaudio_available']}")

    if status["missing"]:
        print("\n  Missing packages:")
        for pkg in status["missing"]:
            print(f"    - {pkg}")

    if TTS_AVAILABLE:
        print("\n  Testing TTS...")
        tts = TextToSpeech()
        voices = tts.list_voices()
        print(f"  Found {len(voices)} voice(s):")
        for v in voices[:5]:
            print(f"    - {v['name']} ({v['id'][:60]}...)")
        tts.speak("Bruce AI voice engine is operational.")
        print("  TTS test complete.")
    else:
        print("\n  Skipping TTS test (pyttsx3 not installed).")

    print("\nDone.")
