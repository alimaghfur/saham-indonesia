"""RTI / Pasardana scraper adapter — SKELETON.

Public web pages (pasardana.id, rti.co.id) expose delayed (~15 min) quotes.
This adapter is a scaffold only; fill in endpoints & parsing carefully.

NOTE on ethics/legality:
    - Respect robots.txt and ToS of whichever site you point this at.
    - Use reasonable rate limits (see `SAHAM_ID_RTI_RATE_LIMIT_PER_MIN`).
    - Prefer caching to avoid hammering.
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
)


class RtiScraperSource(DataSource):
    """Skeleton scraper adapter.

    TODO(impl):
        - choose target site (pasardana.id or rti.co.id)
        - implement `_fetch_quote(ticker)` with tenacity retries
        - add simple token-bucket rate limiter
        - add filesystem cache (cachetools / diskcache) in settings.cache_dir
    """

    name = "rti"
    typical_delay_minutes = 15
    supports_realtime = False

    def __init__(self) -> None:
        self._rate_limit = settings.rti_rate_limit_per_min
        # TODO: initialize httpx.Client(timeout=..., headers={"User-Agent": ...})

    def get_quote(self, ticker: str) -> Quote:
        raise NotImplementedForSource(
            "RTI/Pasardana scraper is a skeleton. "
            "Implement `_fetch_quote` with respect to robots.txt and ToS."
        )

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        raise NotImplementedForSource("RTI scraper OHLC not yet implemented.")
