"""Tests for services and utility modules - indicator engine, risk engine, etc."""

import os
import sys
import math
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# Technical Indicator Engine Tests (from strategy_engine.py)
# ---------------------------------------------------------------------------

from strategy_engine import _sma, _ema, _rsi, _macd, _bollinger_bands


class TestIndicatorEngineSMA:
    """Tests for Simple Moving Average calculations."""

    def test_sma_basic(self):
        """SMA with period 3 on simple data."""
        data = [10.0, 20.0, 30.0, 40.0, 50.0]
        result = _sma(data, 3)
        assert result[2] == pytest.approx(20.0)
        assert result[3] == pytest.approx(30.0)
        assert result[4] == pytest.approx(40.0)

    def test_sma_first_values_are_none(self):
        """SMA values before the period should be None."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = _sma(data, 3)
        assert result[0] is None
        assert result[1] is None
        assert result[2] is not None

    def test_sma_period_equals_data_length(self):
        """SMA with period equal to data length produces one value."""
        data = [10.0, 20.0, 30.0]
        result = _sma(data, 3)
        assert result[2] == pytest.approx(20.0)
        assert result[0] is None
        assert result[1] is None

    def test_sma_constant_data(self):
        """SMA of constant values equals that constant."""
        data = [5.0] * 10
        result = _sma(data, 3)
        for v in result[2:]:
            assert v == pytest.approx(5.0)


class TestIndicatorEngineRSI:
    """Tests for RSI calculations."""

    def test_rsi_range(self, sample_prices):
        """RSI values should be between 0 and 100."""
        result = _rsi(sample_prices, 14)
        for v in result:
            if v is not None:
                assert 0.0 <= v <= 100.0

    def test_rsi_uptrend_high(self):
        """RSI on a strong uptrend should be high."""
        prices = [100 + i for i in range(30)]
        result = _rsi(prices, 14)
        valid = [v for v in result if v is not None]
        assert valid[-1] > 50  # should be above 50 in uptrend

    def test_rsi_downtrend_low(self):
        """RSI on a strong downtrend should be low."""
        prices = [100 - i for i in range(30)]
        result = _rsi(prices, 14)
        valid = [v for v in result if v is not None]
        assert valid[-1] < 50

    def test_rsi_insufficient_data(self):
        """RSI with insufficient data returns all None."""
        result = _rsi([100, 101], 14)
        assert all(v is None for v in result)


class TestIndicatorEngineEMA:
    """Tests for Exponential Moving Average."""

    def test_ema_length(self):
        """EMA output length matches input."""
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = _ema(data, 3)
        assert len(result) == len(data)

    def test_ema_first_value(self):
        """First EMA value equals first data point."""
        data = [10.0, 20.0, 30.0]
        result = _ema(data, 3)
        assert result[0] == 10.0

    def test_ema_empty_data(self):
        """EMA of empty data returns empty list."""
        result = _ema([], 3)
        assert result == []


class TestRiskEngineAssess:
    """Tests for risk assessment via RiskManager."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        from agent_trader import RiskManager
        self.rm = RiskManager()

    def test_risk_assess_clean(self):
        """Portfolio within limits passes risk check."""
        result = self.rm.check_risk_limits(
            portfolio_value=100_000,
            position_value=15_000,
            open_orders=10,
            daily_pnl=100,
            peak_value=100_000,
        )
        assert result["passed"] is True

    def test_risk_assess_multiple_violations(self):
        """Multiple violations are all reported."""
        result = self.rm.check_risk_limits(
            portfolio_value=100_000,
            position_value=30_000,  # 30% > 20%
            open_orders=25,         # > 20
            daily_pnl=-8_000,       # 8% > 5%
            peak_value=130_000,     # 23% drawdown > 15%
        )
        assert result["passed"] is False
        assert len(result["violations"]) >= 3


class TestRiskEngineVaR:
    """Tests for Value at Risk via Monte Carlo (crisis_simulator helpers)."""

    def test_var_from_monte_carlo(self):
        """Monte Carlo stats provide VaR-like percentile data."""
        from crisis_simulator import _monte_carlo_paths, _compute_path_stats
        paths = _monte_carlo_paths(100_000, -0.002, 0.03, 30, 200)
        stats = _compute_path_stats(paths, 100_000)
        # 5th percentile should be less than initial value for negative drift
        assert stats["percentile_5"] < 100_000
        assert stats["prob_loss"] > 0


class TestBollingerBands:
    """Tests for Bollinger Bands calculation."""

    def test_bollinger_bands_shape(self, sample_prices):
        """Bollinger bands return three lists of same length."""
        upper, middle, lower = _bollinger_bands(sample_prices, 20)
        assert len(upper) == len(sample_prices)
        assert len(middle) == len(sample_prices)
        assert len(lower) == len(sample_prices)

    def test_bollinger_upper_above_lower(self, sample_prices):
        """Upper band should always be above lower band."""
        upper, middle, lower = _bollinger_bands(sample_prices, 20)
        for u, l in zip(upper, lower):
            if u is not None and l is not None:
                assert u >= l


class TestMACDCalculation:
    """Tests for MACD calculation."""

    def test_macd_output_lengths(self, sample_prices):
        """MACD returns three lists matching input length."""
        macd_line, signal_line, histogram = _macd(sample_prices)
        assert len(macd_line) == len(sample_prices)
        assert len(signal_line) == len(sample_prices)
        assert len(histogram) == len(sample_prices)

    def test_macd_histogram_is_difference(self, sample_prices):
        """Histogram should equal MACD line minus signal line."""
        macd_line, signal_line, histogram = _macd(sample_prices)
        for m, s, h in zip(macd_line, signal_line, histogram):
            assert h == pytest.approx(m - s, abs=1e-10)
