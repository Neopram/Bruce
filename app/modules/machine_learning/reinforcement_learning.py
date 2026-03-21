import logging
import asyncio
import numpy as np
import aiohttp
import gymnasium as gym
from stable_baselines3 import PPO, DQN
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import BaseCallback
from app.config.settings import Config

# Logger configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
MAX_RETRIES = 3
TRADE_ACTIONS = ["HOLD", "BUY", "SELL"]
DEFAULT_STATE_SIZE = 10  # Default empty state representation

class CustomCallback(BaseCallback):
    """
    Custom callback to log training steps and monitor performance.
    """

    def __init__(self, verbose=0):
        super(CustomCallback, self).__init__(verbose)

    def _on_step(self) -> bool:
        if self.num_timesteps % 1000 == 0:
            logging.info(f"📈 RL Training Step: {self.num_timesteps}")
        return True

class ReinforcementLearningAgent:
    """
    AI-powered Reinforcement Learning Agent for algorithmic trading.
    """

    def __init__(self, env_name="TradingEnv-v1", model_type="PPO", model_file="ppo_trading_model.zip"):
        """
        Initializes the RL agent with a PPO or DQN-based model.
        """
        self.env_name = env_name
        self.model_type = model_type
        self.model_file = model_file
        self.env = self._create_env()
        self.model = None
        self._initialize_model()

    def _create_env(self):
        """
        Creates a trading environment.
        """
        try:
            env = gym.make(self.env_name)
        except gym.error.Error:
            logging.warning(f"⚠️ Environment '{self.env_name}' not found. Using fallback 'CartPole-v1'.")
            env = gym.make("CartPole-v1")
        return DummyVecEnv([lambda: env])

    def _initialize_model(self):
        """
        Initializes the RL model using PPO or DQN.
        """
        if self.model_type == "PPO":
            self.model = PPO("MlpPolicy", self.env, verbose=1)
        elif self.model_type == "DQN":
            self.model = DQN("MlpPolicy", self.env, verbose=1)
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}. Use 'PPO' or 'DQN'.")

    async def fetch_live_order_book(self):
        """
        Retrieves real-time order book data from OKX.
        """
        endpoint = f"https://www.okx.com/api/v5/market/books?instId={Config.TRADING_PAIR.replace('/', '-')}&sz=5"
        return await self._fetch_market_data(endpoint)

    async def _fetch_market_data(self, endpoint):
        """
        Fetches real-time market data asynchronously.
        """
        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint) as response:
                        response.raise_for_status()
                        return await response.json()
            except aiohttp.ClientError as e:
                logging.error(f"🚨 API Request Failed: {e} (Attempt {attempt + 1}/{MAX_RETRIES})")
                await asyncio.sleep(2)
        return {}

    async def process_market_data(self):
        """
        Converts live market data into AI-friendly feature vectors.
        """
        market_data = await self.fetch_live_order_book()
        if not market_data or "data" not in market_data:
            return np.zeros(DEFAULT_STATE_SIZE)
        bids = [float(order[0]) for order in market_data["data"][0]["bids"][:5]]
        asks = [float(order[0]) for order in market_data["data"][0]["asks"][:5]]
        return np.array(bids + asks)

    def train(self, timesteps=100000):
        """
        Trains the RL model on a simulated environment.
        """
        if self.model is None:
            logging.error("❌ Model not initialized. Cannot train.")
            return
        logging.info(f"🚀 Starting RL training on {self.env_name} for {timesteps} steps...")
        self.model.learn(total_timesteps=timesteps, callback=CustomCallback())
        self.save_model()
        logging.info("✅ Training completed and model saved successfully.")

    def save_model(self):
        """
        Saves the trained model.
        """
        if self.model:
            self.model.save(self.model_file)
            logging.info(f"📁 Model saved at {self.model_file}.")
        else:
            logging.error("❌ Cannot save model. No trained model found.")

    def load_model(self):
        """
        Loads a previously trained model.
        """
        try:
            if self.model_type == "PPO":
                self.model = PPO.load(self.model_file, env=self.env)
            elif self.model_type == "DQN":
                self.model = DQN.load(self.model_file, env=self.env)
            logging.info("✅ Reinforcement learning model loaded successfully.")
        except FileNotFoundError:
            logging.error("🚨 Model file not found. Please train the model first.")
            self.model = None

    async def predict_trade_action(self):
        """
        Uses the RL model to predict an optimal trading action.
        """
        if self.model is None:
            logging.error("❌ No trained model found. Train or load a model first.")
            return None
        state = await self.process_market_data()
        action_index = self.model.predict(state, deterministic=True)[0]
        action = TRADE_ACTIONS[action_index]
        logging.info(f"🔮 Predicted Trade Action: {action}")
        return action

if __name__ == "__main__":
    agent = ReinforcementLearningAgent(model_type="PPO")
    agent.train(timesteps=100000)
    agent.save_model()
    agent.load_model()
    asyncio.run(agent.predict_trade_action())
