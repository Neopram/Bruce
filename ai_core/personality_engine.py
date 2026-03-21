
import json
import os

class PersonalityEngine:
    def __init__(self, config_path="data/personality_config.json"):
        self.config_path = config_path
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        self.default_profile = {
            "mode": "balanced",
            "tone": "neutral",
            "style": "precise",
            "bias": "none",
            "creativity": 0.5,
            "emotion": "stable"
        }
        if not os.path.exists(self.config_path):
            self._save_profile(self.default_profile)

    def _save_profile(self, profile):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=4)

    def load_profile(self):
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def update_profile(self, **kwargs):
        profile = self.load_profile()
        profile.update({k: v for k, v in kwargs.items() if k in profile})
        self._save_profile(profile)
        return profile

    def describe_personality(self):
        profile = self.load_profile()
        return f"Mode: {profile['mode']}, Tone: {profile['tone']}, Style: {profile['style']}, Bias: {profile['bias']}, Creativity: {profile['creativity']}, Emotion: {profile['emotion']}"
