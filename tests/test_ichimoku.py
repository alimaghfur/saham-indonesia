"""Tests for Ichimoku Cloud indicator."""
import pandas as pd
from saham_id.analysis.indicators.ichimoku import ichimoku, IchimokuResult


class TestIchimoku:
    def test_basic(self):
        n = 80
        close = [1000 + i * 5 for i in range(n)]
        high = pd.Series([c + 8 for c in close])
        low = pd.Series([c - 5 for c in close])
        close_s = pd.Series(close)
        result = ichimoku(high, low, close_s)
        assert isinstance(result, IchimokuResult)
        assert result.cloud_color in ("green", "red")
        assert result.price_vs_cloud in ("above", "below", "inside", "unknown")
        assert result.tk_cross in ("bullish", "bearish")

    def test_uptrend_above_cloud(self):
        n = 80
        close = [1000 + i * 5 for i in range(n)]
        high = pd.Series([c + 8 for c in close])
        low = pd.Series([c - 5 for c in close])
        result = ichimoku(high, low, pd.Series(close))
        assert result.price_vs_cloud == "above"
        assert result.tk_cross == "bullish"

    def test_lengths_match(self):
        n = 60
        high = pd.Series([110 + i for i in range(n)])
        low = pd.Series([90 + i for i in range(n)])
        close = pd.Series([100 + i for i in range(n)])
        result = ichimoku(high, low, close)
        assert len(result.tenkan) == n
        assert len(result.kijun) == n
