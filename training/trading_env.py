"""
Gymnasium Trading Environment for Bruce AI
Custom environment for training RL agents on financial time series data.
"""

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYM_AVAILABLE = True
except ImportError:
    GYM_AVAILABLE = False


class TradingEnvironment:
    """
    Trading environment compatible with Gymnasium interface.

    Observation space:
        - Price history (look_back steps of normalized close prices)
        - Technical indicators (RSI, MACD, Bollinger Band width)
        - Portfolio state (balance ratio, position ratio, unrealized PnL)

    Action space:
        - Discrete(3): 0=Hold, 1=Buy, 2=Sell
        OR with continuous amount if use_continuous=True:
        - Box(2): [action_type (0-1), amount (0-1)]
    """

    # Gymnasium metadata
    metadata = {"render_modes": ["text"]}

    def __init__(
        self,
        prices: np.ndarray,
        initial_balance: float = 10000.0,
        look_back: int = 60,
        max_steps: int = 200,
        commission: float = 0.001,
        use_continuous: bool = False,
        render_mode: str = None,
    ):
        self.prices = prices
        self.initial_balance = initial_balance
        self.look_back = look_back
        self.max_steps = max_steps
        self.commission = commission
        self.use_continuous = use_continuous
        self.render_mode = render_mode

        # Pre-compute indicators
        self._precompute_indicators()

        # Observation: look_back prices + 3 indicators + 3 portfolio features
        obs_size = look_back + 3 + 3

        if GYM_AVAILABLE:
            self.observation_space = spaces.Box(
                low=-np.inf, high=np.inf, shape=(obs_size,), dtype=np.float32
            )
            if use_continuous:
                self.action_space = spaces.Box(
                    low=np.array([0.0, 0.0]), high=np.array([1.0, 1.0]), dtype=np.float32
                )
            else:
                self.action_space = spaces.Discrete(3)  # Hold, Buy, Sell
        else:
            self.observation_space = None
            self.action_space = None

        # State variables
        self.balance = initial_balance
        self.position = 0.0  # units held
        self.entry_price = 0.0
        self.current_step = 0
        self.start_idx = 0
        self.trades = []
        self.equity_curve = []
        self.returns_history = []

    def _precompute_indicators(self):
        """Pre-compute technical indicators for the entire price series."""
        prices = self.prices

        # RSI (14)
        self.rsi = np.full(len(prices), 50.0)
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        period = 14
        if len(deltas) >= period:
            avg_gain = np.mean(gains[:period])
            avg_loss = np.mean(losses[:period])
            for i in range(period, len(deltas)):
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
                if avg_loss == 0:
                    self.rsi[i + 1] = 100
                else:
                    self.rsi[i + 1] = 100 - (100 / (1 + avg_gain / avg_loss))

        # MACD (simplified as EMA12 - EMA26, normalized)
        self.macd = np.zeros(len(prices))
        if len(prices) > 26:
            ema12 = self._ema(prices, 12)
            ema26 = self._ema(prices, 26)
            self.macd = (ema12 - ema26) / (prices + 1e-10) * 100  # normalized

        # Bollinger Band width
        self.bb_width = np.zeros(len(prices))
        period = 20
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            std = np.std(window)
            mean = np.mean(window)
            self.bb_width[i] = (2 * std) / (mean + 1e-10)

    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        """Compute exponential moving average."""
        ema = np.zeros(len(data))
        ema[0] = data[0]
        mult = 2.0 / (period + 1)
        for i in range(1, len(data)):
            ema[i] = (data[i] - ema[i - 1]) * mult + ema[i - 1]
        return ema

    def _get_observation(self) -> np.ndarray:
        """Construct observation vector."""
        idx = self.start_idx + self.current_step

        # Normalized price history
        price_window = self.prices[max(0, idx - self.look_back):idx]
        if len(price_window) < self.look_back:
            pad = np.full(self.look_back - len(price_window), price_window[0] if len(price_window) > 0 else 0)
            price_window = np.concatenate([pad, price_window])
        # Normalize to [0, 1]
        p_min = price_window.min()
        p_max = price_window.max()
        if p_max - p_min > 0:
            norm_prices = (price_window - p_min) / (p_max - p_min)
        else:
            norm_prices = np.zeros(self.look_back)

        # Indicators
        rsi_val = self.rsi[idx] / 100.0  # [0, 1]
        macd_val = np.clip(self.macd[idx] / 5.0, -1, 1)  # normalized
        bb_val = np.clip(self.bb_width[idx], 0, 1)

        # Portfolio state
        current_price = self.prices[idx]
        total_equity = self.balance + self.position * current_price
        balance_ratio = self.balance / (total_equity + 1e-10)
        position_ratio = (self.position * current_price) / (total_equity + 1e-10)
        unrealized_pnl = 0.0
        if self.position > 0 and self.entry_price > 0:
            unrealized_pnl = (current_price - self.entry_price) / self.entry_price

        obs = np.concatenate([
            norm_prices,
            [rsi_val, macd_val, bb_val],
            [balance_ratio, position_ratio, np.clip(unrealized_pnl, -1, 1)],
        ]).astype(np.float32)

        return obs

    def reset(self, seed=None, options=None):
        """Reset environment for new episode."""
        if seed is not None:
            np.random.seed(seed)

        # Random start position ensuring enough data
        max_start = len(self.prices) - self.max_steps - 1
        min_start = self.look_back
        if max_start <= min_start:
            self.start_idx = min_start
        else:
            self.start_idx = np.random.randint(min_start, max_start)

        self.balance = self.initial_balance
        self.position = 0.0
        self.entry_price = 0.0
        self.current_step = 0
        self.trades = []
        self.equity_curve = [self.initial_balance]
        self.returns_history = []

        obs = self._get_observation()
        info = {}
        return obs, info

    def step(self, action):
        """Execute one step in the environment."""
        idx = self.start_idx + self.current_step
        current_price = self.prices[idx]
        prev_equity = self.balance + self.position * current_price

        # Parse action
        if self.use_continuous:
            action_type = int(round(action[0] * 2))  # 0, 1, 2
            amount_frac = float(action[1])
        else:
            action_type = int(action)
            amount_frac = 1.0

        # Execute action
        trade_pnl = 0.0

        if action_type == 1 and self.balance > 0:  # Buy
            invest = self.balance * amount_frac
            cost = invest * self.commission
            units = (invest - cost) / current_price
            self.position += units
            if self.entry_price == 0:
                self.entry_price = current_price
            else:
                # Average entry
                total_cost = self.entry_price * (self.position - units) + current_price * units
                self.entry_price = total_cost / self.position
            self.balance -= invest

        elif action_type == 2 and self.position > 0:  # Sell
            sell_units = self.position * amount_frac
            revenue = sell_units * current_price
            cost = revenue * self.commission
            trade_pnl = (current_price - self.entry_price) / self.entry_price * amount_frac
            self.trades.append(trade_pnl)
            self.balance += revenue - cost
            self.position -= sell_units
            if self.position < 1e-8:
                self.position = 0
                self.entry_price = 0

        # Move to next step
        self.current_step += 1
        next_idx = self.start_idx + self.current_step
        if next_idx >= len(self.prices):
            next_idx = len(self.prices) - 1

        next_price = self.prices[next_idx]
        new_equity = self.balance + self.position * next_price
        self.equity_curve.append(new_equity)

        # Compute reward
        step_return = (new_equity - prev_equity) / (prev_equity + 1e-10)
        self.returns_history.append(step_return)

        # Reward: PnL adjusted by risk
        reward = step_return * 100  # scale

        # Sharpe bonus for consistent returns
        if len(self.returns_history) > 10:
            ret_arr = np.array(self.returns_history[-20:])
            if np.std(ret_arr) > 0:
                sharpe = np.mean(ret_arr) / np.std(ret_arr)
                reward += sharpe * 0.1

        # Drawdown penalty
        peak_equity = max(self.equity_curve)
        drawdown = (peak_equity - new_equity) / (peak_equity + 1e-10)
        reward -= drawdown * 0.5

        # Check if done
        terminated = self.current_step >= self.max_steps or next_idx >= len(self.prices) - 1
        truncated = new_equity < self.initial_balance * 0.5  # Bankrupt

        # Info
        info = {
            "equity": new_equity,
            "balance": self.balance,
            "position_value": self.position * next_price,
            "total_return": (new_equity - self.initial_balance) / self.initial_balance,
            "n_trades": len(self.trades),
            "step": self.current_step,
        }

        if terminated or truncated:
            # Final stats
            equity_arr = np.array(self.equity_curve)
            peak = np.maximum.accumulate(equity_arr)
            dd = (peak - equity_arr) / (peak + 1e-10)

            info["max_drawdown"] = float(dd.max())
            info["win_rate"] = sum(1 for t in self.trades if t > 0) / max(len(self.trades), 1)
            info["avg_trade_return"] = float(np.mean(self.trades)) if self.trades else 0.0

            ret_arr = np.array(self.returns_history)
            if len(ret_arr) > 1 and np.std(ret_arr) > 0:
                info["sharpe"] = float(np.mean(ret_arr) / np.std(ret_arr) * np.sqrt(252))
            else:
                info["sharpe"] = 0.0

        obs = self._get_observation()
        return obs, float(reward), terminated, truncated, info

    def render(self):
        """Render current state as text."""
        if self.render_mode != "text":
            return
        idx = self.start_idx + self.current_step
        price = self.prices[min(idx, len(self.prices) - 1)]
        equity = self.balance + self.position * price
        print(f"  Step {self.current_step} | Price: {price:.2f} | "
              f"Balance: {self.balance:.2f} | Position: {self.position:.4f} | "
              f"Equity: {equity:.2f}")


# Register with gymnasium if available
if GYM_AVAILABLE:
    # Make it subclass gym.Env
    _OriginalEnv = TradingEnvironment

    class TradingEnvironment(gym.Env, _OriginalEnv):
        def __init__(self, *args, **kwargs):
            _OriginalEnv.__init__(self, *args, **kwargs)
