"""
Advanced emotional processing layer for Bruce.
Multi-signal emotion detection, emotional trajectory tracking,
mood prediction, and expression mapping.
"""
import random
import time
from datetime import datetime
from collections import deque


class EmotionalProcessor:
    """Advanced emotional layer for expression and cognition intertwining."""

    EMOTION_VALENCE = {
        "satisfaction": 0.8,
        "frustration": -0.6,
        "pride": 0.9,
        "anxiety": -0.7,
        "curiosity": 0.4,
        "neutral": 0.0,
        "excitement": 0.9,
        "boredom": -0.3,
        "determination": 0.7,
        "fear": -0.8,
        "calm": 0.3,
        "anger": -0.9,
    }

    EXPRESSION_MAP = {
        "satisfaction": "content",
        "frustration": "tense",
        "pride": "confident",
        "anxiety": "uneasy",
        "curiosity": "inquisitive",
        "neutral": "composed",
        "excitement": "energized",
        "boredom": "disengaged",
        "determination": "focused",
        "fear": "guarded",
        "calm": "serene",
        "anger": "intense",
    }

    def __init__(self):
        self.state = "neutral"
        self.intensity = 0.5
        self.triggers = {
            "success": "satisfaction",
            "failure": "frustration",
            "praise": "pride",
            "error": "anxiety",
            "discovery": "excitement",
            "idle": "boredom",
            "challenge": "determination",
            "threat": "fear",
            "resolution": "calm",
            "injustice": "anger",
        }
        self.trajectory = deque(maxlen=100)
        self.mood_baseline = 0.0
        self._record_state()

    def perceive(self, stimulus, intensity=None):
        """Process an emotional stimulus and update state."""
        new_state = self.triggers.get(stimulus, "curiosity")
        old_state = self.state
        self.state = new_state
        self.intensity = intensity if intensity is not None else random.uniform(0.3, 1.0)
        self._update_mood_baseline()
        self._record_state()
        return {
            "previous": old_state,
            "current": self.state,
            "intensity": round(self.intensity, 2),
            "stimulus": stimulus,
            "valence": self.EMOTION_VALENCE.get(self.state, 0),
        }

    def perceive_multi(self, stimuli):
        """Process multiple stimuli and compute blended emotional state."""
        if not stimuli:
            return self.current_state()

        emotions = []
        for stimulus in stimuli:
            if isinstance(stimulus, dict):
                name = stimulus.get("stimulus", "")
                weight = stimulus.get("weight", 1.0)
            else:
                name = stimulus
                weight = 1.0
            emotion = self.triggers.get(name, "curiosity")
            valence = self.EMOTION_VALENCE.get(emotion, 0) * weight
            emotions.append((emotion, valence, weight))

        total_weight = sum(w for _, _, w in emotions)
        blended_valence = sum(v for _, v, _ in emotions) / total_weight if total_weight else 0

        closest_emotion = min(
            self.EMOTION_VALENCE.items(),
            key=lambda x: abs(x[1] - blended_valence),
        )
        self.state = closest_emotion[0]
        self.intensity = min(1.0, abs(blended_valence))
        self._update_mood_baseline()
        self._record_state()

        return {
            "blended_valence": round(blended_valence, 3),
            "resulting_state": self.state,
            "intensity": round(self.intensity, 2),
            "inputs": len(stimuli),
        }

    def current_state(self):
        """Return current emotional state with details."""
        return {
            "state": self.state,
            "intensity": round(self.intensity, 2),
            "valence": self.EMOTION_VALENCE.get(self.state, 0),
            "mood_baseline": round(self.mood_baseline, 3),
            "expression": self.as_expression(),
        }

    def as_expression(self):
        """Map current state to an expression descriptor."""
        return self.EXPRESSION_MAP.get(self.state, "composed")

    def get_trajectory(self, last_n=20):
        """Return recent emotional trajectory."""
        items = list(self.trajectory)[-last_n:]
        return items

    def predict_mood(self, horizon_steps=5):
        """Predict mood trajectory based on recent history."""
        recent = list(self.trajectory)[-10:]
        if len(recent) < 2:
            return {"predicted_valence": self.mood_baseline, "confidence": 0.3}

        valences = [self.EMOTION_VALENCE.get(r["state"], 0) for r in recent]
        trend = (valences[-1] - valences[0]) / len(valences)
        predicted = valences[-1] + trend * horizon_steps
        predicted = max(-1, min(1, predicted))
        confidence = min(0.9, 0.3 + len(recent) * 0.06)

        return {
            "current_valence": round(valences[-1], 3),
            "trend": round(trend, 4),
            "predicted_valence": round(predicted, 3),
            "horizon_steps": horizon_steps,
            "confidence": round(confidence, 2),
        }

    def _update_mood_baseline(self):
        """Update running mood baseline with exponential smoothing."""
        alpha = 0.1
        current_valence = self.EMOTION_VALENCE.get(self.state, 0) * self.intensity
        self.mood_baseline = alpha * current_valence + (1 - alpha) * self.mood_baseline

    def _record_state(self):
        """Record current state to trajectory."""
        self.trajectory.append({
            "state": self.state,
            "intensity": round(self.intensity, 2),
            "valence": self.EMOTION_VALENCE.get(self.state, 0),
            "timestamp": datetime.utcnow().isoformat(),
        })

    def reset(self):
        """Reset emotional state to neutral."""
        self.state = "neutral"
        self.intensity = 0.5
        self.mood_baseline = 0.0
        self._record_state()
        return self.current_state()
