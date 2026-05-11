"""Abstract `DataSource` interface.

Every concrete adapter (yfinance, RTI, iTick, GoAPI, Sectors) implements
this so screeners / analyzers stay source-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Literal, Optional

import pandas as pd

from saham_id.data.models import FundamentalSnapshot, Mover, Quote

Period = Literal["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
Interval = Literal["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "1wk", "1mo"]
MoverKind = Literal["gainer", "loser", "trending", "most_active"]


class SourceError(Exception):
    """Raised when a data source fails or cannot fulfill a request."""


class NotImplementedForSource(SourceError):
    """Raised when a source doesn't support a particular endpoint."""


class DataSource(ABC):
    """Abstract interface every data adapter implements."""

    #: Human-readable source name used in model attribution (e.g. `"yahoo"`).
    name: str = "base"

    #: Typical delay of this source's data in minutes. 0 = realtime.
    typical_delay_minutes: int = 15

    #: True if this source supports realtime (streaming) quotes.
    supports_realtime: bool = False

    # ----- Quote & OHLC -----

    @abstractmethod
    def get_quote(self, ticker: str) -> Quote:
        """Return the latest snapshot for a single ticker."""

    def get_quotes(self, tickers: Iterable[str]) -> list[Quote]:
        """Default batch implementation — override for efficiency."""
        return [self.get_quote(t) for t in tickers]

    @abstractmethod
    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        """Return historical OHLCV DataFrame indexed by timestamp."""

    # ----- Market movers -----

    def get_movers(
        self,
        kind: MoverKind = "gainer",
        universe: Optional[Iterable[str]] = None,
        top_n: int = 20,
    ) -> list[Mover]:
        """Return top-N market movers. Skeleton sources may raise."""
        raise NotImplementedForSource(
            f"{self.name} does not implement get_movers(kind={kind})"
        )

    # ----- Fundamentals -----

    def get_fundamentals(self, ticker: str) -> FundamentalSnapshot:
        """Return latest fundamental snapshot. Optional per-source."""
        raise NotImplementedForSource(f"{self.name} does not implement get_fundamentals")

    # ----- Lifecycle -----

    def close(self) -> None:
        """Release any network / file resources. Default no-op."""

    def __enter__(self) -> "DataSource":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"<DataSource name={self.name!r} delay={self.typical_delay_minutes}min>"
