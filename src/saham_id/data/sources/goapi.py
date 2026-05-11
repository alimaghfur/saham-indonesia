"""GoAPI adapter — IDX stock data provider.

GoAPI (https://goapi.io/api-data-saham-indonesia/) is an Indonesian provider
offering IDX quotes, indices, corporate actions, etc. Freemium with API key.

Endpoints (v1):
    - GET /stock/idx/{ticker} — latest quote
    - GET /stock/idx/{ticker}/historical — historical OHLC
    - GET /stock/idx/trending — trending stocks
    - GET /stock/idx/top-gainers — top gainers
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Optional

import httpx
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from saham_id.config import settings
from saham_id.data.models import Mover, Quote
from saham_id.data.sources.base import (
    DataSource,
    Interval,
    MoverKind,
    Period,
    SourceError,
)


# Period to date range helpers
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


class GoApiSource(DataSource):
    """GoAPI REST adapter for IDX stock data.

    Features:
        - Realtime/near-realtime quotes (depends on plan)
        - Daily historical OHLC
        - Market movers (top gainers, losers, trending)
        - Corporate actions data
    """

    name = "goapi"
    typical_delay_minutes = 0  # plan-dependent
    supports_realtime = True

    BASE_URL = "https://api.goapi.io/stock/idx"

    _HEADERS_TEMPLATE = {
        "Accept": "application/json",
        "User-Agent": "saham-indonesia/0.1",
    }

    def __init__(self) -> None:
        self._api_key = settings.goapi_api_key
        self._client: Optional[httpx.Client] = None

    def _require_key(self) -> None:
        if not self._api_key:
            raise SourceError(
                "GOAPI_API_KEY is empty. Set it in `.env` or process environment. "
                "Get a key at https://goapi.io"
            )

    def _get_client(self) -> httpx.Client:
        """Lazy-initialize httpx client with API key header."""
        if self._client is None or self._client.is_closed:
            headers = dict(self._HEADERS_TEMPLATE)
            headers["X-API-KEY"] = self._api_key
            self._client = httpx.Client(
                timeout=httpx.Timeout(20.0, connect=10.0),
                headers=headers,
                follow_redirects=True,
            )
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def _request(self, url: str, params: Optional[dict] = None) -> dict:
        """Make authenticated GET request to GoAPI."""
        client = self._get_client()
        try:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 401:
                raise SourceError("GoAPI: invalid API key") from exc
            if exc.response.status_code == 429:
                raise SourceError("GoAPI: rate limit exceeded") from exc
            raise SourceError(
                f"GoAPI HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except httpx.RequestError as exc:
            raise SourceError(f"GoAPI request failed: {exc}") from exc

        # GoAPI returns {"status": "success", "data": {...}} or {"status": "error", ...}
        if isinstance(data, dict):
            status = data.get("status", "")
            if status == "error" or (isinstance(status, bool) and not status):
                msg = data.get("message", data.get("error", "Unknown error"))
                raise SourceError(f"GoAPI error: {msg}")
        return data

    def get_quote(self, ticker: str) -> Quote:
        """Fetch latest quote from GoAPI.

        Endpoint: GET /stock/idx/{ticker}
        """
        self._require_key()
        ticker_upper = ticker.upper().replace(".JK", "")
        url = f"{self.BASE_URL}/{ticker_upper}"

        data = self._request(url)
        stock = data.get("data", data)

        # Handle nested response structures
        if isinstance(stock, dict) and "results" in stock:
            stock = stock["results"]

        last = (
            stock.get("close")
            or stock.get("last")
            or stock.get("price")
            or stock.get("lastPrice")
        )
        if last is None:
            raise SourceError(f"No quote data from GoAPI for {ticker}")

        # Parse timestamp if available
        ts_raw = stock.get("date") or stock.get("timestamp") or stock.get("lastUpdate")
        if ts_raw and isinstance(ts_raw, str):
            try:
                timestamp = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now(timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)

        return Quote(
            ticker=ticker_upper,
            timestamp=timestamp,
            last=Decimal(str(last)),
            open=Decimal(str(stock["open"])) if stock.get("open") else None,
            high=Decimal(str(stock["high"])) if stock.get("high") else None,
            low=Decimal(str(stock["low"])) if stock.get("low") else None,
            prev_close=(
                Decimal(str(stock["previousClose"]))
                if stock.get("previousClose")
                else Decimal(str(stock["prevClose"])) if stock.get("prevClose") else None
            ),
            volume=int(stock.get("volume", 0) or 0),
            value=(
                Decimal(str(stock["value"]))
                if stock.get("value")
                else None
            ),
            delayed_minutes=self.typical_delay_minutes,
            source=self.name,
        )

    def get_quotes(self, tickers: Iterable[str]) -> list[Quote]:
        """Fetch quotes for multiple tickers (sequential, respecting rate limits)."""
        self._require_key()
        quotes: list[Quote] = []
        for ticker in tickers:
            try:
                quotes.append(self.get_quote(ticker))
            except SourceError:
                continue
        return quotes

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        """Fetch historical OHLC data from GoAPI.

        Endpoint: GET /stock/idx/{ticker}/historical?from={date}&to={date}

        GoAPI provides daily OHLC. Intraday intervals are not supported.
        """
        self._require_key()

        if interval not in ("1d", "1wk", "1mo"):
            raise SourceError(
                f"GoAPI only supports daily/weekly/monthly intervals, got '{interval}'"
            )

        ticker_upper = ticker.upper().replace(".JK", "")
        days = _PERIOD_TO_DAYS.get(period, 365)

        # Calculate date range
        to_date = datetime.now(timezone.utc)
        from_date = datetime(
            to_date.year,
            to_date.month,
            to_date.day,
            tzinfo=timezone.utc,
        )
        from_date = to_date.replace(
            year=to_date.year - (days // 365) if days >= 365 else to_date.year,
            month=max(1, to_date.month - (days % 365) // 30) if days < 365 else to_date.month,
        )

        url = f"{self.BASE_URL}/{ticker_upper}/historical"
        params = {
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d"),
        }

        data = self._request(url, params=params)

        # Parse response
        result = data.get("data", data)
        if isinstance(result, dict) and "results" in result:
            records = result["results"]
        elif isinstance(result, list):
            records = result
        else:
            records = result.get("historical", []) if isinstance(result, dict) else []

        if not records:
            raise SourceError(
                f"No OHLC data from GoAPI for {ticker} (period={period})"
            )

        rows = []
        for rec in records:
            try:
                # Parse date
                date_str = rec.get("date") or rec.get("timestamp") or ""
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
            raise SourceError(f"Could not parse OHLC from GoAPI for {ticker}")

        df = pd.DataFrame(rows)
        df = df.set_index("timestamp").sort_index()
        df.index.name = "timestamp"
        return df

    def get_movers(
        self,
        kind: MoverKind = "gainer",
        universe: Optional[Iterable[str]] = None,
        top_n: int = 20,
    ) -> list[Mover]:
        """Fetch market movers from GoAPI.

        Endpoints:
            - GET /stock/idx/top-gainers
            - GET /stock/idx/top-losers
            - GET /stock/idx/most-active
        """
        self._require_key()

        endpoint_map = {
            "gainer": f"{self.BASE_URL}/top-gainers",
            "loser": f"{self.BASE_URL}/top-losers",
            "most_active": f"{self.BASE_URL}/most-active",
            "trending": f"{self.BASE_URL}/trending",
        }

        url = endpoint_map.get(kind)
        if url is None:
            raise SourceError(f"GoAPI does not support mover kind '{kind}'")

        data = self._request(url, params={"limit": top_n})
        result = data.get("data", data)
        records = result.get("results", result) if isinstance(result, dict) else result

        if not isinstance(records, list):
            return []

        movers: list[Mover] = []
        for i, rec in enumerate(records[:top_n]):
            try:
                ticker = rec.get("ticker") or rec.get("symbol") or rec.get("code", "")
                last = rec.get("close") or rec.get("last") or rec.get("price", 0)
                change = rec.get("change", 0)
                change_pct = rec.get("changePct") or rec.get("changePercent") or rec.get("percent", 0)

                # Normalize change_pct (some APIs return as percentage, some as fraction)
                if isinstance(change_pct, (int, float)) and abs(change_pct) > 1:
                    change_pct = change_pct / 100.0

                movers.append(Mover(
                    ticker=ticker.upper().replace(".JK", ""),
                    last=Decimal(str(last)),
                    change=Decimal(str(change)),
                    change_pct=float(change_pct),
                    volume=int(rec.get("volume", 0) or 0),
                    value=Decimal(str(rec.get("value", 0) or 0)),
                    rank=i + 1,
                ))
            except (ValueError, TypeError, KeyError):
                continue

        return movers

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()
            self._client = None
