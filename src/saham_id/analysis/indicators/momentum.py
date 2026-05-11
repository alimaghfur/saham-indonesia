"""Momentum indicators — RSI, Stochastic, Williams %R."""

from __future__ import annotations

import pandas as pd


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Relative Strength Index (Wilder's smoothing)."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def stoch(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_window: int = 14,
    d_window: int = 3,
) -> pd.DataFrame:
    """Stochastic oscillator (%K, %D)."""
    ll = low.rolling(k_window).min()
    hh = high.rolling(k_window).max()
    k = 100 * (close - ll) / (hh - ll).replace(0, pd.NA)
    d = k.rolling(d_window).mean()
    return pd.DataFrame({"k": k, "d": d})


def williams_r(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 14,
) -> pd.Series:
    """Williams %R (range: -100..0)."""
    hh = high.rolling(window).max()
    ll = low.rolling(window).min()
    return -100 * (hh - close) / (hh - ll).replace(0, pd.NA)
