"""Volume indicators — OBV, VWAP, Relative Volume."""

from __future__ import annotations

import numpy as np
import pandas as pd


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """On-Balance Volume (cumulative)."""
    sign = np.sign(close.diff()).fillna(0)
    return (sign * volume).cumsum()


def vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
) -> pd.Series:
    """Volume-Weighted Average Price (cumulative over the series).

    For session-based VWAP, call this after grouping by trading day.
    """
    tp = (high + low + close) / 3.0
    cum_tp_vol = (tp * volume).cumsum()
    cum_vol = volume.cumsum().replace(0, pd.NA)
    return cum_tp_vol / cum_vol


def rvol(volume: pd.Series, window: int = 20) -> pd.Series:
    """Relative Volume = current volume / N-period average volume."""
    avg = volume.rolling(window=window, min_periods=window).mean()
    return volume / avg.replace(0, pd.NA)
