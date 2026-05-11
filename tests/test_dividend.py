"""Tests for dividend tracker module."""
from datetime import date

from saham_id.dividend import (
    DividendRecord, DividendTracker, DRIPResult,
    drip_calculator, get_estimated_dividend, IDX_DIVIDENDS_2024,
)


class TestDividendRecord:
    def test_create(self):
        rec = DividendRecord(ticker="BBCA", amount=275, ex_date=date(2025, 4, 10))
        assert rec.ticker == "BBCA"
        assert rec.amount == 275

    def test_total_auto_calc(self):
        rec = DividendRecord(ticker="BBCA", amount=275, shares_held=1000)
        assert rec.total_received == 275000


class TestDividendTracker:
    def test_add(self):
        tracker = DividendTracker()
        tracker.add(DividendRecord(ticker="BBCA", amount=275, shares_held=1000))
        assert len(tracker.records) == 1

    def test_total_income(self):
        tracker = DividendTracker()
        tracker.add(DividendRecord(ticker="BBCA", amount=275, shares_held=1000))
        tracker.add(DividendRecord(ticker="BBRI", amount=262, shares_held=2000))
        assert tracker.total_income() == 275000 + 524000

    def test_total_income_filtered(self):
        tracker = DividendTracker()
        tracker.add(DividendRecord(ticker="BBCA", amount=275, shares_held=1000))
        tracker.add(DividendRecord(ticker="BBRI", amount=262, shares_held=2000))
        assert tracker.total_income(ticker="BBCA") == 275000

    def test_yield_on_cost(self):
        tracker = DividendTracker()
        tracker.add(DividendRecord(ticker="BBCA", amount=275, shares_held=1000))
        yoc = tracker.yield_on_cost("BBCA", cost_basis=9500)
        assert yoc > 0

    def test_history(self):
        tracker = DividendTracker()
        tracker.add(DividendRecord(ticker="BBCA", amount=275, ex_date=date(2025, 4, 10)))
        tracker.add(DividendRecord(ticker="BBCA", amount=250, ex_date=date(2024, 4, 10)))
        history = tracker.history("BBCA")
        assert len(history) == 2
        # Should be sorted newest first
        assert history[0].ex_date == date(2025, 4, 10)

    def test_remove(self):
        tracker = DividendTracker()
        tracker.add(DividendRecord(ticker="BBCA", amount=275, ex_date=date(2025, 4, 10)))
        tracker.add(DividendRecord(ticker="BBRI", amount=262, ex_date=date(2025, 4, 15)))
        removed = tracker.remove("BBCA")
        assert removed == 1
        assert len(tracker.records) == 1


class TestDRIPCalculator:
    def test_basic(self):
        result = drip_calculator(
            initial_shares=1000,
            annual_dividend_per_share=275,
            stock_price=9500,
            years=10,
            dividend_growth_rate=0.05,
            price_growth_rate=0.08,
        )
        assert result.final_shares > 1000
        assert result.total_dividends_received > 0
        assert result.years == 10

    def test_zero_years(self):
        result = drip_calculator(
            initial_shares=1000,
            annual_dividend_per_share=275,
            stock_price=9500,
            years=0,
        )
        assert result.final_shares == 1000
        assert result.total_dividends_received == 0


class TestIDXDividendData:
    def test_has_blue_chips(self):
        assert "BBCA" in IDX_DIVIDENDS_2024
        assert "BBRI" in IDX_DIVIDENDS_2024
        assert "TLKM" in IDX_DIVIDENDS_2024

    def test_get_estimated(self):
        div = get_estimated_dividend("BBCA")
        assert div == 275

    def test_get_unknown(self):
        div = get_estimated_dividend("ZZZZZ")
        assert div is None
