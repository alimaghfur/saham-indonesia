"""IDX trading session logic.

Regular trading hours (WIB / UTC+7):
    Session 1: 09:00 – 11:30
    Session 2: 13:30 – 14:49 (Fri close 14:49; other days 15:49)
Pre-opening: 08:45 – 08:59
Pre-closing: 15:50 – 16:00
Post-trading: 16:05 – 16:15

This module keeps session logic in one place so screeners can ask
"is it morning?" or "seconds until close?" without re-implementing it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone, timedelta

WIB = timezone(timedelta(hours=7))


@dataclass(frozen=True)
class SessionWindow:
    start: time
    end: time

    def contains(self, t: time) -> bool:
        return self.start <= t <= self.end


SESSION_1 = SessionWindow(time(9, 0), time(11, 30))
SESSION_2_MON_THU = SessionWindow(time(13, 30), time(15, 49))
SESSION_2_FRI = SessionWindow(time(13, 30), time(14, 49))
PRE_OPEN = SessionWindow(time(8, 45), time(8, 59))
PRE_CLOSE = SessionWindow(time(15, 50), time(16, 0))


def now_wib() -> datetime:
    return datetime.now(WIB)


def is_trading_day(dt: datetime) -> bool:
    """Rough check — weekday only. TODO: integrate IDX holiday calendar."""
    return dt.weekday() < 5


def current_session(dt: datetime | None = None) -> str:
    """Returns one of: 'pre_open', 'session_1', 'lunch_break', 'session_2',
    'pre_close', 'closed'.
    """
    dt = dt or now_wib()
    if not is_trading_day(dt):
        return "closed"
    t = dt.time()
    session_2 = SESSION_2_FRI if dt.weekday() == 4 else SESSION_2_MON_THU
    if PRE_OPEN.contains(t):
        return "pre_open"
    if SESSION_1.contains(t):
        return "session_1"
    if SESSION_1.end < t < SESSION_2_MON_THU.start:
        return "lunch_break"
    if session_2.contains(t):
        return "session_2"
    if PRE_CLOSE.contains(t):
        return "pre_close"
    return "closed"
