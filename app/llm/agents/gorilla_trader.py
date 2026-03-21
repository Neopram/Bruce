# LLM agent with Soros-like logic
import time
import random


class GorillaTraderAgent:
    """Legacy agent class."""

    def reason(self):
        return "Markets are reflexive. Buy the rumor."


class GorillaTrader:
    """Aggressive/high-risk trading agent with a Soros-inspired reflexivity philosophy.

    This agent favors momentum, high conviction trades, and aggressive position sizing.
    """

    RISK_PROFILE = "aggressive"
    MAX_POSITION_PCT = 0.40  # Up to 40% of portfolio in a single trade
    CONVICTION_THRESHOLD = 0.6

    def __init__(self):
        self._trades = []
        self._performance = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0,
            "peak_equity": 0.0,
        }
        self._signals_history = []

    def analyze_market(self, symbol, data):
        """Perform aggressive market analysis on a symbol.

        Args:
            symbol: Ticker symbol (e.g., 'BTC/USD').
            data: Dict with 'prices' (list of floats), 'volumes' (list of floats),
                  and optionally 'news_sentiment' (-1 to 1).

        Returns:
            Dict with analysis results and conviction level.
        """
        prices = data.get("prices", [])
        volumes = data.get("volumes", [])
        news_sentiment = data.get("news_sentiment", 0)

        if len(prices) < 5:
            return {"symbol": symbol, "signal": "insufficient_data", "conviction": 0}

        # Momentum indicators
        short_ma = sum(prices[-5:]) / 5
        long_ma = sum(prices[-20:]) / max(len(prices[-20:]), 1)
        momentum = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] != 0 else 0

        # Volume spike detection
        avg_vol = sum(volumes[-20:]) / max(len(volumes[-20:]), 1) if volumes else 0
        recent_vol = sum(volumes[-3:]) / max(len(volumes[-3:]), 1) if volumes else 0
        volume_spike = recent_vol / avg_vol if avg_vol > 0 else 1.0

        # Volatility (simple std dev proxy)
        if len(prices) >= 10:
            mean_p = sum(prices[-10:]) / 10
            variance = sum((p - mean_p) ** 2 for p in prices[-10:]) / 10
            volatility = variance ** 0.5 / mean_p if mean_p > 0 else 0
        else:
            volatility = 0

        # Gorilla conviction scoring - aggressive weighting
        trend_score = 0.4 if short_ma > long_ma else -0.3
        momentum_score = min(0.3, max(-0.3, momentum * 3))
        volume_score = min(0.2, (volume_spike - 1) * 0.1) if volume_spike > 1 else 0
        sentiment_score = news_sentiment * 0.2

        conviction = trend_score + momentum_score + volume_score + sentiment_score
        conviction = max(-1.0, min(1.0, conviction))

        if conviction > self.CONVICTION_THRESHOLD:
            signal = "strong_buy"
        elif conviction > 0.3:
            signal = "buy"
        elif conviction < -self.CONVICTION_THRESHOLD:
            signal = "strong_sell"
        elif conviction < -0.3:
            signal = "sell"
        else:
            signal = "hold"

        return {
            "symbol": symbol,
            "signal": signal,
            "conviction": round(conviction, 4),
            "analysis": {
                "short_ma": round(short_ma, 4),
                "long_ma": round(long_ma, 4),
                "momentum": round(momentum, 4),
                "volume_spike": round(volume_spike, 2),
                "volatility": round(volatility, 4),
                "news_sentiment": news_sentiment,
            },
            "philosophy": "Reflexivity: market perception drives reality. Act decisively.",
        }

    def generate_signal(self, symbol, indicators):
        """Generate a trading signal from technical indicators.

        Args:
            symbol: Ticker symbol.
            indicators: Dict with keys like 'rsi', 'macd', 'macd_signal', 'bb_upper',
                       'bb_lower', 'price', 'volume_ratio'.

        Returns:
            Dict with signal details.
        """
        rsi = indicators.get("rsi", 50)
        macd = indicators.get("macd", 0)
        macd_signal = indicators.get("macd_signal", 0)
        price = indicators.get("price", 0)
        bb_upper = indicators.get("bb_upper", price * 1.02)
        bb_lower = indicators.get("bb_lower", price * 0.98)
        volume_ratio = indicators.get("volume_ratio", 1.0)

        scores = []

        # RSI - gorilla loves oversold bounces and rides overbought momentum
        if rsi < 25:
            scores.append(("rsi_oversold_bounce", 0.35))
        elif rsi > 75 and volume_ratio > 1.5:
            scores.append(("rsi_momentum_ride", 0.2))
        elif rsi > 80:
            scores.append(("rsi_overextended", -0.3))

        # MACD crossover
        if macd > macd_signal:
            scores.append(("macd_bullish", 0.25))
        else:
            scores.append(("macd_bearish", -0.25))

        # Bollinger Band breakout
        if price > bb_upper and volume_ratio > 1.3:
            scores.append(("bb_breakout_long", 0.3))
        elif price < bb_lower:
            scores.append(("bb_breakdown", -0.2))

        # Volume confirmation
        if volume_ratio > 2.0:
            scores.append(("volume_surge", 0.15))

        total_score = sum(s[1] for s in scores)
        total_score = max(-1.0, min(1.0, total_score))

        if total_score > 0.4:
            action = "buy"
            size = "aggressive"
        elif total_score > 0.15:
            action = "buy"
            size = "normal"
        elif total_score < -0.4:
            action = "sell"
            size = "aggressive"
        elif total_score < -0.15:
            action = "sell"
            size = "normal"
        else:
            action = "hold"
            size = "none"

        signal = {
            "symbol": symbol,
            "action": action,
            "size": size,
            "score": round(total_score, 4),
            "components": scores,
            "timestamp": time.time(),
        }
        self._signals_history.append(signal)
        return signal

    def execute_strategy(self, signal, portfolio):
        """Execute an aggressive trading strategy based on signal.

        Args:
            signal: Dict from generate_signal with 'action', 'size', 'symbol', 'score'.
            portfolio: Dict with 'cash', 'positions' (dict of symbol -> shares), 'prices'.

        Returns:
            Dict with execution details.
        """
        cash = portfolio.get("cash", 0)
        positions = portfolio.get("positions", {})
        prices = portfolio.get("prices", {})
        symbol = signal.get("symbol", "")
        action = signal.get("action", "hold")
        size = signal.get("size", "normal")

        price = prices.get(symbol, 0)
        if price <= 0:
            return {"status": "skipped", "reason": "invalid price"}

        if action == "hold":
            return {"status": "hold", "reason": "no actionable signal"}

        # Aggressive position sizing
        size_pct = self.MAX_POSITION_PCT if size == "aggressive" else 0.20
        portfolio_value = cash + sum(positions.get(s, 0) * prices.get(s, 0) for s in positions)

        if action == "buy":
            allocation = portfolio_value * size_pct
            max_spend = min(allocation, cash * 0.95)
            shares = int(max_spend / price)
            if shares <= 0:
                return {"status": "skipped", "reason": "insufficient funds"}

            cost = shares * price
            trade = {
                "action": "buy",
                "symbol": symbol,
                "shares": shares,
                "price": price,
                "cost": round(cost, 2),
                "position_pct": round(cost / portfolio_value, 4) if portfolio_value > 0 else 0,
                "timestamp": time.time(),
            }

        elif action == "sell":
            held = positions.get(symbol, 0)
            if held <= 0:
                return {"status": "skipped", "reason": "no position to sell"}

            sell_shares = held if size == "aggressive" else int(held * 0.5)
            sell_shares = max(1, sell_shares)
            proceeds = sell_shares * price
            trade = {
                "action": "sell",
                "symbol": symbol,
                "shares": sell_shares,
                "price": price,
                "proceeds": round(proceeds, 2),
                "timestamp": time.time(),
            }
        else:
            return {"status": "hold"}

        self._trades.append(trade)
        self._performance["total_trades"] += 1
        return {"status": "executed", "trade": trade}

    def get_performance(self):
        """Return performance tracking data."""
        total = self._performance["total_trades"]
        win_rate = (
            round(self._performance["winning_trades"] / total, 4) if total > 0 else 0
        )
        return {
            **self._performance,
            "win_rate": win_rate,
            "risk_profile": self.RISK_PROFILE,
            "total_signals": len(self._signals_history),
            "recent_trades": self._trades[-5:],
        }

    def update_pnl(self, pnl):
        """Update performance with a realized P&L value."""
        self._performance["total_pnl"] += pnl
        if pnl > 0:
            self._performance["winning_trades"] += 1
        else:
            self._performance["losing_trades"] += 1

        current_equity = self._performance["total_pnl"]
        if current_equity > self._performance["peak_equity"]:
            self._performance["peak_equity"] = current_equity
        drawdown = self._performance["peak_equity"] - current_equity
        if drawdown > self._performance["max_drawdown"]:
            self._performance["max_drawdown"] = drawdown
