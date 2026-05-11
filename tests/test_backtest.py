"""Unit tests for the backtest engine and performance metrics."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from saham_id.backtest import Backtester, compute_metrics
from saham_id.backtest.engine import Order
from tests.conftest import make_ohlc


def _buy_once_hold_strategy(qty: int = 100):
    """Buy `qty` on first bar, hold thereafter."""
    def strategy(bar, state):
        if state["position"] == 0 and not state.get("_entered"):
            # Using dict closure won't persist across calls — rely on position==0 guard
            return [Order(side="buy", quantity=qty, note="entry")]
        return []
    return strategy


def _buy_then_exit_after_n_bars(n: int = 10, qty: int = 100):
    """Buy on first bar, sell after `n` bars."""
    counter = {"steps": 0}
    def strategy(bar, state):
        counter["steps"] += 1
        if state["position"] == 0 and counter["steps"] == 1:
            return [Order(side="buy", quantity=qty, note="entry")]
        if state["position"] > 0 and counter["steps"] == 1 + n:
            return [Order(side="sell", quantity=state["position"], note="exit")]
        return []
    return strategy


class TestBacktester:
    def test_empty_data_raises(self):
        bt = Backtester(strategy=lambda bar, state: [])
        with pytest.raises(ValueError):
            bt.run(pd.DataFrame())

    def test_noop_strategy_preserves_capital(self):
        df = make_ohlc(seed=0, bars=30, trend=0.002)
        bt = Backtester(strategy=lambda bar, state: [], initial_capital=10_000_000)
        result = bt.run(df)
        assert result.final_capital == pytest.approx(10_000_000)
        assert result.total_return == pytest.approx(0.0)
        assert result.trades == []

    def test_buy_and_hold_tracks_price(self):
        df = make_ohlc(seed=1, bars=30, trend=0.002, noise=0.001)
        bt = Backtester(
            strategy=_buy_once_hold_strategy(qty=100),
            initial_capital=10_000_000,
            commission_bps=0.0,  # remove fees for clean math
        )
        result = bt.run(df)
        # After entry, final_capital ≈ cash_after_entry + 100 * close_final
        # cash_after_entry = 10M - 100 * open[1]
        expected = 10_000_000 - 100 * float(df.iloc[1]["open"]) + 100 * float(df.iloc[-1]["close"])
        assert result.final_capital == pytest.approx(expected, rel=1e-9)

    def test_commission_reduces_capital(self):
        df = make_ohlc(seed=1, bars=30, trend=0.0, noise=0.0, start_price=1000.0)
        bt_no_fee = Backtester(
            strategy=_buy_once_hold_strategy(qty=100),
            initial_capital=10_000_000, commission_bps=0.0,
        )
        bt_fee = Backtester(
            strategy=_buy_once_hold_strategy(qty=100),
            initial_capital=10_000_000, commission_bps=50.0,  # 0.5% = 500 bps/10k
        )
        r_no_fee = bt_no_fee.run(df)
        r_fee = bt_fee.run(df)
        assert r_fee.final_capital < r_no_fee.final_capital

    def test_round_trip_records_trade(self):
        df = make_ohlc(seed=2, bars=30, trend=0.003, noise=0.001, start_price=1000.0)
        bt = Backtester(
            strategy=_buy_then_exit_after_n_bars(n=10, qty=100),
            initial_capital=10_000_000, commission_bps=0.0,
        )
        result = bt.run(df)
        assert len(result.trades) == 1
        t = result.trades[0]
        assert t.quantity == 100
        assert t.exit_price is not None
        # P&L should equal qty * (exit - entry)
        assert t.pnl == pytest.approx(100 * (t.exit_price - t.entry_price))

    def test_buy_rejected_when_insufficient_cash(self):
        # Start with almost no capital but try to buy expensive shares
        df = make_ohlc(seed=3, bars=10, trend=0.0, start_price=10_000.0)
        bt = Backtester(
            strategy=_buy_once_hold_strategy(qty=1000),  # cost ~10M
            initial_capital=1_000,  # only 1k
            commission_bps=0.0,
        )
        result = bt.run(df)
        # No entry possible => no trades, full capital preserved
        assert result.final_capital == pytest.approx(1_000)
        assert result.trades == []

    def test_equity_curve_length_matches_bars(self):
        df = make_ohlc(seed=4, bars=15, trend=0.0)
        bt = Backtester(strategy=lambda bar, state: [], initial_capital=5_000_000)
        result = bt.run(df)
        assert len(result.equity_curve) == len(df)

    def test_sell_without_position_ignored(self):
        """A strategy that calls sell when flat should not crash; nothing should happen."""
        df = make_ohlc(seed=5, bars=10, trend=0.0)
        def bad(bar, state):
            return [Order(side="sell", quantity=100)]
        bt = Backtester(strategy=bad, initial_capital=1_000_000, commission_bps=0.0)
        result = bt.run(df)
        assert result.trades == []
        assert result.final_capital == pytest.approx(1_000_000)


class TestComputeMetrics:
    def test_handles_no_trades(self):
        df = make_ohlc(seed=0, bars=60, trend=0.001)
        bt = Backtester(strategy=lambda bar, state: [], initial_capital=10_000_000)
        result = bt.run(df)
        metrics = compute_metrics(result)
        assert metrics.num_trades == 0
        assert metrics.win_rate == 0.0
        assert metrics.profit_factor == math.inf
        assert isinstance(metrics.cagr, float)

    def test_positive_trade_gives_winrate_1(self):
        # Force a strongly uptrending market so the round-trip is a winner
        df = make_ohlc(seed=1, bars=60, trend=0.01, noise=0.001, start_price=1000.0)
        bt = Backtester(
            strategy=_buy_then_exit_after_n_bars(n=20, qty=100),
            initial_capital=10_000_000, commission_bps=0.0,
        )
        result = bt.run(df)
        metrics = compute_metrics(result)
        assert metrics.num_trades == 1
        assert metrics.win_rate == 1.0
