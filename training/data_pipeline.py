"""
Data Pipeline for Bruce AI Training
Handles loading, preprocessing, feature engineering, and batching of market data.
"""

import csv
import os
from typing import Optional, Tuple

import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "market")


# ---------------------------------------------------------------------------
#  Data Loading
# ---------------------------------------------------------------------------

def load_market_data(
    symbol: str = "BTC_USDT",
    timeframe: str = "1d",
    data_dir: Optional[str] = None,
) -> dict:
    """
    Load market data from CSV file.

    Args:
        symbol: Trading pair (e.g., 'BTC_USDT')
        timeframe: Candle timeframe (e.g., '1h', '4h', '1d')
        data_dir: Override default data directory

    Returns:
        Dict with keys: timestamp, open, high, low, close, volume (all np.ndarray)
    """
    directory = data_dir or DATA_DIR
    filename = f"{symbol}_{timeframe}.csv"
    filepath = os.path.join(directory, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Market data not found: {filepath}")

    timestamps = []
    opens = []
    highs = []
    lows = []
    closes = []
    volumes = []

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamps.append(row.get("timestamp", ""))
            opens.append(float(row.get("open", 0)))
            highs.append(float(row.get("high", 0)))
            lows.append(float(row.get("low", 0)))
            closes.append(float(row.get("close", 0)))
            volumes.append(float(row.get("volume", 0)))

    return {
        "timestamp": np.array(timestamps),
        "open": np.array(opens),
        "high": np.array(highs),
        "low": np.array(lows),
        "close": np.array(closes),
        "volume": np.array(volumes),
    }


# ---------------------------------------------------------------------------
#  Feature Engineering
# ---------------------------------------------------------------------------

def prepare_features(data: dict) -> np.ndarray:
    """
    Add technical indicator features to market data.

    Args:
        data: Dict with OHLCV arrays (from load_market_data)

    Returns:
        2D numpy array of shape (n_samples, n_features) with columns:
        [close, returns, log_returns, rsi_14, sma_20, sma_50, ema_12, ema_26,
         macd, bb_upper, bb_lower, bb_width, volume_sma, atr_14]
    """
    close = data["close"]
    high = data["high"]
    low = data["low"]
    volume = data["volume"]
    n = len(close)

    # Returns
    returns = np.zeros(n)
    returns[1:] = np.diff(close) / close[:-1]

    log_returns = np.zeros(n)
    log_returns[1:] = np.log(close[1:] / close[:-1])

    # RSI (14)
    rsi = _compute_rsi(close, 14)

    # SMAs
    sma_20 = _compute_sma(close, 20)
    sma_50 = _compute_sma(close, 50)

    # EMAs
    ema_12 = _compute_ema(close, 12)
    ema_26 = _compute_ema(close, 26)

    # MACD
    macd = ema_12 - ema_26

    # Bollinger Bands
    bb_upper, bb_lower, bb_width = _compute_bollinger(close, 20)

    # Volume SMA
    volume_sma = _compute_sma(volume, 20)

    # ATR (14)
    atr = _compute_atr(high, low, close, 14)

    features = np.column_stack([
        close, returns, log_returns, rsi, sma_20, sma_50,
        ema_12, ema_26, macd, bb_upper, bb_lower, bb_width,
        volume_sma, atr,
    ])

    return features


def _compute_rsi(prices: np.ndarray, period: int) -> np.ndarray:
    """Compute RSI indicator."""
    rsi = np.full(len(prices), 50.0)
    if len(prices) < period + 1:
        return rsi

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi[i + 1] = 100.0
        else:
            rsi[i + 1] = 100 - (100 / (1 + avg_gain / avg_loss))

    return rsi


def _compute_sma(data: np.ndarray, period: int) -> np.ndarray:
    """Compute Simple Moving Average."""
    sma = np.full(len(data), np.nan)
    for i in range(period - 1, len(data)):
        sma[i] = np.mean(data[i - period + 1:i + 1])
    # Fill leading NaNs with first valid value
    first_valid = sma[period - 1] if period - 1 < len(sma) else 0
    sma[:period - 1] = first_valid
    return sma


def _compute_ema(data: np.ndarray, period: int) -> np.ndarray:
    """Compute Exponential Moving Average."""
    ema = np.zeros(len(data))
    if len(data) == 0:
        return ema
    ema[0] = data[0]
    mult = 2.0 / (period + 1)
    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i - 1]) * mult + ema[i - 1]
    return ema


def _compute_bollinger(
    prices: np.ndarray, period: int = 20, std_mult: float = 2.0
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute Bollinger Bands."""
    n = len(prices)
    upper = np.full(n, np.nan)
    lower = np.full(n, np.nan)
    width = np.zeros(n)

    for i in range(period - 1, n):
        window = prices[i - period + 1:i + 1]
        mean = np.mean(window)
        std = np.std(window)
        upper[i] = mean + std_mult * std
        lower[i] = mean - std_mult * std
        width[i] = (2 * std_mult * std) / (mean + 1e-10)

    # Fill leading NaNs
    if period - 1 < n:
        upper[:period - 1] = upper[period - 1]
        lower[:period - 1] = lower[period - 1]

    return upper, lower, width


def _compute_atr(
    high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14
) -> np.ndarray:
    """Compute Average True Range."""
    n = len(close)
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]

    for i in range(1, n):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )

    atr = np.zeros(n)
    if n >= period:
        atr[period - 1] = np.mean(tr[:period])
        for i in range(period, n):
            atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        atr[:period - 1] = atr[period - 1]

    return atr


# ---------------------------------------------------------------------------
#  Sequence Creation
# ---------------------------------------------------------------------------

def create_sequences(
    data: np.ndarray,
    look_back: int = 60,
    target_col: int = 0,
    target_offset: int = 1,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Create time series sequences for supervised learning.

    Args:
        data: 2D array of shape (n_samples, n_features) or 1D price array
        look_back: Number of historical steps per sequence
        target_col: Column index to use as prediction target
        target_offset: How many steps ahead to predict

    Returns:
        X: (n_sequences, look_back, n_features) or (n_sequences, look_back)
        y: (n_sequences,) target values
    """
    if data.ndim == 1:
        data = data.reshape(-1, 1)
        target_col = 0

    n_samples = len(data)
    X, y = [], []

    for i in range(look_back, n_samples - target_offset + 1):
        X.append(data[i - look_back:i])
        y.append(data[i + target_offset - 1, target_col])

    X = np.array(X)
    y = np.array(y)

    # Squeeze if single feature
    if X.shape[-1] == 1:
        X = X.squeeze(-1)

    return X, y


# ---------------------------------------------------------------------------
#  Train/Test Split
# ---------------------------------------------------------------------------

def train_test_split(
    data: np.ndarray,
    ratio: float = 0.8,
    shuffle: bool = False,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Split data into train and test sets.

    Args:
        data: Array to split (first dimension is samples)
        ratio: Fraction for training set
        shuffle: Whether to shuffle before splitting (False for time series)

    Returns:
        train_data, test_data
    """
    n = len(data)
    split_idx = int(n * ratio)

    if shuffle:
        indices = np.random.permutation(n)
        return data[indices[:split_idx]], data[indices[split_idx:]]

    return data[:split_idx], data[split_idx:]


# ---------------------------------------------------------------------------
#  Normalization
# ---------------------------------------------------------------------------

def normalize(
    data: np.ndarray,
    method: str = "minmax",
    params: Optional[dict] = None,
) -> Tuple[np.ndarray, dict]:
    """
    Normalize data.

    Args:
        data: Array to normalize
        method: 'minmax' for [0,1] scaling, 'zscore' for standard scaling
        params: Pre-computed normalization params (for applying to test data)

    Returns:
        normalized_data, normalization_params (for inverse transform)
    """
    if method == "minmax":
        if params is None:
            if data.ndim == 1:
                d_min = data.min()
                d_max = data.max()
            else:
                d_min = data.min(axis=0)
                d_max = data.max(axis=0)
            params = {"min": d_min, "max": d_max, "method": "minmax"}

        d_range = params["max"] - params["min"]
        if isinstance(d_range, np.ndarray):
            d_range[d_range == 0] = 1.0
        elif d_range == 0:
            d_range = 1.0

        normalized = (data - params["min"]) / d_range
        return normalized, params

    elif method == "zscore":
        if params is None:
            if data.ndim == 1:
                mean = data.mean()
                std = data.std()
            else:
                mean = data.mean(axis=0)
                std = data.std(axis=0)
            params = {"mean": mean, "std": std, "method": "zscore"}

        std = params["std"]
        if isinstance(std, np.ndarray):
            std[std == 0] = 1.0
        elif std == 0:
            std = 1.0

        normalized = (data - params["mean"]) / std
        return normalized, params

    else:
        raise ValueError(f"Unknown normalization method: {method}")


def denormalize(data: np.ndarray, params: dict) -> np.ndarray:
    """
    Reverse normalization using saved params.

    Args:
        data: Normalized array
        params: Normalization params from normalize()

    Returns:
        Original-scale data
    """
    method = params.get("method", "minmax")

    if method == "minmax":
        d_range = params["max"] - params["min"]
        if isinstance(d_range, np.ndarray):
            d_range[d_range == 0] = 1.0
        elif d_range == 0:
            d_range = 1.0
        return data * d_range + params["min"]

    elif method == "zscore":
        std = params["std"]
        if isinstance(std, np.ndarray):
            std[std == 0] = 1.0
        elif std == 0:
            std = 1.0
        return data * std + params["mean"]

    else:
        raise ValueError(f"Unknown normalization method: {method}")


# ---------------------------------------------------------------------------
#  DataLoader for Batch Iteration
# ---------------------------------------------------------------------------

class DataLoader:
    """
    Iterator that yields batches of data for training.

    Usage:
        loader = DataLoader(X_train, y_train, batch_size=32, shuffle=True)
        for epoch in range(n_epochs):
            for X_batch, y_batch in loader:
                # train on batch
                pass
    """

    def __init__(
        self,
        X: np.ndarray,
        y: np.ndarray,
        batch_size: int = 32,
        shuffle: bool = True,
        drop_last: bool = False,
    ):
        """
        Args:
            X: Feature array
            y: Target array
            batch_size: Samples per batch
            shuffle: Shuffle data each iteration
            drop_last: Drop last incomplete batch
        """
        assert len(X) == len(y), "X and y must have same length"
        self.X = X
        self.y = y
        self.batch_size = batch_size
        self.shuffle = shuffle
        self.drop_last = drop_last
        self.n_samples = len(X)
        self.n_batches = self.n_samples // batch_size
        if not drop_last and self.n_samples % batch_size != 0:
            self.n_batches += 1

    def __len__(self) -> int:
        return self.n_batches

    def __iter__(self):
        indices = np.arange(self.n_samples)
        if self.shuffle:
            np.random.shuffle(indices)

        for i in range(0, self.n_samples, self.batch_size):
            batch_idx = indices[i:i + self.batch_size]

            if self.drop_last and len(batch_idx) < self.batch_size:
                break

            yield self.X[batch_idx], self.y[batch_idx]
