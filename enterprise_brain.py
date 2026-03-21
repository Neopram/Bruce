# enterprise_brain.py

from datetime import datetime
from personality import TraderProfile
from app.core.volatility_guard import guardian_check
from user_biometrics import UserBiometrics
from vector_logger import VectorLogger
from self_reflection import SelfReflection
from emotion_engine import bruce_emotion_engine

import uuid

# --- Instancias clave ---
persona = TraderProfile()
biometrics = UserBiometrics()
logger = VectorLogger()
reflection_engine = SelfReflection()

# --- 🧠 Núcleo de Decisión Ejecutiva ---
class EnterpriseBrain:
    def __init__(self):
        self.executive_memory = []

    def simulate_executive_decision(self, task: str, context: str = "global"):
        timestamp = datetime.utcnow().isoformat()
        decision_id = str(uuid.uuid4())

        # Evaluación multivariable avanzada
        profile = persona.current_profile()
        stress_guard = guardian_check()
        bio_data = biometrics.read()
        emotions = bruce_emotion_engine.infer_emotion(task, {"context": context})
        reflection = reflection_engine.evaluate()

        if stress_guard["guardian_active"]:
            decision_context = f"⚠️ High volatility detected. Decision postponed. ({stress_guard['volatility']:.2f})"
            result = "🛑 Decision blocked by Bruce's Guardian"
        else:
            decision_context = f"Persona: {profile} | Biometrics: {bio_data} | Reflection: {reflection} | Emotions: {emotions}"
            result = f"✅ Executed: {task} — Context: {context} | Profile: {profile}"

        # Registro en memoria simbiótica
        memory_entry = {
            "id": decision_id,
            "timestamp": timestamp,
            "task": task,
            "context": context,
            "persona": profile,
            "biometrics": bio_data,
            "emotions": emotions,
            "reflection": reflection,
            "volatility": stress_guard["volatility"],
            "guardian_blocked": stress_guard["guardian_active"],
            "result": result
        }

        self.executive_memory.append(memory_entry)
        logger.log_event("EXECUTIVE_DECISION", memory_entry)

        return memory_entry

    def get_history(self):
        return {
            "total_decisions": len(self.executive_memory),
            "memory": self.executive_memory
        }

# ✅ Instancia principal del módulo ejecutivo
bruce_enterprise_brain = EnterpriseBrain()

# ✅ Función exportable para main.py
def simulate_executive_decision(task: str, context: str = "global"):
    return bruce_enterprise_brain.simulate_executive_decision(task, context)
