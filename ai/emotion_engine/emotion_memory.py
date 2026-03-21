from datetime import datetime

class EmotionMemory:
    def __init__(self):
        self.history = []

    def record(self, mood: str, valence: float, arousal: float):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "mood": mood,
            "valence": valence,
            "arousal": arousal
        }
        self.history.append(entry)

    def get_last(self, n=5):
        return self.history[-n:]

    def summarize_emotional_trajectory(self):
        if not self.history:
            return "Sin memoria emocional todavía."
        positive = sum(1 for h in self.history if h["valence"] > 0)
        negative = sum(1 for h in self.history if h["valence"] < 0)
        stable = len(self.history) - positive - negative
        return f"📈 Últimos estados: {positive} positivos, {negative} negativos, {stable} neutros."