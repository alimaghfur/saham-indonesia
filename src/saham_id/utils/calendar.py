"""IDX trading calendar helpers.

Indonesia observes national public holidays (hari libur nasional) plus
joint-leave days (cuti bersama). The IDX (Bursa Efek Indonesia) is closed
on those days. Dates below are compiled from SKB 3 Menteri announcements
and historical IDX trading-holiday notices.

IMPORTANT:
    - Variable-date Islamic holidays (Idul Fitri, Idul Adha, Maulid,
      Isra Miraj, Tahun Baru Islam) depend on moon sighting; final dates
      can shift by ~1 day. The constants below reflect the government's
      published SKB dates at the time of snapshotting. Entries tagged
      `# approximate` should be cross-checked with the official IDX
      holiday calendar before relying on them.
    - Chinese New Year and Vesak (Waisak) vary year to year.
    - For production systems, fetch the authoritative calendar from IDX
      (https://www.idx.co.id/) annually.
"""

from __future__ import annotations

from datetime import date, timedelta


def _d(year: int, month: int, day: int) -> date:
    return date(year, month, day)


# ---------------------------------------------------------------------------
# 2025 — published SKB 3 Menteri + IDX notice
# ---------------------------------------------------------------------------
IDX_HOLIDAYS_2025: set[date] = {
    _d(2025, 1, 1),    # Tahun Baru Masehi
    _d(2025, 1, 27),   # Cuti bersama Isra Miraj
    _d(2025, 1, 28),   # Cuti bersama Imlek
    _d(2025, 1, 29),   # Tahun Baru Imlek 2576
    _d(2025, 3, 28),   # Cuti bersama Nyepi
    _d(2025, 3, 29),   # Hari Raya Nyepi / Tahun Baru Saka 1947
    _d(2025, 3, 31),   # Idul Fitri 1446 H (hari 1)  # approximate
    _d(2025, 4, 1),    # Idul Fitri 1446 H (hari 2)  # approximate
    _d(2025, 4, 2),    # Cuti bersama Idul Fitri
    _d(2025, 4, 3),    # Cuti bersama Idul Fitri
    _d(2025, 4, 4),    # Cuti bersama Idul Fitri
    _d(2025, 4, 7),    # Cuti bersama Idul Fitri
    _d(2025, 4, 18),   # Wafat Isa Al-Masih (Good Friday)
    _d(2025, 5, 1),    # Hari Buruh Internasional
    _d(2025, 5, 12),   # Hari Raya Waisak 2569  # approximate
    _d(2025, 5, 13),   # Cuti bersama Waisak
    _d(2025, 5, 29),   # Kenaikan Isa Al-Masih
    _d(2025, 5, 30),   # Cuti bersama Kenaikan
    _d(2025, 6, 1),    # Hari Lahir Pancasila (Minggu)
    _d(2025, 6, 6),    # Idul Adha 1446 H  # approximate
    _d(2025, 6, 9),    # Cuti bersama Idul Adha
    _d(2025, 6, 27),   # Tahun Baru Islam 1447 H  # approximate
    _d(2025, 8, 17),   # Hari Kemerdekaan RI (Minggu)
    _d(2025, 9, 5),    # Maulid Nabi Muhammad SAW  # approximate
    _d(2025, 12, 25),  # Hari Raya Natal
    _d(2025, 12, 26),  # Cuti bersama Natal
}


# ---------------------------------------------------------------------------
# 2026 — per SKB 3 Menteri (subject to final IDX confirmation)
# ---------------------------------------------------------------------------
IDX_HOLIDAYS_2026: set[date] = {
    _d(2026, 1, 1),    # Tahun Baru Masehi
    _d(2026, 1, 16),   # Isra Miraj Nabi Muhammad SAW  # approximate
    _d(2026, 2, 17),   # Tahun Baru Imlek 2577
    _d(2026, 3, 18),   # Hari Raya Nyepi / Tahun Baru Saka 1948  # approximate
    _d(2026, 3, 19),   # Cuti bersama Nyepi  # approximate
    _d(2026, 3, 20),   # Cuti bersama Idul Fitri (approx window)  # approximate
    _d(2026, 3, 21),   # Idul Fitri 1447 H (hari 1)  # approximate
    _d(2026, 3, 22),   # Idul Fitri 1447 H (hari 2)  # approximate
    _d(2026, 3, 23),   # Cuti bersama Idul Fitri  # approximate
    _d(2026, 3, 24),   # Cuti bersama Idul Fitri  # approximate
    _d(2026, 3, 25),   # Cuti bersama Idul Fitri  # approximate
    _d(2026, 4, 3),    # Wafat Isa Al-Masih (Good Friday)  # approximate
    _d(2026, 5, 1),    # Hari Buruh
    _d(2026, 5, 14),   # Kenaikan Isa Al-Masih  # approximate
    _d(2026, 5, 15),   # Cuti bersama Kenaikan  # approximate
    _d(2026, 5, 27),   # Hari Raya Waisak 2570  # approximate
    _d(2026, 5, 28),   # Idul Adha 1447 H  # approximate
    _d(2026, 6, 1),    # Hari Lahir Pancasila
    _d(2026, 6, 17),   # Tahun Baru Islam 1448 H  # approximate
    _d(2026, 8, 17),   # Hari Kemerdekaan RI
    _d(2026, 8, 26),   # Maulid Nabi Muhammad SAW  # approximate
    _d(2026, 12, 25),  # Hari Raya Natal
    _d(2026, 12, 28),  # Cuti bersama Natal  # approximate
}


ALL_HOLIDAYS: set[date] = IDX_HOLIDAYS_2025 | IDX_HOLIDAYS_2026


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def is_weekend(d: date) -> bool:
    return d.weekday() >= 5


def is_holiday(d: date) -> bool:
    return d in ALL_HOLIDAYS


def is_trading_day(d: date) -> bool:
    """True if `d` is a weekday and not listed as an IDX holiday."""
    return not is_weekend(d) and not is_holiday(d)


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


def trading_days_between(start: date, end: date) -> list[date]:
    """Inclusive list of trading days from `start` to `end`."""
    if end < start:
        return []
    out: list[date] = []
    cur = start
    while cur <= end:
        if is_trading_day(cur):
            out.append(cur)
        cur += timedelta(days=1)
    return out


def trading_days_count(start: date, end: date) -> int:
    return len(trading_days_between(start, end))
