"""IDX trading calendar helpers.

Includes weekend logic + Indonesian public holidays for 2025 and 2026.
Holiday dates are based on official government announcements (SKB).
"""

from __future__ import annotations

from datetime import date, timedelta


# IDX holidays 2025 (based on Indonesian government SKB 3 Menteri 2025)
IDX_HOLIDAYS_2025: set[date] = {
    date(2025, 1, 1),    # Tahun Baru 2025
    date(2025, 1, 27),   # Isra Mi'raj Nabi Muhammad SAW
    date(2025, 1, 29),   # Tahun Baru Imlek 2576
    date(2025, 3, 14),   # Hari Suci Nyepi (Tahun Baru Saka 1947)
    date(2025, 3, 28),   # Cuti Bersama Hari Raya Idul Fitri 1446 H
    date(2025, 3, 31),   # Hari Raya Idul Fitri 1446 H
    date(2025, 4, 1),    # Hari Raya Idul Fitri 1446 H
    date(2025, 4, 2),    # Cuti Bersama Hari Raya Idul Fitri 1446 H
    date(2025, 4, 3),    # Cuti Bersama Hari Raya Idul Fitri 1446 H
    date(2025, 4, 4),    # Cuti Bersama Hari Raya Idul Fitri 1446 H
    date(2025, 4, 18),   # Wafat Isa Al Masih
    date(2025, 5, 1),    # Hari Buruh Internasional
    date(2025, 5, 12),   # Hari Raya Waisak 2569 BE
    date(2025, 5, 29),   # Kenaikan Isa Al Masih
    date(2025, 6, 1),    # Hari Lahir Pancasila
    date(2025, 6, 6),    # Cuti Bersama Hari Raya Idul Adha 1446 H
    date(2025, 6, 7),    # Hari Raya Idul Adha 1446 H
    date(2025, 6, 27),   # Tahun Baru Islam 1447 H
    date(2025, 8, 17),   # Hari Kemerdekaan RI
    date(2025, 9, 5),    # Maulid Nabi Muhammad SAW
    date(2025, 12, 25),  # Hari Natal
    date(2025, 12, 26),  # Cuti Bersama Natal
}

# IDX holidays 2026 (estimated based on typical Islamic/government calendar)
IDX_HOLIDAYS_2026: set[date] = {
    date(2026, 1, 1),    # Tahun Baru 2026
    date(2026, 1, 16),   # Isra Mi'raj Nabi Muhammad SAW
    date(2026, 2, 17),   # Tahun Baru Imlek 2577
    date(2026, 3, 3),    # Hari Suci Nyepi (Tahun Baru Saka 1948)
    date(2026, 3, 19),   # Cuti Bersama Hari Raya Idul Fitri 1447 H
    date(2026, 3, 20),   # Hari Raya Idul Fitri 1447 H
    date(2026, 3, 21),   # Hari Raya Idul Fitri 1447 H
    date(2026, 3, 22),   # Cuti Bersama Hari Raya Idul Fitri 1447 H
    date(2026, 3, 23),   # Cuti Bersama Hari Raya Idul Fitri 1447 H
    date(2026, 4, 3),    # Wafat Isa Al Masih
    date(2026, 5, 1),    # Hari Buruh Internasional
    date(2026, 5, 14),   # Kenaikan Isa Al Masih
    date(2026, 5, 27),   # Hari Raya Idul Adha 1447 H
    date(2026, 5, 31),   # Hari Raya Waisak 2570 BE
    date(2026, 6, 1),    # Hari Lahir Pancasila
    date(2026, 6, 17),   # Tahun Baru Islam 1448 H
    date(2026, 8, 17),   # Hari Kemerdekaan RI
    date(2026, 8, 26),   # Maulid Nabi Muhammad SAW
    date(2026, 12, 25),  # Hari Natal
    date(2026, 12, 26),  # Cuti Bersama Natal
}

ALL_HOLIDAYS: set[date] = IDX_HOLIDAYS_2025 | IDX_HOLIDAYS_2026


def is_weekend(d: date) -> bool:
    """Check if a date falls on Saturday or Sunday."""
    return d.weekday() >= 5


def is_holiday(d: date) -> bool:
    """Check if a date is a known IDX holiday."""
    return d in ALL_HOLIDAYS


def is_trading_day(d: date) -> bool:
    """Check if a date is a valid IDX trading day (not weekend and not holiday)."""
    return not is_weekend(d) and not is_holiday(d)


def next_trading_day(d: date) -> date:
    """Return the next trading day after the given date."""
    n = d + timedelta(days=1)
    while not is_trading_day(n):
        n += timedelta(days=1)
    return n


def previous_trading_day(d: date) -> date:
    """Return the previous trading day before the given date."""
    p = d - timedelta(days=1)
    while not is_trading_day(p):
        p -= timedelta(days=1)
    return p


def trading_days_between(start: date, end: date) -> list[date]:
    """Return all trading days in the range [start, end] inclusive."""
    days = []
    d = start
    while d <= end:
        if is_trading_day(d):
            days.append(d)
        d += timedelta(days=1)
    return days


def trading_days_count(start: date, end: date) -> int:
    """Count trading days between start and end (inclusive)."""
    return len(trading_days_between(start, end))


# ---------------------------------------------------------------------------
# Auto-detection utilities
# ---------------------------------------------------------------------------


def detect_holidays_from_ohlc(
    ohlc_index,
    year: int | None = None,
) -> list[date]:
    """Detect likely IDX holidays by finding weekdays with no trading data.

    Compares weekdays in the given year against dates present in an OHLC
    DataFrame index. Any weekday NOT in the index is a candidate holiday.

    Parameters:
        ohlc_index: DatetimeIndex or iterable of dates/timestamps from
                    a broad-market OHLC (e.g. IHSG/^JKSE daily data).
        year: Year to analyze. If None, uses the most recent year in data.

    Returns:
        Sorted list of date objects representing detected holidays.

    Usage:
        >>> from saham_id.data.sources import get_source
        >>> src = get_source("yahoo")
        >>> df = src.get_ohlc("^JKSE", period="1y", interval="1d")
        >>> holidays = detect_holidays_from_ohlc(df.index, year=2025)
    """
    # Convert index to set of date objects
    trading_dates: set[date] = set()
    for ts in ohlc_index:
        if hasattr(ts, "date"):
            trading_dates.add(ts.date() if callable(ts.date) else ts.date)
        elif isinstance(ts, date):
            trading_dates.add(ts)

    if not trading_dates:
        return []

    # Determine year
    if year is None:
        year = max(d.year for d in trading_dates)

    # Find all weekdays in that year
    jan1 = date(year, 1, 1)
    dec31 = date(year, 12, 31)

    # Only consider dates within the data range to avoid false positives
    data_start = min(d for d in trading_dates if d.year == year) if any(d.year == year for d in trading_dates) else jan1
    data_end = max(d for d in trading_dates if d.year == year) if any(d.year == year for d in trading_dates) else dec31

    detected: list[date] = []
    d = data_start
    while d <= data_end:
        if d.weekday() < 5 and d not in trading_dates:
            detected.append(d)
        d += timedelta(days=1)

    return sorted(detected)


def get_holidays_for_year(year: int) -> set[date]:
    """Return the set of known holidays for a given year.

    Returns an empty set for years without hardcoded data.
    """
    registry: dict[int, set[date]] = {
        2025: IDX_HOLIDAYS_2025,
        2026: IDX_HOLIDAYS_2026,
    }
    return registry.get(year, set())


def add_custom_holidays(holidays: set[date]) -> None:
    """Add custom holidays to the global ALL_HOLIDAYS set at runtime.

    Useful for dynamically adding detected holidays or holidays for
    years not yet hardcoded.

    Parameters:
        holidays: Set of date objects to add.
    """
    global ALL_HOLIDAYS
    ALL_HOLIDAYS = ALL_HOLIDAYS | holidays


def estimate_trading_days_per_year(year: int) -> int:
    """Estimate total trading days for a given year.

    Uses known holidays if available, otherwise assumes ~15 holidays.
    """
    holidays = get_holidays_for_year(year)
    jan1 = date(year, 1, 1)
    dec31 = date(year, 12, 31)

    if holidays:
        # Count weekdays minus known holidays
        count = 0
        d = jan1
        while d <= dec31:
            if d.weekday() < 5 and d not in holidays:
                count += 1
            d += timedelta(days=1)
        return count
    else:
        # Approximate: 52 weeks * 5 days - ~15 holidays
        weekdays = sum(1 for i in range((dec31 - jan1).days + 1) if (jan1 + timedelta(days=i)).weekday() < 5)
        return weekdays - 15  # conservative estimate
