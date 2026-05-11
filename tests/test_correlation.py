"""Tests for correlation module."""
from saham_id.analysis.correlation import _pearson_correlation, CorrelationResult


class TestPearsonCorrelation:
    def test_perfect_positive(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [2.0, 4.0, 6.0, 8.0, 10.0]
        corr = _pearson_correlation(x, y)
        assert abs(corr - 1.0) < 0.001

    def test_perfect_negative(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0]
        y = [10.0, 8.0, 6.0, 4.0, 2.0]
        corr = _pearson_correlation(x, y)
        assert abs(corr - (-1.0)) < 0.001

    def test_uncorrelated(self):
        x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        y = [5.0, 3.0, 8.0, 2.0, 7.0, 4.0, 9.0, 1.0, 6.0, 10.0]
        corr = _pearson_correlation(x, y)
        # Should be close to 0 (not perfectly but roughly)
        assert abs(corr) < 0.7

    def test_same_values_zero_std(self):
        x = [5.0, 5.0, 5.0, 5.0, 5.0]
        y = [1.0, 2.0, 3.0, 4.0, 5.0]
        corr = _pearson_correlation(x, y)
        assert corr == 0.0  # Zero std dev -> 0 correlation

    def test_short_series(self):
        x = [1.0, 2.0]
        y = [3.0, 4.0]
        corr = _pearson_correlation(x, y)
        assert corr == 0.0  # Too short (<5)

    def test_with_none_values(self):
        x = [1.0, None, 3.0, 4.0, 5.0, 6.0]
        y = [2.0, 4.0, None, 8.0, 10.0, 12.0]
        corr = _pearson_correlation(x, y)
        # Should still work with fewer valid pairs
        assert -1 <= corr <= 1


class TestCorrelationResult:
    def test_empty_result(self):
        result = CorrelationResult(
            tickers=[],
            period="1y",
            matrix={},
        )
        assert len(result.tickers) == 0
        assert result.highest_pairs == []
        assert result.lowest_pairs == []
