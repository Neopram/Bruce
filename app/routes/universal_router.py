
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from datetime import datetime
import os

router = APIRouter()

# Simulated in-memory data (replace with actual DB or files later)
memory_data = [
    {"episode": 1, "reward": 15.2, "avg_loss_like_signal": 0.34},
    {"episode": 2, "reward": 12.7, "avg_loss_like_signal": 0.29},
]
train_logs = ["Training initialized...", "Episode 1 complete.", "Loss decreased."]
prediction_result = {"AI Prediction": "Market will likely go up in short term."}
status_flag = {"running": False}

@router.get("/memory/summary")
def get_memory_summary():
    return memory_data

@router.get("/memory/stats")
def get_memory_stats():
    if not memory_data:
        raise HTTPException(status_code=404, detail="No memory data found")
    total = len(memory_data)
    avg_reward = sum(d["reward"] for d in memory_data) / total
    avg_loss = sum(d["avg_loss_like_signal"] for d in memory_data) / total
    return {
        "total_episodes": total,
        "average_reward": round(avg_reward, 2),
        "average_loss_signal": round(avg_loss, 3)
    }

@router.post("/train/start")
def start_training(params: Dict):
    status_flag["running"] = True
    train_logs.append(f"Training started with params: {params}")
    return {"status": "training_started"}

@router.post("/train/stop")
def stop_training():
    status_flag["running"] = False
    train_logs.append("Training stopped by user.")
    return {"status": "training_stopped"}

@router.get("/train/logs")
def get_train_logs():
    return {"logs": train_logs[-10:]}

@router.get("/predict")
def get_prediction():
    return prediction_result

@router.get("/meta/info")
def get_meta_info():
    return {
        "version": "v1.0.0",
        "environment": "development",
        "uptime": str(datetime.utcnow())
    }

@router.get("/health")
def health_check():
    return {"status": "ok"}
