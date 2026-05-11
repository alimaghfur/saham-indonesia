"""Tests for multi-timeframe analysis module."""
from saham_id.analysis.mtf import (
    MTFResult, TimeframeView, _analyze_single_timeframe,
)
import pandas as pd


def _make_uptrend(n=60):
    """Create uptrending OHLCV data."""
    close = [100 + i * 0.5 + (i % 3 - 1) * 0.3 for i in range(n)]
    return pd.DataFrame({
        "open": [c - 0.3 for c in close],
        "high": [c + 1.5 for c in close],
        "low": [c - 1.0 for c in close],
        "close": close,
        "volume": [1000000 + i * 10000 for i in range(n)],
    })


def _make_downtrend(n=60):
    """Create downtrending OHLCV data."""
    close = [200 - i * 0.5 - (i % 3 - 1) * 0.3 for i in range(n)]
    return pd.DataFrame({
        "open": [c + 0.3 for c in close],
        "high": [c + 1.0 for c in close],
        "low": [c - 1.5 for c in close],
        "close": close,
        "volume": [1000000 - i * 5000 for i in range(n)],
    })


class TestTimeframeView:
    def test_create(self):
        view = TimeframeView(
            name="daily", bias="BULLISH", confidence=0.8,
            rsi=45.0, trend="uptrend",
        )
        assert view.name == "daily"
        assert view.bias == "BULLISH"
        assert view.confidence == 0.8


class TestAnalyzeSingleTimeframe:
    def test_uptrend_detection(self):
        df = _make_uptrend(60)
        view = _analyze_single_timeframe(df, "daily")
        # Should detect bullish bias in uptrend
        assert view.bias in ("BULLISH", "NEUTRAL")
        assert view.trend in ("uptrend", "sideways")

    def test_downtrend_detection(self):
        df = _make_downtrend(60)
        view = _analyze_single_timeframe(df, "daily")
        # Should detect bearish bias in downtrend
        assert view.bias in ("BEARISH", "NEUTRAL")
        assert view.trend in ("downtrend", "sideways")

    def test_insufficient_data(self):
        df = pd.DataFrame({
            "open": [100]*5, "high": [105]*5, "low": [95]*5,
            "close": [102]*5, "volume": [1000]*5,
        })
        view = _analyze_single_timeframe(df, "test")
        assert view.bias == "NEUTRAL"
        assert "Insufficient data" in view.notes


class TestMTFResult:
    def test_create(self):
        result = MTFResult(
            ticker="BBCA",
            consensus="BULLISH",
            alignment_score=0.8,
            recommendation="Strong BUY",
        )
        assert result.ticker == "BBCA"
        assert result.consensus == "BULLISH"
        assert result.alignment_score == 0.8
