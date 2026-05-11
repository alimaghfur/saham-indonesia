"""Unit tests for IDX trading session logic."""

from __future__ import annotations

from datetime import datetime

from saham_id.screener.intraday.session import (
    WIB,
    current_session,
    is_trading_day,
    now_wib,
)


class TestSession:
    def test_weekday_is_trading_day(self):
        # Monday June 17, 2024 10:00 WIB
        dt = datetime(2024, 6, 17, 10, 0, tzinfo=WIB)
        assert is_trading_day(dt) is True

    def test_weekend_is_not_trading_day(self):
        saturday = datetime(2024, 6, 15, 10, 0, tzinfo=WIB)
        sunday = datetime(2024, 6, 16, 10, 0, tzinfo=WIB)
        assert is_trading_day(saturday) is False
        assert is_trading_day(sunday) is False

    def test_current_session_pre_open(self):
        dt = datetime(2024, 6, 17, 8, 50, tzinfo=WIB)
        assert current_session(dt) == "pre_open"

    def test_current_session_session_1_mid(self):
        dt = datetime(2024, 6, 17, 10, 30, tzinfo=WIB)
        assert current_session(dt) == "session_1"

    def test_current_session_lunch_break(self):
        dt = datetime(2024, 6, 17, 12, 30, tzinfo=WIB)
        assert current_session(dt) == "lunch_break"

    def test_current_session_session_2_mon_thu(self):
        # Monday afternoon
        dt = datetime(2024, 6, 17, 15, 0, tzinfo=WIB)
        assert current_session(dt) == "session_2"

    def test_current_session_session_2_friday_earlier_close(self):
        # Friday June 21, 2024 15:30 — Mon-Thu would still be in session_2,
        # but Friday's session_2 ends at 14:49.
        dt = datetime(2024, 6, 21, 15, 30, tzinfo=WIB)
        # 15:30 falls in pre_close window (15:50-16:00)? No: it's between
        # session_2 end (14:49) and pre_close (15:50) => "closed".
        assert current_session(dt) == "closed"

    def test_current_session_pre_close(self):
        dt = datetime(2024, 6, 17, 15, 55, tzinfo=WIB)
        assert current_session(dt) == "pre_close"

    def test_current_session_after_hours(self):
        dt = datetime(2024, 6, 17, 20, 0, tzinfo=WIB)
        assert current_session(dt) == "closed"

    def test_current_session_weekend_closed(self):
        saturday = datetime(2024, 6, 15, 10, 30, tzinfo=WIB)
        assert current_session(saturday) == "closed"

    def test_holiday_returns_closed(self):
        # Jan 1, 2025 is a Wednesday but also New Year (holiday)
        new_year = datetime(2025, 1, 1, 10, 30, tzinfo=WIB)
        assert current_session(new_year) == "closed"
        assert is_trading_day(new_year) is False

    def test_now_wib_returns_aware_datetime(self):
        n = now_wib()
        assert n.tzinfo is not None
