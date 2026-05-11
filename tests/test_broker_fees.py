"""Tests for broker fee calculator."""
from saham_id.broker_fees import (
    calculate_fees, compare_brokers, list_brokers,
    BROKERS, IDX_LEVY, SELL_TAX, _get_tick_size,
)


class TestCalculateFees:
    def test_basic(self):
        r = calculate_fees(price=9500, lots=10, broker="bca_sekuritas")
        assert r.shares == 1000
        assert r.total_buy_cost > 9500 * 1000
        assert r.total_sell_proceeds < 9500 * 1000
        assert r.round_trip_fee > 0
        assert r.breakeven_price > 9500

    def test_buy_more_than_value(self):
        r = calculate_fees(price=5000, lots=5)
        # Buy cost should be > raw value
        raw = 5000 * 500
        assert r.total_buy_cost > raw

    def test_sell_less_than_value(self):
        r = calculate_fees(price=5000, lots=5)
        raw = 5000 * 500
        assert r.total_sell_proceeds < raw

    def test_breakeven_above_entry(self):
        r = calculate_fees(price=10000, lots=10)
        assert r.breakeven_price > 10000

    def test_breakeven_ticks(self):
        r = calculate_fees(price=9500, lots=10)
        assert r.breakeven_ticks >= 1

    def test_different_brokers(self):
        r1 = calculate_fees(price=9500, lots=10, broker="stockbit")
        r2 = calculate_fees(price=9500, lots=10, broker="indo_premier")
        # Stockbit cheaper
        assert r1.round_trip_fee < r2.round_trip_fee


class TestCompareBrokers:
    def test_returns_all(self):
        results = compare_brokers(price=9500, lots=10)
        assert len(results) == len(BROKERS)
        # Should be sorted by fee (cheapest first)
        assert results[0].round_trip_fee <= results[-1].round_trip_fee


class TestListBrokers:
    def test_returns_list(self):
        brokers = list_brokers()
        assert len(brokers) >= 7
        assert all("name" in b for b in brokers)
        assert all("buy_fee_pct" in b for b in brokers)


class TestTickSize:
    def test_penny_stock(self):
        assert _get_tick_size(150) == 1

    def test_mid_price(self):
        assert _get_tick_size(1000) == 5

    def test_blue_chip(self):
        assert _get_tick_size(9500) == 25

    def test_boundaries(self):
        assert _get_tick_size(199) == 1
        assert _get_tick_size(200) == 2
        assert _get_tick_size(499) == 2
        assert _get_tick_size(500) == 5
        assert _get_tick_size(1999) == 5
        assert _get_tick_size(2000) == 10
        assert _get_tick_size(4999) == 10
        assert _get_tick_size(5000) == 25


class TestConstants:
    def test_levy(self):
        assert IDX_LEVY == 0.00043

    def test_sell_tax(self):
        assert SELL_TAX == 0.001

    def test_brokers_have_required_fields(self):
        for key, info in BROKERS.items():
            assert "name" in info
            assert "buy_fee" in info
            assert "sell_fee" in info
            assert info["sell_fee"] > info["buy_fee"]  # sell always more expensive (includes tax component)
