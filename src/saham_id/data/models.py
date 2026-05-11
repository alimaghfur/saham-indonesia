"""Pydantic models shared across data sources.

Keeping a single canonical shape means every screener / analyzer / UI
can consume data without knowing which source produced it.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MarketBoard(str, Enum):
    """IDX trading boards."""

    MAIN = "main"
    DEVELOPMENT = "development"
    ACCELERATION = "acceleration"
    NEW_ECONOMY = "new_economy"
    UNKNOWN = "unknown"


class Sector(str, Enum):
    """IDX-IC sector classification (high level)."""

    ENERGY = "energy"
    BASIC_MATERIALS = "basic_materials"
    INDUSTRIALS = "industrials"
    CONSUMER_CYCLICALS = "consumer_cyclicals"
    CONSUMER_NON_CYCLICALS = "consumer_non_cyclicals"
    HEALTHCARE = "healthcare"
    FINANCIALS = "financials"
    PROPERTY_REAL_ESTATE = "property_real_estate"
    TECHNOLOGY = "technology"
    INFRASTRUCTURE = "infrastructure"
    TRANSPORTATION_LOGISTIC = "transportation_logistic"
    UNKNOWN = "unknown"


class Stock(BaseModel):
    """Static metadata for a listed stock."""

    model_config = ConfigDict(frozen=False, use_enum_values=True)

    ticker: str = Field(..., description="IDX code, e.g. 'BBCA'")
    name: str = ""
    sector: Sector = Sector.UNKNOWN
    board: MarketBoard = MarketBoard.UNKNOWN
    listing_date: Optional[date] = None
    shares_outstanding: Optional[int] = None


class Quote(BaseModel):
    """Snapshot of a stock's current market state."""

    model_config = ConfigDict(use_enum_values=True)

    ticker: str
    timestamp: datetime
    last: Decimal
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    prev_close: Optional[Decimal] = None
    volume: Optional[int] = None
    value: Optional[Decimal] = Field(None, description="Transaction value (IDR)")
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    delayed_minutes: int = Field(0, description="0 = realtime, 15 = delayed 15min")
    source: str = "unknown"

    @property
    def change(self) -> Optional[Decimal]:
        if self.prev_close is None:
            return None
        return self.last - self.prev_close

    @property
    def change_pct(self) -> Optional[float]:
        if self.prev_close is None or self.prev_close == 0:
            return None
        return float((self.last - self.prev_close) / self.prev_close)


class Bar(BaseModel):
    """Single OHLCV bar (daily or intraday)."""

    ticker: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    value: Optional[Decimal] = None


class FundamentalSnapshot(BaseModel):
    """Latest fundamental ratios (typically TTM / latest reporting period)."""

    ticker: str
    as_of: date
    # Valuation
    market_cap: Optional[Decimal] = None
    per: Optional[float] = Field(None, description="Price to Earnings Ratio")
    pbv: Optional[float] = Field(None, description="Price to Book Value")
    ps: Optional[float] = Field(None, description="Price to Sales")
    ev_ebitda: Optional[float] = None
    # Profitability
    roe: Optional[float] = Field(None, description="Return on Equity")
    roa: Optional[float] = Field(None, description="Return on Assets")
    net_margin: Optional[float] = None
    # Solvency
    der: Optional[float] = Field(None, description="Debt to Equity Ratio")
    current_ratio: Optional[float] = None
    # Growth
    revenue_growth_yoy: Optional[float] = None
    earnings_growth_yoy: Optional[float] = None
    # Dividend
    dividend_yield: Optional[float] = None
    payout_ratio: Optional[float] = None
    # Source attribution
    source: str = "unknown"


class Mover(BaseModel):
    """Entry in a market-movers list (gainer / loser / trending)."""

    ticker: str
    name: str = ""
    last: Decimal
    change: Decimal
    change_pct: float
    volume: int = 0
    value: Decimal = Decimal(0)
    rank: int = 0
    extra: dict = Field(default_factory=dict, description="Source-specific fields")
