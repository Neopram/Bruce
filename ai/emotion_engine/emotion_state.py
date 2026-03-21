from typing import Dict
from datetime import datetime

class EmotionState:
    def __init__(self):
        self.state = {
            "mood": "curioso",
            "valence": 0.1,     # -1 = muy negativo, +1 = muy positivo
            "arousal": 0.4,     # 0 = tranquilo, 1 = hiperactivo
            "last_update": datetime.utcnow().isoformat()
        }

    def get_emotion(self) -> Dict:
        return self.state

    def update_emotion(self, mood: str, valence: float, arousal: float):
        self.state.update({
            "mood": mood,
            "valence": valence,
            "arousal": arousal,
            "last_update": datetime.utcnow().isoformat()
        })

    def adjust_emotion(self, delta_val: float = 0.0, delta_arousal: float = 0.0):
        self.state["valence"] = max(-1, min(1, self.state["valence"] + delta_val))
        self.state["arousal"] = max(0, min(1, self.state["arousal"] + delta_arousal))
        self.state["last_update"] = datetime.utcnow().isoformat()
        self._update_mood_from_state()

    def _update_mood_from_state(self):
        v = self.state["valence"]
        a = self.state["arousal"]
        if v > 0.5 and a > 0.6:
            self.state["mood"] = "eufórico"
        elif v < -0.3 and a > 0.5:
            self.state["mood"] = "estresado"
        elif v < -0.5:
            self.state["mood"] = "triste"
        elif a < 0.2:
            self.state["mood"] = "relajado"
        else:
            self.state["mood"] = "curioso"