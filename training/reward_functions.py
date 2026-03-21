"""
Reward Functions for RL Trading Agents
Various reward formulations for training reinforcement learning trading agents.
"""

import numpy as np
from typing import Optional


def pnl_reward(pnl: float, scale: float = 100.0) -> float:
    """
    Simple P&L reward.

    Args:
        pnl: Profit/loss as a decimal (e.g., 0.05 = 5% gain)
        scale: Multiplier to scale reward magnitude

    Returns:
        Scaled reward value
    """
    return pnl * scale


def sharpe_reward(
    returns: np.ndarray,
    window: int = 20,
    annualization: float = 252.0,
    min_periods: int = 5,
) -> float:
    """
    Sharpe ratio reward computed over a rolling window.

    Args:
        returns: Array of period returns
        window: Rolling window size
        annualization: Annualization factor (252 for daily, 365 for crypto)
        min_periods: Minimum periods required to compute

    Returns:
        Annualized Sharpe ratio as reward
    """
    if len(returns) < min_periods:
        return 0.0

    recent = returns[-window:] if len(returns) > window else returns
    mean_ret = np.mean(recent)
    std_ret = np.std(recent)

    if std_ret < 1e-10:
        return 0.0

    sharpe = (mean_ret / std_ret) * np.sqrt(annualization)
    return float(sharpe)


def risk_adjusted_reward(
    pnl: float,
    max_drawdown: float,
    drawdown_penalty: float = 2.0,
    scale: float = 100.0,
) -> float:
    """
    Risk-adjusted reward that penalizes drawdown.

    Args:
        pnl: Profit/loss as a decimal
        max_drawdown: Maximum drawdown as a decimal (0-1)
        drawdown_penalty: Multiplier for drawdown penalty
        scale: Reward scaling factor

    Returns:
        Risk-adjusted reward
    """
    reward = pnl * scale
    penalty = max_drawdown * drawdown_penalty * scale
    return reward - penalty


def combined_reward(
    pnl: float,
    sharpe: float,
    drawdown: float,
    weights: Optional[dict] = None,
) -> float:
    """
    Weighted combination of multiple reward components.

    Args:
        pnl: Profit/loss as a decimal
        sharpe: Sharpe ratio
        drawdown: Maximum drawdown as a decimal (0-1)
        weights: Dict with keys 'pnl', 'sharpe', 'drawdown' and float values.
                 Defaults to {'pnl': 0.4, 'sharpe': 0.4, 'drawdown': 0.2}

    Returns:
        Combined weighted reward
    """
    if weights is None:
        weights = {"pnl": 0.4, "sharpe": 0.4, "drawdown": 0.2}

    reward = 0.0
    reward += weights.get("pnl", 0.4) * pnl * 100
    reward += weights.get("sharpe", 0.4) * sharpe
    reward -= weights.get("drawdown", 0.2) * drawdown * 100

    return float(reward)


def sortino_reward(
    returns: np.ndarray,
    window: int = 20,
    target_return: float = 0.0,
    annualization: float = 252.0,
) -> float:
    """
    Sortino ratio reward - like Sharpe but only penalizes downside volatility.

    Args:
        returns: Array of period returns
        window: Rolling window size
        target_return: Minimum acceptable return (usually 0)
        annualization: Annualization factor

    Returns:
        Annualized Sortino ratio as reward
    """
    if len(returns) < 5:
        return 0.0

    recent = returns[-window:] if len(returns) > window else returns
    excess = recent - target_return
    mean_excess = np.mean(excess)

    downside = excess[excess < 0]
    if len(downside) == 0:
        return float(mean_excess * np.sqrt(annualization) * 10)  # All positive

    downside_std = np.sqrt(np.mean(downside ** 2))
    if downside_std < 1e-10:
        return 0.0

    sortino = (mean_excess / downside_std) * np.sqrt(annualization)
    return float(sortino)


def calmar_reward(
    total_return: float,
    max_drawdown: float,
    min_drawdown: float = 0.01,
) -> float:
    """
    Calmar ratio reward - return over maximum drawdown.

    Args:
        total_return: Total return as decimal
        max_drawdown: Maximum drawdown as decimal (0-1)
        min_drawdown: Minimum drawdown to prevent division by zero

    Returns:
        Calmar ratio as reward
    """
    effective_dd = max(max_drawdown, min_drawdown)
    return float(total_return / effective_dd)


def trade_efficiency_reward(
    pnl: float,
    n_trades: int,
    holding_time: float,
    max_trades_penalty: int = 50,
) -> float:
    """
    Reward that penalizes excessive trading (encourages efficiency).

    Args:
        pnl: Profit/loss as decimal
        n_trades: Number of trades executed
        holding_time: Average holding time in steps
        max_trades_penalty: Threshold above which trades are penalized

    Returns:
        Efficiency-adjusted reward
    """
    base_reward = pnl * 100

    # Penalize excessive trading
    if n_trades > max_trades_penalty:
        trade_penalty = (n_trades - max_trades_penalty) * 0.01
        base_reward -= trade_penalty

    # Bonus for reasonable holding times (not too short, not too long)
    if 5 <= holding_time <= 50:
        base_reward *= 1.1  # 10% bonus

    return float(base_reward)


def asymmetric_reward(
    pnl: float,
    gain_multiplier: float = 1.0,
    loss_multiplier: float = 2.0,
    scale: float = 100.0,
) -> float:
    """
    Asymmetric reward that penalizes losses more than rewarding gains.
    Encourages risk-averse behavior.

    Args:
        pnl: Profit/loss as decimal
        gain_multiplier: Multiplier for positive returns
        loss_multiplier: Multiplier for negative returns (higher = more risk averse)
        scale: Base scaling factor

    Returns:
        Asymmetrically scaled reward
    """
    if pnl >= 0:
        return pnl * gain_multiplier * scale
    else:
        return pnl * loss_multiplier * scale


class RewardCalculator:
    """
    Configurable reward calculator that combines multiple reward signals.
    Tracks state needed for computing rolling metrics.
    """

    def __init__(
        self,
        reward_type: str = "combined",
        weights: Optional[dict] = None,
        window: int = 20,
    ):
        self.reward_type = reward_type
        self.weights = weights or {"pnl": 0.4, "sharpe": 0.4, "drawdown": 0.2}
        self.window = window
        self.returns_history = []
        self.peak_equity = 0.0
        self.n_trades = 0

    def reset(self):
        """Reset state for new episode."""
        self.returns_history = []
        self.peak_equity = 0.0
        self.n_trades = 0

    def compute(
        self,
        step_return: float,
        equity: float,
        trade_executed: bool = False,
    ) -> float:
        """
        Compute reward for the current step.

        Args:
            step_return: Return for this step as decimal
            equity: Current portfolio equity
            trade_executed: Whether a trade was executed this step

        Returns:
            Computed reward value
        """
        self.returns_history.append(step_return)
        self.peak_equity = max(self.peak_equity, equity)
        if trade_executed:
            self.n_trades += 1

        drawdown = (self.peak_equity - equity) / (self.peak_equity + 1e-10)

        if self.reward_type == "pnl":
            return pnl_reward(step_return)

        elif self.reward_type == "sharpe":
            return sharpe_reward(np.array(self.returns_history), window=self.window)

        elif self.reward_type == "risk_adjusted":
            return risk_adjusted_reward(step_return, drawdown)

        elif self.reward_type == "sortino":
            return sortino_reward(np.array(self.returns_history), window=self.window)

        elif self.reward_type == "asymmetric":
            return asymmetric_reward(step_return)

        elif self.reward_type == "combined":
            sharpe_val = sharpe_reward(np.array(self.returns_history), window=self.window)
            return combined_reward(step_return, sharpe_val, drawdown, self.weights)

        else:
            return pnl_reward(step_return)
