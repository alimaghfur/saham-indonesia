"""Risk metrics — volatility, Sharpe, Sortino, max drawdown, beta, VaR."""

from __future__ import annotations

import numpy as np
import pandas as pd


def log_returns(close: pd.Series) -> pd.Series:
    return np.log(close / close.shift(1)).dropna()


def volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Annualized volatility from a return series."""
    return float(returns.std(ddof=0) * np.sqrt(periods_per_year))


def sharpe(returns: pd.Series, risk_free: float = 0.0, periods_per_year: int = 252) -> float:
    """Annualized Sharpe ratio. `risk_free` is annual rate (e.g. 0.06)."""
    excess = returns - (risk_free / periods_per_year)
    sd = excess.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return 0.0
    return float(excess.mean() / sd * np.sqrt(periods_per_year))


def sortino(returns: pd.Series, risk_free: float = 0.0, periods_per_year: int = 252) -> float:
    """Annualized Sortino ratio — only downside deviation in denominator."""
    excess = returns - (risk_free / periods_per_year)
    downside = excess[excess < 0]
    dd = downside.std(ddof=0)
    if dd == 0 or np.isnan(dd):
        return 0.0
    return float(excess.mean() / dd * np.sqrt(periods_per_year))


def max_drawdown(equity_curve: pd.Series) -> float:
    """Largest peak-to-trough decline (as a negative fraction, e.g. -0.35)."""
    roll_max = equity_curve.cummax()
    drawdown = equity_curve / roll_max - 1.0
    return float(drawdown.min())


def beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
    """Asset beta vs market — cov(a, m) / var(m)."""
    aligned = pd.concat([asset_returns, market_returns], axis=1).dropna()
    aligned.columns = ["a", "m"]
    var = aligned["m"].var(ddof=0)
    if var == 0:
        return 0.0
    return float(aligned.cov(ddof=0).loc["a", "m"] / var)


def historical_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """Historical VaR — loss level at the given confidence (positive number)."""
    if returns.empty:
        return 0.0
    q = returns.quantile(1 - confidence)
    return float(-q)
