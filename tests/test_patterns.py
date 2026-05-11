"""Tests for candlestick pattern recognition."""
from saham_id.analysis.patterns import (
    PatternBias, PatternResult,
    detect_doji, detect_hammer, detect_inverted_hammer,
    detect_marubozu, detect_engulfing, detect_harami,
    detect_three_white_soldiers, detect_three_black_crows,
    detect_patterns, pattern_summary,
)
import pandas as pd


class TestSingleBarPatterns:
    def test_doji(self):
        # Open = close, long wicks
        assert detect_doji(100, 105, 95, 100.5) is True
        # Normal bar, not doji
        assert detect_doji(100, 108, 99, 107) is False

    def test_hammer(self):
        # Small body at top, long lower shadow
        assert detect_hammer(104, 105, 95, 105) is True
        # Not a hammer (body too large)
        assert detect_hammer(95, 110, 94, 108) is False

    def test_inverted_hammer(self):
        # Small body at bottom, long upper shadow, tiny lower shadow
        assert detect_inverted_hammer(96, 105, 95.8, 96.5) is True
        # Normal bar
        assert detect_inverted_hammer(100, 105, 99, 104) is False

    def test_marubozu_bullish(self):
        # Full-body bullish candle
        result = detect_marubozu(100, 110.2, 99.8, 110)
        assert result == "bullish"

    def test_marubozu_bearish(self):
        result = detect_marubozu(110, 110.2, 99.8, 100)
        assert result == "bearish"

    def test_marubozu_none(self):
        # Normal bar with shadows
        result = detect_marubozu(100, 108, 95, 105)
        assert result is None


class TestTwoBarPatterns:
    def test_bullish_engulfing(self):
        # Bar1: bearish, Bar2: bullish engulfs
        result = detect_engulfing(105, 106, 99, 100, 99, 107, 98, 106)
        assert result == "bullish"

    def test_bearish_engulfing(self):
        # Bar1: bullish, Bar2: bearish engulfs
        result = detect_engulfing(100, 106, 99, 105, 106, 107, 98, 99)
        assert result == "bearish"

    def test_no_engulfing(self):
        result = detect_engulfing(100, 103, 99, 102, 101, 104, 100, 103)
        assert result is None

    def test_bullish_harami(self):
        # Bar1: large bearish, Bar2: small bullish inside
        result = detect_harami(110, 111, 99, 100, 103, 106, 102, 105)
        assert result == "bullish"

    def test_bearish_harami(self):
        # Bar1: large bullish, Bar2: small bearish inside
        result = detect_harami(100, 111, 99, 110, 107, 108, 103, 104)
        assert result == "bearish"


class TestThreeBarPatterns:
    def test_three_white_soldiers(self):
        bars = [
            (100, 106, 99, 105),   # bullish, close=105
            (103, 109, 102, 108),  # bullish, close=108, open inside prev body
            (106, 113, 105, 112),  # bullish, close=112, open inside prev body
        ]
        assert detect_three_white_soldiers(bars) is True

    def test_three_black_crows(self):
        bars = [
            (110, 111, 104, 105),  # bearish, close=105
            (106, 107, 100, 101),  # bearish, close=101
            (102, 103, 96, 97),    # bearish, close=97
        ]
        assert detect_three_black_crows(bars) is True

    def test_not_three_white(self):
        bars = [
            (100, 106, 99, 105),
            (103, 109, 102, 108),
            (106, 110, 105, 104),  # bearish — breaks pattern
        ]
        assert detect_three_white_soldiers(bars) is False


class TestDetectPatterns:
    def test_empty_df(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": []})
        patterns = detect_patterns(df)
        assert patterns == []

    def test_detects_doji(self):
        # Create data with a doji at the end
        n = 10
        data = {
            "open": [100 + i for i in range(n - 1)] + [110],
            "high": [103 + i for i in range(n - 1)] + [115],
            "low": [98 + i for i in range(n - 1)] + [105],
            "close": [102 + i for i in range(n - 1)] + [110.5],  # doji: open≈close
        }
        df = pd.DataFrame(data)
        patterns = detect_patterns(df, lookback=3)
        dojis = [p for p in patterns if p.name == "Doji"]
        assert len(dojis) >= 1


class TestPatternSummary:
    def test_basic_summary(self):
        n = 10
        data = {
            "open": [100 + i for i in range(n)],
            "high": [103 + i for i in range(n)],
            "low": [98 + i for i in range(n)],
            "close": [102 + i for i in range(n)],
        }
        df = pd.DataFrame(data)
        summary = pattern_summary(df, lookback=5)
        assert "patterns" in summary
        assert "overall_bias" in summary
        assert summary["overall_bias"] in ("bullish", "bearish", "neutral")
