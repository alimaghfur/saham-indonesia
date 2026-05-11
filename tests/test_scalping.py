"""Tests for the scalping screener."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from saham_id.data.sources.base import NotImplementedForSource
from saham_id.screener.intraday import scalping
from tests.conftest import FakeSource


def _intraday_bars(
    *,
    bars: int = 300,
    seed: int = 0,
    base_price: float = 5000.0,
    trend_per_bar: float = 0.0,
    noise: float = 0.002,
    volume_mean: int = 50_000,
    volume_std: int = 5_000,
    final_return_boost: float = 0.0,
    final_volume_multiplier: float = 1.0,
) -> pd.DataFrame:
    """Generate deterministic 5m intraday bars for scalping tests."""
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2024-06-17 09:00", periods=bars, freq="5min", name="timestamp")
    log_rets = rng.normal(loc=trend_per_bar, scale=noise, size=bars)
    closes = base_price * np.exp(np.cumsum(log_rets))
    # Boost the final bar(s) to simulate a momentum push
    if final_return_boost:
        closes[-1] = closes[-2] * (1 + final_return_boost)

    opens = np.r_[closes[0], closes[:-1]]
    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0, noise / 2, bars)))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0, noise / 2, bars)))
    vols = np.maximum(
        1, rng.normal(volume_mean, volume_std, bars).astype(int)
    )
    if final_volume_multiplier != 1.0:
        vols[-1] = int(vols[-1] * final_volume_multiplier)

    return pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": vols},
        index=idx,
    )


class TestScalpingScreener:
    def test_identifies_momentum_candidate(self):
        """A ticker with a volume spike + positive late-bar return should score high."""
        src = FakeSource()
        src.add(
            "HOT",
            _intraday_bars(
                seed=1,
                bars=300,
                volume_mean=100_000,
                final_return_boost=0.015,
                final_volume_multiplier=4.0,
            ),
        )
        src.add(
            "MEH",
            _intraday_bars(
                seed=2, bars=300, volume_mean=100_000, noise=0.0015,
            ),
        )

        result = scalping.screen(
            universe=["HOT", "MEH"],
            interval="5m",
            period="5d",
            min_avg_volume_per_bar=1_000,
            min_avg_value_per_bar=0,
            min_atr_pct=0.0,
            min_rvol=0.0,
            source=src,
        )
        tickers = [r.ticker for r in result.rows]
        assert "HOT" in tickers
        # HOT's rvol & momentum should place it above MEH (when MEH qualifies)
        idx_hot = tickers.index("HOT")
        if "MEH" in tickers:
            idx_meh = tickers.index("MEH")
            assert idx_hot < idx_meh

    def test_rejects_low_liquidity_ticker(self):
        src = FakeSource()
        src.add(
            "ILLIQUID",
            _intraday_bars(
                seed=1, bars=300, volume_mean=500, volume_std=50,
                final_return_boost=0.02, final_volume_multiplier=5.0,
            ),
        )
        # Volume far below 10k/bar minimum
        result = scalping.screen(
            universe=["ILLIQUID"], interval="5m", period="5d",
            min_avg_volume_per_bar=10_000, min_avg_value_per_bar=0,
            min_atr_pct=0.0, min_rvol=0.0, source=src,
        )
        assert result.rows == []

    def test_rejects_low_volatility_ticker(self):
        # Near-zero noise: flat bars, ATR% tiny
        src = FakeSource()
        src.add(
            "FLAT",
            _intraday_bars(
                seed=1, bars=300, noise=1e-5, volume_mean=100_000,
            ),
        )
        result = scalping.screen(
            universe=["FLAT"], interval="5m", period="5d",
            min_avg_volume_per_bar=1_000, min_avg_value_per_bar=0,
            min_atr_pct=0.01,  # demand ATR >= 1%
            min_rvol=0.0, source=src,
        )
        assert result.rows == []

    def test_rejects_low_rvol(self):
        src = FakeSource()
        src.add(
            "QUIET",
            _intraday_bars(
                seed=1, bars=300, volume_mean=100_000, volume_std=500,
                # No final_volume_multiplier => rvol ~ 1.0
            ),
        )
        result = scalping.screen(
            universe=["QUIET"], interval="5m", period="5d",
            min_avg_volume_per_bar=1_000, min_avg_value_per_bar=0,
            min_atr_pct=0.0,
            min_rvol=3.0,  # impossibly high
            source=src,
        )
        assert result.rows == []

    def test_insufficient_data_ticker_skipped_not_raised(self):
        src = FakeSource()
        # Only 30 bars — below the default 60-bar rvol window
        src.add("TINY", _intraday_bars(seed=1, bars=30, volume_mean=100_000))
        # Well-behaved populated ticker alongside it
        src.add(
            "OK",
            _intraday_bars(
                seed=2, bars=300, volume_mean=100_000,
                final_volume_multiplier=3.0, final_return_boost=0.01,
            ),
        )
        result = scalping.screen(
            universe=["TINY", "OK"], interval="5m", period="5d",
            min_avg_volume_per_bar=1_000, min_avg_value_per_bar=0,
            min_atr_pct=0.0, min_rvol=0.0, source=src,
        )
        tickers = [r.ticker for r in result.rows]
        assert "TINY" not in tickers

    def test_raises_if_source_has_no_intraday_and_no_candidates(self):
        """If the source cannot deliver intraday bars at all and nothing
        qualifies, surface the source error so callers know to upgrade."""
        src = FakeSource()  # empty — every ticker request raises NotImplementedForSource
        with pytest.raises(NotImplementedForSource):
            scalping.screen(
                universe=["ANY"], interval="1m", period="5d",
                min_avg_volume_per_bar=0, min_avg_value_per_bar=0,
                min_atr_pct=0.0, min_rvol=0.0, source=src,
            )

    def test_result_metadata(self):
        src = FakeSource()
        src.add(
            "META",
            _intraday_bars(
                seed=1, bars=300, volume_mean=100_000,
                final_volume_multiplier=3.0, final_return_boost=0.01,
            ),
        )
        result = scalping.screen(
            universe=["META"], interval="5m", period="5d",
            min_avg_volume_per_bar=1_000, min_avg_value_per_bar=0,
            min_atr_pct=0.0, min_rvol=0.0, source=src,
        )
        assert result.strategy == "scalping"
        assert result.params["interval"] == "5m"
        if result.rows:
            required = {"last", "momentum_z", "rvol", "atr_pct", "breakout_z"}
            assert required <= set(result.rows[0].metrics)
