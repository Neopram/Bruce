# ai_core/emotion_engine.py

"""
███████╗ ███╗   ███╗ ██████╗ ██████╗  ██████╗ ███╗   ██╗
██╔════╝ ████╗ ████║██╔═══██╗██╔══██╗██╔═══██╗████╗  ██║
███████╗ ██╔████╔██║██║   ██║██████╔╝██║   ██║██╔██╗ ██║
╚════██║ ██║╚██╔╝██║██║   ██║██╔═══╝ ██║   ██║██║╚██╗██║
███████║ ██║ ╚═╝ ██║╚██████╔╝██║     ╚██████╔╝██║ ╚████║
╚══════╝ ╚═╝     ╚═╝ ╚═════╝ ╚═╝      ╚═════╝ ╚═╝  ╚═══╝
"""

import asyncio
import random
import hashlib

class EmotionalAnalyzer:
    """
    Simulated emotional intelligence engine.
    Detects and scores emotional tone, useful for adaptive response modeling.
    """

    def __init__(self):
        print("💓 EmotionalAnalyzer initialized (simulation mode)")
        self.known_emotions = [
            "joy", "curiosity", "neutral", "fear", "anger", "sadness",
            "hope", "trust", "disgust", "surprise", "anticipation", "shame"
        ]

    async def analyze(self, text: str) -> dict:
        """
        Perform asynchronous emotional analysis on the given text.

        Returns:
            dict: {
                'primary': dominant emotion,
                'score': intensity [0.0–1.0],
                'distribution': {emotion: probability}
            }
        """
        await asyncio.sleep(0.01)  # Simula latencia de IA

        base_seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
        rng = random.Random(base_seed)

        distribution = self._simulate_distribution(rng)
        primary = max(distribution, key=distribution.get)
        score = round(distribution[primary], 2)

        return {
            "primary": primary,
            "score": score,
            "distribution": distribution
        }

    def _simulate_distribution(self, rng) -> dict:
        """
        Simula una distribución probabilística sobre las emociones.
        """
        raw = {emotion: rng.uniform(0, 1) for emotion in self.known_emotions}
        total = sum(raw.values())
        return {k: round(v / total, 4) for k, v in raw.items()}
