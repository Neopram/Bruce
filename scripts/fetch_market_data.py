#!/usr/bin/env python3
"""
Bruce AI - Market Data Fetching Pipeline
Fetches OHLCV data using ccxt, calculates technical indicators, and saves to CSV.
Falls back to synthetic data generation if ccxt is unavailable.
"""

import argparse
import csv
import math
import os
import sys
import time
from datetime import datetime, timedelta

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "market")
os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
#  Technical Indicators
# ---------------------------------------------------------------------------

def compute_rsi(closes: np.ndarray, period: int = 14) -> np.ndarray:
    """Compute Relative Strength Index."""
    rsi = np.full(len(closes), np.nan)
    if len(closes) < period + 1:
        return rsi

    deltas = np.diff(closes)
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
            rs = avg_gain / avg_loss
            rsi[i + 1] = 100 - (100 / (1 + rs))

    return rsi


def compute_sma(data: np.ndarray, period: int) -> np.ndarray:
    """Compute Simple Moving Average."""
    sma = np.full(len(data), np.nan)
    for i in range(period - 1, len(data)):
        sma[i] = np.mean(data[i - period + 1:i + 1])
    return sma


def compute_ema(data: np.ndarray, period: int) -> np.ndarray:
    """Compute Exponential Moving Average."""
    ema = np.full(len(data), np.nan)
    if len(data) < period:
        return ema
    multiplier = 2 / (period + 1)
    ema[period - 1] = np.mean(data[:period])
    for i in range(period, len(data)):
        ema[i] = (data[i] - ema[i - 1]) * multiplier + ema[i - 1]
    return ema


def compute_macd(closes: np.ndarray) -> tuple:
    """Compute MACD line, signal line, and histogram."""
    ema12 = compute_ema(closes, 12)
    ema26 = compute_ema(closes, 26)
    macd_line = ema12 - ema26
    signal = compute_ema(macd_line[~np.isnan(macd_line)], 9)

    # Align signal with macd
    full_signal = np.full(len(closes), np.nan)
    non_nan_start = np.where(~np.isnan(macd_line))[0]
    if len(non_nan_start) > 0 and len(signal) > 0:
        start = non_nan_start[0]
        sig_start = np.where(~np.isnan(signal))[0]
        if len(sig_start) > 0:
            offset = start + sig_start[0]
            valid_signal = signal[~np.isnan(signal)]
            end = min(offset + len(valid_signal), len(full_signal))
            full_signal[offset:end] = valid_signal[:end - offset]

    histogram = macd_line - full_signal
    return macd_line, full_signal, histogram


def compute_bollinger_bands(closes: np.ndarray, period: int = 20, std_dev: float = 2.0) -> tuple:
    """Compute Bollinger Bands."""
    sma = compute_sma(closes, period)
    upper = np.full(len(closes), np.nan)
    lower = np.full(len(closes), np.nan)

    for i in range(period - 1, len(closes)):
        std = np.std(closes[i - period + 1:i + 1])
        upper[i] = sma[i] + std_dev * std
        lower[i] = sma[i] - std_dev * std

    return upper, sma, lower


def add_indicators(ohlcv: list) -> list:
    """Add technical indicators to OHLCV data."""
    closes = np.array([row[4] for row in ohlcv])  # close prices
    highs = np.array([row[2] for row in ohlcv])
    lows = np.array([row[3] for row in ohlcv])

    rsi = compute_rsi(closes)
    sma_20 = compute_sma(closes, 20)
    sma_50 = compute_sma(closes, 50)
    ema_12 = compute_ema(closes, 12)
    macd_line, macd_signal, macd_hist = compute_macd(closes)
    bb_upper, bb_mid, bb_lower = compute_bollinger_bands(closes)

    enriched = []
    for i, row in enumerate(ohlcv):
        enriched.append(list(row) + [
            round(rsi[i], 2) if not np.isnan(rsi[i]) else "",
            round(sma_20[i], 2) if not np.isnan(sma_20[i]) else "",
            round(sma_50[i], 2) if not np.isnan(sma_50[i]) else "",
            round(ema_12[i], 2) if not np.isnan(ema_12[i]) else "",
            round(macd_line[i], 4) if not np.isnan(macd_line[i]) else "",
            round(macd_signal[i], 4) if not np.isnan(macd_signal[i]) else "",
            round(macd_hist[i], 4) if not np.isnan(macd_hist[i]) else "",
            round(bb_upper[i], 2) if not np.isnan(bb_upper[i]) else "",
            round(bb_mid[i], 2) if not np.isnan(bb_mid[i]) else "",
            round(bb_lower[i], 2) if not np.isnan(bb_lower[i]) else "",
        ])

    return enriched


# ---------------------------------------------------------------------------
#  Data Fetching
# ---------------------------------------------------------------------------

INDICATOR_HEADERS = [
    "rsi_14", "sma_20", "sma_50", "ema_12",
    "macd", "macd_signal", "macd_hist",
    "bb_upper", "bb_mid", "bb_lower",
]

OHLCV_HEADERS = ["timestamp", "open", "high", "low", "close", "volume"]


def fetch_with_ccxt(symbol: str, timeframe: str, days: int) -> list:
    """Fetch OHLCV data using ccxt."""
    import ccxt

    exchange = ccxt.binance({"enableRateLimit": True})
    since = exchange.parse8601((datetime.utcnow() - timedelta(days=days)).isoformat())
    all_data = []
    limit = 1000

    print(f"    Fetching from Binance...")
    while True:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        if not ohlcv:
            break
        all_data.extend(ohlcv)
        since = ohlcv[-1][0] + 1
        if len(ohlcv) < limit:
            break
        time.sleep(exchange.rateLimit / 1000)

    # Convert timestamps to ISO strings
    for row in all_data:
        row[0] = datetime.utcfromtimestamp(row[0] / 1000).strftime("%Y-%m-%d %H:%M:%S")

    return all_data


def generate_synthetic_ohlcv(symbol: str, timeframe: str, days: int) -> list:
    """Generate synthetic OHLCV data."""
    np.random.seed(hash(symbol) % 2**31)

    # Determine number of candles and base price
    tf_hours = {"1h": 1, "4h": 4, "1d": 24}
    hours = tf_hours.get(timeframe, 24)
    n_candles = (days * 24) // hours

    base_prices = {"BTC": 42000, "ETH": 2500, "SOL": 100, "BNB": 300}
    base = 30000
    for key, val in base_prices.items():
        if key in symbol:
            base = val
            break

    # Generate prices with realistic dynamics
    dt = hours / 24  # fraction of day
    daily_vol = 0.03
    vol = daily_vol * math.sqrt(dt)
    drift = 0.0001 * dt

    prices = np.zeros(n_candles)
    prices[0] = base

    for i in range(1, n_candles):
        ret = drift + vol * np.random.randn()
        prices[i] = prices[i - 1] * (1 + ret)

    # Build OHLCV
    start_time = datetime.utcnow() - timedelta(hours=hours * n_candles)
    data = []

    for i in range(n_candles):
        ts = (start_time + timedelta(hours=hours * i)).strftime("%Y-%m-%d %H:%M:%S")
        close = prices[i]
        # Simulate intra-candle movement
        intra_vol = vol * 0.5
        o = close * (1 + np.random.randn() * intra_vol)
        h = max(o, close) * (1 + abs(np.random.randn()) * intra_vol * 0.5)
        l = min(o, close) * (1 - abs(np.random.randn()) * intra_vol * 0.5)
        v = abs(np.random.randn()) * base * 100 + base * 10

        data.append([
            ts,
            round(o, 2),
            round(h, 2),
            round(l, 2),
            round(close, 2),
            round(v, 2),
        ])

    return data


def save_csv(data: list, headers: list, filepath: str):
    """Save data to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(data)


# ---------------------------------------------------------------------------
#  Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Fetch market data for Bruce AI training")
    parser.add_argument("--pairs", type=str, default="BTC/USDT,ETH/USDT,SOL/USDT",
                        help="Comma-separated trading pairs")
    parser.add_argument("--timeframe", type=str, default="1d",
                        help="Candle timeframe: 1h, 4h, 1d")
    parser.add_argument("--days", type=int, default=365,
                        help="Number of days of history")
    args = parser.parse_args()

    pairs = [p.strip() for p in args.pairs.split(",")]

    print(f"\n{'='*60}")
    print(f"  Bruce AI - Market Data Pipeline")
    print(f"  Pairs: {', '.join(pairs)}")
    print(f"  Timeframe: {args.timeframe}")
    print(f"  Days: {args.days}")
    print(f"{'='*60}\n")

    total_rows = 0

    for pair in pairs:
        print(f"  [{pair}] Fetching {args.timeframe} data for {args.days} days...")
        start = time.time()

        try:
            data = fetch_with_ccxt(pair, args.timeframe, args.days)
            source = "ccxt/binance"
        except Exception as e:
            print(f"    ccxt failed ({e}), generating synthetic data...")
            data = generate_synthetic_ohlcv(pair, args.timeframe, args.days)
            source = "synthetic"

        print(f"    Retrieved {len(data)} candles from {source}")

        # Save raw OHLCV
        filename = pair.replace("/", "_") + f"_{args.timeframe}.csv"
        raw_path = os.path.join(DATA_DIR, filename)
        save_csv(data, OHLCV_HEADERS, raw_path)
        print(f"    Raw data saved to {raw_path}")

        # Add indicators and save enriched version
        enriched = add_indicators(data)
        enriched_filename = pair.replace("/", "_") + f"_{args.timeframe}_indicators.csv"
        enriched_path = os.path.join(DATA_DIR, enriched_filename)
        save_csv(enriched, OHLCV_HEADERS + INDICATOR_HEADERS, enriched_path)

        elapsed = time.time() - start
        total_rows += len(data)
        print(f"    Indicators saved to {enriched_path} ({elapsed:.1f}s)\n")

    print(f"{'='*60}")
    print(f"  Pipeline Complete!")
    print(f"  Total candles fetched: {total_rows}")
    print(f"  Output directory: {DATA_DIR}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
