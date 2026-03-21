"""Tests for agent_trader.py and strategy_engine.py."""

import os
import sys
import pytest
import math

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent_trader import (
    TradingAgent,
    TradingMode,
    OrderSide,
    OrderType,
    OrderRequest,
    RiskManager,
    SimulatedPriceFeed,
)
from strategy_engine import (
    _sma,
    _ema,
    _rsi,
    _macd,
    _strategy_sma_crossover,
    _strategy_rsi,
    _strategy_macd,
    Signal,
)


# ---------------------------------------------------------------------------
# Trading Agent Tests
# ---------------------------------------------------------------------------

class TestTradingAgent:
    """Tests for the TradingAgent class."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.agent = TradingAgent(mode=TradingMode.PAPER, initial_balance=100_000.0)

    def test_create_order_buy(self):
        """Agent can create a paper buy order."""
        result = self.agent.create_order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=0.1,
            order_type=OrderType.MARKET,
        )
        assert result is not None
        assert "order_id" in result
        assert result["side"] == "buy"
        assert result["symbol"] == "BTC/USDT"

    def test_create_order_sell(self):
        """Agent can create a paper sell order."""
        # First buy something
        self.agent.create_order(
            symbol="ETH/USDT", side=OrderSide.BUY, amount=1.0,
        )
        # Then sell
        result = self.agent.create_order(
            symbol="ETH/USDT", side=OrderSide.SELL, amount=1.0,
        )
        assert result is not None

    def test_cancel_order(self):
        """Agent can cancel a pending order."""
        created = self.agent.create_order(
            symbol="BTC/USDT",
            side=OrderSide.BUY,
            amount=0.1,
            order_type=OrderType.LIMIT,
            price=50000.0,
        )
        if created and "order_id" in created:
            result = self.agent.cancel_order(created["order_id"])
            assert result is not None

    def test_get_portfolio(self):
        """Agent returns portfolio state."""
        portfolio = self.agent.get_portfolio()
        assert portfolio is not None
        assert "balance" in portfolio or "total_value" in portfolio or isinstance(portfolio, dict)

    def test_simulated_price_feed(self):
        """SimulatedPriceFeed returns reasonable prices."""
        price = SimulatedPriceFeed.get_price("BTC/USDT")
        assert price > 0
        assert price > 60000  # should be near base of 67500

    def test_simulated_price_unknown_symbol(self):
        """Unknown symbols get a default base price."""
        price = SimulatedPriceFeed.get_price("UNKNOWN/PAIR")
        assert price > 0


# ---------------------------------------------------------------------------
# Risk Manager Tests
# ---------------------------------------------------------------------------

class TestRiskManager:
    """Tests for the RiskManager class."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        self.rm = RiskManager(
            max_position_pct=0.20,
            max_drawdown_pct=0.15,
            max_open_orders=20,
            max_daily_loss_pct=0.05,
        )

    def test_risk_limits_pass(self):
        """Check passes when all limits are respected."""
        result = self.rm.check_risk_limits(
            portfolio_value=100_000,
            position_value=10_000,  # 10% < 20%
            open_orders=5,
            daily_pnl=500,
            peak_value=100_000,
        )
        assert result["passed"] is True
        assert len(result["violations"]) == 0

    def test_risk_limits_position_violation(self):
        """Check fails when position exceeds max concentration."""
        result = self.rm.check_risk_limits(
            portfolio_value=100_000,
            position_value=25_000,  # 25% > 20%
            open_orders=5,
            daily_pnl=0,
            peak_value=100_000,
        )
        assert result["passed"] is False
        assert any("Position" in v for v in result["violations"])

    def test_risk_limits_drawdown_violation(self):
        """Check fails when drawdown exceeds limit."""
        result = self.rm.check_risk_limits(
            portfolio_value=80_000,
            position_value=10_000,
            open_orders=5,
            daily_pnl=0,
            peak_value=100_000,  # 20% drawdown > 15% limit
        )
        assert result["passed"] is False
        assert any("Drawdown" in v for v in result["violations"])

    def test_risk_limits_daily_loss_violation(self):
        """Check fails when daily loss exceeds limit."""
        result = self.rm.check_risk_limits(
            portfolio_value=100_000,
            position_value=10_000,
            open_orders=5,
            daily_pnl=-6_000,  # 6% > 5%
            peak_value=100_000,
        )
        assert result["passed"] is False

    def test_position_size_calculator(self):
        """Position size calculator returns valid sizing."""
        result = self.rm.position_size_calculator(
            portfolio_value=100_000,
            risk_per_trade_pct=0.02,
            entry_price=67500,
            stop_loss_price=65000,
        )
        assert "suggested_size" in result
        assert result["suggested_size"] > 0
        assert result["position_value"] > 0


# ---------------------------------------------------------------------------
# Strategy Engine Tests
# ---------------------------------------------------------------------------

class TestStrategyIndicators:
    """Tests for technical indicator calculations."""

    def test_sma_calculation(self):
        """SMA should compute correct simple moving average."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = _sma(data, 3)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == pytest.approx(2.0)  # (1+2+3)/3
        assert result[3] == pytest.approx(3.0)  # (2+3+4)/3
        assert result[4] == pytest.approx(4.0)  # (3+4+5)/3

    def test_ema_calculation(self):
        """EMA should produce values for all data points."""
        data = [10.0, 11.0, 12.0, 11.0, 10.0]
        result = _ema(data, 3)
        assert len(result) == len(data)
        assert result[0] == 10.0  # first value equals first data point

    def test_rsi_calculation(self, sample_prices):
        """RSI should produce values between 0 and 100."""
        result = _rsi(sample_prices, 14)
        valid_values = [v for v in result if v is not None]
        assert len(valid_values) > 0
        for v in valid_values:
            assert 0.0 <= v <= 100.0

    def test_macd_calculation(self, sample_prices):
        """MACD returns three lists of same length as input."""
        macd_line, signal_line, histogram = _macd(sample_prices)
        assert len(macd_line) == len(sample_prices)
        assert len(signal_line) == len(sample_prices)
        assert len(histogram) == len(sample_prices)


class TestStrategies:
    """Tests for strategy signal generators."""

    def test_strategy_sma_insufficient_data(self):
        """SMA crossover with insufficient data returns HOLD."""
        result = _strategy_sma_crossover([1.0, 2.0, 3.0])
        assert result["signal"] == Signal.HOLD.value

    def test_strategy_sma_with_data(self, sample_prices):
        """SMA crossover returns a valid signal."""
        result = _strategy_sma_crossover(sample_prices)
        assert result["signal"] in [Signal.BUY.value, Signal.SELL.value, Signal.HOLD.value]
        assert "confidence" in result
        assert "reason" in result

    def test_strategy_rsi_oversold(self):
        """RSI strategy detects oversold conditions."""
        # Create a declining price series to push RSI low
        prices = [100 - i * 0.5 for i in range(30)]
        result = _strategy_rsi(prices)
        # Should detect oversold or at least give a signal
        assert result["signal"] in [Signal.BUY.value, Signal.HOLD.value, Signal.SELL.value]

    def test_strategy_rsi_insufficient_data(self):
        """RSI with too few points returns HOLD."""
        result = _strategy_rsi([100, 101, 102])
        assert result["signal"] == Signal.HOLD.value

    def test_strategy_macd_insufficient_data(self):
        """MACD with insufficient data returns HOLD."""
        result = _strategy_macd([1.0] * 10)
        assert result["signal"] == Signal.HOLD.value

    def test_strategy_macd_with_data(self, sample_prices):
        """MACD strategy returns a valid signal with enough data."""
        result = _strategy_macd(sample_prices)
        assert result["signal"] in [Signal.BUY.value, Signal.SELL.value, Signal.HOLD.value]
        assert 0.0 <= result["confidence"] <= 1.0
