"""Unit tests for the IDX trading calendar."""

from __future__ import annotations

from datetime import date

from saham_id.utils.calendar import (
    ALL_HOLIDAYS,
    IDX_HOLIDAYS_2025,
    IDX_HOLIDAYS_2026,
    is_holiday,
    is_trading_day,
    is_weekend,
    next_trading_day,
    previous_trading_day,
    trading_days_between,
    trading_days_count,
)


class TestBasicChecks:
    def test_is_weekend(self):
        assert is_weekend(date(2025, 1, 4))   # Saturday
        assert is_weekend(date(2025, 1, 5))   # Sunday
        assert not is_weekend(date(2025, 1, 6))  # Monday

    def test_new_year_is_holiday(self):
        assert is_holiday(date(2025, 1, 1))
        assert is_holiday(date(2026, 1, 1))

    def test_kemerdekaan_is_holiday(self):
        assert is_holiday(date(2026, 8, 17))

    def test_regular_weekday_is_trading_day(self):
        assert is_trading_day(date(2025, 1, 6))   # Monday, non-holiday
        assert is_trading_day(date(2025, 7, 15))  # Tuesday, non-holiday

    def test_holiday_not_trading_day(self):
        assert not is_trading_day(date(2025, 1, 1))

    def test_weekend_not_trading_day(self):
        assert not is_trading_day(date(2025, 1, 4))


class TestNavigation:
    def test_next_trading_day_skips_weekend(self):
        # Friday Jan 3, 2025 -> next trading day should be Monday Jan 6
        assert next_trading_day(date(2025, 1, 3)) == date(2025, 1, 6)

    def test_next_trading_day_skips_holiday(self):
        # Dec 31, 2024 -> skip Jan 1 (holiday) -> Jan 2, 2025 (Thursday)
        assert next_trading_day(date(2024, 12, 31)) == date(2025, 1, 2)

    def test_previous_trading_day(self):
        # Monday Jan 6, 2025 -> previous trading day should be Friday Jan 3
        assert previous_trading_day(date(2025, 1, 6)) == date(2025, 1, 3)


class TestRanges:
    def test_trading_days_between_inclusive(self):
        # Jan 6–10, 2025 (Mon–Fri, no holidays) => 5 days
        days = trading_days_between(date(2025, 1, 6), date(2025, 1, 10))
        assert len(days) == 5
        assert days[0] == date(2025, 1, 6)
        assert days[-1] == date(2025, 1, 10)

    def test_trading_days_count_excludes_weekends(self):
        # Jan 1–12, 2025: Jan 1 holiday, 4–5 weekend, 11–12 weekend
        # So trading: Jan 2, 3, 6, 7, 8, 9, 10 => 7 days
        count = trading_days_count(date(2025, 1, 1), date(2025, 1, 12))
        assert count == 7

    def test_trading_days_empty_when_reversed(self):
        assert trading_days_between(date(2025, 1, 10), date(2025, 1, 1)) == []


class TestDataIntegrity:
    def test_2025_and_2026_share_no_dates(self):
        assert not (IDX_HOLIDAYS_2025 & IDX_HOLIDAYS_2026)

    def test_all_holidays_union(self):
        assert ALL_HOLIDAYS == IDX_HOLIDAYS_2025 | IDX_HOLIDAYS_2026

    def test_every_2025_holiday_is_in_2025(self):
        assert all(d.year == 2025 for d in IDX_HOLIDAYS_2025)

    def test_every_2026_holiday_is_in_2026(self):
        assert all(d.year == 2026 for d in IDX_HOLIDAYS_2026)

    def test_has_17_august_both_years(self):
        # Independence Day — observed both years
        assert date(2025, 8, 17) in ALL_HOLIDAYS
        assert date(2026, 8, 17) in ALL_HOLIDAYS

    def test_has_christmas_both_years(self):
        assert date(2025, 12, 25) in ALL_HOLIDAYS
        assert date(2026, 12, 25) in ALL_HOLIDAYS
