import os
import json
import numpy as np
import torch
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from gymnasium import Env
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

# Configuración de logging
LOG_DIR = "./data/logs/episodes"
MODEL_SAVE_PATH = "trained_models/ppo_trading_model.zip"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "rl_agent.log")),
        logging.StreamHandler()
    ]
)

class PPOTrainer:
    """
    Núcleo Autónomo de Entrenamiento Cognitivo:
    Entrenador inteligente con memoria episódica, introspección de decisiones y persistencia continua.
    """

    def __init__(self, model_name: str = "ppo_gorilla_agent", env_name: str = "TradingEnv-v1", learning_rate: float = 0.00025):
        self.model_name = model_name
        self.env_name = env_name
        self.learning_rate = learning_rate
        self.env: Optional[Env] = None
        self.model: Optional[PPO] = None
        self.episode_count = 0
        self._init_environment()
        self._init_model()

    def _init_environment(self):
        try:
            import gymnasium as gym
            env = gym.make(self.env_name)
            self.env = DummyVecEnv([lambda: env])
            logging.info(f"✅ Loaded environment: {self.env_name}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to load env '{self.env_name}': {e}. Fallback to 'CartPole-v1'.")
            import gymnasium as gym
            fallback = gym.make("CartPole-v1")
            self.env = DummyVecEnv([lambda: fallback])

    def _init_model(self):
        if os.path.exists(MODEL_SAVE_PATH):
            try:
                self.model = PPO.load(MODEL_SAVE_PATH, env=self.env)
                logging.info("♻️ Loaded existing PPO model from checkpoint.")
            except Exception as e:
                logging.error(f"❌ Failed to load model: {e}. Starting fresh.")
                self.model = PPO("MlpPolicy", self.env, verbose=0, learning_rate=self.learning_rate)
        else:
            self.model = PPO("MlpPolicy", self.env, verbose=0, learning_rate=self.learning_rate)
            logging.info("🧠 Initialized new PPO model.")

    def train_episode(self) -> Dict[str, Any]:
        obs = self.env.reset()
        done = False
        total_reward = 0.0
        step_counter = 0
        rewards = []

        while not done:
            action, _states = self.model.predict(obs, deterministic=False)
            obs, reward, terminated, truncated, info = self.env.step(action)
            done = bool(terminated or truncated)
            reward_value = float(reward[0]) if isinstance(reward, (list, np.ndarray)) else float(reward)
            rewards.append(reward_value)
            total_reward += reward_value
            step_counter += 1

        self.model.learn(total_timesteps=1024, reset_num_timesteps=False)
        avg_loss = -np.mean(rewards) if rewards else 0.0
        self.episode_count += 1

        result = {
            "episode": self.episode_count,
            "total_steps": step_counter,
            "reward": round(total_reward, 4),
            "avg_loss_like_signal": round(avg_loss, 4),
            "timestamp": datetime.now().isoformat()
        }

        self._log_episode(result)
        self._auto_save_model()

        return result

    def _log_episode(self, result: Dict[str, Any]):
        filename = f"episode_{str(self.episode_count).zfill(4)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(LOG_DIR, filename)
        try:
            with open(path, "w") as f:
                json.dump(result, f, indent=2)
            logging.info(f"📊 Episode {self.episode_count} saved to {path}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to log episode: {e}")

    def _auto_save_model(self):
        try:
            self.model.save(MODEL_SAVE_PATH)
            logging.info(f"💾 Model checkpoint saved at {MODEL_SAVE_PATH}")
        except Exception as e:
            logging.error(f"❌ Failed to save model: {e}")
