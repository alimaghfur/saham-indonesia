"""Tests for earnings calendar."""
from datetime import date
from saham_id.earnings_calendar import (
    EarningsEvent, get_reporting_schedule, upcoming_reports,
    earnings_impact_window, get_current_quarter, REPORTING_DEADLINES, QUARTER_ENDS,
)


class TestEarningsEvent:
    def test_create(self):
        event = EarningsEvent(ticker="BBCA", period="Q4 2024", quarter="Q4",
                             fiscal_year=2024, quarter_end=date(2024, 12, 31), deadline=date(2025, 4, 30))
        assert event.ticker == "BBCA"
        assert event.trading_window in ("pre_earnings", "earnings_week", "post_earnings")

    def test_days_until(self):
        event = EarningsEvent(ticker="BBCA", period="Q4 2024", quarter="Q4",
                             fiscal_year=2024, quarter_end=date(2024, 12, 31), deadline=date(2099, 12, 31))
        assert event.days_until_deadline > 0
        assert event.is_overdue is False


class TestGetReportingSchedule:
    def test_returns_4_quarters(self):
        schedule = get_reporting_schedule("BBCA", year=2025)
        assert len(schedule) == 4

    def test_deadlines_after_quarter_end(self):
        for event in get_reporting_schedule("BBRI", year=2025):
            assert event.deadline > event.quarter_end


class TestUpcomingReports:
    def test_returns_list(self):
        upcoming = upcoming_reports(tickers=["BBCA"], days_ahead=365)
        assert isinstance(upcoming, list)


class TestEarningsImpactWindow:
    def test_basic(self):
        result = earnings_impact_window("BBCA", quarter="Q4", year=2025)
        assert "deadline" in result
        assert "trading_window" in result


class TestGetCurrentQuarter:
    def test_valid(self):
        q, y = get_current_quarter()
        assert q in ("Q1", "Q2", "Q3", "Q4")
        assert y >= 2024


class TestConstants:
    def test_deadlines(self):
        assert REPORTING_DEADLINES["Q1"] == 60
        assert REPORTING_DEADLINES["Q4"] == 120

    def test_quarter_ends(self):
        assert QUARTER_ENDS["Q1"] == (3, 31)
