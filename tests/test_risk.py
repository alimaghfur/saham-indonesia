"""Tests for risk metrics module."""
import pandas as pd

from saham_id.analysis.risk import (
    beta,
    historical_var,
    log_returns,
    max_drawdown,
    sharpe,
    sortino,
    volatility,
)


class TestVolatility:
    def test_constant_returns_near_zero_vol(self):
        returns = pd.Series([0.01] * 50)
        vol = volatility(returns)
        # With floating point, this may be very small but not exactly 0
        assert vol < 0.001  # Effectively zero

    def test_positive_volatility(self):
        returns = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02, -0.005, 0.015] * 5)
        vol = volatility(returns)
        assert vol > 0


class TestSharpe:
    def test_sharpe_positive_returns(self):
        returns = pd.Series([0.01, 0.02, 0.015, 0.005, 0.01, 0.02, 0.008] * 5)
        s = sharpe(returns)
        assert s > 0  # All positive returns

    def test_sharpe_low_vol(self):
        # Nearly constant returns — sharpe should be very high or zero if std rounds to 0
        returns = pd.Series([0.01] * 50)
        s = sharpe(returns)
        # Could be 0 (if std is treated as 0) or very high
        assert s >= 0


class TestSortino:
    def test_sortino_all_positive(self):
        returns = pd.Series([0.01, 0.02, 0.015, 0.005, 0.01, 0.02, 0.008] * 5)
        s = sortino(returns)
        # With no downside, sortino should be 0 (no downside deviation)
        assert s == 0.0

    def test_sortino_mixed_returns(self):
        returns = pd.Series([0.03, -0.02, 0.04, -0.01, 0.02, -0.015, 0.025] * 5)
        s = sortino(returns)
        assert s > 0  # Net positive with some downside


class TestMaxDrawdown:
    def test_max_drawdown_uptrend(self):
        equity = pd.Series([100, 105, 110, 115, 120, 125])
        mdd = max_drawdown(equity)
        assert mdd == 0.0  # No drawdown in pure uptrend

    def test_max_drawdown_with_dip(self):
        equity = pd.Series([100, 110, 105, 115, 108, 120])
        mdd = max_drawdown(equity)
        assert mdd < 0  # Should have negative drawdown
        # The drawdown from 115 to 108 = -(115-108)/115 = -0.0609
        expected = (108 / 115) - 1.0
        assert abs(mdd - expected) < 0.001


class TestBeta:
    def test_beta_positive(self):
        # Asset moves in same direction as market
        asset = pd.Series([0.02, -0.01, 0.03, -0.02, 0.01, 0.015, -0.005, 0.02, -0.01, 0.025])
        market = pd.Series([0.01, -0.005, 0.02, -0.01, 0.005, 0.01, -0.003, 0.015, -0.005, 0.02])
        b = beta(asset, market)
        assert b > 0  # Positive correlation


class TestHistoricalVaR:
    def test_var_positive(self):
        returns = pd.Series([0.03, -0.02, 0.04, -0.05, 0.02, -0.03, 0.01, -0.04, 0.03, -0.01] * 3)
        var = historical_var(returns, confidence=0.95)
        assert var > 0

    def test_var_empty(self):
        returns = pd.Series([])
        var = historical_var(returns, confidence=0.95)
        assert var == 0.0
