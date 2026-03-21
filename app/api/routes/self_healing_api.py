# 📂 Ruta: C:\Users\feder\Desktop\OKK_Gorilla_Bot\app\api\routes\self_healing_api.py

from fastapi import APIRouter, HTTPException
from prometheus_client import generate_latest
from typing import Dict
import logging
import requests
import os
import json

router = APIRouter()

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "deepseek-coder:7b-instruct"

@router.get("/ai/self-healing/status", response_model=Dict)
def get_system_status():
    try:
        metrics = generate_latest().decode("utf-8")
        status = {
            "cpu_load": _extract_metric(metrics, "process_cpu_seconds_total"),
            "memory_usage": _extract_metric(metrics, "process_resident_memory_bytes"),
            "trades_executed": _extract_metric(metrics, "trades_executed")
        }
        logging.info("[Self-Healing] Metrics captured")
        return status
    except Exception as e:
        logging.error(f"[Self-Healing] Error capturing metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch Prometheus metrics")

@router.post("/ai/self-healing/heal")
def trigger_self_healing():
    try:
        prompt = """
        The AI system is showing performance or stability issues based on the following metrics.
        Analyze the situation and return corrective actions (code fixes, strategy tweaks, module restarts).
        """

        status = get_system_status()

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": "You are a self-healing diagnostic AI."},
                {"role": "user", "content": prompt + json.dumps(status, indent=2)}
            ]
        }

        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        result = response.json()

        healing_plan = result["message"]["content"]
        logging.info(f"[Self-Healing] Suggested fix: {healing_plan}")
        return {"response": healing_plan}

    except Exception as e:
        logging.error(f"[Self-Healing] Diagnostic failed: {e}")
        raise HTTPException(status_code=500, detail="Unable to process healing request")

def _extract_metric(metrics: str, metric_name: str) -> float:
    for line in metrics.splitlines():
        if line.startswith(metric_name):
            try:
                return float(line.split()[-1])
            except:
                return 0.0
    return 0.0
