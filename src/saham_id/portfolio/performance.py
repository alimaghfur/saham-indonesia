"""Portfolio performance tracker — daily P/L, benchmark comparison, monthly returns.

Usage:
    from saham_id.portfolio.performance import PortfolioPerformance
    perf = PortfolioPerformance(portfolio, source=src)
    print(perf.total_return_pct)
    print(perf.vs_benchmark("^JKSE"))
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


@dataclass
class DailyPnL:
    date: date
    portfolio_value: float
    daily_pnl: float
    daily_pnl_pct: float
    cumulative_pnl: float
    cumulative_pnl_pct: float


@dataclass
class BenchmarkComparison:
    ticker: str = "^JKSE"
    portfolio_return: float = 0.0
    benchmark_return: float = 0.0
    alpha: float = 0.0
    outperforming: bool = False
    period: str = ""


@dataclass
class MonthlyReturn:
    year: int
    month: int
    month_name: str
    return_pct: float
    is_positive: bool = True


@dataclass
class PerformanceSummary:
    total_return_pct: float = 0.0
    total_pnl: float = 0.0
    best_day_pct: float = 0.0
    worst_day_pct: float = 0.0
    positive_days: int = 0
    negative_days: int = 0
    win_rate: float = 0.0
    max_drawdown_pct: float = 0.0
    current_drawdown_pct: float = 0.0
    sharpe_estimate: float = 0.0
    benchmark: Optional[BenchmarkComparison] = None
    monthly_returns: list[MonthlyReturn] = field(default_factory=list)


def calculate_performance(
    daily_values: list[float],
    initial_capital: float,
    benchmark_ticker: str = "^JKSE",
    period: str = "1y",
    source: Optional[DataSource] = None,
) -> PerformanceSummary:
    """Calculate portfolio performance from daily portfolio values."""
    if not daily_values or len(daily_values) < 2:
        return PerformanceSummary()

    # Daily returns
    daily_returns = []
    for i in range(1, len(daily_values)):
        if daily_values[i - 1] > 0:
            daily_returns.append((daily_values[i] - daily_values[i - 1]) / daily_values[i - 1])
        else:
            daily_returns.append(0.0)

    # Total return
    total_return = (daily_values[-1] - initial_capital) / initial_capital if initial_capital > 0 else 0
    total_pnl = daily_values[-1] - initial_capital

    # Win/loss days
    positive = sum(1 for r in daily_returns if r > 0)
    negative = sum(1 for r in daily_returns if r < 0)
    win_rate = positive / len(daily_returns) if daily_returns else 0

    # Best/worst
    best = max(daily_returns) if daily_returns else 0
    worst = min(daily_returns) if daily_returns else 0

    # Max drawdown
    peak = daily_values[0]
    max_dd = 0.0
    for v in daily_values:
        if v > peak:
            peak = v
        dd = (v - peak) / peak if peak > 0 else 0
        if dd < max_dd:
            max_dd = dd

    current_dd = (daily_values[-1] - peak) / peak if peak > 0 else 0

    # Sharpe estimate (annualized)
    if daily_returns:
        import math
        mean_r = sum(daily_returns) / len(daily_returns)
        if len(daily_returns) > 1:
            var = sum((r - mean_r) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
            std_r = math.sqrt(var) if var > 0 else 0.001
        else:
            std_r = 0.001
        sharpe = (mean_r / std_r) * math.sqrt(252) if std_r > 0 else 0
    else:
        sharpe = 0

    # Benchmark comparison
    bench = None
    try:
        src = source or get_source()
        bench_df = src.get_ohlc(benchmark_ticker, period=period, interval="1d")
        if not bench_df.empty and len(bench_df) > 2:
            bench_first = float(bench_df["close"].iloc[0])
            bench_last = float(bench_df["close"].iloc[-1])
            if bench_first > 0:
                bench_return = (bench_last - bench_first) / bench_first
                alpha = total_return - bench_return
                bench = BenchmarkComparison(
                    ticker=benchmark_ticker, portfolio_return=total_return,
                    benchmark_return=bench_return, alpha=alpha,
                    outperforming=alpha > 0, period=period,
                )
    except Exception:
        pass

    return PerformanceSummary(
        total_return_pct=total_return, total_pnl=total_pnl,
        best_day_pct=best, worst_day_pct=worst,
        positive_days=positive, negative_days=negative,
        win_rate=win_rate, max_drawdown_pct=max_dd,
        current_drawdown_pct=current_dd, sharpe_estimate=sharpe,
        benchmark=bench,
    )
