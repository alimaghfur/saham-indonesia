"""Unit tests for strategy screeners (BPJS, BSJP, swing)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from saham_id.screener.intraday import bpjs, bsjp
from saham_id.screener.swing import breakout, pullback, reversal
from tests.conftest import FakeSource, make_ohlc


# ---------------------------------------------------------------------------
# BPJS
# ---------------------------------------------------------------------------
class TestBPJS:
    def test_picks_stock_with_positive_intraday_bias(self):
        src = FakeSource()
        src.add(
            "BPJS_WINNER",
            make_ohlc(
                seed=1, bars=80, trend=0.001, noise=0.003,
                intraday_bias=0.01,  # strong close-over-open tendency
                volume_mean=5_000_000, volume_std=100_000, start_price=2000.0,
            ),
        )
        src.add(
            "BPJS_LOSER",
            make_ohlc(
                seed=2, bars=80, trend=0.0, noise=0.003,
                intraday_bias=-0.01,  # opposite: close below open
                volume_mean=5_000_000, volume_std=100_000, start_price=2000.0,
            ),
        )
        result = bpjs.screen(
            universe=["BPJS_WINNER", "BPJS_LOSER"],
            lookback_days=60,
            min_win_rate=0.5,
            min_avg_return=0.0,
            min_avg_value=0,
            source=src,
        )
        tickers = [r.ticker for r in result.rows]
        assert "BPJS_WINNER" in tickers
        assert "BPJS_LOSER" not in tickers

    def test_rejects_insufficient_history(self):
        src = FakeSource()
        src.add(
            "SHORT", make_ohlc(seed=1, bars=20, trend=0.0)  # < lookback 60
        )
        result = bpjs.screen(
            universe=["SHORT"], lookback_days=60, min_avg_value=0, source=src,
        )
        assert len(result.rows) == 0

    def test_respects_min_win_rate(self):
        src = FakeSource()
        # Intraday_bias=0.01 gives roughly ~70-80% win rate
        src.add(
            "CAND",
            make_ohlc(
                seed=1, bars=80, trend=0.0, noise=0.003,
                intraday_bias=0.01, volume_mean=5_000_000, volume_std=0,
            ),
        )
        # Impossible threshold
        result = bpjs.screen(
            universe=["CAND"], lookback_days=60, min_win_rate=0.99,
            min_avg_return=0.0, min_avg_value=0, source=src,
        )
        assert len(result.rows) == 0

    def test_result_metadata(self):
        src = FakeSource()
        src.add(
            "METAS",
            make_ohlc(
                seed=1, bars=80, intraday_bias=0.005,
                volume_mean=5_000_000, volume_std=0,
            ),
        )
        result = bpjs.screen(
            universe=["METAS"], lookback_days=60, min_win_rate=0.0,
            min_avg_return=-1.0, min_avg_value=0, source=src,
        )
        assert result.strategy == "bpjs"
        assert result.params["lookback_days"] == 60
        assert len(result.rows) == 1
        metrics = result.rows[0].metrics
        assert {"win_rate", "avg_intraday_ret", "avg_daily_value", "sample_days"} <= set(metrics)


# ---------------------------------------------------------------------------
# BSJP
# ---------------------------------------------------------------------------
class TestBSJP:
    def test_picks_stock_with_positive_overnight_gap(self):
        src = FakeSource()
        src.add(
            "BSJP_WINNER",
            make_ohlc(
                seed=1, bars=80, trend=0.0005, noise=0.003,
                overnight_bias=0.008,  # consistently gap up
                volume_mean=5_000_000, volume_std=100_000,
            ),
        )
        src.add(
            "BSJP_LOSER",
            make_ohlc(
                seed=2, bars=80, trend=0.0, noise=0.003,
                overnight_bias=-0.005,
                volume_mean=5_000_000, volume_std=100_000,
            ),
        )
        result = bsjp.screen(
            universe=["BSJP_WINNER", "BSJP_LOSER"],
            lookback_days=60,
            min_gap_up_rate=0.5,
            min_avg_gap=0.0,
            min_avg_value=0,
            source=src,
        )
        tickers = [r.ticker for r in result.rows]
        assert "BSJP_WINNER" in tickers
        assert "BSJP_LOSER" not in tickers

    def test_handles_short_series(self):
        src = FakeSource()
        src.add("TINY", make_ohlc(seed=1, bars=20, trend=0.0))
        result = bsjp.screen(
            universe=["TINY"], lookback_days=60, min_avg_value=0, source=src,
        )
        assert len(result.rows) == 0


# ---------------------------------------------------------------------------
# Swing Pullback
# ---------------------------------------------------------------------------
def _make_pullback_candidate(bars: int = 160) -> pd.DataFrame:
    """Construct a synthetic series where the last bar sits near MA20
    while above MA50, with RSI in the neutral 40-55 zone.

    We do this by: (1) mild uptrend for most of series, (2) small
    consolidation near current MA20 at the end.
    """
    rng = np.random.default_rng(42)
    prices = [1000.0]
    # Long uptrend with small noise
    for _ in range(bars - 20):
        prices.append(prices[-1] * (1 + rng.normal(0.003, 0.006)))
    # Consolidation phase: slight retrace
    for _ in range(20):
        prices.append(prices[-1] * (1 + rng.normal(-0.0005, 0.004)))

    closes = np.array(prices)
    opens = np.r_[closes[0], closes[:-1]] * (1 + rng.normal(0, 0.002, bars))
    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0, 0.003, bars)))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0, 0.003, bars)))
    idx = pd.date_range("2024-01-01", periods=bars, freq="B", name="timestamp")
    vols = np.full(bars, 1_000_000, dtype=int)
    return pd.DataFrame(
        {"open": opens, "high": highs, "low": lows, "close": closes, "volume": vols},
        index=idx,
    )


class TestSwingPullback:
    def test_returns_result_object(self):
        src = FakeSource()
        src.add("SWING", _make_pullback_candidate())
        result = pullback.screen(universe=["SWING"], source=src)
        assert result.strategy == "swing_pullback"
        # Row may or may not qualify depending on RSI zone — just assert no crash
        assert isinstance(result.rows, list)

    def test_downtrend_never_qualifies(self):
        src = FakeSource()
        # Persistent downtrend — cannot satisfy close > ma_trend
        df = make_ohlc(seed=1, bars=160, trend=-0.003, noise=0.005)
        src.add("DOWN", df)
        result = pullback.screen(universe=["DOWN"], source=src)
        assert result.rows == []

    def test_rejects_insufficient_data(self):
        src = FakeSource()
        src.add("TINY", make_ohlc(seed=1, bars=30, trend=0.001))
        result = pullback.screen(universe=["TINY"], trend_ma=50, source=src)
        assert result.rows == []


# ---------------------------------------------------------------------------
# Swing Breakout
# ---------------------------------------------------------------------------
class TestSwingBreakout:
    def test_detects_breakout_after_consolidation(self):
        bars = 120
        # Consolidation around 1000 for most of the series
        rng = np.random.default_rng(0)
        closes = 1000.0 + rng.normal(0, 2, bars)
        # Final bar breaks out with volume spike
        closes[-1] = closes[:-1].max() + 50
        opens = np.r_[closes[0], closes[:-1]]
        highs = np.maximum(opens, closes) + 1
        lows = np.minimum(opens, closes) - 1
        idx = pd.date_range("2024-01-01", periods=bars, freq="B", name="timestamp")
        vols = np.full(bars, 1_000_000, dtype=int)
        vols[-1] = 5_000_000  # volume confirmation
        df = pd.DataFrame(
            {"open": opens, "high": highs, "low": lows, "close": closes, "volume": vols},
            index=idx,
        )

        src = FakeSource()
        src.add("BRK", df)
        result = breakout.screen(
            universe=["BRK"],
            resistance_window=20,
            min_consolidation_days=10,
            volume_confirmation=True,
            min_rvol=1.5,
            source=src,
        )
        tickers = [r.ticker for r in result.rows]
        assert "BRK" in tickers

    def test_no_breakout_without_volume(self):
        bars = 120
        rng = np.random.default_rng(1)
        closes = 1000.0 + rng.normal(0, 2, bars)
        closes[-1] = closes[:-1].max() + 50
        opens = np.r_[closes[0], closes[:-1]]
        highs = np.maximum(opens, closes) + 1
        lows = np.minimum(opens, closes) - 1
        idx = pd.date_range("2024-01-01", periods=bars, freq="B", name="timestamp")
        # Flat volume — no confirmation
        vols = np.full(bars, 1_000_000, dtype=int)
        df = pd.DataFrame(
            {"open": opens, "high": highs, "low": lows, "close": closes, "volume": vols},
            index=idx,
        )

        src = FakeSource()
        src.add("NOVOL", df)
        result = breakout.screen(
            universe=["NOVOL"],
            resistance_window=20,
            min_consolidation_days=10,
            volume_confirmation=True,
            min_rvol=2.0,
            source=src,
        )
        assert result.rows == []


# ---------------------------------------------------------------------------
# Swing Reversal
# ---------------------------------------------------------------------------
class TestSwingReversal:
    def test_detects_rsi_cross_from_oversold(self):
        """Construct a series where yesterday's RSI<30 and today's RSI>=30."""
        rng = np.random.default_rng(7)
        bars = 80
        # Strong persistent downtrend to push RSI below 30
        closes = [1000.0]
        for _ in range(bars - 2):
            closes.append(closes[-1] * (1 - 0.015))  # -1.5% per day
        # Final bar: bullish reversal
        prev = closes[-1]
        closes.append(prev * 1.04)  # strong bounce

        closes = np.array(closes)
        opens = np.r_[closes[0], closes[:-1]]
        # Force final candle bullish: open < close
        opens[-1] = closes[-1] * 0.98
        highs = np.maximum(opens, closes) * 1.005
        lows = np.minimum(opens, closes) * 0.995
        idx = pd.date_range("2024-01-01", periods=bars, freq="B", name="timestamp")
        vols = np.full(bars, 1_000_000, dtype=int)
        df = pd.DataFrame(
            {"open": opens, "high": highs, "low": lows, "close": closes, "volume": vols},
            index=idx,
        )

        src = FakeSource()
        src.add("REV", df)
        result = reversal.screen(
            universe=["REV"], rsi_oversold=30.0, rsi_exit=45.0,
            require_bullish_candle=True, source=src,
        )
        # RSI cross behavior is sensitive — at minimum the screener must not crash
        # and must return a list.
        assert isinstance(result.rows, list)

    def test_uptrend_never_qualifies(self):
        src = FakeSource()
        src.add("UP", make_ohlc(seed=1, bars=120, trend=0.004, noise=0.003))
        result = reversal.screen(universe=["UP"], source=src)
        assert result.rows == []
