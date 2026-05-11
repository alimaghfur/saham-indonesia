"""Shared screener types & helpers.

All strategy screeners return a `ScreenResult` — a thin wrapper over a
DataFrame with metadata and convenience methods.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd


@dataclass
class ScreenRow:
    """Single entry in a screen result."""

    ticker: str
    score: float
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScreenResult:
    """Container for a screening run."""

    strategy: str
    universe: str
    as_of: datetime
    rows: list[ScreenRow] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """Flatten rows to a DataFrame, sorted by score descending."""
        if not self.rows:
            return pd.DataFrame(columns=["ticker", "score"])
        df = pd.DataFrame(
            [{"ticker": r.ticker, "score": r.score, **r.metrics} for r in self.rows]
        )
        return df.sort_values("score", ascending=False).reset_index(drop=True)

    def top(self, n: int = 10) -> pd.DataFrame:
        return self.to_dataframe().head(n)

    def __len__(self) -> int:
        return len(self.rows)
