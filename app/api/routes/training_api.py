# Ruta: C:\Users\feder\Desktop\OKK_Gorilla_Bot\app\api\routes\training_api.py

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import logging
import os
import uuid

from app.ai.rl_agent import PPOTrainer
from cognitive_memory.episodic_memory_handler import append_episode, summarize_memory, get_statistics

router = APIRouter()

LOG_FILE = "data/logs/train.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Reiniciar log al arranque
with open(LOG_FILE, "w") as f:
    f.write(f"[INIT - {datetime.utcnow().isoformat()}] Training API online\n")

class TrainConfig(BaseModel):
    model_name: str
    env_name: str
    learning_rate: float
    episodes: int

@router.post("/train/start")
async def start_training(config: TrainConfig, background_tasks: BackgroundTasks):
    def run_training():
        trainer = PPOTrainer(
            model_name=config.model_name,
            env_name=config.env_name,
            learning_rate=config.learning_rate
        )
        for episode in range(config.episodes):
            episode_id = str(uuid.uuid4())[:8]
            result = trainer.train_episode()
            result["timestamp"] = datetime.utcnow().isoformat()
            result["episode"] = episode + 1
            result["episode_id"] = episode_id
            append_episode(result)

            with open(LOG_FILE, "a") as f:
                f.write(f"[{datetime.utcnow().isoformat()}] EP{episode+1} ({episode_id}) → Reward: {result['reward']} | Loss: {result['avg_loss_like_signal']}\n")

    background_tasks.add_task(run_training)
    return {"message": "🧠 Training started in background with RL agent."}

@router.get("/train/logs")
async def get_logs() -> Dict:
    try:
        with open(LOG_FILE, "r") as f:
            logs = f.readlines()
        return {"logs": [l.strip() for l in logs[-200:]]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {str(e)}"]}

@router.get("/memory/summary")
async def memory_summary() -> List[dict]:
    return summarize_memory(10)

@router.get("/memory/stats")
async def memory_stats() -> Dict:
    return get_statistics()