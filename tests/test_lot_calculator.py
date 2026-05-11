"""Tests for lot calculator."""
from saham_id.lot_calculator import calculate_lots, lots_for_target_allocation, multi_stock_allocation


class TestCalculateLots:
    def test_basic(self):
        r = calculate_lots(budget=10_000_000, price=9500)
        assert r.lots >= 1
        assert r.shares == r.lots * 100
        assert r.total_with_fee <= 10_000_000
        assert r.remaining_cash >= 0

    def test_cannot_afford(self):
        r = calculate_lots(budget=100_000, price=50000)
        assert r.lots == 0

    def test_fee_included(self):
        r = calculate_lots(budget=10_000_000, price=9500, fee_pct=0.0015)
        assert r.fee > 0

    def test_zero_price(self):
        r = calculate_lots(budget=10_000_000, price=0)
        assert r.lots == 0


class TestTargetAllocation:
    def test_basic(self):
        r = lots_for_target_allocation(portfolio_value=100_000_000, target_pct=0.20, price=9500)
        assert r.lots >= 1


class TestMultiStock:
    def test_basic(self):
        stocks = [
            {"ticker": "BBCA", "price": 9500, "weight": 0.5},
            {"ticker": "BBRI", "price": 5000, "weight": 0.5},
        ]
        results = multi_stock_allocation(budget=20_000_000, stocks=stocks)
        assert len(results) == 2
        assert results[0].lots >= 1
