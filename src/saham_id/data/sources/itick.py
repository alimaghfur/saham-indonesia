"""iTick adapter — SKELETON.

iTick (https://itick.org) offers realtime IDX quotes and WebSocket streaming
with a free tier. Requires an API key (`ITICK_API_KEY` in `.env`).

Docs: https://blog.itick.org/en/stock-api/indonesia-stock-api-quantitative-integration
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


class ITickSource(DataSource):
    """Skeleton adapter for iTick REST + WebSocket APIs.

    TODO(impl):
        - REST: GET /stock/quote?symbol=BBCA.JK with header `token: <key>`
        - WS: wss://ws.itick.org/stream for realtime ticks
        - handle 429 rate limiting with tenacity exponential backoff
    """

    name = "itick"
    typical_delay_minutes = 0
    supports_realtime = True

    BASE_URL = "https://api.itick.org"

    def __init__(self) -> None:
        self._api_key = settings.itick_api_key
        if not self._api_key:
            # Not fatal at construction; fail on first call so users can
            # still instantiate for inspection (e.g. CLI `list-sources`).
            pass

    def _require_key(self) -> None:
        if not self._api_key:
            raise SourceError(
                "ITICK_API_KEY is empty. Set it in `.env` or process environment."
            )

    def get_quote(self, ticker: str) -> Quote:
        self._require_key()
        raise NotImplementedForSource("iTick get_quote not yet implemented (skeleton).")

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        self._require_key()
        raise NotImplementedForSource("iTick get_ohlc not yet implemented (skeleton).")

    # Streaming hook for future Scalping module
    def stream_ticks(self, tickers: list[str]):  # pragma: no cover - placeholder
        """Async generator yielding tick updates (for scalping). TODO."""
        raise NotImplementedForSource("iTick WebSocket streaming not yet implemented.")
