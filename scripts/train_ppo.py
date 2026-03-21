#!/usr/bin/env python3
"""
Train Bruce AI - PPO Reinforcement Learning for Trading
Uses stable_baselines3 PPO with a custom Gymnasium trading environment.
Falls back to a simple Q-learning implementation if SB3 is unavailable.
"""

import argparse
import json
import os
import sys
import time
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "market")
os.makedirs(MODELS_DIR, exist_ok=True)


def load_price_data(symbol: str) -> np.ndarray:
    """Load price data from CSV or generate synthetic data."""
    csv_name = symbol.replace("/", "_") + "_1d.csv"
    csv_path = os.path.join(DATA_DIR, csv_name)

    if os.path.exists(csv_path):
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            if "close" in df.columns:
                return df["close"].values
        except ImportError:
            pass

    # Generate synthetic price data
    print("  Generating synthetic price data...")
    np.random.seed(42)
    n = 2000
    returns = np.random.normal(0.0002, 0.02, n)
    prices = np.zeros(n)
    prices[0] = 40000.0 if "BTC" in symbol else 2000.0
    for i in range(1, n):
        prices[i] = prices[i - 1] * (1 + returns[i])
    return prices


def compute_indicators(prices: np.ndarray) -> dict:
    """Compute technical indicators from price series."""
    # RSI
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    window = 14
    avg_gain = np.convolve(gains, np.ones(window) / window, mode="valid")
    avg_loss = np.convolve(losses, np.ones(window) / window, mode="valid")
    avg_loss[avg_loss == 0] = 1e-10
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    # Simple Moving Averages
    sma_20 = np.convolve(prices, np.ones(20) / 20, mode="valid")
    sma_50 = np.convolve(prices, np.ones(50) / 50, mode="valid")

    return {"rsi": rsi, "sma_20": sma_20, "sma_50": sma_50}


# ---------------------------------------------------------------------------
#  Simple Q-Learning Fallback
# ---------------------------------------------------------------------------

class SimpleQLearningTrader:
    """Tabular Q-learning trader as fallback when SB3 is unavailable."""

    def __init__(self, n_states: int = 100, n_actions: int = 3, lr: float = 0.1, gamma: float = 0.99):
        self.n_states = n_states
        self.n_actions = n_actions  # 0=hold, 1=buy, 2=sell
        self.lr = lr
        self.gamma = gamma
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.q_table = np.zeros((n_states, n_actions))

    def _discretize_state(self, price_change: float, rsi: float, position: int) -> int:
        """Map continuous state to discrete bucket."""
        pc_bucket = min(max(int((price_change + 0.1) / 0.2 * 10), 0), 9)
        rsi_bucket = min(int(rsi / 10), 9)
        pos_part = 0 if position == 0 else 1
        return pc_bucket * 10 + rsi_bucket  # simplified

    def choose_action(self, state: int) -> int:
        if np.random.random() < self.epsilon:
            return np.random.randint(self.n_actions)
        return int(np.argmax(self.q_table[state]))

    def update(self, state: int, action: int, reward: float, next_state: int, done: bool):
        target = reward + (0 if done else self.gamma * np.max(self.q_table[next_state]))
        self.q_table[state, action] += self.lr * (target - self.q_table[state, action])
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def train(self, prices: np.ndarray, episodes: int = 1000) -> list:
        """Train the Q-learning agent on price data."""
        indicators = compute_indicators(prices)
        rsi = indicators["rsi"]
        min_idx = 60  # need look-back for indicators
        max_idx = min(len(prices), len(rsi) + 14) - 1
        episode_rewards = []

        for ep in range(episodes):
            start_idx = np.random.randint(min_idx, max_idx - 100)
            balance = 10000.0
            position = 0.0
            entry_price = 0.0
            total_reward = 0.0

            for t in range(100):
                idx = start_idx + t
                if idx >= max_idx:
                    break

                price = prices[idx]
                price_change = (prices[idx] - prices[idx - 1]) / prices[idx - 1]
                rsi_val = rsi[min(idx - 14, len(rsi) - 1)] if idx - 14 < len(rsi) else 50.0

                state = self._discretize_state(price_change, rsi_val, int(position > 0))
                action = self.choose_action(state)

                # Execute action
                reward = 0.0
                if action == 1 and position == 0:  # Buy
                    position = balance / price
                    entry_price = price
                    balance = 0.0
                elif action == 2 and position > 0:  # Sell
                    balance = position * price
                    pnl = (price - entry_price) / entry_price
                    reward = pnl * 100  # scale reward
                    position = 0.0
                    entry_price = 0.0

                # Next state
                next_idx = idx + 1
                if next_idx < max_idx:
                    next_pc = (prices[next_idx] - prices[next_idx - 1]) / prices[next_idx - 1]
                    next_rsi = rsi[min(next_idx - 14, len(rsi) - 1)] if next_idx - 14 < len(rsi) else 50.0
                    next_state = self._discretize_state(next_pc, next_rsi, int(position > 0))
                else:
                    next_state = state

                done = (t == 99) or (next_idx >= max_idx)
                self.update(state, action, reward, next_state, done)
                total_reward += reward

            # Close any open position
            if position > 0:
                final_price = prices[min(start_idx + 99, max_idx - 1)]
                total_reward += ((final_price - entry_price) / entry_price) * 100

            episode_rewards.append(total_reward)

            if (ep + 1) % max(1, episodes // 10) == 0:
                avg = np.mean(episode_rewards[-100:])
                print(f"  Episode {ep + 1}/{episodes} | Avg Reward (last 100): {avg:.2f} | Epsilon: {self.epsilon:.3f}")

        return episode_rewards

    def save(self, path: str):
        np.save(path, self.q_table)
        print(f"  Q-table saved to {path}")


# ---------------------------------------------------------------------------
#  PPO Training with stable_baselines3
# ---------------------------------------------------------------------------

def train_with_sb3(prices: np.ndarray, episodes: int, symbol: str) -> list:
    """Train using stable_baselines3 PPO."""
    from training.trading_env import TradingEnvironment

    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.vec_env import DummyVecEnv
    except ImportError:
        raise ImportError("stable_baselines3 not available")

    env = DummyVecEnv([lambda: TradingEnvironment(prices)])
    total_timesteps = episodes * 200  # approximate steps per episode

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01,
    )

    print(f"\n  Training PPO for {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps)

    save_path = os.path.join(MODELS_DIR, "ppo_trading.zip")
    model.save(save_path)
    print(f"  Model saved to {save_path}")

    # Evaluate
    eval_env = TradingEnvironment(prices)
    episode_rewards = []
    for _ in range(20):
        obs, _ = eval_env.reset()
        total_reward = 0
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, _ = eval_env.step(action)
            total_reward += reward
            done = terminated or truncated
        episode_rewards.append(total_reward)

    return episode_rewards


# ---------------------------------------------------------------------------
#  Plot Results
# ---------------------------------------------------------------------------

def plot_rewards(rewards: list, output_path: str):
    """Plot training reward curve."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        ax1.plot(rewards, alpha=0.3, color="blue", label="Episode Reward")
        # Moving average
        window = min(50, len(rewards) // 5) if len(rewards) > 10 else 1
        if window > 1:
            ma = np.convolve(rewards, np.ones(window) / window, mode="valid")
            ax1.plot(range(window - 1, len(rewards)), ma, color="red", label=f"MA({window})")
        ax1.set_xlabel("Episode")
        ax1.set_ylabel("Reward")
        ax1.set_title("Training Rewards")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        ax2.hist(rewards, bins=30, color="steelblue", edgecolor="black", alpha=0.7)
        ax2.axvline(np.mean(rewards), color="red", linestyle="--", label=f"Mean: {np.mean(rewards):.2f}")
        ax2.set_xlabel("Reward")
        ax2.set_ylabel("Frequency")
        ax2.set_title("Reward Distribution")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        print(f"  Reward plot saved to {output_path}")
    except ImportError:
        print("  matplotlib not available, skipping plot.")


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Train PPO trading agent for Bruce AI")
    parser.add_argument("--episodes", type=int, default=1000, help="Number of training episodes")
    parser.add_argument("--symbol", type=str, default="BTC/USDT", help="Trading pair symbol")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Bruce AI - PPO Trading Training")
    print(f"  Symbol: {args.symbol}")
    print(f"  Episodes: {args.episodes}")
    print(f"{'='*60}\n")

    prices = load_price_data(args.symbol)
    print(f"  Price data: {len(prices)} data points")
    print(f"  Price range: {prices.min():.2f} - {prices.max():.2f}")

    start_time = time.time()

    # Try SB3 PPO first, fallback to Q-learning
    try:
        print("\n  Attempting stable_baselines3 PPO training...")
        rewards = train_with_sb3(prices, args.episodes, args.symbol)
        method = "PPO (stable_baselines3)"
    except (ImportError, Exception) as e:
        print(f"  SB3 not available ({e}), using Q-learning fallback...\n")
        agent = SimpleQLearningTrader()
        rewards = agent.train(prices, episodes=args.episodes)
        q_path = os.path.join(MODELS_DIR, "q_trading.npy")
        agent.save(q_path)
        method = "Q-Learning (fallback)"

    elapsed = time.time() - start_time

    # Plot results
    plot_path = os.path.join(MODELS_DIR, "training_rewards.png")
    plot_rewards(rewards, plot_path)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Training Complete!")
    print(f"  Method: {method}")
    print(f"  Duration: {elapsed:.1f}s")
    print(f"  Episodes: {len(rewards)}")
    print(f"  Mean Reward: {np.mean(rewards):.4f}")
    print(f"  Max Reward: {np.max(rewards):.4f}")
    print(f"  Min Reward: {np.min(rewards):.4f}")
    print(f"  Std Reward: {np.std(rewards):.4f}")
    print(f"{'='*60}\n")

    # Save training metadata
    meta = {
        "symbol": args.symbol,
        "method": method,
        "episodes": len(rewards),
        "duration_s": round(elapsed, 1),
        "mean_reward": round(float(np.mean(rewards)), 4),
        "max_reward": round(float(np.max(rewards)), 4),
        "min_reward": round(float(np.min(rewards)), 4),
        "trained_at": datetime.utcnow().isoformat(),
    }
    meta_path = os.path.join(MODELS_DIR, "ppo_training_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  Metadata saved to {meta_path}")


if __name__ == "__main__":
    main()
