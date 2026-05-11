"""Tests for IDX trading session logic."""
from datetime import datetime, timedelta, timezone

from saham_id.screener.intraday.session import (
    SESSION_1,
    SESSION_2_FRI,
    SESSION_2_MON_THU,
    WIB,
    current_session,
    is_trading_day,
)


class TestSessionWindows:
    def test_session_1_start(self):
        dt = datetime(2025, 1, 6, 9, 0, tzinfo=WIB)  # Monday 9:00
        assert current_session(dt) == "session_1"

    def test_session_1_end(self):
        dt = datetime(2025, 1, 6, 11, 30, tzinfo=WIB)  # Monday 11:30
        assert current_session(dt) == "session_1"

    def test_lunch_break(self):
        dt = datetime(2025, 1, 6, 12, 0, tzinfo=WIB)  # Monday 12:00
        assert current_session(dt) == "lunch_break"

    def test_session_2_monday(self):
        dt = datetime(2025, 1, 6, 14, 0, tzinfo=WIB)  # Monday 14:00
        assert current_session(dt) == "session_2"

    def test_session_2_friday(self):
        dt = datetime(2025, 1, 10, 14, 0, tzinfo=WIB)  # Friday 14:00
        assert current_session(dt) == "session_2"

    def test_friday_after_close(self):
        dt = datetime(2025, 1, 10, 15, 0, tzinfo=WIB)  # Friday 15:00
        assert current_session(dt) == "closed"

    def test_pre_open(self):
        dt = datetime(2025, 1, 6, 8, 50, tzinfo=WIB)
        assert current_session(dt) == "pre_open"

    def test_early_morning_closed(self):
        dt = datetime(2025, 1, 6, 7, 0, tzinfo=WIB)
        assert current_session(dt) == "closed"

    def test_weekend_closed(self):
        dt = datetime(2025, 1, 11, 10, 0, tzinfo=WIB)  # Saturday
        assert current_session(dt) == "closed"


class TestIsTradingDay:
    def test_weekday_is_trading(self):
        dt = datetime(2025, 1, 6, 10, 0, tzinfo=WIB)  # Monday
        assert is_trading_day(dt) is True

    def test_saturday_not_trading(self):
        dt = datetime(2025, 1, 4, 10, 0, tzinfo=WIB)
        assert is_trading_day(dt) is False

    def test_sunday_not_trading(self):
        dt = datetime(2025, 1, 5, 10, 0, tzinfo=WIB)
        assert is_trading_day(dt) is False
