"""Dividend tracker — yield, ex-date, payment tracking, reinvestment calculator.

Usage:
    from saham_id.dividend import DividendTracker, DividendRecord

    tracker = DividendTracker()
    tracker.add(DividendRecord(ticker="BBCA", amount=275, ex_date=date(2025,4,10)))
    print(tracker.total_income())
    print(tracker.yield_on_cost("BBCA", cost_basis=9500))

    # Dividend reinvestment
    from saham_id.dividend import drip_calculator
    result = drip_calculator(ticker="BBCA", shares=1000, years=10, source=src)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from saham_id.config import settings


@dataclass
class DividendRecord:
    """A single dividend payment record."""

    ticker: str
    amount: float  # dividend per share (IDR)
    ex_date: Optional[date] = None
    payment_date: Optional[date] = None
    record_date: Optional[date] = None
    div_type: str = "cash"  # cash, stock, special
    shares_held: int = 0  # shares owned at ex-date
    total_received: float = 0.0  # amount * shares_held
    note: str = ""

    def __post_init__(self):
        if self.shares_held > 0 and self.total_received == 0:
            self.total_received = self.amount * self.shares_held


@dataclass
class DividendYieldInfo:
    """Dividend yield calculation."""

    ticker: str
    annual_dividend: float  # total dividend per share last 12 months
    current_price: float
    forward_yield: float  # annual_dividend / current_price
    trailing_yield: float  # same, based on paid dividends
    payout_ratio: Optional[float] = None  # div / EPS


@dataclass
class DRIPResult:
    """Dividend Reinvestment Plan calculation result."""

    ticker: str
    initial_shares: int
    final_shares: float
    total_dividends_received: float
    total_reinvested: float
    years: int
    annual_dividend: float
    assumed_price: float
    assumed_growth: float


class DividendTracker:
    """Track dividend payments across portfolio.

    Records dividend history, calculates yield-on-cost,
    and projects future income.
    """

    def __init__(self):
        self.records: list[DividendRecord] = []

    def add(self, record: DividendRecord) -> None:
        """Add a dividend record."""
        self.records.append(record)

    def remove(self, ticker: str, ex_date: Optional[date] = None) -> int:
        """Remove records. Returns number removed."""
        before = len(self.records)
        if ex_date:
            self.records = [r for r in self.records if not (r.ticker == ticker and r.ex_date == ex_date)]
        else:
            self.records = [r for r in self.records if r.ticker != ticker]
        return before - len(self.records)

    def total_income(self, ticker: Optional[str] = None, year: Optional[int] = None) -> float:
        """Total dividend income received."""
        filtered = self.records
        if ticker:
            filtered = [r for r in filtered if r.ticker.upper() == ticker.upper()]
        if year:
            filtered = [r for r in filtered if r.ex_date and r.ex_date.year == year]
        return sum(r.total_received for r in filtered)

    def annual_income(self, ticker: Optional[str] = None) -> dict[int, float]:
        """Income grouped by year."""
        income: dict[int, float] = {}
        filtered = self.records if not ticker else [r for r in self.records if r.ticker.upper() == ticker.upper()]
        for r in filtered:
            if r.ex_date:
                year = r.ex_date.year
                income[year] = income.get(year, 0) + r.total_received
        return dict(sorted(income.items()))

    def yield_on_cost(self, ticker: str, cost_basis: float) -> float:
        """Calculate yield on cost (annual dividend / cost basis)."""
        if cost_basis <= 0:
            return 0.0
        ticker_records = [r for r in self.records if r.ticker.upper() == ticker.upper()]
        if not ticker_records:
            return 0.0
        # Use last 12 months of dividends
        total_div_per_share = sum(r.amount for r in ticker_records[-4:])  # assume quarterly
        return total_div_per_share / cost_basis

    def upcoming_ex_dates(self, days_ahead: int = 30) -> list[DividendRecord]:
        """Get records with ex-dates in the next N days."""
        today = date.today()
        upcoming = []
        for r in self.records:
            if r.ex_date and today <= r.ex_date <= date(today.year, today.month + (days_ahead // 30), today.day):
                upcoming.append(r)
        return sorted(upcoming, key=lambda r: r.ex_date or date.max)

    def history(self, ticker: Optional[str] = None) -> list[DividendRecord]:
        """Get dividend history, sorted by ex-date."""
        filtered = self.records
        if ticker:
            filtered = [r for r in filtered if r.ticker.upper() == ticker.upper()]
        return sorted(filtered, key=lambda r: r.ex_date or date.min, reverse=True)

    def save(self, name: str = "dividends") -> Path:
        """Save dividend records to JSON."""
        storage = settings.cache_dir / "dividends"
        storage.mkdir(parents=True, exist_ok=True)
        filepath = storage / f"{name}.json"

        data = {
            "saved_at": datetime.utcnow().isoformat(),
            "records": [
                {
                    "ticker": r.ticker,
                    "amount": r.amount,
                    "ex_date": r.ex_date.isoformat() if r.ex_date else None,
                    "payment_date": r.payment_date.isoformat() if r.payment_date else None,
                    "div_type": r.div_type,
                    "shares_held": r.shares_held,
                    "total_received": r.total_received,
                    "note": r.note,
                }
                for r in self.records
            ],
        }
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return filepath

    @classmethod
    def load(cls, name: str = "dividends") -> "DividendTracker":
        """Load dividend records from JSON."""
        tracker = cls()
        storage = settings.cache_dir / "dividends"
        filepath = storage / f"{name}.json"

        if not filepath.exists():
            return tracker

        try:
            data = json.loads(filepath.read_text())
            for rec in data.get("records", []):
                tracker.records.append(DividendRecord(
                    ticker=rec["ticker"],
                    amount=rec["amount"],
                    ex_date=date.fromisoformat(rec["ex_date"]) if rec.get("ex_date") else None,
                    payment_date=date.fromisoformat(rec["payment_date"]) if rec.get("payment_date") else None,
                    div_type=rec.get("div_type", "cash"),
                    shares_held=rec.get("shares_held", 0),
                    total_received=rec.get("total_received", 0),
                    note=rec.get("note", ""),
                ))
        except (json.JSONDecodeError, KeyError):
            pass

        return tracker


def drip_calculator(
    initial_shares: int,
    annual_dividend_per_share: float,
    stock_price: float,
    years: int = 10,
    dividend_growth_rate: float = 0.05,
    price_growth_rate: float = 0.08,
) -> DRIPResult:
    """Calculate Dividend Reinvestment Plan (DRIP) projection.

    Simulates buying additional shares with dividend income each year.

    Parameters:
        initial_shares: Starting number of shares
        annual_dividend_per_share: Current annual dividend per share
        stock_price: Current stock price
        years: Projection years
        dividend_growth_rate: Annual dividend growth rate (e.g. 0.05 = 5%)
        price_growth_rate: Annual price appreciation rate

    Returns:
        DRIPResult with final shares, total dividends, etc.
    """
    shares = float(initial_shares)
    price = stock_price
    div_per_share = annual_dividend_per_share
    total_dividends = 0.0
    total_reinvested = 0.0

    for year in range(years):
        # Receive dividend
        div_income = shares * div_per_share
        total_dividends += div_income

        # Reinvest: buy more shares at current price
        new_shares = div_income / price if price > 0 else 0
        shares += new_shares
        total_reinvested += div_income

        # Growth for next year
        div_per_share *= (1 + dividend_growth_rate)
        price *= (1 + price_growth_rate)

    return DRIPResult(
        ticker="",
        initial_shares=initial_shares,
        final_shares=shares,
        total_dividends_received=total_dividends,
        total_reinvested=total_reinvested,
        years=years,
        annual_dividend=annual_dividend_per_share,
        assumed_price=stock_price,
        assumed_growth=price_growth_rate,
    )


# --- IDX Dividend Data (common blue-chips) ---

# Approximate annual dividends for major IDX stocks (2024 data, IDR per share)
IDX_DIVIDENDS_2024: dict[str, float] = {
    "BBCA": 275,
    "BBRI": 262,
    "BMRI": 410,
    "BBNI": 325,
    "TLKM": 170,
    "ASII": 600,
    "UNVR": 825,
    "ICBP": 238,
    "INDF": 350,
    "KLBF": 28,
    "ADRO": 808,
    "ITMG": 3550,
    "PTBA": 471,
    "SMGR": 100,
    "UNTR": 1058,
}


def get_estimated_dividend(ticker: str) -> Optional[float]:
    """Get estimated annual dividend per share for an IDX stock.

    Returns None if not in the database.
    """
    return IDX_DIVIDENDS_2024.get(ticker.upper())
