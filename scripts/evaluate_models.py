#!/usr/bin/env python3
"""
Bruce AI - Model Evaluation Script
Loads trained models, runs backtests, compares performance, and generates reports.
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "market")
EVAL_DIR = os.path.join(PROJECT_ROOT, "data", "evaluations")
os.makedirs(EVAL_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
#  Data Loading
# ---------------------------------------------------------------------------

def load_test_data(symbol: str = "BTC_USDT", timeframe: str = "1d") -> np.ndarray:
    """Load test price data."""
    csv_path = os.path.join(DATA_DIR, f"{symbol}_{timeframe}.csv")
    if os.path.exists(csv_path):
        try:
            import pandas as pd
            df = pd.read_csv(csv_path)
            if "close" in df.columns:
                prices = df["close"].values
                # Use last 20% as test data
                split = int(len(prices) * 0.8)
                return prices[split:]
        except ImportError:
            # Manual CSV reading
            with open(csv_path, "r") as f:
                reader = csv.DictReader(f)
                closes = [float(row["close"]) for row in reader if "close" in row]
            if closes:
                split = int(len(closes) * 0.8)
                return np.array(closes[split:])

    # Generate synthetic test data
    np.random.seed(99)
    n = 200
    base = 40000.0 if "BTC" in symbol else 2000.0
    returns = np.random.normal(0.0001, 0.02, n)
    prices = np.zeros(n)
    prices[0] = base
    for i in range(1, n):
        prices[i] = prices[i - 1] * (1 + returns[i])
    return prices


# ---------------------------------------------------------------------------
#  Backtest Strategies
# ---------------------------------------------------------------------------

def backtest_buy_hold(prices: np.ndarray) -> dict:
    """Buy and hold benchmark strategy."""
    returns = (prices[-1] - prices[0]) / prices[0]
    daily_returns = np.diff(prices) / prices[:-1]
    sharpe = np.mean(daily_returns) / (np.std(daily_returns) + 1e-10) * np.sqrt(252)

    # Max drawdown
    peak = prices[0]
    max_dd = 0
    for p in prices:
        if p > peak:
            peak = p
        dd = (peak - p) / peak
        if dd > max_dd:
            max_dd = dd

    return {
        "strategy": "Buy & Hold",
        "total_return": round(returns * 100, 2),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(max_dd * 100, 2),
        "win_rate": round((np.sum(daily_returns > 0) / len(daily_returns)) * 100, 1),
        "n_trades": 1,
        "avg_trade_return": round(returns * 100, 2),
    }


def backtest_sma_crossover(prices: np.ndarray, fast: int = 10, slow: int = 30) -> dict:
    """Simple SMA crossover strategy."""
    if len(prices) < slow + 1:
        return {"strategy": f"SMA({fast}/{slow})", "total_return": 0, "sharpe_ratio": 0,
                "max_drawdown": 0, "win_rate": 0, "n_trades": 0, "avg_trade_return": 0}

    fast_sma = np.convolve(prices, np.ones(fast) / fast, mode="valid")
    slow_sma = np.convolve(prices, np.ones(slow) / slow, mode="valid")

    # Align
    offset = slow - fast
    fast_sma = fast_sma[offset:]
    min_len = min(len(fast_sma), len(slow_sma))
    fast_sma = fast_sma[:min_len]
    slow_sma = slow_sma[:min_len]
    aligned_prices = prices[slow - 1:slow - 1 + min_len]

    # Signals
    position = 0
    balance = 10000
    entry_price = 0
    trades = []
    equity = [balance]

    for i in range(1, min_len):
        if fast_sma[i] > slow_sma[i] and fast_sma[i - 1] <= slow_sma[i - 1] and position == 0:
            position = balance / aligned_prices[i]
            entry_price = aligned_prices[i]
            balance = 0
        elif fast_sma[i] < slow_sma[i] and fast_sma[i - 1] >= slow_sma[i - 1] and position > 0:
            balance = position * aligned_prices[i]
            trade_ret = (aligned_prices[i] - entry_price) / entry_price
            trades.append(trade_ret)
            position = 0

        current_equity = balance + position * aligned_prices[i]
        equity.append(current_equity)

    # Close final position
    if position > 0:
        balance = position * aligned_prices[-1]
        trade_ret = (aligned_prices[-1] - entry_price) / entry_price
        trades.append(trade_ret)

    final_equity = balance if balance > 0 else equity[-1]
    total_return = (final_equity - 10000) / 10000

    equity = np.array(equity)
    daily_ret = np.diff(equity) / equity[:-1]
    sharpe = np.mean(daily_ret) / (np.std(daily_ret) + 1e-10) * np.sqrt(252)

    peak = equity[0]
    max_dd = 0
    for e in equity:
        if e > peak:
            peak = e
        dd = (peak - e) / peak
        if dd > max_dd:
            max_dd = dd

    win_rate = (sum(1 for t in trades if t > 0) / len(trades) * 100) if trades else 0
    avg_trade = (sum(trades) / len(trades) * 100) if trades else 0

    return {
        "strategy": f"SMA({fast}/{slow})",
        "total_return": round(total_return * 100, 2),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(max_dd * 100, 2),
        "win_rate": round(win_rate, 1),
        "n_trades": len(trades),
        "avg_trade_return": round(avg_trade, 2),
    }


def backtest_rsi_strategy(prices: np.ndarray, period: int = 14, oversold: float = 30, overbought: float = 70) -> dict:
    """RSI mean-reversion strategy."""
    if len(prices) < period + 2:
        return {"strategy": f"RSI({period})", "total_return": 0, "sharpe_ratio": 0,
                "max_drawdown": 0, "win_rate": 0, "n_trades": 0, "avg_trade_return": 0}

    # Compute RSI
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    rsi = np.full(len(prices), 50.0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi[i + 1] = 100
        else:
            rsi[i + 1] = 100 - (100 / (1 + avg_gain / avg_loss))

    position = 0
    balance = 10000
    entry_price = 0
    trades = []
    equity = [balance]

    for i in range(period + 1, len(prices)):
        if rsi[i] < oversold and position == 0:
            position = balance / prices[i]
            entry_price = prices[i]
            balance = 0
        elif rsi[i] > overbought and position > 0:
            balance = position * prices[i]
            trade_ret = (prices[i] - entry_price) / entry_price
            trades.append(trade_ret)
            position = 0

        current_equity = balance + position * prices[i]
        equity.append(current_equity)

    if position > 0:
        balance = position * prices[-1]
        trades.append((prices[-1] - entry_price) / entry_price)

    final_equity = balance if balance > 0 else equity[-1]
    total_return = (final_equity - 10000) / 10000

    equity = np.array(equity)
    daily_ret = np.diff(equity) / equity[:-1]
    sharpe = np.mean(daily_ret) / (np.std(daily_ret) + 1e-10) * np.sqrt(252)

    peak = equity[0]
    max_dd = 0
    for e in equity:
        if e > peak:
            peak = e
        dd = (peak - e) / peak
        if dd > max_dd:
            max_dd = dd

    win_rate = (sum(1 for t in trades if t > 0) / len(trades) * 100) if trades else 0
    avg_trade = (sum(trades) / len(trades) * 100) if trades else 0

    return {
        "strategy": f"RSI({period})",
        "total_return": round(total_return * 100, 2),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(max_dd * 100, 2),
        "win_rate": round(win_rate, 1),
        "n_trades": len(trades),
        "avg_trade_return": round(avg_trade, 2),
    }


def backtest_ppo_model(prices: np.ndarray) -> dict:
    """Evaluate PPO model if available."""
    ppo_path = os.path.join(MODELS_DIR, "ppo_trading.zip")
    q_path = os.path.join(MODELS_DIR, "q_trading.npy")

    if os.path.exists(ppo_path):
        try:
            from stable_baselines3 import PPO
            from training.trading_env import TradingEnvironment

            model = PPO.load(ppo_path)
            env = TradingEnvironment(prices)
            obs, _ = env.reset()
            total_reward = 0
            done = False
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)
                total_reward += reward
                done = terminated or truncated

            return {
                "strategy": "PPO (SB3)",
                "total_return": round(total_reward, 2),
                "sharpe_ratio": round(info.get("sharpe", 0), 4),
                "max_drawdown": round(info.get("max_drawdown", 0) * 100, 2),
                "win_rate": round(info.get("win_rate", 0) * 100, 1),
                "n_trades": info.get("n_trades", 0),
                "avg_trade_return": round(info.get("avg_trade_return", 0) * 100, 2),
            }
        except Exception as e:
            print(f"    PPO model load failed: {e}")

    if os.path.exists(q_path):
        return {
            "strategy": "Q-Learning",
            "total_return": 0,
            "sharpe_ratio": 0,
            "max_drawdown": 0,
            "win_rate": 0,
            "n_trades": 0,
            "avg_trade_return": 0,
            "note": "Q-learning model found but backtest not implemented for tabular model",
        }

    return None


def backtest_lstm_model(prices: np.ndarray) -> dict:
    """Evaluate LSTM prediction model if available."""
    lstm_path = os.path.join(MODELS_DIR, "lstm_predictor.h5")
    linear_path = os.path.join(MODELS_DIR, "linear_predictor.npz")

    model_name = None
    predictions = None

    if os.path.exists(lstm_path):
        try:
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
            from tensorflow.keras.models import load_model
            model = load_model(lstm_path)
            model_name = "LSTM"

            # Prepare sequences
            look_back = 60
            d_min, d_max = prices.min(), prices.max()
            norm = (prices - d_min) / (d_max - d_min + 1e-10)
            X = []
            for i in range(look_back, len(norm)):
                X.append(norm[i - look_back:i])
            X = np.array(X).reshape(-1, look_back, 1)
            predictions = model.predict(X).flatten()
            predictions = predictions * (d_max - d_min) + d_min
        except Exception as e:
            print(f"    LSTM model load failed: {e}")

    if predictions is None and os.path.exists(linear_path):
        try:
            data = np.load(linear_path)
            weights = data["weights"]
            bias = float(data["bias"])
            look_back = int(data["look_back"])
            model_name = "Linear Regression"

            d_min, d_max = prices.min(), prices.max()
            norm = (prices - d_min) / (d_max - d_min + 1e-10)
            X = []
            for i in range(look_back, len(norm)):
                X.append(norm[i - look_back:i])
            X = np.array(X)
            pred_norm = X @ weights + bias
            predictions = pred_norm * (d_max - d_min) + d_min
        except Exception as e:
            print(f"    Linear model load failed: {e}")

    if predictions is None:
        return None

    # Use predictions for a simple trading strategy: buy if predicted up, sell if down
    actual = prices[60:60 + len(predictions)] if len(prices) > 60 + len(predictions) else prices[-len(predictions):]
    if len(actual) != len(predictions):
        actual = actual[:len(predictions)]

    balance = 10000
    position = 0
    trades = []
    entry_price = 0
    equity = [balance]

    for i in range(1, len(predictions)):
        predicted_dir = predictions[i] > actual[i - 1]  # predicts up
        if predicted_dir and position == 0:
            position = balance / actual[i]
            entry_price = actual[i]
            balance = 0
        elif not predicted_dir and position > 0:
            balance = position * actual[i]
            trades.append((actual[i] - entry_price) / entry_price)
            position = 0
        equity.append(balance + position * actual[i])

    if position > 0:
        balance = position * actual[-1]
        trades.append((actual[-1] - entry_price) / entry_price)

    final = balance if balance > 0 else equity[-1]
    total_return = (final - 10000) / 10000

    equity = np.array(equity)
    daily_ret = np.diff(equity) / (equity[:-1] + 1e-10)
    sharpe = np.mean(daily_ret) / (np.std(daily_ret) + 1e-10) * np.sqrt(252)

    peak = equity[0]
    max_dd = 0
    for e in equity:
        if e > peak:
            peak = e
        dd = (peak - e) / (peak + 1e-10)
        if dd > max_dd:
            max_dd = dd

    # Directional accuracy
    if len(predictions) > 1 and len(actual) > 1:
        pred_dir = np.diff(predictions) > 0
        actual_dir = np.diff(actual[:len(predictions)]) > 0
        min_len = min(len(pred_dir), len(actual_dir))
        dir_acc = np.mean(pred_dir[:min_len] == actual_dir[:min_len]) * 100
    else:
        dir_acc = 0

    win_rate = (sum(1 for t in trades if t > 0) / len(trades) * 100) if trades else 0
    avg_trade = (sum(trades) / len(trades) * 100) if trades else 0

    return {
        "strategy": f"{model_name} Predictor",
        "total_return": round(total_return * 100, 2),
        "sharpe_ratio": round(sharpe, 4),
        "max_drawdown": round(max_dd * 100, 2),
        "win_rate": round(win_rate, 1),
        "n_trades": len(trades),
        "avg_trade_return": round(avg_trade, 2),
        "directional_accuracy": round(dir_acc, 1),
    }


# ---------------------------------------------------------------------------
#  Report Generation
# ---------------------------------------------------------------------------

def print_comparison_table(results: list):
    """Print formatted comparison table."""
    print(f"\n  {'Strategy':<25} {'Return %':<12} {'Sharpe':<10} {'Max DD %':<10} "
          f"{'Win Rate %':<12} {'Trades':<8} {'Avg Trade %':<12}")
    print(f"  {'-'*89}")

    for r in sorted(results, key=lambda x: x["total_return"], reverse=True):
        print(f"  {r['strategy']:<25} {r['total_return']:<12} {r['sharpe_ratio']:<10} "
              f"{r['max_drawdown']:<10} {r['win_rate']:<12} {r['n_trades']:<8} "
              f"{r['avg_trade_return']:<12}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate all Bruce AI trading models")
    parser.add_argument("--symbol", type=str, default="BTC_USDT", help="Symbol for test data")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Bruce AI - Model Evaluation")
    print(f"  Symbol: {args.symbol}")
    print(f"{'='*60}\n")

    # Load test data
    prices = load_test_data(args.symbol)
    print(f"  Test data: {len(prices)} data points")
    print(f"  Price range: {prices.min():.2f} - {prices.max():.2f}\n")

    results = []
    start_time = time.time()

    # Benchmark strategies
    print("  Running backtests...")

    print("    Buy & Hold...", end=" ")
    results.append(backtest_buy_hold(prices))
    print("done")

    print("    SMA(10/30) Crossover...", end=" ")
    results.append(backtest_sma_crossover(prices, 10, 30))
    print("done")

    print("    SMA(20/50) Crossover...", end=" ")
    results.append(backtest_sma_crossover(prices, 20, 50))
    print("done")

    print("    RSI(14) Mean Reversion...", end=" ")
    results.append(backtest_rsi_strategy(prices))
    print("done")

    # ML Models
    print("    PPO/Q-Learning Model...", end=" ")
    ppo_result = backtest_ppo_model(prices)
    if ppo_result:
        results.append(ppo_result)
        print("done")
    else:
        print("not found")

    print("    LSTM/Linear Predictor...", end=" ")
    lstm_result = backtest_lstm_model(prices)
    if lstm_result:
        results.append(lstm_result)
        print("done")
    else:
        print("not found")

    elapsed = time.time() - start_time

    # Print comparison table
    print(f"\n{'='*95}")
    print(f"  PERFORMANCE COMPARISON")
    print(f"{'='*95}")
    print_comparison_table(results)

    # Best strategy
    best = max(results, key=lambda x: x.get("sharpe_ratio", 0))
    print(f"\n  Best by Sharpe Ratio: {best['strategy']} (Sharpe: {best['sharpe_ratio']})")
    best_ret = max(results, key=lambda x: x.get("total_return", 0))
    print(f"  Best by Return: {best_ret['strategy']} (Return: {best_ret['total_return']}%)")

    print(f"\n  Evaluation completed in {elapsed:.1f}s")

    # Save results
    report = {
        "symbol": args.symbol,
        "test_data_points": len(prices),
        "evaluated_at": datetime.utcnow().isoformat(),
        "duration_s": round(elapsed, 1),
        "results": results,
        "best_sharpe": best["strategy"],
        "best_return": best_ret["strategy"],
    }

    report_path = os.path.join(EVAL_DIR, "model_evaluation.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Report saved to {report_path}")

    # CSV export
    csv_path = os.path.join(EVAL_DIR, "model_comparison.csv")
    if results:
        keys = list(results[0].keys())
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(results)
        print(f"  CSV saved to {csv_path}")

    print()


if __name__ == "__main__":
    main()
