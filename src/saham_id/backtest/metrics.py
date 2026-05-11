"""Performance metrics for a `BacktestResult`."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from saham_id.analysis.risk import max_drawdown, sharpe, sortino


@dataclass
class PerformanceMetrics:
    total_return: float
    cagr: float
    sharpe: float
    sortino: float
    max_drawdown: float
    win_rate: float
    num_trades: int
    avg_trade_pct: float
    profit_factor: float


def compute_metrics(result, periods_per_year: int = 252) -> PerformanceMetrics:
    """Compute standard performance metrics from a BacktestResult."""
    curve: pd.Series = result.equity_curve
    returns = curve.pct_change().dropna()

    years = max(1e-9, len(curve) / periods_per_year)
    cagr = (curve.iloc[-1] / curve.iloc[0]) ** (1 / years) - 1 if curve.iloc[0] > 0 else 0.0

    trades = result.trades
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl < 0]
    win_rate = len(wins) / len(trades) if trades else 0.0
    avg_trade_pct = float(np.mean([t.pnl_pct for t in trades])) if trades else 0.0

    gross_profit = sum(t.pnl for t in wins)
    gross_loss = abs(sum(t.pnl for t in losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    return PerformanceMetrics(
        total_return=result.total_return,
        cagr=float(cagr),
        sharpe=sharpe(returns, periods_per_year=periods_per_year),
        sortino=sortino(returns, periods_per_year=periods_per_year),
        max_drawdown=max_drawdown(curve),
        win_rate=win_rate,
        num_trades=len(trades),
        avg_trade_pct=avg_trade_pct,
        profit_factor=profit_factor,
    )
