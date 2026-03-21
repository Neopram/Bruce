# 📂 Ruta: C:\Users\feder\Desktop\OKK_Gorilla_Bot\app\services\self_healing_ai.py

import requests
import logging
import time
from typing import Dict, Any
from prometheus_client.parser import text_string_to_metric_families

DEEPSEEK_ENDPOINT = "http://localhost:11434/api/chat"
MODEL_NAME = "deepseek-coder:7b-instruct"
PROMETHEUS_URL = "http://localhost:8000/metrics"

# Reglas simples (pueden ser reemplazadas por aprendizaje RL más adelante)
THRESHOLDS = {
    "cpu_usage": 0.8,
    "memory_usage": 0.85,
    "rl_reward": -0.1,
    "training_errors": 5
}

def fetch_prometheus_metrics() -> Dict[str, float]:
    """Consulta Prometheus y extrae las métricas necesarias."""
    try:
        response = requests.get(PROMETHEUS_URL)
        metrics = {}
        for family in text_string_to_metric_families(response.text):
            for sample in family.samples:
                name = sample.name
                value = sample.value
                if name in ["cpu_usage", "memory_usage", "rl_reward", "training_errors"]:
                    metrics[name] = float(value)
        return metrics
    except Exception as e:
        logging.error(f"Error fetching Prometheus metrics: {e}")
        return {}

def deepseek_self_diagnose(context: Dict[str, Any]) -> str:
    """Consulta DeepSeek con contexto actual para diagnóstico y acciones."""
    prompt = f"""
    You are a cognitive supervisor. Diagnose system health and recommend actions.

    Context:
    {context}

    Return step-by-step recovery strategy and root cause analysis.
    """
    try:
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are DeepSeek Healing AI."},
                {"role": "user", "content": prompt}
            ]
        }
        response = requests.post(DEEPSEEK_ENDPOINT, json=payload)
        response.raise_for_status()
        reply = response.json()["message"]["content"]
        return reply
    except Exception as e:
        logging.error(f"DeepSeek Healing AI error: {e}")
        return "Failed to diagnose via DeepSeek."

def evaluate_and_heal():
    """Ciclo principal de autoevaluación y reparación del sistema."""
    logging.info("✨ Evaluando salud del sistema con DeepSelf-Healing AI...")
    metrics = fetch_prometheus_metrics()
    if not metrics:
        logging.warning("No se pudieron obtener métricas.")
        return

    anomalies = {}
    for key, threshold in THRESHOLDS.items():
        if metrics.get(key, 0) > threshold:
            anomalies[key] = metrics[key]

    if anomalies:
        logging.warning(f"⚠️ Anomalías detectadas: {anomalies}")
        analysis = deepseek_self_diagnose(anomalies)
        logging.info(f"DeepSeek Diagnostic Response:\n{analysis}")
    else:
        logging.info("🚀 Sistema estable. No se requiere acción correctiva.")

# Punto de entrada manual o desde scheduler
if __name__ == "__main__":
    while True:
        evaluate_and_heal()
        time.sleep(60)  # Revisa cada minuto
