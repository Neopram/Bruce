
import json
from datetime import datetime
import os

class FeedbackCollector:
    def __init__(self, dataset_path="data/feedback_dataset.json"):
        self.dataset_path = dataset_path
        os.makedirs(os.path.dirname(self.dataset_path), exist_ok=True)
        if not os.path.exists(self.dataset_path):
            with open(self.dataset_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def save_feedback(self, user_prompt, bruce_reply, quality="neutral", model="deepseek", notes=""):
        feedback_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "prompt": user_prompt,
            "response": bruce_reply,
            "quality": quality,
            "model": model,
            "notes": notes
        }
        with open(self.dataset_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data.append(feedback_entry)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

    def get_feedback_stats(self):
        with open(self.dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "total": len(data),
            "by_quality": {
                "positive": sum(1 for d in data if d["quality"] == "positive"),
                "neutral": sum(1 for d in data if d["quality"] == "neutral"),
                "negative": sum(1 for d in data if d["quality"] == "negative"),
            }
        }
