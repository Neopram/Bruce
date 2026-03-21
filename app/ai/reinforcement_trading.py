import gym
import numpy as np
import tensorflow as tf
import gym.spaces
import logging
from stable_baselines3 import PPO, DQN, A2C, SAC, TD3
from gym import Env
from gym.spaces import Discrete, Box
from datetime import datetime
from app.utils.database import DatabaseManager
from app.modules.machine_learning.predictive_model import PredictiveModel

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Database Manager for Market Data
db_manager = DatabaseManager()

# AI Prediction Model
predictive_model = PredictiveModel()


class TradingEnv(Env):
    """
    Custom Reinforcement Learning Environment for Self-Adaptive Trading.
    """

    def __init__(self):
        super(TradingEnv, self).__init__()

        # Define Action & Observation Space
        self.action_space = Discrete(3)  # 0 = Sell, 1 = Hold, 2 = Buy
        self.observation_space = Box(low=-1, high=1, shape=(5,), dtype=np.float32)

        # Initialize state variables
        self.current_step = 0
        self.trade_history = []
        self.balance = 100000  # Initial capital
        self.position = 0  # Number of assets held
        self.last_price = 0

    def reset(self):
        """
        Resets the trading environment for a new episode.
        """
        self.current_step = 0
        self.trade_history = []
        self.balance = 100000
        self.position = 0
        return self._next_observation()

    def _next_observation(self):
        """
        Fetches the latest market data and formats it for the RL agent.
        """
        market_data = db_manager.get_recent_market_data()
        self.last_price = market_data[-1]["price"]

        return np.array([
            market_data[-1]["price_change"],
            market_data[-1]["volatility"],
            market_data[-1]["liquidity"],
            market_data[-1]["sentiment"],
            self.balance / 100000  # Normalize balance
        ], dtype=np.float32)

    def step(self, action):
        """
        Executes an action (trade) and moves to the next state.
        """
        current_price = self.last_price
        reward = 0

        if action == 0:  # Sell
            if self.position > 0:
                self.balance += self.position * current_price
                self.position = 0
                reward = 1  # Reward for profit realization

        elif action == 2:  # Buy
            buy_amount = self.balance * 0.1  # Use 10% of balance per trade
            self.position += buy_amount / current_price
            self.balance -= buy_amount
            reward = -1  # Small penalty for taking risk

        self.current_step += 1
        done = self.current_step >= 200  # End episode after 200 steps

        return self._next_observation(), reward, done, {}

    def render(self):
        """
        Displays the current trading state.
        """
        logging.info(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Position: {self.position:.4f}")


def train_rl_model():
    """
    Trains a reinforcement learning model for autonomous trading.
    """
    env = TradingEnv()
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=50000)  # Train for 50,000 steps
    model.save("ppo_trading_model")

    logging.info("✅ Reinforcement Learning Model Trained and Saved!")


def trade_with_rl():
    """
    Runs an RL-based trading strategy in live mode.
    """
    env = TradingEnv()
    model = PPO.load("ppo_trading_model")

    obs = env.reset()
    for _ in range(200):  # Trade for 200 steps
        action, _states = model.predict(obs)
        obs, reward, done, _ = env.step(action)
        env.render()
        if done:
            break


# Example Usage
if __name__ == "__main__":
    train_rl_model()
    trade_with_rl()
