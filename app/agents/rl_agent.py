import os
import gym
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from dotenv import load_dotenv

# Carga configuración desde .env.overdrive
load_dotenv(dotenv_path=".env.overdrive")

# Configuración general
MODEL_PATH = os.getenv("MODEL_PATH", "data/models/ppo_gorilla_agent.zip")
RL_SEED = int(os.getenv("RL_SEED", "42"))
RL_LEARNING_RATE = float(os.getenv("RL_LEARNING_RATE", "0.00025"))
RL_BATCH_SIZE = int(os.getenv("RL_BATCH_SIZE", "128"))
RL_BUFFER_SIZE = int(os.getenv("RL_BUFFER_SIZE", "100000"))
RL_TRAIN_FREQUENCY = int(os.getenv("RL_TRAIN_FREQUENCY", "32"))

# Importa entorno personalizado
from gym_envs.market_env import MarketEnv


class PPOGorillaAgent:
    def __init__(self, train_mode=False):
        self.env = DummyVecEnv([lambda: MarketEnv()])
        self.train_mode = train_mode
        self.model = None

        if train_mode or not os.path.exists(MODEL_PATH):
            self._create_model()
        else:
            self._load_model()

    def _create_model(self):
        print("[RL_AGENT] Creating new PPO model...")
        self.model = PPO(
            "MlpPolicy",
            self.env,
            verbose=1,
            learning_rate=RL_LEARNING_RATE,
            batch_size=RL_BATCH_SIZE,
            seed=RL_SEED,
            tensorboard_log="./logs/ppo_tensorboard/"
        )

    def _load_model(self):
        print(f"[RL_AGENT] Loading PPO model from {MODEL_PATH}")
        self.model = PPO.load(MODEL_PATH, env=self.env)

    def train(self, timesteps=100_000):
        print(f"[RL_AGENT] Starting training for {timesteps} timesteps...")
        self.model.learn(total_timesteps=timesteps)
        self.model.save(MODEL_PATH)
        print(f"[RL_AGENT] Model saved to {MODEL_PATH}")

    def predict(self, observation):
        action, _ = self.model.predict(observation, deterministic=True)
        return action

    def retrain_incremental(self, additional_timesteps=10_000):
        print(f"[RL_AGENT] Incremental training for {additional_timesteps} timesteps...")
        self.model.learn(total_timesteps=additional_timesteps)
        self.model.save(MODEL_PATH)
        print(f"[RL_AGENT] Updated model saved.")

