"""iTick adapter — REST API + WebSocket streaming.

iTick (https://itick.org) offers realtime IDX quotes and WebSocket streaming
with a free tier. Requires an API key (`ITICK_API_KEY` in `.env`).

Docs: https://blog.itick.org/en/stock-api/indonesia-stock-api-quantitative-integration

Endpoints:
    - GET /stock/quote?region=ID&code={ticker} — latest quote
    - GET /stock/kline?region=ID&code={ticker}&kType={interval}&num={count} — OHLC bars
    - WSS wss://ws.itick.org/stream — realtime tick streaming
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import AsyncIterator, Optional

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


# Map our standard periods to bar count for iTick kline endpoint
_PERIOD_TO_BARS: dict[str, int] = {
    "1d": 1,
    "5d": 5,
    "1mo": 22,
    "3mo": 66,
    "6mo": 132,
    "1y": 252,
    "2y": 504,
    "5y": 1260,
    "10y": 2520,
    "ytd": 252,
    "max": 5000,
}

# Map our standard intervals to iTick kType parameter
_INTERVAL_TO_KTYPE: dict[str, str] = {
    "1m": "1",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "60m": "60",
    "1h": "60",
    "1d": "D",
    "1wk": "W",
    "1mo": "M",
}


def _to_itick_symbol(ticker: str) -> str:
    """Convert IDX ticker to iTick format (e.g. BBCA -> BBCA.JK)."""
    t = ticker.upper().strip()
    if not t.endswith(".JK"):
        return f"{t}.JK"
    return t


class ITickSource(DataSource):
    """iTick REST API adapter for IDX stocks.

    Features:
        - Realtime quotes (no delay with paid tier, ~1s on free tier)
        - Intraday kline data (1m, 5m, 15m, 30m, 60m)
        - Daily/Weekly/Monthly OHLC
        - WebSocket streaming (for scalping module)
    """

    name = "itick"
    typical_delay_minutes = 0
    supports_realtime = True

    BASE_URL = "https://api.itick.org/stock"

    _HEADERS_TEMPLATE = {
        "Accept": "application/json",
        "User-Agent": "saham-indonesia/0.1",
    }

    def __init__(self) -> None:
        self._api_key = settings.itick_api_key
        self._client: Optional[httpx.Client] = None

    def _require_key(self) -> None:
        if not self._api_key:
            raise SourceError(
                "ITICK_API_KEY is empty. Set it in `.env` or process environment. "
                "Get a free key at https://itick.org"
            )

    def _get_client(self) -> httpx.Client:
        """Lazy-initialize httpx client with auth token."""
        if self._client is None or self._client.is_closed:
            headers = dict(self._HEADERS_TEMPLATE)
            headers["token"] = self._api_key
            self._client = httpx.Client(
                base_url=self.BASE_URL,
                timeout=httpx.Timeout(15.0, connect=10.0),
                headers=headers,
                follow_redirects=True,
            )
        return self._client

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    def _request(self, endpoint: str, params: dict) -> dict:
        """Make authenticated GET request to iTick API."""
        client = self._get_client()
        try:
            response = client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                raise SourceError("iTick rate limit exceeded. Wait and retry.") from exc
            raise SourceError(
                f"iTick HTTP {exc.response.status_code}: {exc.response.text[:200]}"
            ) from exc
        except httpx.RequestError as exc:
            raise SourceError(f"iTick request failed: {exc}") from exc

        # iTick returns {"code": 0, "data": {...}} on success
        if isinstance(data, dict):
            code = data.get("code", data.get("ret", -1))
            if code != 0 and "data" not in data:
                msg = data.get("msg", data.get("message", "Unknown error"))
                raise SourceError(f"iTick API error (code={code}): {msg}")
        return data

    def get_quote(self, ticker: str) -> Quote:
        """Fetch realtime quote from iTick REST API.

        Endpoint: GET /stock/quote?region=ID&code={symbol}
        """
        self._require_key()
        symbol = _to_itick_symbol(ticker)

        data = self._request("/quote", params={"region": "ID", "code": symbol})

        # Parse response
        quote_data = data.get("data", {})
        if isinstance(quote_data, list):
            quote_data = quote_data[0] if quote_data else {}

        last = quote_data.get("last") or quote_data.get("close") or quote_data.get("price")
        if last is None:
            raise SourceError(f"No quote data from iTick for {ticker}")

        # Parse timestamp
        ts_raw = quote_data.get("timestamp") or quote_data.get("time")
        if ts_raw and isinstance(ts_raw, (int, float)):
            timestamp = datetime.fromtimestamp(ts_raw, tz=timezone.utc)
        else:
            timestamp = datetime.now(timezone.utc)

        return Quote(
            ticker=ticker.upper().replace(".JK", ""),
            timestamp=timestamp,
            last=Decimal(str(last)),
            open=Decimal(str(quote_data["open"])) if quote_data.get("open") else None,
            high=Decimal(str(quote_data["high"])) if quote_data.get("high") else None,
            low=Decimal(str(quote_data["low"])) if quote_data.get("low") else None,
            prev_close=(
                Decimal(str(quote_data["prevClose"]))
                if quote_data.get("prevClose")
                else None
            ),
            volume=int(quote_data.get("volume", 0) or 0),
            value=(
                Decimal(str(quote_data["amount"]))
                if quote_data.get("amount")
                else None
            ),
            bid=Decimal(str(quote_data["bid"])) if quote_data.get("bid") else None,
            ask=Decimal(str(quote_data["ask"])) if quote_data.get("ask") else None,
            delayed_minutes=0,
            source=self.name,
        )

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        """Fetch historical OHLC bars from iTick kline endpoint.

        Endpoint: GET /stock/kline?region=ID&code={symbol}&kType={type}&num={count}

        Supports intraday intervals (1m, 5m, 15m, 30m, 60m) as well as
        daily, weekly, monthly.
        """
        self._require_key()
        symbol = _to_itick_symbol(ticker)

        ktype = _INTERVAL_TO_KTYPE.get(interval)
        if ktype is None:
            raise SourceError(
                f"iTick does not support interval '{interval}'. "
                f"Supported: {list(_INTERVAL_TO_KTYPE.keys())}"
            )

        num_bars = _PERIOD_TO_BARS.get(period, 252)
        # For intraday, limit bars (iTick free tier may cap)
        if interval in ("1m", "5m", "15m", "30m"):
            num_bars = min(num_bars, 1000)

        data = self._request(
            "/kline",
            params={
                "region": "ID",
                "code": symbol,
                "kType": ktype,
                "num": num_bars,
            },
        )

        # Parse response: {"data": {"kline": [{"time": ..., "open": ..., ...}, ...]}}
        kline_data = data.get("data", {})
        if isinstance(kline_data, dict):
            records = kline_data.get("kline", kline_data.get("list", []))
        elif isinstance(kline_data, list):
            records = kline_data
        else:
            records = []

        if not records:
            raise SourceError(
                f"No OHLC data from iTick for {ticker} (period={period}, interval={interval})"
            )

        rows = []
        for rec in records:
            try:
                # Parse timestamp (iTick returns unix epoch seconds)
                ts_raw = rec.get("time") or rec.get("timestamp") or rec.get("t")
                if isinstance(ts_raw, (int, float)):
                    ts = datetime.fromtimestamp(ts_raw, tz=timezone.utc)
                elif isinstance(ts_raw, str):
                    ts = pd.Timestamp(ts_raw)
                else:
                    continue

                rows.append({
                    "timestamp": ts,
                    "open": float(rec.get("open") or rec.get("o", 0)),
                    "high": float(rec.get("high") or rec.get("h", 0)),
                    "low": float(rec.get("low") or rec.get("l", 0)),
                    "close": float(rec.get("close") or rec.get("c", 0)),
                    "volume": int(rec.get("volume") or rec.get("v", 0)),
                })
            except (ValueError, TypeError, KeyError):
                continue

        if not rows:
            raise SourceError(f"Could not parse kline data from iTick for {ticker}")

        df = pd.DataFrame(rows)
        df = df.set_index("timestamp").sort_index()
        df.index.name = "timestamp"
        return df

    def stream_ticks(self, tickers: list[str]) -> AsyncIterator:
        """Connect to iTick WebSocket for realtime tick streaming.

        WebSocket URL: wss://ws.itick.org/stream
        Subscribe message: {"type": "subscribe", "code": "BBCA.JK", "region": "ID"}

        Returns an async iterator yielding tick dicts.
        Requires `websockets` package (optional dependency).

        Usage:
            async for tick in source.stream_ticks(["BBCA", "BBRI"]):
                print(tick)
        """
        self._require_key()

        async def _stream():
            try:
                import websockets
            except ImportError as exc:
                raise SourceError(
                    "websockets package required for streaming. "
                    "Install with: pip install websockets"
                ) from exc

            import json

            ws_url = "wss://ws.itick.org/stream"
            symbols = [_to_itick_symbol(t) for t in tickers]

            async with websockets.connect(
                ws_url,
                additional_headers={"token": self._api_key},
            ) as ws:
                # Subscribe to tickers
                for sym in symbols:
                    subscribe_msg = json.dumps({
                        "type": "subscribe",
                        "code": sym,
                        "region": "ID",
                    })
                    await ws.send(subscribe_msg)

                # Yield incoming ticks
                async for message in ws:
                    try:
                        tick = json.loads(message)
                        if tick.get("type") == "tick":
                            yield tick.get("data", tick)
                    except (json.JSONDecodeError, KeyError):
                        continue

        return _stream()

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            self._client.close()
            self._client = None
