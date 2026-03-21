
import os
import shutil
import json
from datetime import datetime

class BruceEvolver:
    def __init__(self, base_model_path="models/deepseek", output_dir="models", feedback_path="data/feedback_dataset.json"):
        self.base_model_path = base_model_path
        self.output_dir = output_dir
        self.feedback_path = feedback_path
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_new_version_name(self):
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"bruce_kernel_v{timestamp}"

    def clone_model(self):
        new_version = self.generate_new_version_name()
        target_path = os.path.join(self.output_dir, new_version)
        shutil.copytree(self.base_model_path, target_path)
        return target_path

    def summarize_feedback(self):
        if not os.path.exists(self.feedback_path):
            return {"total": 0}
        with open(self.feedback_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        positive = sum(1 for d in data if d["quality"] == "positive")
        negative = sum(1 for d in data if d["quality"] == "negative")
        return {
            "total": len(data),
            "positive": positive,
            "negative": negative,
            "score": round((positive - negative) / max(1, len(data)), 3)
        }

    def evolve(self):
        stats = self.summarize_feedback()
        if stats["total"] < 5:
            return {"msg": "Not enough data to evolve."}
        target_path = self.clone_model()
        return {
            "status": "evolved",
            "new_model_path": target_path,
            "feedback_score": stats["score"]
        }
