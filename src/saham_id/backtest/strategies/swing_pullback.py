"""Swing pullback strategy — buy on pullback to MA20 in uptrend, exit on MA50 break."""

from __future__ import annotations

import pandas as pd

from saham_id.backtest.engine import Order


def swing_pullback_strategy(bar: pd.Series, state: dict) -> list[Order]:
    """Entry: price touches MA20 while above MA50. Exit: close below MA50.

    Assumes `bar` has ma_20 and ma_50 pre-computed. A runner should enrich
    the OHLC DataFrame before calling the backtester. TODO: make strategies
    responsible for their own feature computation via a callback.
    """
    ma20 = bar.get("ma_20")
    ma50 = bar.get("ma_50")
    close = bar.get("close")
    position = state.get("position", 0)

    if ma20 is None or ma50 is None or pd.isna(ma20) or pd.isna(ma50):
        return []

    # Entry
    if position == 0 and close > ma50 and abs(close - ma20) / ma20 < 0.02:
        return [Order(side="buy", quantity=100, note="pullback_entry")]

    # Exit
    if position > 0 and close < ma50:
        return [Order(side="sell", quantity=position, note="ma50_break_exit")]

    return []
