"""RTI Business scraper adapter.

Uses the RTI Business (rti.co.id) public API endpoints to fetch
delayed stock quotes and historical OHLC data for IDX stocks.

NOTE on ethics/legality:
    - Respect robots.txt and ToS.
    - Use reasonable rate limits (see `SAHAM_ID_RTI_RATE_LIMIT_PER_MIN`).
    - Prefer caching to avoid hammering.
    - Data is delayed ~15 minutes.
"""

from __future__ import annotations

import time
from datetime import datetime
from decimal import Decimal
from typing import Optional

import httpx
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from saham_id.config import settings
from saham_id.data.models import Quote
from saham_id.data.sources.base import (
    DataSource,
    Interval,
    Period,
    SourceError,
)


# Period mapping to approximate number of days for RTI history requests
_PERIOD_TO_DAYS: dict[str, int] = {
    "1d": 1,
    "5d": 5,
    "1mo": 30,
    "3mo": 90,
    "6mo": 180,
    "1y": 365,
    "2y": 730,
    "5y": 1825,
    "10y": 3650,
    "ytd": 365,  # approximate
    "max": 7300,
}


class _RateLimiter:
    """Simple token-bucket rate limiter."""

    def __init__(self, max_per_minute: int = 30):
        self._max = max_per_minute
        self._tokens: list[float] = []

    def acquire(self) -> None:
        """Block until a request slot is available."""
        now = time.time()
        # Remove tokens older than 60 seconds
        self._tokens = [t for t in self._tokens if now - t < 60.0]
        if len(self._tokens) >= self._max:
            # Wait until oldest token expires
            sleep_time = 60.0 - (now - self._tokens[0]) + 0.1
            if sleep_time > 0:
                time.sleep(sleep_time)
            self._tokens = self._tokens[1:]
        self._tokens.append(time.time())


class RtiScraperSource(DataSource):
    """RTI Business scraper adapter.

    Fetches data from RTI Business public JSON endpoints.
    Requires no API key but is rate-limited to be polite.
    """

    name = "rti"
    typical_delay_minutes = 15
    supports_realtime = False

    # RTI Business API base URL
    BASE_URL = "https://www.rti.co.id"
    QUOTE_URL = "https://www.rti.co.id/api/stock/{ticker}/info"
    HISTORY_URL = "https://www.rti.co.id/api/stock/{ticker}/history"

    _HEADERS = {
        "User-Agent": "Mozilla/5.0 (compatible; saham-indonesia/0.1; +https://github.com/alimaghfur/saham-indonesia)",
        "Accept": "application/json",
        "Referer": "https://www.rti.co.id/",
    }

    def __init__(self) -> None:
        self._rate_limit = settings.rti_rate_limit_per_min
        self._limiter = _RateLimiter(max_per_minute=self._rate_limit)
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Lazy-initialize httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                timeout=httpx.Timeout(15.0, connect=10.0),
                headers=self._HEADERS,
                follow_redirects=True,
            )
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_json(self, url: str) -> dict:
        """Fetch JSON from URL with rate limiting and retries."""
        self._limiter.acquire()
        client = self._get_client()
        try:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            raise SourceError(
                f"RTI HTTP {exc.response.status_code} for {url}"
            ) from exc
        except httpx.RequestError as exc:
            raise SourceError(f"RTI request failed: {exc}") from exc

    def get_quote(self, ticker: str) -> Quote:
        """Fetch latest quote for a ticker from RTI Business.

        Parses the RTI stock info API response.
        """
        ticker_upper = ticker.upper().replace(".JK", "")
        url = self.QUOTE_URL.format(ticker=ticker_upper)

        try:
            data = self._fetch_json(url)
        except SourceError:
            raise
        except Exception as exc:
            raise SourceError(f"RTI quote fetch failed for {ticker}: {exc}") from exc

        # Parse response - RTI returns nested JSON
        # Expected structure: {"data": {"last": ..., "open": ..., ...}}
        stock_data = data.get("data", data)

        last = stock_data.get("last") or stock_data.get("close") or stock_data.get("lastPrice")
        if last is None:
            raise SourceError(f"No quote data returned from RTI for {ticker}")

        return Quote(
            ticker=ticker_upper,
            timestamp=datetime.utcnow(),
            last=Decimal(str(last)),
            open=Decimal(str(stock_data["open"])) if stock_data.get("open") else None,
            high=Decimal(str(stock_data["high"])) if stock_data.get("high") else None,
            low=Decimal(str(stock_data["low"])) if stock_data.get("low") else None,
            prev_close=Decimal(str(stock_data["prevClose"])) if stock_data.get("prevClose") else None,
            volume=int(stock_data.get("volume", 0) or 0),
            value=Decimal(str(stock_data["value"])) if stock_data.get("value") else None,
            delayed_minutes=self.typical_delay_minutes,
            source=self.name,
        )

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        """Fetch historical OHLC data from RTI Business.

        RTI provides daily data. Intraday intervals are not supported.
        """
        if interval not in ("1d", "1wk", "1mo"):
            raise SourceError(
                f"RTI scraper only supports daily/weekly/monthly intervals, got '{interval}'"
            )

        ticker_upper = ticker.upper().replace(".JK", "")
        days = _PERIOD_TO_DAYS.get(period, 365)

        # Build URL with date range parameters
        end_date = datetime.utcnow()
        start_date = datetime(
            end_date.year - (days // 365),
            end_date.month,
            end_date.day,
        ) if days > 365 else datetime.utcnow()

        url = self.HISTORY_URL.format(ticker=ticker_upper)
        # Add query params for period
        url = f"{url}?period={days}d"

        try:
            data = self._fetch_json(url)
        except SourceError:
            raise
        except Exception as exc:
            raise SourceError(f"RTI OHLC fetch failed for {ticker}: {exc}") from exc

        # Parse response - expected: {"data": [{"date": ..., "open": ..., ...}, ...]}
        records = data.get("data", data) if isinstance(data, dict) else data
        if not isinstance(records, list):
            records = records.get("history", []) if isinstance(records, dict) else []

        if not records:
            raise SourceError(f"No OHLC data returned from RTI for {ticker} (period={period})")

        rows = []
        for rec in records:
            try:
                row = {
                    "timestamp": pd.Timestamp(rec.get("date") or rec.get("timestamp", "")),
                    "open": float(rec.get("open", 0)),
                    "high": float(rec.get("high", 0)),
                    "low": float(rec.get("low", 0)),
                    "close": float(rec.get("close", 0)),
                    "volume": int(rec.get("volume", 0) or 0),
                }
                rows.append(row)
            except (ValueError, TypeError, KeyError):
                continue

        if not rows:
            raise SourceError(f"Could not parse OHLC data from RTI for {ticker}")

        df = pd.DataFrame(rows)
        df = df.set_index("timestamp").sort_index()
        df.index.name = "timestamp"
        return df

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()
            self._client = None
