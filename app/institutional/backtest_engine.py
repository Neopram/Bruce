"""
Backtesting engine module.
Runs trading strategies against historical data and computes
comprehensive performance metrics including Sharpe, drawdown, and more.
"""
import math
import random
from datetime import datetime


class BacktestEngine:
    """Quantitative backtesting engine with advanced performance metrics."""

    def __init__(self, initial_capital=100000, commission_pct=0.001):
        self.initial_capital = initial_capital
        self.commission_pct = commission_pct
        self.backtest_results = []

    def run_backtest(self, strategy_name, prices=None, signals=None, n_periods=252):
        """Run a full backtest of a strategy.

        Args:
            strategy_name: Name of the strategy being tested.
            prices: Optional list of historical prices.
            signals: Optional list of signals (1=long, -1=short, 0=flat).
            n_periods: Number of periods to simulate if no data provided.
        """
        if prices is None:
            prices = self._generate_price_series(n_periods)
        if signals is None:
            signals = self._generate_signals(len(prices))

        min_len = min(len(prices), len(signals))
        prices = prices[:min_len]
        signals = signals[:min_len]

        equity_curve = [self.initial_capital]
        trades = []
        position = 0
        entry_price = 0
        daily_returns = []

        for i in range(1, min_len):
            price_return = (prices[i] - prices[i - 1]) / prices[i - 1]
            strategy_return = price_return * position
            commission = self.commission_pct if signals[i] != signals[i - 1] else 0
            net_return = strategy_return - commission

            new_equity = equity_curve[-1] * (1 + net_return)
            equity_curve.append(new_equity)
            daily_returns.append(net_return)

            if signals[i] != position:
                if position != 0:
                    pnl_pct = (prices[i] - entry_price) / entry_price * (1 if position > 0 else -1)
                    trades.append({
                        "entry_price": round(entry_price, 4),
                        "exit_price": round(prices[i], 4),
                        "direction": "long" if position > 0 else "short",
                        "pnl_pct": round(pnl_pct * 100, 4),
                    })
                position = signals[i]
                entry_price = prices[i]

        metrics = self._compute_metrics(equity_curve, daily_returns, trades)
        result = {
            "strategy": strategy_name,
            "initial_capital": self.initial_capital,
            "final_equity": round(equity_curve[-1], 2),
            "total_return_pct": round((equity_curve[-1] / self.initial_capital - 1) * 100, 2),
            "n_periods": min_len,
            "n_trades": len(trades),
            **metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.backtest_results.append(result)
        return result

    def _compute_metrics(self, equity_curve, daily_returns, trades):
        """Compute comprehensive performance metrics."""
        if not daily_returns:
            return {"sharpe": 0, "max_drawdown": 0, "cagr": 0}

        mean_ret = sum(daily_returns) / len(daily_returns)
        var_ret = sum((r - mean_ret) ** 2 for r in daily_returns) / max(1, len(daily_returns) - 1)
        std_ret = math.sqrt(var_ret) if var_ret > 0 else 1e-8

        sharpe = (mean_ret / std_ret) * math.sqrt(252) if std_ret > 0 else 0

        peak = equity_curve[0]
        max_dd = 0
        max_dd_duration = 0
        dd_start = 0
        for i, eq in enumerate(equity_curve):
            if eq > peak:
                peak = eq
                dd_start = i
            dd = (peak - eq) / peak
            if dd > max_dd:
                max_dd = dd
                max_dd_duration = i - dd_start

        n_years = len(daily_returns) / 252
        total_return = equity_curve[-1] / equity_curve[0]
        cagr = (total_return ** (1 / n_years) - 1) if n_years > 0 and total_return > 0 else 0

        calmar = cagr / max_dd if max_dd > 0 else 0

        negative_returns = [r for r in daily_returns if r < 0]
        downside_var = sum(r ** 2 for r in negative_returns) / max(1, len(negative_returns))
        downside_std = math.sqrt(downside_var) if downside_var > 0 else 1e-8
        sortino = (mean_ret / downside_std) * math.sqrt(252) if downside_std > 0 else 0

        win_trades = [t for t in trades if t["pnl_pct"] > 0]
        loss_trades = [t for t in trades if t["pnl_pct"] <= 0]
        win_rate = len(win_trades) / len(trades) if trades else 0
        avg_win = sum(t["pnl_pct"] for t in win_trades) / len(win_trades) if win_trades else 0
        avg_loss = sum(t["pnl_pct"] for t in loss_trades) / len(loss_trades) if loss_trades else 0
        profit_factor = abs(sum(t["pnl_pct"] for t in win_trades) / sum(t["pnl_pct"] for t in loss_trades)) if loss_trades and sum(t["pnl_pct"] for t in loss_trades) != 0 else float("inf")

        return {
            "sharpe": round(sharpe, 4),
            "sortino": round(sortino, 4),
            "cagr": round(cagr, 4),
            "max_drawdown": round(-max_dd, 4),
            "max_drawdown_duration_days": max_dd_duration,
            "calmar_ratio": round(calmar, 4),
            "win_rate": round(win_rate, 4),
            "avg_win_pct": round(avg_win, 4),
            "avg_loss_pct": round(avg_loss, 4),
            "profit_factor": round(profit_factor, 4) if profit_factor != float("inf") else "inf",
            "volatility_annual_pct": round(std_ret * math.sqrt(252) * 100, 2),
        }

    def _generate_price_series(self, n, start=100):
        """Generate a simulated price series using geometric Brownian motion."""
        prices = [start]
        for _ in range(n - 1):
            ret = random.gauss(0.0003, 0.015)
            prices.append(round(prices[-1] * (1 + ret), 4))
        return prices

    def _generate_signals(self, n):
        """Generate simulated trading signals."""
        signals = [0]
        for i in range(1, n):
            if random.random() < 0.05:
                signals.append(random.choice([-1, 0, 1]))
            else:
                signals.append(signals[-1])
        return signals

    def compare_strategies(self, results_list):
        """Compare multiple backtest results."""
        if not results_list:
            return {"status": "error", "message": "No results to compare"}

        comparison = []
        for r in results_list:
            comparison.append({
                "strategy": r["strategy"],
                "total_return_pct": r["total_return_pct"],
                "sharpe": r["sharpe"],
                "max_drawdown": r["max_drawdown"],
                "cagr": r["cagr"],
                "win_rate": r.get("win_rate", 0),
            })

        best_sharpe = max(comparison, key=lambda x: x["sharpe"])
        best_return = max(comparison, key=lambda x: x["total_return_pct"])

        return {
            "strategies": comparison,
            "best_sharpe": best_sharpe["strategy"],
            "best_return": best_return["strategy"],
        }

    def get_backtest_results(self, limit=10):
        """Return recent backtest results."""
        return self.backtest_results[-limit:]
