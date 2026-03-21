# user_biometrics.py

import random
import datetime
from datetime import timezone

class UserBiometrics:
    """
    🧠 UserBiometrics – Simulated real-time biometric interface for Bruce AI.

    This module simulates biometric feedback, intended to evolve into a 
    real-world interface for health, focus, and emotional monitoring.
    """

    def __init__(self):
        self.last_sync = datetime.datetime.now(timezone.utc)
        self.biometrics = self._generate_initial_state()

    def _generate_initial_state(self) -> dict:
        return {
            "heartbeat_bpm": random.randint(65, 75),
            "brainwave_pattern": "Alpha",  # Could simulate Alpha/Beta/Theta/Delta
            "blood_oxygen_pct": round(random.uniform(96.5, 99.0), 1),
            "focus_level_pct": random.randint(60, 90),
            "stress_level_pct": random.randint(5, 20),
        }

    def _simulate_fluctuation(self, base: int, variance: int) -> int:
        return max(0, base + random.randint(-variance, variance))

    def refresh(self):
        """
        Refresh the simulated biometrics to reflect new real-time values.
        """
        self.biometrics["heartbeat_bpm"] = self._simulate_fluctuation(self.biometrics["heartbeat_bpm"], 3)
        self.biometrics["focus_level_pct"] = self._simulate_fluctuation(self.biometrics["focus_level_pct"], 5)
        self.biometrics["stress_level_pct"] = self._simulate_fluctuation(self.biometrics["stress_level_pct"], 3)
        self.biometrics["blood_oxygen_pct"] = round(random.uniform(96.0, 99.5), 1)
        self.biometrics["brainwave_pattern"] = random.choice(["Alpha", "Beta", "Theta", "Delta", "Gamma"])
        self.last_sync = datetime.datetime.now(timezone.utc)

    def get_metrics(self) -> dict:
        """
        Return the current biometric metrics.
        """
        self.refresh()
        return {
            "heartbeat": f"❤️ {self.biometrics['heartbeat_bpm']} BPM",
            "oxygen": f"🩸 {self.biometrics['blood_oxygen_pct']}% SpO2",
            "focus": f"🎯 {self.biometrics['focus_level_pct']}% focus",
            "stress": f"🔥 {self.biometrics['stress_level_pct']}% stress",
            "brainwaves": f"🧠 {self.biometrics['brainwave_pattern']} waves",
            "timestamp": self.last_sync.isoformat() + "Z"
        }

    def as_json(self) -> dict:
        """
        Returns structured biometric data suitable for API responses or logging.
        """
        return self.get_metrics()
