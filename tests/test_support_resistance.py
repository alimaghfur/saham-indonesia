"""Tests for support/resistance detection."""
import pandas as pd
from saham_id.analysis.support_resistance import (
    SRLevels, FibonacciLevels, PriceLevel,
    pivot_points, fibonacci_retracement, detect_levels,
    find_nearest_levels, _cluster_levels, _find_swing_points,
)


def _make_oscillating(n=60, base=100, amplitude=10):
    """Create oscillating price data with clear support/resistance."""
    import math
    close = [base + amplitude * math.sin(i * 0.3) for i in range(n)]
    return pd.DataFrame({
        "open": [c - 0.5 for c in close],
        "high": [c + 2 for c in close],
        "low": [c - 2 for c in close],
        "close": close,
        "volume": [1000000] * n,
    })


class TestPivotPoints:
    def test_classic(self):
        result = pivot_points(high=105, low=95, close=102, method="classic")
        assert "P" in result
        assert "S1" in result
        assert "R1" in result
        assert result["R1"] > result["P"] > result["S1"]

    def test_fibonacci(self):
        result = pivot_points(high=110, low=90, close=100, method="fibonacci")
        assert result["R1"] > result["P"] > result["S1"]

    def test_camarilla(self):
        result = pivot_points(high=105, low=95, close=100, method="camarilla")
        assert result["R1"] > result["S1"]


class TestFibonacciRetracement:
    def test_basic(self):
        df = _make_oscillating(60)
        fib = fibonacci_retracement(df)
        assert fib.swing_high > fib.swing_low
        assert len(fib.levels) == 5
        assert 0.382 in fib.levels
        assert 0.618 in fib.levels

    def test_direction(self):
        df = _make_oscillating(60)
        fib = fibonacci_retracement(df)
        assert fib.direction in ("up", "down")


class TestClusterLevels:
    def test_basic_clustering(self):
        prices = [100, 101, 100.5, 200, 201, 200.5]
        clusters = _cluster_levels(prices, tolerance_pct=0.02)
        assert len(clusters) == 2  # Two distinct clusters

    def test_empty(self):
        assert _cluster_levels([]) == []

    def test_single_price(self):
        clusters = _cluster_levels([100])
        assert len(clusters) == 1
        assert clusters[0][1] == 1


class TestDetectLevels:
    def test_oscillating_data(self):
        df = _make_oscillating(100, base=1000, amplitude=50)
        levels = detect_levels(df)
        assert isinstance(levels, SRLevels)
        assert levels.current_price > 0

    def test_empty_df(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        levels = detect_levels(df)
        assert levels.support == []
        assert levels.resistance == []

    def test_nearest_properties(self):
        levels = SRLevels(
            support=[95, 90, 85],
            resistance=[105, 110, 115],
            current_price=100,
        )
        assert levels.nearest_support == 95
        assert levels.nearest_resistance == 105


class TestFindNearestLevels:
    def test_basic(self):
        df = _make_oscillating(100, base=1000, amplitude=50)
        result = find_nearest_levels(df, n=3)
        assert "support" in result
        assert "resistance" in result
        assert "current" in result
        assert result["current"] > 0
