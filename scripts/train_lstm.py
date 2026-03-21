#!/usr/bin/env python3
"""
Train Bruce AI - LSTM Price Predictor
Trains an LSTM neural network for price prediction.
Falls back to simple linear regression if Keras/TensorFlow is unavailable.
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
                print(f"  Loaded {len(df)} rows from {csv_path}")
                return df["close"].values
        except ImportError:
            pass

    # Generate synthetic data
    print("  Generating synthetic price data...")
    np.random.seed(42)
    n = 1000
    base = 40000.0 if "BTC" in symbol else 2000.0
    returns = np.random.normal(0.0003, 0.02, n)
    prices = np.zeros(n)
    prices[0] = base
    for i in range(1, n):
        prices[i] = prices[i - 1] * (1 + returns[i])
    return prices


def create_sequences(data: np.ndarray, look_back: int = 60):
    """Create sliding window sequences for time series prediction."""
    X, y = [], []
    for i in range(look_back, len(data)):
        X.append(data[i - look_back:i])
        y.append(data[i])
    return np.array(X), np.array(y)


def normalize_data(data: np.ndarray):
    """Min-max normalize data. Returns normalized data, min, max."""
    d_min = data.min()
    d_max = data.max()
    if d_max - d_min == 0:
        return data, d_min, d_max
    return (data - d_min) / (d_max - d_min), d_min, d_max


def denormalize(data: np.ndarray, d_min: float, d_max: float) -> np.ndarray:
    """Reverse min-max normalization."""
    return data * (d_max - d_min) + d_min


# ---------------------------------------------------------------------------
#  Simple Linear Regression Fallback
# ---------------------------------------------------------------------------

class SimpleLinearPredictor:
    """Multi-feature linear regression as fallback for LSTM."""

    def __init__(self, look_back: int = 60):
        self.look_back = look_back
        self.weights = None
        self.bias = 0.0

    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 50, lr: float = 0.001):
        """Train using gradient descent."""
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0.0
        losses = []

        for epoch in range(epochs):
            predictions = X @ self.weights + self.bias
            errors = predictions - y
            loss = np.mean(errors ** 2)
            losses.append(loss)

            # Gradient descent
            grad_w = (2 / n_samples) * (X.T @ errors)
            grad_b = (2 / n_samples) * np.sum(errors)
            self.weights -= lr * grad_w
            self.bias -= lr * grad_b

            if (epoch + 1) % max(1, epochs // 10) == 0:
                print(f"    Epoch {epoch + 1}/{epochs} | MSE: {loss:.6f}")

        return losses

    def predict(self, X: np.ndarray) -> np.ndarray:
        return X @ self.weights + self.bias

    def save(self, path: str):
        np.savez(path, weights=self.weights, bias=self.bias, look_back=self.look_back)
        print(f"  Model saved to {path}")


# ---------------------------------------------------------------------------
#  LSTM Training with Keras/TensorFlow
# ---------------------------------------------------------------------------

def train_with_keras(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    epochs: int,
    look_back: int,
) -> tuple:
    """Train LSTM using Keras."""
    try:
        os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"
        from tensorflow import keras
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        from tensorflow.keras.callbacks import EarlyStopping
    except ImportError:
        try:
            from keras.models import Sequential
            from keras.layers import LSTM, Dense, Dropout
            from keras.callbacks import EarlyStopping
        except ImportError:
            raise ImportError("Neither tensorflow.keras nor standalone keras is available")

    # Reshape for LSTM: (samples, timesteps, features)
    X_train_r = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
    X_test_r = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))

    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=(look_back, 1)),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(16, activation="relu"),
        Dense(1),
    ])

    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    model.summary()

    early_stop = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)

    history = model.fit(
        X_train_r, y_train,
        epochs=epochs,
        batch_size=32,
        validation_data=(X_test_r, y_test),
        callbacks=[early_stop],
        verbose=1,
    )

    # Predictions
    train_pred = model.predict(X_train_r).flatten()
    test_pred = model.predict(X_test_r).flatten()

    # Save model
    save_path = os.path.join(MODELS_DIR, "lstm_predictor.h5")
    model.save(save_path)
    print(f"  Model saved to {save_path}")

    return train_pred, test_pred, history.history, "LSTM (Keras)"


# ---------------------------------------------------------------------------
#  Plot Results
# ---------------------------------------------------------------------------

def plot_predictions(
    y_test_actual: np.ndarray,
    y_test_pred: np.ndarray,
    y_train_actual: np.ndarray,
    y_train_pred: np.ndarray,
    output_path: str,
):
    """Plot predictions vs actual values."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))

        # Training predictions
        axes[0, 0].plot(y_train_actual, label="Actual", alpha=0.7)
        axes[0, 0].plot(y_train_pred, label="Predicted", alpha=0.7)
        axes[0, 0].set_title("Training Set: Predictions vs Actual")
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Test predictions
        axes[0, 1].plot(y_test_actual, label="Actual", alpha=0.7)
        axes[0, 1].plot(y_test_pred, label="Predicted", alpha=0.7)
        axes[0, 1].set_title("Test Set: Predictions vs Actual")
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)

        # Scatter plot
        axes[1, 0].scatter(y_test_actual, y_test_pred, alpha=0.5, s=10)
        min_val = min(y_test_actual.min(), y_test_pred.min())
        max_val = max(y_test_actual.max(), y_test_pred.max())
        axes[1, 0].plot([min_val, max_val], [min_val, max_val], "r--", label="Perfect prediction")
        axes[1, 0].set_xlabel("Actual")
        axes[1, 0].set_ylabel("Predicted")
        axes[1, 0].set_title("Prediction Scatter (Test Set)")
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)

        # Error distribution
        errors = y_test_pred - y_test_actual
        axes[1, 1].hist(errors, bins=30, color="steelblue", edgecolor="black", alpha=0.7)
        axes[1, 1].axvline(0, color="red", linestyle="--")
        axes[1, 1].set_xlabel("Prediction Error")
        axes[1, 1].set_ylabel("Frequency")
        axes[1, 1].set_title(f"Error Distribution (Mean: {errors.mean():.4f})")
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close()
        print(f"  Plot saved to {output_path}")
    except ImportError:
        print("  matplotlib not available, skipping plot.")


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Train LSTM price predictor for Bruce AI")
    parser.add_argument("--symbol", type=str, default="BTC/USDT", help="Trading pair symbol")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--look-back", type=int, default=60, help="Look-back window in days")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Bruce AI - LSTM Price Predictor Training")
    print(f"  Symbol: {args.symbol}")
    print(f"  Epochs: {args.epochs}")
    print(f"  Look-back: {args.look_back} days")
    print(f"{'='*60}\n")

    # Load and prepare data
    prices = load_price_data(args.symbol)
    print(f"  Price data: {len(prices)} data points")

    normalized, d_min, d_max = normalize_data(prices)
    X, y = create_sequences(normalized, look_back=args.look_back)
    print(f"  Sequences created: {X.shape[0]} samples, {X.shape[1]} timesteps")

    # Train/test split (80/20)
    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]
    print(f"  Train: {len(X_train)} | Test: {len(X_test)}")

    start_time = time.time()

    # Try Keras LSTM first, then fallback to linear regression
    try:
        print("\n  Attempting Keras LSTM training...")
        train_pred, test_pred, history, method = train_with_keras(
            X_train, y_train, X_test, y_test, args.epochs, args.look_back
        )
    except (ImportError, Exception) as e:
        print(f"  Keras not available ({e}), using linear regression fallback...\n")
        model = SimpleLinearPredictor(look_back=args.look_back)
        losses = model.fit(X_train, y_train, epochs=args.epochs)
        train_pred = model.predict(X_train)
        test_pred = model.predict(X_test)
        model.save(os.path.join(MODELS_DIR, "linear_predictor.npz"))
        method = "Linear Regression (fallback)"

    elapsed = time.time() - start_time

    # Denormalize for plotting
    y_train_actual = denormalize(y_train, d_min, d_max)
    y_test_actual = denormalize(y_test, d_min, d_max)
    train_pred_actual = denormalize(train_pred, d_min, d_max)
    test_pred_actual = denormalize(test_pred, d_min, d_max)

    # Metrics
    test_mse = np.mean((y_test - test_pred) ** 2)
    test_mae = np.mean(np.abs(y_test - test_pred))
    test_rmse = np.sqrt(test_mse)
    # Directional accuracy
    actual_dir = np.diff(y_test_actual) > 0
    pred_dir = np.diff(test_pred_actual) > 0
    dir_accuracy = np.mean(actual_dir == pred_dir) if len(actual_dir) > 0 else 0

    # Plot
    plot_path = os.path.join(MODELS_DIR, "lstm_predictions.png")
    plot_predictions(y_test_actual, test_pred_actual, y_train_actual, train_pred_actual, plot_path)

    # Summary
    print(f"\n{'='*60}")
    print(f"  Training Complete!")
    print(f"  Method: {method}")
    print(f"  Duration: {elapsed:.1f}s")
    print(f"  Test MSE (normalized): {test_mse:.6f}")
    print(f"  Test MAE (normalized): {test_mae:.6f}")
    print(f"  Test RMSE (normalized): {test_rmse:.6f}")
    print(f"  Directional Accuracy: {dir_accuracy:.2%}")
    print(f"{'='*60}\n")

    # Save metadata
    meta = {
        "symbol": args.symbol,
        "method": method,
        "epochs": args.epochs,
        "look_back": args.look_back,
        "duration_s": round(elapsed, 1),
        "test_mse": round(float(test_mse), 6),
        "test_mae": round(float(test_mae), 6),
        "test_rmse": round(float(test_rmse), 6),
        "directional_accuracy": round(float(dir_accuracy), 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "trained_at": datetime.utcnow().isoformat(),
    }
    meta_path = os.path.join(MODELS_DIR, "lstm_training_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  Metadata saved to {meta_path}")


if __name__ == "__main__":
    main()
