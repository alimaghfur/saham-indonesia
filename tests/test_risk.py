"""Unit tests for risk metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from saham_id.analysis.risk import (
    beta,
    historical_var,
    log_returns,
    max_drawdown,
    sharpe,
    sortino,
    volatility,
)


class TestRisk:
    def test_log_returns_consistency(self):
        closes = pd.Series([100, 105, 110, 108])
        rets = log_returns(closes)
        assert len(rets) == 3
        expected = np.log(closes.iloc[-1] / closes.iloc[0])
        assert rets.sum() == pytest.approx(expected)

    def test_volatility_non_negative(self):
        rets = pd.Series([0.01, -0.02, 0.005, 0.015, -0.01])
        assert volatility(rets) >= 0

    def test_volatility_zero_for_flat_returns(self):
        rets = pd.Series([0.001] * 50)
        assert volatility(rets) == pytest.approx(0.0)

    def test_sharpe_positive_for_uptrending_returns(self):
        rng = np.random.default_rng(0)
        rets = pd.Series(rng.normal(0.001, 0.005, 252))
        assert sharpe(rets) > 0

    def test_sharpe_zero_for_flat_returns(self):
        rets = pd.Series([0.0] * 50)
        assert sharpe(rets) == 0.0

    def test_sortino_handles_no_downside(self):
        rets = pd.Series([0.01] * 50)
        # No negative returns => downside std = 0 => sortino returns 0
        assert sortino(rets) == 0.0

    def test_max_drawdown_simple(self):
        curve = pd.Series([100, 110, 120, 90, 100, 130])
        # Peak 120 -> trough 90 => (90/120 - 1) = -0.25
        assert max_drawdown(curve) == pytest.approx(-0.25)

    def test_max_drawdown_monotonic_up(self):
        curve = pd.Series([100, 110, 120, 130])
        assert max_drawdown(curve) == pytest.approx(0.0)

    def test_beta_self_is_one(self):
        rng = np.random.default_rng(1)
        market = pd.Series(rng.normal(0, 0.01, 100))
        assert beta(market, market) == pytest.approx(1.0)

    def test_beta_zero_for_uncorrelated(self):
        rng = np.random.default_rng(2)
        a = pd.Series(rng.normal(0, 0.01, 500))
        b = pd.Series(rng.normal(0, 0.01, 500))
        # Independent draws should give |beta| small
        assert abs(beta(a, b)) < 0.3

    def test_historical_var_positive(self):
        rng = np.random.default_rng(3)
        rets = pd.Series(rng.normal(0, 0.02, 1000))
        v = historical_var(rets, confidence=0.95)
        assert v > 0

    def test_historical_var_empty(self):
        assert historical_var(pd.Series([], dtype=float)) == 0.0
