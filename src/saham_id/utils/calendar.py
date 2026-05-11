"""IDX trading calendar helpers.

Includes weekend logic + a placeholder for Indonesian public holidays.
TODO: Integrate official IDX holiday calendar (annually published PDF).
"""

from __future__ import annotations

from datetime import date, timedelta


# Placeholder for IDX public holidays — populate from IDX announcements.
# Format: ISO date strings. Examples below are illustrative, not authoritative.
IDX_HOLIDAYS_2025: set[date] = set()
IDX_HOLIDAYS_2026: set[date] = set()

ALL_HOLIDAYS: set[date] = IDX_HOLIDAYS_2025 | IDX_HOLIDAYS_2026


def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def is_trading_day(d: date) -> bool:
    return not is_weekend(d) and d not in ALL_HOLIDAYS


def next_trading_day(d: date) -> date:
    n = d + timedelta(days=1)
    while not is_trading_day(n):
        n += timedelta(days=1)
    return n


def previous_trading_day(d: date) -> date:
    p = d - timedelta(days=1)
    while not is_trading_day(p):
        p -= timedelta(days=1)
    return p
