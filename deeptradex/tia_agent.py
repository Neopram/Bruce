import os
import json
import logging
import requests
from typing import Dict, Any, Optional

TEMPLATE_PATH = os.path.join("core", "promptTemplates")
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "deepseek-coder:7b-instruct"

class TIAAgent:
    def __init__(self, template_file: str = "tia_default.json"):
        self.template = self.load_template(template_file)
        self.last_result: Optional[str] = None

    def load_template(self, filename: str) -> Dict[str, Any]:
        full_path = os.path.join(TEMPLATE_PATH, filename)
        if not os.path.exists(full_path):
            logging.error(f"❌ Template file not found: {full_path}")
            raise FileNotFoundError(f"Prompt template not found: {filename}")
        with open(full_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logging.info(f"✅ Template loaded: {filename}")
        return data

    def build_prompt(self, command: str, context: Dict[str, Any] = {}) -> str:
        intro = self.template.get("intro", "")
        outro = self.template.get("outro", "")
        context_str = json.dumps(context, indent=2)
        return f"{intro}\n\nCOMMAND:\n{command}\n\nCONTEXT:\n{context_str}\n\n{outro}"

    def execute(self, command: str, context: Dict[str, Any] = {}) -> str:
        prompt = self.build_prompt(command, context)
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": self.template.get("system_role", "You are a cognitive task agent.")},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            result = response.json()
            message = result.get("message", {}).get("content", "").strip()
            self.last_result = message
            logging.info("🧠 TIAAgent executed task successfully.")
            return message

        except Exception as e:
            logging.error(f"❌ TIAAgent execution failed: {str(e)}")
            raise RuntimeError("Failed to execute TIA task")

    def last_output(self) -> Optional[str]:
        return self.last_result

    def execute_and_store(self, command: str, context: Dict[str, Any], output_path: str):
        result = self.execute(command, context)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
        logging.info(f"📄 TIA result saved to {output_path}")
