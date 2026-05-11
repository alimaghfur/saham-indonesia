"""GoAPI adapter — SKELETON.

GoAPI (https://goapi.io/api-data-saham-indonesia/) is an Indonesian provider
offering IDX quotes, indices, corporate actions, etc. Freemium with API key.
"""

from __future__ import annotations

import pandas as pd

from saham_id.config import settings
from saham_id.data.models import Quote
from saham_id.data.sources.base import (
    DataSource,
    Interval,
    NotImplementedForSource,
    Period,
    SourceError,
)


class GoApiSource(DataSource):
    """Skeleton adapter for GoAPI REST endpoints."""

    name = "goapi"
    typical_delay_minutes = 0  # plan-dependent; check your tier
    supports_realtime = True

    BASE_URL = "https://api.goapi.io/stock/idx"

    def __init__(self) -> None:
        self._api_key = settings.goapi_api_key

    def _require_key(self) -> None:
        if not self._api_key:
            raise SourceError("GOAPI_API_KEY is empty. Set it in `.env`.")

    def get_quote(self, ticker: str) -> Quote:
        self._require_key()
        raise NotImplementedForSource("GoAPI get_quote not yet implemented (skeleton).")

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        self._require_key()
        raise NotImplementedForSource("GoAPI get_ohlc not yet implemented (skeleton).")
