"""Sectors.app / Supertype adapter — SKELETON.

Sectors.app (https://sectors.app) is a premium financial data layer for
IDX + SGX with rich fundamental, sector, and ownership data. Paid plan.

Docs: https://docs.sectors.app
"""

from __future__ import annotations

import pandas as pd

from saham_id.config import settings
from saham_id.data.models import FundamentalSnapshot, Quote
from saham_id.data.sources.base import (
    DataSource,
    Interval,
    NotImplementedForSource,
    Period,
    SourceError,
)


class SectorsAppSource(DataSource):
    """Skeleton adapter for Sectors.app API (v2)."""

    name = "sectors"
    typical_delay_minutes = 0
    supports_realtime = True

    BASE_URL = "https://api.sectors.app/v2"

    def __init__(self) -> None:
        self._api_key = settings.sectors_api_key

    def _require_key(self) -> None:
        if not self._api_key:
            raise SourceError("SECTORS_API_KEY is empty. Set it in `.env`.")

    def get_quote(self, ticker: str) -> Quote:
        self._require_key()
        raise NotImplementedForSource("Sectors.app get_quote not yet implemented (skeleton).")

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        self._require_key()
        raise NotImplementedForSource("Sectors.app get_ohlc not yet implemented (skeleton).")

    def get_fundamentals(self, ticker: str) -> FundamentalSnapshot:
        self._require_key()
        raise NotImplementedForSource(
            "Sectors.app get_fundamentals not yet implemented (skeleton)."
        )
