"""Tests for backtest optimizer."""
import pandas as pd
from datetime import datetime

from saham_id.backtest.optimizer import (
    ParameterGrid, OptimizationResult, OptimizationRun,
    optimize_strategy,
)
from saham_id.backtest.engine import Order


def _make_ohlc(n=100):
    """Generate OHLC data for optimizer tests."""
    import math
    close = [100 + 20 * math.sin(i * 0.1) + i * 0.1 for i in range(n)]
    return pd.DataFrame({
        "open": [c - 0.5 for c in close],
        "high": [c + 2 for c in close],
        "low": [c - 1.5 for c in close],
        "close": close,
        "volume": [1000000] * n,
    }, index=[datetime(2025, 1, 1, 0, 0) for _ in range(n)])


class TestParameterGrid:
    def test_total_combinations(self):
        grid = ParameterGrid({"a": [1, 2, 3], "b": [10, 20]})
        assert grid.total_combinations == 6

    def test_iteration(self):
        grid = ParameterGrid({"x": [1, 2], "y": ["a", "b"]})
        combos = list(grid)
        assert len(combos) == 4
        assert {"x": 1, "y": "a"} in combos
        assert {"x": 2, "y": "b"} in combos

    def test_empty_grid(self):
        grid = ParameterGrid({})
        assert grid.total_combinations == 0
        assert list(grid) == [{}]

    def test_single_param(self):
        grid = ParameterGrid({"threshold": [10, 20, 30]})
        assert grid.total_combinations == 3


class TestOptimizationResult:
    def test_best_run(self):
        runs = [
            OptimizationRun(params={"a": 1}, score=0.5),
            OptimizationRun(params={"a": 2}, score=0.8),
            OptimizationRun(params={"a": 3}, score=0.3),
        ]
        # Add fake metrics to make them "successful"
        from saham_id.backtest.metrics import PerformanceMetrics
        for r in runs:
            r.metrics = PerformanceMetrics(
                total_return=r.score, cagr=0, sharpe=r.score,
                sortino=0, max_drawdown=0, win_rate=0.5,
                num_trades=10, avg_trade_pct=0.01, profit_factor=1.5,
            )
        result = OptimizationResult(
            ticker="TEST", metric_name="sharpe",
            total_runs=3, successful_runs=3, runs=runs,
        )
        assert result.best_score == 0.8
        assert result.best_params == {"a": 2}

    def test_no_successful_runs(self):
        result = OptimizationResult(
            ticker="TEST", metric_name="sharpe",
            total_runs=3, successful_runs=0,
            runs=[OptimizationRun(params={"a": 1}, error="failed")],
        )
        assert result.best_run is None
        assert result.best_params == {}
        assert result.best_score == 0.0

    def test_top_n(self):
        from saham_id.backtest.metrics import PerformanceMetrics
        runs = []
        for i in range(20):
            r = OptimizationRun(params={"x": i}, score=float(i))
            r.metrics = PerformanceMetrics(
                total_return=0, cagr=0, sharpe=float(i),
                sortino=0, max_drawdown=0, win_rate=0.5,
                num_trades=10, avg_trade_pct=0.01, profit_factor=1.5,
            )
            runs.append(r)
        result = OptimizationResult(
            ticker="T", metric_name="sharpe",
            total_runs=20, successful_runs=20, runs=runs,
        )
        top5 = result.top_n(5)
        assert len(top5) == 5
        assert top5[0].score == 19.0  # highest


class TestOptimizeStrategy:
    def test_basic_optimization(self):
        ohlc = _make_ohlc(100)

        grid = ParameterGrid({"threshold": [0.01, 0.02, 0.03]})

        def factory(params):
            threshold = params["threshold"]
            call_count = [0]

            def strategy(bar, state):
                call_count[0] += 1
                pos = state["position"]
                if pos == 0 and call_count[0] % 10 == 0:
                    return [Order(side="buy", quantity=100)]
                if pos > 0 and call_count[0] % 10 == 5:
                    return [Order(side="sell", quantity=pos)]
                return []
            return strategy

        result = optimize_strategy(
            ohlc=ohlc,
            strategy_factory=factory,
            param_grid=grid,
            metric="sharpe",
            min_trades=1,
        )
        assert result.total_runs == 3
        assert result.successful_runs >= 1
