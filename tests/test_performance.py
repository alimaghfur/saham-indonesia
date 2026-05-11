"""Tests for portfolio performance tracker."""
from saham_id.portfolio.performance import calculate_performance, PerformanceSummary, BenchmarkComparison


class TestCalculatePerformance:
    def test_basic(self):
        values = [100_000_000, 101_000_000, 102_000_000, 101_500_000, 103_000_000]
        result = calculate_performance(values, initial_capital=100_000_000)
        assert result.total_return_pct > 0
        assert result.total_pnl == 3_000_000
        assert result.positive_days >= 2
        assert result.win_rate > 0

    def test_losing_portfolio(self):
        values = [100_000_000, 99_000_000, 98_000_000, 97_000_000]
        result = calculate_performance(values, initial_capital=100_000_000)
        assert result.total_return_pct < 0
        assert result.max_drawdown_pct < 0
        assert result.negative_days >= 2

    def test_max_drawdown(self):
        values = [100, 110, 105, 115, 100, 120]
        result = calculate_performance(values, initial_capital=100)
        # Peak was 115, dropped to 100 = -13%
        assert result.max_drawdown_pct < -0.10

    def test_empty(self):
        result = calculate_performance([], initial_capital=100_000_000)
        assert result.total_return_pct == 0.0

    def test_sharpe(self):
        # Steady gains = high sharpe
        values = [100 + i for i in range(100)]
        result = calculate_performance(values, initial_capital=100)
        assert result.sharpe_estimate > 0


class TestBenchmarkComparison:
    def test_create(self):
        bc = BenchmarkComparison(
            ticker="^JKSE", portfolio_return=0.15,
            benchmark_return=0.10, alpha=0.05, outperforming=True,
        )
        assert bc.alpha == 0.05
        assert bc.outperforming is True
