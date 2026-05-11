"""Unit tests for technical indicators."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from saham_id.analysis.indicators import (
    atr,
    bollinger_bands,
    ema,
    macd,
    obv,
    rsi,
    rvol,
    sma,
    stoch,
    vwap,
    williams_r,
)


# ---------------------------------------------------------------------------
# Trend indicators
# ---------------------------------------------------------------------------
class TestTrend:
    def test_sma_matches_rolling_mean(self):
        s = pd.Series(range(30), dtype=float)
        result = sma(s, window=5)
        expected = s.rolling(5).mean()
        pd.testing.assert_series_equal(result, expected)

    def test_sma_has_nans_at_start(self):
        s = pd.Series(range(20), dtype=float)
        result = sma(s, window=5)
        assert result.iloc[:4].isna().all()
        assert not result.iloc[4:].isna().any()

    def test_ema_differs_from_sma(self, ohlc_trending_up):
        close = ohlc_trending_up["close"]
        ema_20 = ema(close, 20)
        sma_20 = sma(close, 20)
        # Both should have the same number of defined values, but values differ
        defined = ema_20.dropna().index.intersection(sma_20.dropna().index)
        diffs = (ema_20.loc[defined] - sma_20.loc[defined]).abs()
        assert diffs.sum() > 0

    def test_macd_histogram_equals_macd_minus_signal(self, ohlc_trending_up):
        close = ohlc_trending_up["close"]
        result = macd(close)
        assert {"macd", "signal", "histogram"} == set(result.columns)
        calc = (result["macd"] - result["signal"]).dropna()
        pd.testing.assert_series_equal(
            result["histogram"].dropna(), calc, check_names=False
        )


# ---------------------------------------------------------------------------
# Momentum indicators
# ---------------------------------------------------------------------------
class TestMomentum:
    def test_rsi_range(self, ohlc_trending_up):
        result = rsi(ohlc_trending_up["close"], 14).dropna()
        assert (result >= 0).all() and (result <= 100).all()

    def test_rsi_monotonic_uptrend_high(self):
        # Perfectly monotonic rising series -> RSI should be near 100
        s = pd.Series(range(1, 101), dtype=float)
        result = rsi(s, 14).dropna()
        assert result.iloc[-1] > 95

    def test_rsi_monotonic_downtrend_low(self):
        s = pd.Series(range(100, 0, -1), dtype=float)
        result = rsi(s, 14).dropna()
        assert result.iloc[-1] < 5

    def test_stoch_has_k_and_d(self, ohlc_trending_up):
        result = stoch(
            ohlc_trending_up["high"],
            ohlc_trending_up["low"],
            ohlc_trending_up["close"],
        )
        assert {"k", "d"} == set(result.columns)
        # %K should stay in [0, 100] (allowing small float slack)
        k = result["k"].dropna()
        assert k.min() >= -1e-9 and k.max() <= 100 + 1e-9

    def test_williams_r_range(self, ohlc_trending_up):
        r = williams_r(
            ohlc_trending_up["high"],
            ohlc_trending_up["low"],
            ohlc_trending_up["close"],
        ).dropna()
        assert r.min() >= -100 - 1e-9 and r.max() <= 0 + 1e-9


# ---------------------------------------------------------------------------
# Volatility indicators
# ---------------------------------------------------------------------------
class TestVolatility:
    def test_atr_non_negative(self, ohlc_trending_up):
        result = atr(
            ohlc_trending_up["high"],
            ohlc_trending_up["low"],
            ohlc_trending_up["close"],
        ).dropna()
        assert (result >= 0).all()

    def test_bollinger_bands_ordering(self, ohlc_trending_up):
        bb = bollinger_bands(ohlc_trending_up["close"], 20, 2.0).dropna()
        assert (bb["upper"] >= bb["middle"]).all()
        assert (bb["middle"] >= bb["lower"]).all()

    def test_bollinger_percent_b_typical_range(self, ohlc_range_bound):
        bb = bollinger_bands(ohlc_range_bound["close"], 20, 2.0).dropna()
        # Most values should sit in a reasonable band around [0, 1]
        assert bb["percent_b"].between(-0.5, 1.5).mean() > 0.9


# ---------------------------------------------------------------------------
# Volume indicators
# ---------------------------------------------------------------------------
class TestVolume:
    def test_obv_cumulative(self):
        close = pd.Series([10, 11, 10, 12, 12, 13], dtype=float)
        vol = pd.Series([100, 200, 150, 300, 50, 400], dtype=float)
        result = obv(close, vol)
        # +200 (up), -150 (down), +300 (up), 0 (flat), +400 (up) => 0, 200, 50, 350, 350, 750
        assert list(result) == [0.0, 200.0, 50.0, 350.0, 350.0, 750.0]

    def test_vwap_bounded_by_high_low(self, ohlc_trending_up):
        df = ohlc_trending_up.reset_index(drop=True)
        v = vwap(df["high"], df["low"], df["close"], df["volume"]).dropna()
        # VWAP should sit roughly between the min low and max high
        assert v.min() >= df["low"].min() * 0.5
        assert v.max() <= df["high"].max() * 2

    def test_rvol_around_one_for_stable_volume(self):
        vol = pd.Series([1000] * 30)
        result = rvol(vol, window=20).dropna()
        np.testing.assert_allclose(result.values, 1.0, atol=1e-9)

    def test_rvol_spike(self):
        vol = pd.Series([1000] * 25 + [5000])
        result = rvol(vol, window=20)
        assert float(result.iloc[-1]) == pytest.approx(5.0)
