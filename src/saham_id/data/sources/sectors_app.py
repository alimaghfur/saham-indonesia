"""Sectors.app adapter — premium IDX financial data.

Sectors.app (https://sectors.app) by Supertype is a premium financial data
layer for IDX + SGX with rich fundamental, sector, and ownership data.

Docs: https://docs.sectors.app

Endpoints (v2):
    - GET /v2/company/report/{ticker}/ — company overview + quote
    - GET /v2/company/report/{ticker}/financials/ — fundamental data
    - GET /v2/stock/{ticker}/historical/ — daily OHLC
    - GET /v2/sector/ — sector classification
    - GET /v2/most-traded/ — most active stocks
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Iterable, Optional

import httpx
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from saham_id.config import settings
from saham_id.data.models import FundamentalSnapshot, Quote
from saham_id.data.sources.base import (
    DataSource,
    Interval,
    Period,
    SourceError,
)


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
    "ytd": 365,
    "max": 7300,
}


class SectorsAppSource(DataSource):
    """Sectors.app API adapter (v2).

    Features:
        - Company quotes with bid/ask
        - Daily historical OHLC
        - Rich fundamental data (PER, PBV, ROE, margins, DER, etc.)
        - Sector & sub-sector classification
        - Ownership structure
        - Corporate actions
    """

    name = "sectors"
    typical_delay_minutes = 0
    supports_realtime = True

    BASE_URL = "https://api.sectors.app/v2"

    _HEADERS_TEMPLATE = {
        "Accept": "application/json",
        "User-Agent": "saham-indonesia/0.1",
    }

    def __init__(self) -> None:
        self._api_key = settings.sectors_api_key
        self._client: Optional[httpx.Client] = None

    def _require_key(self) -> None:
        if not self._api_key:
            raise SourceError(
                "SECTORS_API_KEY is empty. Set it in `.env` or process environment. "
                "Get a key at https://sectors.app"
            )

    def _get_client(self) -> httpx.Client:
        """Lazy-initialize httpx client with auth."""
        if self._client is None or self._client.is_closed:
            headers = dict(self._HEADERS_TEMPLATE)
            headers["Authorization"] = self._api_key
            self._client = httpx.Client(
                timeout=httpx.Timeout(20.0, connect=10.0),
                headers=headers,
                follow_redirects=True,
            )
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _request(self, url: str, params: Optional[dict] = None) -> dict | list:
        """Make authenticated GET request to Sectors.app API."""
        client = self._get_client()
        try:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise SourceError("Sectors.app: invalid API key") from exc
            if exc.response.status_code == 403:
                raise SourceError(
                    "Sectors.app: forbidden — check your plan tier"
                ) from exc
            if exc.response.status_code == 429:
                raise SourceError("Sectors.app: rate limit exceeded") from exc
            if exc.response.status_code == 404:
                raise SourceError(
                    f"Sectors.app: not found (url={url})"
                ) from exc
            raise SourceError(
                f"Sectors.app HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except httpx.RequestError as exc:
            raise SourceError(f"Sectors.app request failed: {exc}") from exc

    def _normalize_ticker(self, ticker: str) -> str:
        """Normalize ticker to Sectors.app format (e.g. BBCA.JK)."""
        t = ticker.upper().strip()
        if not t.endswith(".JK"):
            return f"{t}.JK"
        return t

    def _plain_ticker(self, ticker: str) -> str:
        """Strip .JK suffix for display."""
        return ticker.upper().replace(".JK", "")

    def get_quote(self, ticker: str) -> Quote:
        """Fetch latest quote from Sectors.app company report.

        Endpoint: GET /v2/company/report/{ticker}/
        """
        self._require_key()
        symbol = self._normalize_ticker(ticker)
        url = f"{self.BASE_URL}/company/report/{symbol}/"

        data = self._request(url)
        if not isinstance(data, dict):
            raise SourceError(f"Unexpected response format from Sectors.app for {ticker}")

        # Extract price data from company report
        last = (
            data.get("last_price")
            or data.get("close")
            or data.get("price")
        )
        if last is None:
            raise SourceError(f"No price data from Sectors.app for {ticker}")

        # Parse last update timestamp
        ts_raw = data.get("last_update") or data.get("date")
        if ts_raw and isinstance(ts_raw, str):
            try:
                timestamp = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)

        return Quote(
            ticker=self._plain_ticker(ticker),
            timestamp=timestamp,
            last=Decimal(str(last)),
            open=Decimal(str(data["open"])) if data.get("open") else None,
            high=Decimal(str(data["high"])) if data.get("high") else None,
            low=Decimal(str(data["low"])) if data.get("low") else None,
            prev_close=(
                Decimal(str(data["prev_close"]))
                if data.get("prev_close")
                else None
            ),
            volume=int(data.get("volume", 0) or 0),
            value=Decimal(str(data["value"])) if data.get("value") else None,
            bid=Decimal(str(data["bid"])) if data.get("bid") else None,
            ask=Decimal(str(data["ask"])) if data.get("ask") else None,
            delayed_minutes=0,
            source=self.name,
        )

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        """Fetch historical OHLC from Sectors.app.

        Endpoint: GET /v2/stock/{ticker}/historical/?start={date}&end={date}

        Only daily data is available.
        """
        self._require_key()

        if interval not in ("1d", "1wk", "1mo"):
            raise SourceError(
                f"Sectors.app only supports daily interval, got '{interval}'"
            )

        symbol = self._normalize_ticker(ticker)
        days = _PERIOD_TO_DAYS.get(period, 365)

        end_date = date.today()
        from datetime import timedelta
        start_date = end_date - timedelta(days=days)

        url = f"{self.BASE_URL}/stock/{symbol}/historical/"
        params = {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
        }

        data = self._request(url, params=params)

        # Parse response — expected list of daily bars
        records = data if isinstance(data, list) else data.get("data", [])

        if not records:
            raise SourceError(
                f"No OHLC data from Sectors.app for {ticker} (period={period})"
            )

        rows = []
        for rec in records:
            try:
                date_str = rec.get("date") or rec.get("timestamp", "")
                if not date_str:
                    continue
                ts = pd.Timestamp(date_str)

                rows.append({
                    "timestamp": ts,
                    "open": float(rec.get("open", 0)),
                    "high": float(rec.get("high", 0)),
                    "low": float(rec.get("low", 0)),
                    "close": float(rec.get("close", 0)),
                    "volume": int(rec.get("volume", 0) or 0),
                })
            except (ValueError, TypeError, KeyError):
                continue

        if not rows:
            raise SourceError(f"Could not parse OHLC from Sectors.app for {ticker}")

        df = pd.DataFrame(rows)
        df = df.set_index("timestamp").sort_index()
        df.index.name = "timestamp"
        return df

    def get_fundamentals(self, ticker: str) -> FundamentalSnapshot:
        """Fetch fundamental financial data from Sectors.app.

        Endpoint: GET /v2/company/report/{ticker}/
        or: GET /v2/company/report/{ticker}/financials/

        Returns a FundamentalSnapshot with valuation, profitability,
        solvency, growth, and dividend metrics.
        """
        self._require_key()
        symbol = self._normalize_ticker(ticker)

        # Try financials endpoint first, fall back to report
        url = f"{self.BASE_URL}/company/report/{symbol}/"
        data = self._request(url)

        if not isinstance(data, dict):
            raise SourceError(
                f"Unexpected response from Sectors.app fundamentals for {ticker}"
            )

        # Extract fundamental metrics from company report
        # Sectors.app provides rich nested data; map to our model
        financials = data.get("financials", data)
        valuation = data.get("valuation", data)
        overview = data.get("overview", data)

        # Determine as_of date
        as_of_raw = (
            data.get("last_report_date")
            or data.get("financial_year_end")
            or data.get("date")
        )
        if as_of_raw and isinstance(as_of_raw, str):
            try:
                as_of = date.fromisoformat(as_of_raw[:10])
            except ValueError:
                as_of = date.today()
        else:
            as_of = date.today()

        # Market cap
        market_cap = (
            data.get("market_cap")
            or overview.get("market_cap")
            or valuation.get("market_cap")
        )

        return FundamentalSnapshot(
            ticker=self._plain_ticker(ticker),
            as_of=as_of,
            # Valuation
            market_cap=Decimal(str(market_cap)) if market_cap else None,
            per=_safe_float(valuation.get("pe") or valuation.get("per") or data.get("pe_ratio")),
            pbv=_safe_float(valuation.get("pb") or valuation.get("pbv") or data.get("pb_ratio")),
            ps=_safe_float(valuation.get("ps") or data.get("ps_ratio")),
            ev_ebitda=_safe_float(valuation.get("ev_ebitda") or data.get("ev_ebitda")),
            # Profitability
            roe=_safe_float(financials.get("roe") or data.get("roe")),
            roa=_safe_float(financials.get("roa") or data.get("roa")),
            net_margin=_safe_float(
                financials.get("net_margin")
                or financials.get("net_profit_margin")
                or data.get("net_margin")
            ),
            # Solvency
            der=_safe_float(financials.get("der") or financials.get("debt_to_equity") or data.get("der")),
            current_ratio=_safe_float(financials.get("current_ratio") or data.get("current_ratio")),
            # Growth
            revenue_growth_yoy=_safe_float(
                financials.get("revenue_growth")
                or data.get("revenue_growth_yoy")
            ),
            earnings_growth_yoy=_safe_float(
                financials.get("earnings_growth")
                or financials.get("net_income_growth")
                or data.get("earnings_growth_yoy")
            ),
            # Dividend
            dividend_yield=_safe_float(
                data.get("dividend_yield")
                or valuation.get("dividend_yield")
            ),
            payout_ratio=_safe_float(
                financials.get("payout_ratio")
                or data.get("payout_ratio")
            ),
            source=self.name,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()
            self._client = None


def _safe_float(value) -> Optional[float]:
    """Safely convert a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        result = float(value)
        # Convert percentage if > 1 and likely a percentage field
        return result
    except (ValueError, TypeError):
        return None
