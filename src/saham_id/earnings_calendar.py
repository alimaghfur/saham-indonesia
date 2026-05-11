"""Earnings calendar — track laporan keuangan emiten IDX.

IDX companies report quarterly (Q1/Q2/Q3/Q4) with deadlines set by OJK.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal, Optional

REPORTING_DEADLINES = {"Q1": 60, "Q2": 60, "Q3": 60, "Q4": 120}
QUARTER_ENDS = {"Q1": (3, 31), "Q2": (6, 30), "Q3": (9, 30), "Q4": (12, 31)}


@dataclass
class EarningsEvent:
    ticker: str
    period: str
    quarter: Literal["Q1", "Q2", "Q3", "Q4"]
    fiscal_year: int
    quarter_end: date
    deadline: date
    reported_date: Optional[date] = None
    status: str = "upcoming"

    @property
    def days_until_deadline(self) -> int:
        return (self.deadline - date.today()).days

    @property
    def is_overdue(self) -> bool:
        return date.today() > self.deadline and self.status != "reported"

    @property
    def trading_window(self) -> str:
        if self.days_until_deadline > 14:
            return "pre_earnings"
        elif self.days_until_deadline > 0:
            return "earnings_week"
        return "post_earnings"


def get_reporting_schedule(ticker: str, year: int = 0) -> list[EarningsEvent]:
    if year == 0:
        year = date.today().year
    events = []
    for quarter, (month, day) in QUARTER_ENDS.items():
        quarter_end = date(year, month, day)
        deadline = quarter_end + timedelta(days=REPORTING_DEADLINES[quarter])
        events.append(EarningsEvent(
            ticker=ticker.upper(), period=f"{quarter} {year}",
            quarter=quarter, fiscal_year=year,
            quarter_end=quarter_end, deadline=deadline,
        ))
    return events


def upcoming_reports(tickers: Optional[list[str]] = None, days_ahead: int = 60, year: int = 0) -> list[EarningsEvent]:
    from saham_id.data.universe import get_universe
    if tickers is None:
        tickers = get_universe("IDX30")
    if year == 0:
        year = date.today().year
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)
    upcoming = []
    for ticker in tickers:
        for event in get_reporting_schedule(ticker, year) + get_reporting_schedule(ticker, year - 1):
            if today <= event.deadline <= cutoff:
                upcoming.append(event)
    upcoming.sort(key=lambda e: e.deadline)
    return upcoming


def earnings_impact_window(ticker: str, quarter: str = "Q4", year: int = 0, pre_days: int = 5, post_days: int = 5) -> dict:
    if year == 0:
        year = date.today().year
    events = get_reporting_schedule(ticker, year)
    target = next((e for e in events if e.quarter == quarter), None)
    if not target:
        return {"error": f"No {quarter} {year} for {ticker}"}
    return {
        "ticker": ticker, "period": target.period,
        "deadline": target.deadline.isoformat(),
        "pre_earnings_start": (target.deadline - timedelta(days=pre_days)).isoformat(),
        "post_earnings_end": (target.deadline + timedelta(days=post_days)).isoformat(),
        "days_until_deadline": target.days_until_deadline,
        "trading_window": target.trading_window,
    }


def get_current_quarter() -> tuple[str, int]:
    today = date.today()
    month = today.month
    year = today.year
    if month <= 3:
        return "Q4", year - 1
    elif month <= 6:
        return "Q1", year
    elif month <= 9:
        return "Q2", year
    return "Q3", year
