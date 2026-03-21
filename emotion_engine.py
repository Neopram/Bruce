# emotion_engine.py

"""
Emotion Engine for Bruce AI.
Detects emotions from text using keyword-based sentiment analysis (with optional
transformer model upgrade), tracks emotion history, and provides emotion trends
and influence on response generation.
"""

from fastapi import APIRouter, Request
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, List
import logging
import re
import json
import os

from user_biometrics import UserBiometrics
from personality import TraderProfile

router = APIRouter()
logger = logging.getLogger("Bruce.EmotionEngine")
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
#  Keyword-based sentiment lexicon (fallback when transformers not available)
# ---------------------------------------------------------------------------

EMOTION_LEXICON = {
    "joy": {
        "keywords": [
            "happy", "great", "awesome", "amazing", "love", "excellent", "perfect",
            "wonderful", "fantastic", "feliz", "gracias", "thank", "bravo", "nice",
            "good", "profit", "win", "moon", "pump", "rally", "bull", "gain",
        ],
        "weight": 1.0,
    },
    "gratitude": {
        "keywords": [
            "thanks", "thank you", "gracias", "appreciate", "grateful", "agradecido",
        ],
        "weight": 0.9,
    },
    "fear": {
        "keywords": [
            "afraid", "scared", "fear", "panic", "crash", "dump", "rug",
            "liquidation", "miedo", "panico", "rekt", "scam", "hack",
        ],
        "weight": -0.8,
    },
    "anger": {
        "keywords": [
            "angry", "furious", "hate", "stupid", "ridiculous", "enojado",
            "frustrado", "molesto", "damn", "crap", "terrible",
        ],
        "weight": -0.7,
    },
    "frustration": {
        "keywords": [
            "frustrated", "annoying", "stuck", "broken", "fail", "error",
            "fracaso", "mistake", "wrong", "bug", "loss", "losing",
        ],
        "weight": -0.6,
    },
    "anxiety": {
        "keywords": [
            "anxious", "worried", "nervous", "uncertain", "volatile",
            "ansioso", "preocupado", "risk", "danger", "warning",
        ],
        "weight": -0.5,
    },
    "excitement": {
        "keywords": [
            "exciting", "wow", "incredible", "breakout", "surge", "rocket",
            "launch", "explosion", "boom", "massive", "huge",
        ],
        "weight": 0.8,
    },
    "sadness": {
        "keywords": [
            "sad", "disappointed", "unfortunate", "triste", "lost", "miss",
            "regret", "lament", "sorry", "down", "bearish",
        ],
        "weight": -0.4,
    },
    "confidence": {
        "keywords": [
            "confident", "sure", "certain", "strong", "solid", "confirmed",
            "seguro", "trust", "reliable", "proven",
        ],
        "weight": 0.7,
    },
    "neutral": {
        "keywords": [],
        "weight": 0.0,
    },
}

# Attempt to load transformer-based sentiment model
_transformer_pipeline = None
try:
    from transformers import pipeline as _hf_pipeline
    _transformer_pipeline = _hf_pipeline(
        "sentiment-analysis",
        model="nlptown/bert-base-multilingual-uncased-sentiment",
        truncation=True,
    )
    logger.info("[EmotionEngine] Transformer sentiment model loaded")
except Exception:
    logger.info("[EmotionEngine] Transformers not available, using keyword fallback")

# ---------------------------------------------------------------------------
#  Emotion history storage
# ---------------------------------------------------------------------------

EMOTION_LOG_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "logs", "emotion_history.jsonl"
)
os.makedirs(os.path.dirname(EMOTION_LOG_PATH), exist_ok=True)


def _persist_emotion(record: dict):
    try:
        with open(EMOTION_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _load_emotion_history(user_id: Optional[str] = None) -> List[dict]:
    records: List[dict] = []
    if not os.path.exists(EMOTION_LOG_PATH):
        return records
    try:
        with open(EMOTION_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if user_id is None or rec.get("user_id") == user_id:
                        records.append(rec)
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass
    return records


# ---------------------------------------------------------------------------
#  Keyword-based emotion detection
# ---------------------------------------------------------------------------

def detect_emotion_keywords(text: str) -> Dict:
    """
    Detect emotion from text using keyword matching.
    Returns dict with emotion, confidence, valence, and matched keywords.
    """
    text_lower = text.lower()
    tokens = set(re.findall(r"\w+", text_lower))

    best_emotion = "neutral"
    best_score = 0
    best_matches: List[str] = []

    for emotion, data in EMOTION_LEXICON.items():
        if emotion == "neutral":
            continue
        matches = [kw for kw in data["keywords"] if kw in tokens]
        score = len(matches)
        if score > best_score:
            best_score = score
            best_emotion = emotion
            best_matches = matches

    # Confidence is based on how many keywords matched (cap at 1.0)
    confidence = min(best_score / 3.0, 1.0) if best_score > 0 else 0.1
    valence = EMOTION_LEXICON.get(best_emotion, {}).get("weight", 0.0)

    return {
        "emotion": best_emotion,
        "confidence": round(confidence, 3),
        "valence": round(valence, 3),
        "matched_keywords": best_matches,
        "method": "keyword",
    }


def detect_emotion_transformer(text: str) -> Dict:
    """
    Detect sentiment using a transformer model.
    Maps star ratings to emotions.
    """
    if _transformer_pipeline is None:
        return detect_emotion_keywords(text)

    try:
        result = _transformer_pipeline(text[:512])[0]
        label = result.get("label", "3 stars")
        score = result.get("score", 0.5)

        # Map star rating to emotion
        star_map = {
            "1 star": ("frustration", -0.8),
            "2 stars": ("sadness", -0.4),
            "3 stars": ("neutral", 0.0),
            "4 stars": ("confidence", 0.5),
            "5 stars": ("joy", 0.9),
        }
        emotion, valence = star_map.get(label, ("neutral", 0.0))

        return {
            "emotion": emotion,
            "confidence": round(score, 3),
            "valence": round(valence, 3),
            "transformer_label": label,
            "method": "transformer",
        }
    except Exception as e:
        logger.warning(f"[EmotionEngine] Transformer failed, falling back: {e}")
        return detect_emotion_keywords(text)


# ---------------------------------------------------------------------------
#  Response style modifiers based on emotion
# ---------------------------------------------------------------------------

EMOTION_RESPONSE_MODIFIERS = {
    "joy": {
        "tone": "enthusiastic and positive",
        "prefix": "Great news! ",
        "temperature_delta": 0.1,
    },
    "gratitude": {
        "tone": "warm and appreciative",
        "prefix": "",
        "temperature_delta": 0.0,
    },
    "fear": {
        "tone": "calm and reassuring",
        "prefix": "Let me help clarify the situation. ",
        "temperature_delta": -0.1,
    },
    "anger": {
        "tone": "empathetic and solution-oriented",
        "prefix": "I understand your frustration. ",
        "temperature_delta": -0.1,
    },
    "frustration": {
        "tone": "patient and helpful",
        "prefix": "Let's work through this together. ",
        "temperature_delta": -0.05,
    },
    "anxiety": {
        "tone": "steady and factual",
        "prefix": "Here's what we know. ",
        "temperature_delta": -0.1,
    },
    "excitement": {
        "tone": "energetic but grounded",
        "prefix": "",
        "temperature_delta": 0.05,
    },
    "sadness": {
        "tone": "supportive and constructive",
        "prefix": "",
        "temperature_delta": -0.05,
    },
    "confidence": {
        "tone": "direct and affirmative",
        "prefix": "",
        "temperature_delta": 0.0,
    },
    "neutral": {
        "tone": "balanced and informative",
        "prefix": "",
        "temperature_delta": 0.0,
    },
}


# ---------------------------------------------------------------------------
#  Main EmotionEngine class
# ---------------------------------------------------------------------------

class EmotionEngine:
    def __init__(self):
        self.state: str = "neutral"
        self.last_input: Optional[str] = None
        self.trader_profile = TraderProfile()
        self.biometrics = UserBiometrics()
        # Per-user emotion history (in-memory cache)
        self._history: Dict[str, List[dict]] = {}

    def _get_biometric_data(self) -> dict:
        """Safely read biometrics, handling different API shapes."""
        try:
            if hasattr(self.biometrics, "read"):
                return self.biometrics.read()
            elif hasattr(self.biometrics, "get_metrics"):
                raw = self.biometrics.get_metrics()
                # Normalize percentage-based keys to 0-1 floats
                stress_val = self.biometrics.biometrics.get("stress_level_pct", 0)
                focus_val = self.biometrics.biometrics.get("focus_level_pct", 0)
                return {
                    "stress_level": stress_val / 100.0 if stress_val > 1 else stress_val,
                    "focus_level": focus_val / 100.0 if focus_val > 1 else focus_val,
                    "raw": raw,
                }
            else:
                return {"stress_level": 0.0, "focus_level": 0.0}
        except Exception:
            return {"stress_level": 0.0, "focus_level": 0.0}

    def infer_emotion(
        self,
        input_text: Optional[str] = "",
        context: Optional[dict] = None,
        user_id: Optional[str] = None,
    ) -> Dict:
        """
        Infer the current emotional state from text, biometrics, and context.
        Logs the result to history.
        """
        text = input_text or ""
        biometric_data = self._get_biometric_data()
        stress = biometric_data.get("stress_level", 0.0)
        focus = biometric_data.get("focus_level", 0.0)

        # Priority: biometric signals override text-based detection
        if stress > 0.85:
            self.state = "anxious"
            detection = {"emotion": "anxious", "confidence": 0.9, "method": "biometric", "valence": -0.7}
        elif stress > 0.65:
            self.state = "tense"
            detection = {"emotion": "tense", "confidence": 0.7, "method": "biometric", "valence": -0.4}
        elif focus > 0.85:
            self.state = "focused"
            detection = {"emotion": "focused", "confidence": 0.8, "method": "biometric", "valence": 0.3}
        elif text:
            # Use transformer if available, else keywords
            if _transformer_pipeline is not None:
                detection = detect_emotion_transformer(text)
            else:
                detection = detect_emotion_keywords(text)
            self.state = detection["emotion"]
        else:
            self.state = "neutral"
            detection = {"emotion": "neutral", "confidence": 0.5, "method": "default", "valence": 0.0}

        self.last_input = text

        # Build the record
        record = {
            "emotion": self.state,
            "detection": detection,
            "biometrics": biometric_data,
            "user_id": user_id or "anonymous",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Store in history
        uid = user_id or "anonymous"
        self._history.setdefault(uid, []).append(record)
        _persist_emotion(record)

        logger.info(f"[EMOTION] Detected: {self.state} | Text: {text[:60]}")
        return self._compose_state(biometric_data, detection)

    def _compose_state(self, biometric_data: Dict, detection: Optional[Dict] = None) -> Dict:
        modifier = EMOTION_RESPONSE_MODIFIERS.get(self.state, EMOTION_RESPONSE_MODIFIERS["neutral"])
        return {
            "emotion": self.state,
            "persona": self.trader_profile.current_profile(),
            "biometrics": biometric_data,
            "detection": detection,
            "response_modifier": modifier,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": f"Emotional state: {self.state.upper()}",
        }

    def snapshot(self) -> Dict:
        """
        Return a snapshot of the current emotional state, useful for other modules.
        """
        biometric_data = self._get_biometric_data()
        modifier = EMOTION_RESPONSE_MODIFIERS.get(self.state, EMOTION_RESPONSE_MODIFIERS["neutral"])
        return {
            "emotion": self.state,
            "last_input": self.last_input,
            "persona": self.trader_profile.current_profile(),
            "biometrics": biometric_data,
            "response_modifier": modifier,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_response_influence(self) -> Dict:
        """
        Return how the current emotion should influence response generation.
        Useful for injecting into LLM system prompts.
        """
        modifier = EMOTION_RESPONSE_MODIFIERS.get(self.state, EMOTION_RESPONSE_MODIFIERS["neutral"])
        return {
            "emotion": self.state,
            "tone": modifier["tone"],
            "prefix": modifier["prefix"],
            "temperature_delta": modifier["temperature_delta"],
            "system_prompt_addition": (
                f"The user appears to be feeling {self.state}. "
                f"Respond in a {modifier['tone']} manner."
            ),
        }

    def get_emotion_trend(self, user_id: str, hours: int = 24) -> Dict:
        """
        Analyze emotion trends for a user over the last N hours.
        Returns distribution, dominant emotion, and valence trend.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        cutoff_iso = cutoff.isoformat()

        # Combine in-memory and disk history
        records = self._history.get(user_id, [])
        if not records:
            records = _load_emotion_history(user_id)

        recent = [r for r in records if r.get("timestamp", "") >= cutoff_iso]

        if not recent:
            return {
                "user_id": user_id,
                "hours": hours,
                "total_samples": 0,
                "dominant_emotion": "unknown",
                "distribution": {},
                "valence_trend": [],
                "average_valence": 0.0,
            }

        # Build distribution
        distribution: Dict[str, int] = {}
        valence_points: List[float] = []
        for r in recent:
            em = r.get("emotion", "neutral")
            distribution[em] = distribution.get(em, 0) + 1
            det = r.get("detection", {})
            if isinstance(det, dict) and "valence" in det:
                valence_points.append(det["valence"])

        dominant = max(distribution, key=distribution.get)
        avg_valence = sum(valence_points) / len(valence_points) if valence_points else 0.0

        return {
            "user_id": user_id,
            "hours": hours,
            "total_samples": len(recent),
            "dominant_emotion": dominant,
            "distribution": distribution,
            "valence_trend": valence_points[-20:],  # last 20 data points
            "average_valence": round(avg_valence, 3),
        }

    def get_history(self, user_id: str, limit: int = 20) -> List[dict]:
        """Return recent emotion history for a user."""
        records = self._history.get(user_id, [])
        if not records:
            records = _load_emotion_history(user_id)
        return records[-limit:]


# Global instance
bruce_emotion_engine = EmotionEngine()


# ---------------------------------------------------------------------------
#  API Routes
# ---------------------------------------------------------------------------

@router.post("/emotions/infer")
async def infer_emotion_endpoint(request: Request):
    data = await request.json()
    input_text = data.get("input_text", "")
    context = data.get("context", {})
    user_id = data.get("user_id", "anonymous")
    result = bruce_emotion_engine.infer_emotion(input_text, context, user_id)
    return result


@router.get("/emotions/state")
async def get_emotional_state():
    return {
        "status": "Bruce Emotion Engine active",
        "current_state": bruce_emotion_engine.state,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/emotions/trend/{user_id}")
async def get_emotion_trend_endpoint(user_id: str, hours: int = 24):
    return bruce_emotion_engine.get_emotion_trend(user_id, hours)


@router.get("/emotions/history/{user_id}")
async def get_emotion_history_endpoint(user_id: str, limit: int = 20):
    return bruce_emotion_engine.get_history(user_id, limit)


@router.get("/emotions/influence")
async def get_response_influence():
    return bruce_emotion_engine.get_response_influence()


# Exportable from other modules
def emotion_snapshot() -> Dict:
    return bruce_emotion_engine.snapshot()
