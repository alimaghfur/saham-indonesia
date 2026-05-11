"""Unit tests for trending, unusual_activity, and breadth."""

from __future__ import annotations

import pandas as pd
import pytest

from saham_id.market import breadth, trending, unusual_activity
from tests.conftest import FakeSource, make_ohlc


class TestTrending:
    def test_high_rvol_with_positive_momentum_ranks_top(self):
        src = FakeSource()
        # Boring ticker: flat volume + flat returns
        src.add(
            "BORE",
            make_ohlc(
                seed=1,
                bars=120,
                trend=0.0,
                noise=0.003,
                volume_mean=1_000_000,
                volume_std=50_000,
                start_price=2000.0,
            ),
        )
        # Trending ticker: positive trend + last-day volume spike
        hot = make_ohlc(
            seed=2,
            bars=120,
            trend=0.003,
            noise=0.005,
            volume_mean=1_000_000,
            volume_std=50_000,
            start_price=2000.0,
        )
        # Spike last-day volume to 5x normal
        hot.iloc[-1, hot.columns.get_loc("volume")] = 5_000_000
        # Also mark a breakout
        hot.iloc[-1, hot.columns.get_loc("close")] = (
            hot["high"].iloc[:-1].max() * 1.02
        )
        src.add("HOT", hot)

        result = trending.detect(
            universe=["BORE", "HOT"],
            timeframe="1D",
            min_rvol=1.5,
            min_avg_value=0,
            top_n=5,
            source=src,
        )
        tickers = [r.ticker for r in result.rows]
        assert "HOT" in tickers
        # HOT should sort above BORE (when both qualify)
        if "BORE" in tickers:
            idx_hot = tickers.index("HOT")
            idx_bore = tickers.index("BORE")
            assert idx_hot < idx_bore

    def test_rejects_low_volume(self):
        src = FakeSource()
        src.add(
            "QUIET",
            make_ohlc(
                seed=1, bars=120, trend=0.002, volume_mean=500_000, volume_std=10_000
            ),
        )
        result = trending.detect(
            universe=["QUIET"],
            timeframe="1D",
            min_rvol=10.0,  # impossibly high bar
            min_avg_value=0,
            source=src,
        )
        assert len(result.rows) == 0


class TestUnusualActivity:
    def test_detects_volume_spike(self):
        src = FakeSource()
        df = make_ohlc(
            seed=1, bars=120, trend=0.0, noise=0.002,
            volume_mean=1_000_000, volume_std=20_000,
        )
        df.iloc[-1, df.columns.get_loc("volume")] = 10_000_000  # huge spike
        src.add("SPIKE", df)
        result = unusual_activity.detect(
            universe=["SPIKE"], volume_sigma=2.5, price_sigma=10.0, source=src,
        )
        assert len(result.rows) == 1
        assert result.rows[0].metrics["volume_sigma"] > 2.5

    def test_detects_price_anomaly(self):
        src = FakeSource()
        df = make_ohlc(
            seed=1, bars=120, trend=0.0, noise=0.002,
            volume_mean=1_000_000, volume_std=100_000,
        )
        # Force last-day return way above baseline
        df.iloc[-1, df.columns.get_loc("close")] = df["close"].iloc[-2] * 1.15
        src.add("JUMPER", df)
        result = unusual_activity.detect(
            universe=["JUMPER"], volume_sigma=99.0, price_sigma=2.0, source=src,
        )
        assert len(result.rows) == 1
        assert abs(result.rows[0].metrics["price_sigma"]) > 2.0

    def test_quiet_ticker_not_flagged(self):
        src = FakeSource()
        src.add(
            "QUIET",
            make_ohlc(
                seed=1, bars=120, trend=0.0, noise=0.002,
                volume_mean=1_000_000, volume_std=20_000,
            ),
        )
        result = unusual_activity.detect(
            universe=["QUIET"], volume_sigma=2.5, price_sigma=2.0, source=src,
        )
        assert len(result.rows) == 0


class TestBreadth:
    def test_counts_advancers_decliners(self):
        src = FakeSource()
        # Advancer: rising last day
        up = make_ohlc(seed=1, bars=260, trend=0.0)
        up.iloc[-1, up.columns.get_loc("close")] = up["close"].iloc[-2] * 1.02
        src.add("UP", up)
        # Decliner: falling last day
        dn = make_ohlc(seed=2, bars=260, trend=0.0)
        dn.iloc[-1, dn.columns.get_loc("close")] = dn["close"].iloc[-2] * 0.98
        src.add("DN", dn)
        # Unchanged
        fl = make_ohlc(seed=3, bars=260, trend=0.0)
        fl.iloc[-1, fl.columns.get_loc("close")] = fl["close"].iloc[-2]
        src.add("FL", fl)

        snap = breadth.snapshot(universe=["UP", "DN", "FL"], source=src)
        assert snap.advancers == 1
        assert snap.decliners == 1
        assert snap.unchanged == 1
        assert snap.total == 3
        assert snap.ad_ratio == pytest.approx(1.0)
        assert snap.advancing_pct == pytest.approx(1 / 3)

    def test_new_high_detection(self):
        src = FakeSource()
        df = make_ohlc(seed=4, bars=260, trend=0.0, noise=0.001)
        # Force last close to exceed the rolling 252-day high
        df.iloc[-1, df.columns.get_loc("close")] = (
            df["high"].tail(252).max() * 1.01
        )
        src.add("NH", df)
        snap = breadth.snapshot(universe=["NH"], source=src)
        assert snap.new_highs_52w == 1
