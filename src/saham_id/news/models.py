"""News data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class NewsSource(str, Enum):
    """Supported news sources."""

    CNBC_ID = "cnbc_indonesia"
    KONTAN = "kontan"
    BISNIS = "bisnis"
    IDN_FINANCIALS = "idn_financials"
    INVESTING = "investing_id"


@dataclass
class NewsArticle:
    """Represents a single news article."""

    title: str
    url: str
    source: NewsSource
    published_at: Optional[datetime] = None
    summary: str = ""
    tickers: list[str] = field(default_factory=list)
    category: str = "market"
    image_url: Optional[str] = None

    @property
    def age_hours(self) -> float:
        """Hours since publication."""
        if self.published_at is None:
            return 0.0
        delta = datetime.utcnow() - self.published_at
        return delta.total_seconds() / 3600

    @property
    def age_display(self) -> str:
        """Human-readable age string."""
        hours = self.age_hours
        if hours < 1:
            return f"{int(hours * 60)} menit lalu"
        elif hours < 24:
            return f"{int(hours)} jam lalu"
        elif hours < 48:
            return "Kemarin"
        else:
            days = int(hours / 24)
            return f"{days} hari lalu"

    def matches_ticker(self, ticker: str) -> bool:
        """Check if article is related to a ticker."""
        t = ticker.upper()
        # Check explicit tickers list
        if t in self.tickers:
            return True
        # Check if ticker appears in title or summary
        if t in self.title.upper() or t in self.summary.upper():
            return True
        return False
