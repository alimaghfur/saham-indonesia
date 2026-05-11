"""Tests for backtest engine."""
from datetime import datetime

import pandas as pd

from saham_id.backtest.engine import BacktestResult, Backtester, Order, Trade
from saham_id.backtest.metrics import compute_metrics
from saham_id.backtest.strategies import bpjs_strategy, swing_pullback_strategy


def _make_ohlc(n=20, start_price=100, trend=1.0):
    """Generate simple OHLC data."""
    close_data = [start_price + i * trend for i in range(n)]
    data = {
        "open": [c - 0.5 for c in close_data],
        "high": [c + 2 for c in close_data],
        "low": [c - 1.5 for c in close_data],
        "close": close_data,
        "volume": [1_000_000] * n,
    }
    index = [datetime(2025, 1, 6 + i, 0, 0) for i in range(n)]
    return pd.DataFrame(data, index=index)


class TestBacktester:
    def test_buy_and_hold(self):
        df = _make_ohlc(10, start_price=100, trend=2.0)

        def buy_once(bar, state):
            if state["position"] == 0:
                return [Order(side="buy", quantity=100)]
            return []

        bt = Backtester(strategy=buy_once, initial_capital=100_000_000)
        result = bt.run(df)
        assert result.final_capital > result.initial_capital  # uptrend profit

    def test_empty_ohlc_raises(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        bt = Backtester(strategy=lambda bar, state: [], initial_capital=100_000_000)
        try:
            bt.run(df)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_commission_reduces_profit(self):
        df = _make_ohlc(10, start_price=100, trend=2.0)

        def buy_sell(bar, state):
            if state["position"] == 0:
                return [Order(side="buy", quantity=100)]
            return [Order(side="sell", quantity=state["position"])]

        bt_no_fee = Backtester(strategy=buy_sell, initial_capital=100_000_000, commission_bps=0)
        bt_fee = Backtester(strategy=buy_sell, initial_capital=100_000_000, commission_bps=30)
        r1 = bt_no_fee.run(df)
        r2 = bt_fee.run(df)
        assert r1.final_capital >= r2.final_capital

    def test_cannot_buy_more_than_cash(self):
        df = _make_ohlc(5, start_price=1_000_000)  # Expensive stock

        def buy_lots(bar, state):
            return [Order(side="buy", quantity=10_000)]  # Way too expensive

        bt = Backtester(strategy=buy_lots, initial_capital=100)  # Only 100 cash
        result = bt.run(df)
        assert result.final_capital == 100  # No trades executed


class TestBPJSStrategy:
    def test_bpjs_alternates(self):
        df = _make_ohlc(10)
        bt = Backtester(strategy=bpjs_strategy, initial_capital=100_000_000)
        result = bt.run(df)
        assert len(result.trades) > 0


class TestSwingPullbackStrategy:
    def test_with_ma_columns(self):
        n = 10
        data = {
            "open": [100] * n,
            "high": [105] * n,
            "low": [95] * n,
            "close": [101, 100.5, 101, 100, 99, 98, 97, 96, 95, 94],
            "volume": [1_000_000] * n,
            "ma_20": [100] * n,
            "ma_50": [95] * n,
        }
        index = [datetime(2025, 1, 6 + i, 0, 0) for i in range(n)]
        df = pd.DataFrame(data, index=index)

        bt = Backtester(strategy=swing_pullback_strategy, initial_capital=100_000_000)
        result = bt.run(df)
        # Strategy should attempt entry near MA20 when above MA50
        assert result.final_capital > 0


class TestMetrics:
    def test_compute_metrics(self):
        df = _make_ohlc(20, trend=1.0)

        def simple(bar, state):
            if state["position"] == 0:
                return [Order(side="buy", quantity=100)]
            return [Order(side="sell", quantity=state["position"])]

        bt = Backtester(strategy=simple, initial_capital=100_000_000)
        result = bt.run(df)
        metrics = compute_metrics(result)
        assert metrics.num_trades >= 0
        assert 0 <= metrics.win_rate <= 1
        assert metrics.max_drawdown <= 0
