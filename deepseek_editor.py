# deepseek_editor.py

import os
import json
from typing import Dict

class DeepSeekEditor:
    """
    🧠 DeepSeekEditor
    Clase base para manejar operaciones relacionadas con modelos locales de IA
    como DeepSeek, Phi3, TinyLlama, etc. Permite consultar disponibilidad de modelos,
    simular inferencias y administrar archivos relacionados con la IA local.
    """

    def __init__(self, data_path: str = "backend/data"):
        self.data_path = data_path
        self.status_file = os.path.join(self.data_path, "status.json")
        self.infer_file = os.path.join(self.data_path, "infer.json")
        self._load_status()

    def _load_status(self):
        try:
            with open(self.status_file, "r", encoding="utf-8") as f:
                self.status_data = json.load(f)
        except FileNotFoundError:
            self.status_data = {
                "deepseek": True,
                "phi3": False,
                "tinyllama": True
            }
            self._save_status()
        except Exception as e:
            raise RuntimeError(f"Error loading model status: {e}")

    def _save_status(self):
        os.makedirs(self.data_path, exist_ok=True)
        with open(self.status_file, "w", encoding="utf-8") as f:
            json.dump(self.status_data, f, indent=2)

    def get_model_status(self) -> Dict[str, bool]:
        """
        Devuelve un diccionario con los modelos disponibles localmente.
        """
        return self.status_data

    def infer(self, model: str, prompt: str, language: str = "en") -> Dict[str, str]:
        """
        Simula una inferencia local devolviendo una respuesta de ejemplo.
        En el futuro puede conectarse con modelos reales cargados en GPU.
        """
        if not self.status_data.get(model, False):
            return {"error": f"Model '{model}' is not available locally."}

        simulated_output = f"[{model.upper()}-{language}] Bruce responde: '{prompt[::-1]}'"
        self._save_last_inference(simulated_output)

        return {"output": simulated_output}

    def _save_last_inference(self, output: str):
        with open(self.infer_file, "w", encoding="utf-8") as f:
            json.dump({"output": output}, f, indent=2)
