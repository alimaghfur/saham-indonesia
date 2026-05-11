"""Unit tests for `saham_id.market.movers`."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from saham_id.market import movers
from tests.conftest import FakeSource, make_ohlc


def _rig_source_with_last_day_changes(changes: dict[str, float]) -> FakeSource:
    """Build a FakeSource where each ticker has a final-day return = `changes[ticker]`.

    Keeps other bars neutral so only the last day drives the 1D mover rank.
    """
    src = FakeSource()
    for i, (ticker, pct) in enumerate(changes.items()):
        df = make_ohlc(seed=i, bars=30, trend=0.0, noise=0.001, start_price=1000.0)
        # Adjust final close to produce the target 1-day return vs previous close
        prev_close = float(df["close"].iloc[-2])
        new_close = prev_close * (1 + pct)
        df.iloc[-1, df.columns.get_loc("close")] = new_close
        df.iloc[-1, df.columns.get_loc("high")] = max(new_close, df["high"].iloc[-1])
        df.iloc[-1, df.columns.get_loc("low")] = min(new_close, df["low"].iloc[-1])
        src.add(ticker, df)
    return src


class TestTopGainers:
    def test_ordering_desc_by_change_pct(self):
        src = _rig_source_with_last_day_changes(
            {"AAA": 0.02, "BBB": 0.05, "CCC": -0.01, "DDD": 0.08, "EEE": 0.01}
        )
        result = movers.top_gainers(
            universe=["AAA", "BBB", "CCC", "DDD", "EEE"],
            period="1D",
            min_price=0,
            min_value=0,
            source=src,
        )
        tickers = [m.ticker for m in result]
        assert tickers[:3] == ["DDD", "BBB", "AAA"]

    def test_filters_by_min_price(self):
        src = FakeSource()
        # LOW has prices ~10, HIGH has prices ~5000
        low = make_ohlc(seed=1, bars=10, trend=0.0, noise=0.001, start_price=10.0)
        high = make_ohlc(seed=2, bars=10, trend=0.0, noise=0.001, start_price=5000.0)
        # Boost last-day change for both so they'd otherwise qualify
        for df in (low, high):
            df.iloc[-1, df.columns.get_loc("close")] = (
                df["close"].iloc[-2] * 1.03
            )
        src.add("LOW", low)
        src.add("HIGH", high)

        result = movers.top_gainers(
            universe=["LOW", "HIGH"],
            period="1D",
            min_price=100,
            min_value=0,
            source=src,
        )
        assert {m.ticker for m in result} == {"HIGH"}

    def test_empty_universe(self):
        assert movers.top_gainers(universe=[], source=FakeSource()) == []

    def test_top_n_limit(self):
        src = _rig_source_with_last_day_changes(
            {f"T{i:02d}": 0.01 + i * 0.001 for i in range(10)}
        )
        result = movers.top_gainers(
            universe=list(src._data.keys()),
            period="1D",
            min_price=0,
            min_value=0,
            top_n=3,
            source=src,
        )
        assert len(result) == 3


class TestTopLosers:
    def test_ordering_asc_by_change_pct(self):
        src = _rig_source_with_last_day_changes(
            {"AAA": 0.02, "BBB": -0.05, "CCC": -0.08, "DDD": 0.01, "EEE": -0.02}
        )
        result = movers.top_losers(
            universe=["AAA", "BBB", "CCC", "DDD", "EEE"],
            period="1D",
            min_price=0,
            min_value=0,
            source=src,
        )
        tickers = [m.ticker for m in result]
        assert tickers[:3] == ["CCC", "BBB", "EEE"]


class TestMostActive:
    def test_by_value_ordering(self):
        src = FakeSource()
        src.add("LOW", make_ohlc(seed=1, bars=5, volume_mean=10_000, volume_std=0))
        src.add("MID", make_ohlc(seed=2, bars=5, volume_mean=100_000, volume_std=0))
        src.add("HIGH", make_ohlc(seed=3, bars=5, volume_mean=1_000_000, volume_std=0))
        result = movers.most_active(
            universe=["LOW", "MID", "HIGH"],
            by="value",
            source=src,
        )
        assert result[0].ticker == "HIGH"
