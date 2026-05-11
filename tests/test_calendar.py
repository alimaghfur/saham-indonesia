"""Tests for IDX trading calendar."""
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


class TestIsWeekend:
    def test_saturday(self):
        assert is_weekend(date(2025, 1, 4)) is True

    def test_sunday(self):
        assert is_weekend(date(2025, 1, 5)) is True

    def test_monday(self):
        assert is_weekend(date(2025, 1, 6)) is False

    def test_friday(self):
        assert is_weekend(date(2025, 1, 3)) is False


class TestIsHoliday:
    def test_new_year_2025(self):
        assert is_holiday(date(2025, 1, 1)) is True

    def test_idul_fitri_2025(self):
        assert is_holiday(date(2025, 3, 31)) is True
        assert is_holiday(date(2025, 4, 1)) is True

    def test_independence_day(self):
        assert is_holiday(date(2025, 8, 17)) is True

    def test_not_holiday(self):
        assert is_holiday(date(2025, 1, 6)) is False


class TestIsTradingDay:
    def test_normal_weekday(self):
        # Monday Jan 6, 2025 — not a holiday
        assert is_trading_day(date(2025, 1, 6)) is True

    def test_weekend_not_trading(self):
        assert is_trading_day(date(2025, 1, 4)) is False  # Saturday

    def test_holiday_not_trading(self):
        assert is_trading_day(date(2025, 1, 1)) is False  # New Year

    def test_cuti_bersama_not_trading(self):
        assert is_trading_day(date(2025, 3, 28)) is False  # Cuti Bersama Idul Fitri


class TestNextTradingDay:
    def test_friday_to_monday(self):
        nxt = next_trading_day(date(2025, 1, 3))  # Friday
        assert nxt == date(2025, 1, 6)  # Monday

    def test_skip_holiday(self):
        # Dec 24 (Wed) -> skip Dec 25, 26 (holidays) -> skip 27 (Sat), 28 (Sun) -> Dec 29 (Mon)
        nxt = next_trading_day(date(2025, 12, 24))
        assert nxt == date(2025, 12, 29)


class TestPreviousTradingDay:
    def test_monday_to_friday(self):
        prev = previous_trading_day(date(2025, 1, 6))  # Monday
        assert prev == date(2025, 1, 3)  # Friday

    def test_skip_holiday(self):
        # Jan 2 (Thu) -> prev -> Jan 1 is holiday -> Dec 31
        prev = previous_trading_day(date(2025, 1, 2))
        assert prev == date(2024, 12, 31)


class TestTradingDaysBetween:
    def test_one_week(self):
        days = trading_days_between(date(2025, 1, 6), date(2025, 1, 10))
        # Mon-Fri, all trading days (no holidays that week)
        assert len(days) == 5

    def test_includes_no_weekends(self):
        days = trading_days_between(date(2025, 1, 4), date(2025, 1, 12))
        for d in days:
            assert d.weekday() < 5


class TestTradingDaysCount:
    def test_full_week(self):
        count = trading_days_count(date(2025, 1, 6), date(2025, 1, 10))
        assert count == 5

    def test_empty_range(self):
        count = trading_days_count(date(2025, 1, 4), date(2025, 1, 5))
        assert count == 0  # Sat-Sun


class TestHolidayData:
    def test_2025_holidays_exist(self):
        assert len(IDX_HOLIDAYS_2025) > 15  # At least 15 holidays

    def test_2026_holidays_exist(self):
        assert len(IDX_HOLIDAYS_2026) > 15

    def test_all_holidays_combined(self):
        assert len(ALL_HOLIDAYS) == len(IDX_HOLIDAYS_2025) + len(IDX_HOLIDAYS_2026)
