import numpy as np
import tensorflow as tf
import gym
import gym.spaces
import time
import requests
import logging
from stable_baselines3 import PPO, A2C, DQN, TD3, SAC
from collections import deque
from app.utils.database import DatabaseManager
from app.modules.machine_learning.predictive_model import PredictiveModel

# Logger Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# AI Model Components
db_manager = DatabaseManager()
predictive_model = PredictiveModel()

# API Endpoints for Market Data
ORDER_BOOK_API = "http://localhost:8000/api/order-book"
TRADE_EXEC_API = "http://localhost:8000/api/order"


class HFTTradingEnv(gym.Env):
    """
    High-Frequency Trading (HFT) AI Environment with AI-Based Order Book Manipulation Detection.
    """

    def __init__(self):
        super(HFTTradingEnv, self).__init__()

        # Action Space: 0 = Sell, 1 = Hold, 2 = Buy
        self.action_space = gym.spaces.Discrete(3)

        # Observation Space: Order book imbalance, latency spreads, AI prediction confidence
        self.observation_space = gym.spaces.Box(low=-1, high=1, shape=(6,), dtype=np.float32)

        # Latency & Trade Execution History
        self.execution_latency = deque(maxlen=100)
        self.order_book_history = deque(maxlen=500)
        self.last_trade_time = time.time()
        self.position = 0
        self.balance = 100000

    def reset(self):
        """
        Resets the AI trading environment.
        """
        self.execution_latency.clear()
        self.order_book_history.clear()
        self.last_trade_time = time.time()
        self.position = 0
        self.balance = 100000
        return self._next_observation()

    def _fetch_order_book(self):
        """
        Fetches real-time order book data from the API.
        """
        try:
            response = requests.get(ORDER_BOOK_API)
            if response.status_code == 200:
                data = response.json()
                return data["order_book"]
        except Exception as e:
            logging.error(f"❌ Order Book API Error: {e}")
        return None

    def _detect_manipulation(self, order_book):
        """
        Uses AI to detect order book manipulation (spoofing, layering, wash trading).
        """
        bid_sizes = [order["size"] for order in order_book["bids"][:5]]
        ask_sizes = [order["size"] for order in order_book["asks"][:5]]

        bid_imbalance = np.mean(bid_sizes) - np.mean(ask_sizes)

        # AI detection for spoofing (large order cancellations before execution)
        spoofing_detected = np.abs(bid_imbalance) > 5  # Arbitrary threshold
        return spoofing_detected

    def _next_observation(self):
        """
        Generates the next AI input based on order book and AI price predictions.
        """
        order_book = self._fetch_order_book()
        ai_prediction = predictive_model.predict()

        if order_book is None:
            return np.zeros(6)

        # Manipulation detection
        manipulation_flag = 1 if self._detect_manipulation(order_book) else 0

        return np.array([
            order_book["bids"][0]["price"] - order_book["asks"][0]["price"],  # Spread
            order_book["bids"][0]["size"] / order_book["asks"][0]["size"],  # Order book imbalance
            ai_prediction["confidence"],  # AI prediction confidence
            ai_prediction["price_trend"],  # AI-predicted trend direction
            self.balance / 100000,  # Normalized balance
            manipulation_flag  # AI-detected spoofing flag
        ], dtype=np.float32)

    def step(self, action):
        """
        Executes an AI-based high-frequency trade.
        """
        order_size = self.balance * 0.1  # Trade 10% of balance
        order_side = "BUY" if action == 2 else "SELL"

        if action != 1:  # Not holding
            trade_response = requests.post(TRADE_EXEC_API, json={"side": order_side, "amount": order_size, "price": 0})
            execution_time = time.time() - self.last_trade_time
            self.execution_latency.append(execution_time)

        self.last_trade_time = time.time()
        self.current_step += 1
        done = self.current_step >= 200
        reward = -np.mean(self.execution_latency)  # Penalize latency

        return self._next_observation(), reward, done, {}

    def render(self):
        """
        Displays trade execution data.
        """
        logging.info(f"🔍 Execution Latency: {np.mean(self.execution_latency):.4f}s")


def train_hft_ai():
    """
    Trains the HFT AI using Reinforcement Learning.
    """
    env = HFTTradingEnv()
    model = TD3("MlpPolicy", env, verbose=1)  # Using TD3 for HFT speed
    model.learn(total_timesteps=100000)
    model.save("hft_ai_model")

    logging.info("✅ HFT AI Model Trained and Saved!")


def trade_with_hft_ai():
    """
    Runs the trained HFT AI in live trading mode.
    """
    env = HFTTradingEnv()
    model = TD3.load("hft_ai_model")

    obs = env.reset()
    for _ in range(500):  # Trade for 500 steps
        action, _states = model.predict(obs)
        obs, reward, done, _ = env.step(action)
        env.render()
        if done:
            break


# Example Usage
if __name__ == "__main__":
    train_hft_ai()
    trade_with_hft_ai()
