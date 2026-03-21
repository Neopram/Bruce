"""
Quantitative trading strategies module.
Implements momentum, mean reversion, pairs trading,
and statistical arbitrage strategies.
"""
import math
import random
from datetime import datetime


class QuantStrategy:
    """Suite of quantitative trading strategies."""

    def __init__(self):
        self.signal_history = []

    def momentum_signal(self, prices, lookback=10, threshold=0.0):
        """Generate momentum signal based on price trend.

        Args:
            prices: List of historical prices (most recent last).
            lookback: Number of periods to look back.
            threshold: Minimum return to trigger signal.
        """
        if len(prices) < max(lookback, 2):
            return {"signal": "HOLD", "reason": "insufficient_data"}

        recent = prices[-lookback:]
        returns = (recent[-1] - recent[0]) / recent[0]
        short_momentum = (prices[-1] - prices[-3]) / prices[-3] if len(prices) >= 3 else 0
        avg_price = sum(recent) / len(recent)
        price_vs_avg = (prices[-1] - avg_price) / avg_price

        if returns > threshold and short_momentum > 0:
            signal = "BUY"
            strength = min(1.0, abs(returns) * 10)
        elif returns < -threshold and short_momentum < 0:
            signal = "SELL"
            strength = min(1.0, abs(returns) * 10)
        else:
            signal = "HOLD"
            strength = 0

        result = {
            "signal": signal,
            "strength": round(strength, 3),
            "momentum_return": round(returns, 6),
            "short_momentum": round(short_momentum, 6),
            "price_vs_avg": round(price_vs_avg, 6),
            "lookback": lookback,
        }
        self.signal_history.append({"strategy": "momentum", **result, "timestamp": datetime.utcnow().isoformat()})
        return result

    def mean_reversion(self, prices, window=20, z_threshold=2.0):
        """Mean reversion strategy based on z-score of price vs moving average.

        Args:
            prices: List of historical prices.
            window: Moving average window.
            z_threshold: Z-score threshold for signals.
        """
        if len(prices) < window:
            return {"signal": "HOLD", "reason": "insufficient_data"}

        recent = prices[-window:]
        mean = sum(recent) / len(recent)
        variance = sum((p - mean) ** 2 for p in recent) / len(recent)
        std = math.sqrt(variance) if variance > 0 else 1e-8

        z_score = (prices[-1] - mean) / std
        spread = abs(z_score)

        if z_score > z_threshold:
            signal = "SELL"  # Overbought, expect reversion down
        elif z_score < -z_threshold:
            signal = "BUY"  # Oversold, expect reversion up
        else:
            signal = "HOLD"

        result = {
            "signal": signal,
            "z_score": round(z_score, 4),
            "spread": round(spread, 4),
            "moving_avg": round(mean, 4),
            "std_dev": round(std, 4),
            "current_price": prices[-1],
            "window": window,
        }
        self.signal_history.append({"strategy": "mean_reversion", **result, "timestamp": datetime.utcnow().isoformat()})
        return result

    def cointegration_entry(self, prices_a, prices_b, z_threshold=2.0, hedge_ratio=None):
        """Pairs trading based on cointegration spread.

        Args:
            prices_a: Prices of asset A.
            prices_b: Prices of asset B.
            z_threshold: Entry z-score threshold.
            hedge_ratio: Optional hedge ratio (auto-calculated if None).
        """
        if len(prices_a) < 10 or len(prices_b) < 10:
            return {"signal": "WAIT", "reason": "insufficient_data"}

        min_len = min(len(prices_a), len(prices_b))
        a = prices_a[-min_len:]
        b = prices_b[-min_len:]

        if hedge_ratio is None:
            mean_a = sum(a) / len(a)
            mean_b = sum(b) / len(b)
            hedge_ratio = mean_a / mean_b if mean_b != 0 else 1.0

        spread = [a[i] - hedge_ratio * b[i] for i in range(min_len)]
        spread_mean = sum(spread) / len(spread)
        spread_var = sum((s - spread_mean) ** 2 for s in spread) / len(spread)
        spread_std = math.sqrt(spread_var) if spread_var > 0 else 1e-8

        z_score = (spread[-1] - spread_mean) / spread_std

        if z_score > z_threshold:
            signal = "ENTER SHORT"  # Short A, Long B
            action = {"asset_a": "SELL", "asset_b": "BUY"}
        elif z_score < -z_threshold:
            signal = "ENTER LONG"  # Long A, Short B
            action = {"asset_a": "BUY", "asset_b": "SELL"}
        elif abs(z_score) < 0.5:
            signal = "EXIT"  # Close positions
            action = {"asset_a": "CLOSE", "asset_b": "CLOSE"}
        else:
            signal = "WAIT"
            action = {"asset_a": "HOLD", "asset_b": "HOLD"}

        result = {
            "signal": signal,
            "z_score": round(z_score, 4),
            "hedge_ratio": round(hedge_ratio, 4),
            "spread_current": round(spread[-1], 4),
            "spread_mean": round(spread_mean, 4),
            "spread_std": round(spread_std, 4),
            "action": action,
        }
        self.signal_history.append({"strategy": "pairs_trading", **result, "timestamp": datetime.utcnow().isoformat()})
        return result

    def stat_arb_basket(self, assets_prices, lookback=30):
        """Statistical arbitrage across a basket of assets.

        Args:
            assets_prices: Dict of {asset_name: [prices]}.
            lookback: Lookback period.
        """
        if not assets_prices:
            return {"signals": {}, "message": "No assets provided"}

        signals = {}
        returns = {}

        for name, prices in assets_prices.items():
            if len(prices) < lookback:
                signals[name] = {"signal": "HOLD", "reason": "insufficient_data"}
                continue

            recent = prices[-lookback:]
            ret = (recent[-1] - recent[0]) / recent[0]
            returns[name] = ret

        if not returns:
            return {"signals": signals}

        avg_return = sum(returns.values()) / len(returns)

        for name, ret in returns.items():
            deviation = ret - avg_return
            if deviation > 0.02:
                signals[name] = {"signal": "SELL", "deviation": round(deviation, 4),
                                 "return": round(ret, 4), "reason": "outperformer_reversion"}
            elif deviation < -0.02:
                signals[name] = {"signal": "BUY", "deviation": round(deviation, 4),
                                 "return": round(ret, 4), "reason": "underperformer_catch_up"}
            else:
                signals[name] = {"signal": "HOLD", "deviation": round(deviation, 4),
                                 "return": round(ret, 4)}

        return {
            "signals": signals,
            "basket_avg_return": round(avg_return, 6),
            "n_assets": len(assets_prices),
            "lookback": lookback,
        }

    def get_signal_history(self, strategy=None, limit=30):
        """Return recent signal history, optionally filtered by strategy."""
        if strategy:
            filtered = [s for s in self.signal_history if s.get("strategy") == strategy]
            return filtered[-limit:]
        return self.signal_history[-limit:]
