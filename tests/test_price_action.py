"""Tests for price action analysis."""
import pandas as pd
from saham_id.analysis.price_action import bar_analysis, compression_detection


def _uptrend_df(n=20):
    close = [100 + i * 2 for i in range(n)]
    return pd.DataFrame({"open": [c-1 for c in close], "high": [c+2 for c in close],
                        "low": [c-2 for c in close], "close": close, "volume": [1000000]*n})


def _compressed_df(n=30):
    close = [1000] * n
    ranges = [50]*20 + [10, 8, 6, 5, 4, 3, 3, 2, 2, 2]
    return pd.DataFrame({"open": [c - r*0.3 for c, r in zip(close, ranges)],
                        "high": [c + r*0.5 for c, r in zip(close, ranges)],
                        "low": [c - r*0.5 for c, r in zip(close, ranges)],
                        "close": close, "volume": [1000000]*n})


class TestBarAnalysis:
    def test_uptrend(self):
        result = bar_analysis(_uptrend_df(15), lookback=10)
        assert result.consecutive_up > 0
        assert result.last_bar_type == "bullish"

    def test_empty(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        assert bar_analysis(df).consecutive_up == 0

    def test_body_ratio(self):
        result = bar_analysis(_uptrend_df(10), lookback=5)
        assert 0 < result.avg_body_ratio <= 1.0


class TestCompression:
    def test_compressed(self):
        result = compression_detection(_compressed_df(30), lookback=20, threshold=0.5)
        assert result.is_compressed is True
        assert result.compression_bars >= 3

    def test_not_compressed(self):
        result = compression_detection(_uptrend_df(20), lookback=10, threshold=0.3)
        assert result.is_compressed is False

    def test_empty(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        assert compression_detection(df).is_compressed is False
