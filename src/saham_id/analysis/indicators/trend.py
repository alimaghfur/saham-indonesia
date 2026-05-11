"""Trend indicators — SMA, EMA, MACD."""

from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, window: int = 20) -> pd.Series:
    """Simple Moving Average."""
    return close.rolling(window=window, min_periods=window).mean()


def ema(close: pd.Series, window: int = 20) -> pd.Series:
    """Exponential Moving Average."""
    return close.ewm(span=window, adjust=False, min_periods=window).mean()


def macd(
    close: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> pd.DataFrame:
    """Moving Average Convergence Divergence.

    Returns DataFrame with columns ``macd``, ``signal``, ``histogram``.
    """
    fast_ema = ema(close, fast)
    slow_ema = ema(close, slow)
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return pd.DataFrame(
        {"macd": macd_line, "signal": signal_line, "histogram": hist}
    )
