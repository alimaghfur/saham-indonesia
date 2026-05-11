"""Backtest parameter optimizer — grid search for optimal strategy parameters.

Usage:
    from saham_id.backtest.optimizer import optimize_strategy, ParameterGrid

    grid = ParameterGrid({"rsi_period": [7, 14, 21], "oversold": [25, 30, 35]})
    results = optimize_strategy(ohlc, strategy_factory, grid, metric="sharpe")
    print(results.best_params)
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import pandas as pd

from saham_id.backtest.engine import Backtester, BacktestResult
from saham_id.backtest.metrics import PerformanceMetrics, compute_metrics


@dataclass
class ParameterGrid:
    """Grid of parameter combinations."""
    params: dict[str, list[Any]]

    @property
    def total_combinations(self) -> int:
        if not self.params:
            return 0
        result = 1
        for values in self.params.values():
            result *= len(values)
        return result

    def __iter__(self):
        keys = list(self.params.keys())
        values = list(self.params.values())
        if not keys:
            yield {}
            return
        for combo in itertools.product(*values):
            yield dict(zip(keys, combo))


@dataclass
class OptimizationRun:
    """Result of one parameter combination."""
    params: dict[str, Any]
    metrics: Optional[PerformanceMetrics] = None
    score: float = 0.0
    error: str = ""


@dataclass
class OptimizationResult:
    """Result of a full optimization run."""
    ticker: str
    metric_name: str
    total_runs: int
    successful_runs: int
    runs: list[OptimizationRun] = field(default_factory=list)

    @property
    def best_run(self) -> Optional[OptimizationRun]:
        successful = [r for r in self.runs if r.metrics is not None]
        return max(successful, key=lambda r: r.score) if successful else None

    @property
    def best_params(self) -> dict[str, Any]:
        best = self.best_run
        return best.params if best else {}

    @property
    def best_score(self) -> float:
        best = self.best_run
        return best.score if best else 0.0

    @property
    def best_metrics(self) -> Optional[PerformanceMetrics]:
        best = self.best_run
        return best.metrics if best else None

    def top_n(self, n: int = 10) -> list[OptimizationRun]:
        successful = [r for r in self.runs if r.metrics is not None]
        successful.sort(key=lambda r: r.score, reverse=True)
        return successful[:n]

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for run in self.runs:
            if run.metrics is None:
                continue
            row = dict(run.params)
            row["score"] = run.score
            row["total_return"] = run.metrics.total_return
            row["sharpe"] = run.metrics.sharpe
            row["max_drawdown"] = run.metrics.max_drawdown
            row["win_rate"] = run.metrics.win_rate
            row["num_trades"] = run.metrics.num_trades
            rows.append(row)
        return pd.DataFrame(rows)


StrategyFactory = Callable[[dict[str, Any]], Callable]


def _get_metric_value(metrics: PerformanceMetrics, metric_name: str) -> float:
    metric_map = {
        "sharpe": metrics.sharpe,
        "sortino": metrics.sortino,
        "total_return": metrics.total_return,
        "cagr": metrics.cagr,
        "win_rate": metrics.win_rate,
        "profit_factor": metrics.profit_factor,
        "max_drawdown": -metrics.max_drawdown,
        "num_trades": float(metrics.num_trades),
        "avg_trade_pct": metrics.avg_trade_pct,
    }
    return metric_map.get(metric_name, 0.0)


def optimize_strategy(
    ohlc: pd.DataFrame,
    strategy_factory: StrategyFactory,
    param_grid: ParameterGrid,
    metric: str = "sharpe",
    initial_capital: float = 100_000_000,
    commission_bps: float = 15.0,
    min_trades: int = 5,
    ticker: str = "",
) -> OptimizationResult:
    """Run grid search optimization over strategy parameters."""
    runs: list[OptimizationRun] = []
    successful = 0

    for params in param_grid:
        run = OptimizationRun(params=dict(params))
        try:
            strategy = strategy_factory(params)
            bt = Backtester(strategy=strategy, initial_capital=initial_capital, commission_bps=commission_bps)
            result = bt.run(ohlc)
            metrics = compute_metrics(result)
            if metrics.num_trades < min_trades:
                run.error = f"Only {metrics.num_trades} trades (min: {min_trades})"
                runs.append(run)
                continue
            run.metrics = metrics
            run.score = _get_metric_value(metrics, metric)
            successful += 1
        except Exception as exc:
            run.error = str(exc)
        runs.append(run)

    return OptimizationResult(
        ticker=ticker, metric_name=metric,
        total_runs=len(runs), successful_runs=successful, runs=runs,
    )


def optimize_rsi_strategy(
    ohlc: pd.DataFrame,
    rsi_periods: list[int] = None,
    oversold_levels: list[float] = None,
    overbought_levels: list[float] = None,
    metric: str = "sharpe",
    ticker: str = "",
) -> OptimizationResult:
    """Pre-built optimizer for RSI mean-reversion strategy."""
    from saham_id.backtest.engine import Order
    from saham_id.analysis.indicators import rsi as rsi_fn

    if rsi_periods is None:
        rsi_periods = [7, 10, 14, 21]
    if oversold_levels is None:
        oversold_levels = [20, 25, 30, 35]
    if overbought_levels is None:
        overbought_levels = [65, 70, 75, 80]

    grid = ParameterGrid({"rsi_period": rsi_periods, "oversold": oversold_levels, "overbought": overbought_levels})

    def factory(params: dict) -> Callable:
        period = params["rsi_period"]
        oversold = params["oversold"]
        overbought = params["overbought"]
        rsi_series = rsi_fn(ohlc["close"], period)

        def strategy(bar, state):
            idx = state.get("_bar_idx", 0)
            state["_bar_idx"] = idx + 1
            position = state["position"]
            rsi_val = rsi_series.iloc[idx] if idx < len(rsi_series) else None
            if rsi_val is None:
                return []
            rsi_float = float(rsi_val)
            if position == 0 and rsi_float < oversold:
                return [Order(side="buy", quantity=100)]
            if position > 0 and rsi_float > overbought:
                return [Order(side="sell", quantity=position)]
            return []
        return strategy

    return optimize_strategy(ohlc=ohlc, strategy_factory=factory, param_grid=grid, metric=metric, ticker=ticker)


def optimize_ma_crossover(
    ohlc: pd.DataFrame,
    fast_periods: list[int] = None,
    slow_periods: list[int] = None,
    metric: str = "sharpe",
    ticker: str = "",
) -> OptimizationResult:
    """Pre-built optimizer for MA crossover strategy."""
    from saham_id.backtest.engine import Order
    from saham_id.analysis.indicators import sma

    if fast_periods is None:
        fast_periods = [5, 10, 15, 20]
    if slow_periods is None:
        slow_periods = [30, 40, 50, 60, 100]

    grid = ParameterGrid({"ma_fast": fast_periods, "ma_slow": slow_periods})

    def factory(params: dict) -> Callable:
        fast = params["ma_fast"]
        slow = params["ma_slow"]
        if fast >= slow:
            return lambda bar, state: []
        fast_ma = sma(ohlc["close"], fast)
        slow_ma = sma(ohlc["close"], slow)

        def strategy(bar, state):
            idx = state.get("_bar_idx", 0)
            state["_bar_idx"] = idx + 1
            position = state["position"]
            fast_val = fast_ma.iloc[idx] if idx < len(fast_ma) else None
            slow_val = slow_ma.iloc[idx] if idx < len(slow_ma) else None
            if fast_val is None or slow_val is None:
                return []
            if position == 0 and float(fast_val) > float(slow_val):
                if idx > 0:
                    pf = fast_ma.iloc[idx - 1]
                    ps = slow_ma.iloc[idx - 1]
                    if pf is not None and ps is not None and float(pf) <= float(ps):
                        return [Order(side="buy", quantity=100)]
            if position > 0 and float(fast_val) < float(slow_val):
                if idx > 0:
                    pf = fast_ma.iloc[idx - 1]
                    ps = slow_ma.iloc[idx - 1]
                    if pf is not None and ps is not None and float(pf) >= float(ps):
                        return [Order(side="sell", quantity=position)]
            return []
        return strategy

    return optimize_strategy(ohlc=ohlc, strategy_factory=factory, param_grid=grid, metric=metric, ticker=ticker)
