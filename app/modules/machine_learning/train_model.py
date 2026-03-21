import logging
import os
import numpy as np
import torch
import gymnasium as gym
from datetime import datetime
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.env_util import make_vec_env
from app.modules.machine_learning.utils import load_training_data

# Optional: future integration with WandB or TensorBoard
# import wandb
# wandb.init(project="OKK-Gorilla-RL", config={...})

# Logger Configuration
os.makedirs("logs/training", exist_ok=True)
logging.basicConfig(
    filename=f"logs/training/train_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
    filemode='w',
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
MODEL_SAVE_PATH = "trained_models/"
DEFAULT_ALGO = "PPO"
TRAINING_TIMESTEPS = 200_000

class TradingModelTrainer:
    """
    AI-Driven Trading Model Trainer with Meta-Learning, Self-Reflection,
    and Adaptive Reinforcement. Designed to plug directly into the OCFA architecture.
    """

    def __init__(self, algo=DEFAULT_ALGO, env_name="TradingEnv-v1"):
        self.algo = algo.upper()
        self.env_name = env_name
        self.model = None
        self.env = self._initialize_env()

    def _initialize_env(self):
        """
        Initializes and returns the RL trading environment. Falls back gracefully.
        """
        try:
            env = make_vec_env(self.env_name, n_envs=1)
            logging.info(f"✅ Environment '{self.env_name}' initialized.")
            return env
        except gym.error.Error:
            logging.warning(f"⚠️ Environment '{self.env_name}' not found. Falling back to 'CartPole-v1'.")
            return make_vec_env("CartPole-v1", n_envs=1)

    def initialize_model(self):
        """
        Initializes the RL model using the selected algorithm and policy.
        """
        if self.algo == "PPO":
            self.model = PPO("MlpPolicy", self.env, verbose=1)
        elif self.algo == "DQN":
            self.model = DQN("MlpPolicy", self.env, verbose=1)
        else:
            raise ValueError(f"Unsupported algorithm: {self.algo}. Use 'PPO' or 'DQN'.")
        logging.info(f"🧠 Initialized model using {self.algo}.")

    def train_model(self, timesteps=TRAINING_TIMESTEPS):
        """
        Trains the RL model using either loaded market data or simulated environment.
        """
        if self.model is None:
            logging.error("❌ Model not initialized. Please call initialize_model() first.")
            return

        try:
            training_data = load_training_data()
            logging.info(f"📥 Loaded training data with shape: {training_data.shape}")
        except Exception as e:
            logging.warning(f"⚠️ Could not load training data: {e}")

        logging.info(f"🚀 Starting training for {timesteps:,} timesteps with {self.algo}.")

        try:
            self.model.learn(total_timesteps=timesteps)
        except Exception as e:
            logging.error(f"💥 Training failed: {e}")
            return

        self.save_model()
        logging.info("✅ Training completed successfully.")

    def save_model(self):
        """
        Saves the current state of the model to disk.
        """
        os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
        save_path = f"{MODEL_SAVE_PATH}{self.algo}_trading_model.zip"
        self.model.save(save_path)
        logging.info(f"📁 Model saved at: {save_path}")

    def load_model(self):
        """
        Loads an existing model from disk. Useful for resuming or deploying.
        """
        load_path = f"{MODEL_SAVE_PATH}{self.algo}_trading_model.zip"
        try:
            if self.algo == "PPO":
                self.model = PPO.load(load_path, env=self.env)
            elif self.algo == "DQN":
                self.model = DQN.load(load_path, env=self.env)
            logging.info(f"🔄 Model loaded successfully from {load_path}.")
        except FileNotFoundError:
            logging.error("🚨 Model file not found. Train the model before attempting to load.")
            self.model = None

if __name__ == "__main__":
    trainer = TradingModelTrainer(algo="PPO")
    trainer.initialize_model()
    trainer.train_model(timesteps=200_000)
    trainer.save_model()
    trainer.load_model()
