"""BPJS reference strategy — buy at open, sell at close same day.

This is the canonical intraday test: if entered every day, what's the
net return after fees? Useful as a baseline for the BPJS screener.
"""

from __future__ import annotations

import pandas as pd

from saham_id.backtest.engine import Order


def bpjs_strategy(bar: pd.Series, state: dict) -> list[Order]:
    """Always long during the day: buy at today's open, sell at today's close.

    In the daily-bar engine, this means: issue a buy if flat, sell next bar.
    TODO: replace with realistic intraday logic when intraday engine is built.
    """
    position = state.get("position", 0)
    if position == 0:
        # naive sizing: 1 lot placeholder; real implementation should size
        # by cash * allocation / entry price.
        return [Order(side="buy", quantity=100, note="bpjs_entry")]
    return [Order(side="sell", quantity=position, note="bpjs_exit")]
