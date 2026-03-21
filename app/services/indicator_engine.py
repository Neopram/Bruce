"""
Technical Indicator Engine - Full library of technical indicators with a
unified calculation interface and signal aggregation.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple


class IndicatorEngine:
    """Calculates technical indicators and aggregates signals."""

    # ------------------------------------------------------------------
    # Individual indicators
    # ------------------------------------------------------------------

    def compute_sma(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Simple Moving Average."""
        return prices.rolling(window=period).mean()

    def compute_ema(self, prices: pd.Series, period: int = 20) -> pd.Series:
        """Exponential Moving Average."""
        return prices.ewm(span=period, adjust=False).mean()

    def compute_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def compute_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
    ) -> Dict[str, pd.Series]:
        """MACD with signal line and histogram."""
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    def bollinger_bands(
        self, prices: pd.Series, window: int = 20, std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands - returns (sma, upper, lower)."""
        sma = prices.rolling(window).mean()
        rstd = prices.rolling(window).std()
        upper = sma + std_dev * rstd
        lower = sma - std_dev * rstd
        return sma, upper, lower

    def compute_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
    ) -> pd.Series:
        """Average True Range."""
        prev_close = close.shift(1)
        tr = pd.concat(
            [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
            axis=1,
        ).max(axis=1)
        return tr.rolling(window=period).mean()

    def compute_stochastic(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        k_period: int = 14,
        d_period: int = 3,
    ) -> Dict[str, pd.Series]:
        """Stochastic Oscillator (%K and %D)."""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d = k.rolling(window=d_period).mean()
        return {"k": k, "d": d}

    def compute_obv(self, close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume."""
        direction = np.sign(close.diff())
        obv = (volume * direction).fillna(0).cumsum()
        return obv

    # ------------------------------------------------------------------
    # Unified interface
    # ------------------------------------------------------------------

    def calculate(
        self,
        indicator_name: str,
        data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Unified calculation interface.

        Parameters
        ----------
        indicator_name : str
            One of: sma, ema, rsi, macd, bollinger, atr, stochastic, obv
        data : pd.DataFrame
            Must contain at least a 'close' column. For ATR/Stochastic also
            needs 'high' and 'low'. For OBV also needs 'volume'.
        params : dict, optional
            Indicator-specific parameters (period, std_dev, etc.)
        """
        params = params or {}
        name = indicator_name.lower().replace(" ", "_")

        dispatch = {
            "sma": lambda: self.compute_sma(data["close"], **params),
            "ema": lambda: self.compute_ema(data["close"], **params),
            "rsi": lambda: self.compute_rsi(data["close"], **params),
            "macd": lambda: self.compute_macd(data["close"], **params),
            "bollinger": lambda: self.bollinger_bands(data["close"], **params),
            "bollinger_bands": lambda: self.bollinger_bands(data["close"], **params),
            "atr": lambda: self.compute_atr(data["high"], data["low"], data["close"], **params),
            "stochastic": lambda: self.compute_stochastic(data["high"], data["low"], data["close"], **params),
            "obv": lambda: self.compute_obv(data["close"], data["volume"]),
        }

        if name not in dispatch:
            raise ValueError(f"Unknown indicator: {indicator_name}. Available: {list(dispatch.keys())}")

        return dispatch[name]()

    # ------------------------------------------------------------------
    # Signal aggregation
    # ------------------------------------------------------------------

    def get_all_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run all applicable indicators on *data* and return a summary
        with individual signals and an aggregated recommendation.

        Expects columns: close. Optional: high, low, volume.
        """
        signals: Dict[str, Any] = {}
        close = data["close"]
        last_close = close.iloc[-1]

        # SMA
        sma20 = self.compute_sma(close, 20)
        signals["sma_20"] = {
            "value": round(float(sma20.iloc[-1]), 4) if not pd.isna(sma20.iloc[-1]) else None,
            "signal": "bullish" if last_close > (sma20.iloc[-1] or 0) else "bearish",
        }

        # EMA
        ema20 = self.compute_ema(close, 20)
        signals["ema_20"] = {
            "value": round(float(ema20.iloc[-1]), 4),
            "signal": "bullish" if last_close > ema20.iloc[-1] else "bearish",
        }

        # RSI
        rsi = self.compute_rsi(close)
        rsi_val = rsi.iloc[-1]
        if not pd.isna(rsi_val):
            if rsi_val > 70:
                rsi_signal = "overbought"
            elif rsi_val < 30:
                rsi_signal = "oversold"
            else:
                rsi_signal = "neutral"
            signals["rsi"] = {"value": round(float(rsi_val), 2), "signal": rsi_signal}

        # MACD
        macd = self.compute_macd(close)
        macd_val = macd["macd"].iloc[-1]
        sig_val = macd["signal"].iloc[-1]
        if not pd.isna(macd_val):
            signals["macd"] = {
                "macd": round(float(macd_val), 4),
                "signal_line": round(float(sig_val), 4),
                "signal": "bullish" if macd_val > sig_val else "bearish",
            }

        # Bollinger Bands
        sma_bb, upper, lower = self.bollinger_bands(close)
        if not pd.isna(upper.iloc[-1]):
            if last_close > upper.iloc[-1]:
                bb_signal = "overbought"
            elif last_close < lower.iloc[-1]:
                bb_signal = "oversold"
            else:
                bb_signal = "neutral"
            signals["bollinger"] = {
                "upper": round(float(upper.iloc[-1]), 4),
                "lower": round(float(lower.iloc[-1]), 4),
                "signal": bb_signal,
            }

        # ATR (if high/low available)
        if "high" in data.columns and "low" in data.columns:
            atr = self.compute_atr(data["high"], data["low"], close)
            if not pd.isna(atr.iloc[-1]):
                signals["atr"] = {"value": round(float(atr.iloc[-1]), 4)}

            stoch = self.compute_stochastic(data["high"], data["low"], close)
            k_val = stoch["k"].iloc[-1]
            if not pd.isna(k_val):
                if k_val > 80:
                    st_signal = "overbought"
                elif k_val < 20:
                    st_signal = "oversold"
                else:
                    st_signal = "neutral"
                signals["stochastic"] = {"k": round(float(k_val), 2), "signal": st_signal}

        # OBV
        if "volume" in data.columns:
            obv = self.compute_obv(close, data["volume"])
            signals["obv"] = {"value": round(float(obv.iloc[-1]), 2)}

        # Aggregate
        bullish = sum(1 for s in signals.values() if isinstance(s, dict) and s.get("signal") in ("bullish", "oversold"))
        bearish = sum(1 for s in signals.values() if isinstance(s, dict) and s.get("signal") in ("bearish", "overbought"))
        total = bullish + bearish
        if total == 0:
            recommendation = "neutral"
        elif bullish / total >= 0.6:
            recommendation = "buy"
        elif bearish / total >= 0.6:
            recommendation = "sell"
        else:
            recommendation = "hold"

        return {
            "indicators": signals,
            "summary": {
                "bullish_count": bullish,
                "bearish_count": bearish,
                "recommendation": recommendation,
            },
        }
