"""Tests for portfolio optimizer module."""
from saham_id.portfolio.optimizer import (
    AllocationResult, equal_weight, risk_parity, min_correlation_allocation,
)


class TestEqualWeight:
    def test_basic(self):
        result = equal_weight(["BBCA", "BBRI", "TLKM", "ASII"])
        assert len(result.weights) == 4
        assert abs(sum(result.weights.values()) - 1.0) < 0.001
        assert all(abs(w - 0.25) < 0.001 for w in result.weights.values())

    def test_single_stock(self):
        result = equal_weight(["BBCA"])
        assert result.weights["BBCA"] == 1.0

    def test_empty(self):
        result = equal_weight([])
        assert len(result.weights) == 0

    def test_allocation_pct(self):
        result = equal_weight(["BBCA", "BBRI"])
        amounts = result.allocation_pct(100_000_000)
        assert abs(amounts["BBCA"] - 50_000_000) < 1
        assert abs(amounts["BBRI"] - 50_000_000) < 1

    def test_top_allocations_sorted(self):
        result = equal_weight(["A", "B", "C"])
        top = result.top_allocations
        assert len(top) == 3
        # Equal weight so all same
        assert all(abs(w - 1/3) < 0.001 for _, w in top)


class TestAllocationResult:
    def test_method(self):
        result = AllocationResult(
            tickers=["BBCA"], weights={"BBCA": 1.0}, method="test"
        )
        assert result.method == "test"
