"""iTick adapter (https://itick.org).

REST endpoints used:
    GET /stock/quote    — realtime single-ticker quote
    GET /stock/quotes   — realtime multi-ticker quotes (batch)
    GET /stock/kline    — historical candles (K-line)

Auth:
    Header `token: <ITICK_API_KEY>`

Region:
    IDX stocks use `region=ID`. Ticker is the bare symbol (e.g. `BBCA`).

Docs:
    https://blog.itick.org/en/stock-api/indonesia-stock-api-quantitative-integration
    https://docs.itick.org/rest-api/stocks/stock-quote
    https://docs.itick.org/rest-api/stocks/stock-kline
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable

import httpx
import pandas as pd
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from saham_id.config import settings
from saham_id.data.models import Quote
from saham_id.data.sources.base import (
    DataSource,
    Interval,
    NotImplementedForSource,
    Period,
    SourceError,
)


# ---------------------------------------------------------------------------
# Interval & period mapping
# ---------------------------------------------------------------------------
# iTick `kType` values (from docs):
#   1  = 1m, 2  = 5m, 3  = 15m, 4  = 30m, 5  = 1h,
#   6  = 2h, 7  = 4h, 8  = 1d, 9  = 1w, 10 = 1mo
_INTERVAL_TO_KTYPE: dict[str, int] = {
    "1m": 1,
    "5m": 2,
    "15m": 3,
    "30m": 4,
    "60m": 5,
    "1h": 5,
    "1d": 8,
    "1wk": 9,
    "1mo": 10,
}


def _period_to_bar_count(period: Period, interval: Interval) -> int:
    """Rough translation of period string to a bar count for the `limit` arg.

    iTick's kline endpoint uses a bar-count limit rather than a date range,
    so we approximate with conservative upper bounds.
    """
    # Approx trading days per unit (IDX has ~247 per year)
    days = {
        "1d": 1, "5d": 5, "1mo": 22, "3mo": 66, "6mo": 132,
        "1y": 247, "2y": 494, "5y": 1235, "10y": 2470, "ytd": 247, "max": 2470,
    }.get(period, 247)

    # Bars per trading day for common intraday intervals (IDX ~4h session)
    bars_per_day = {
        "1m": 4 * 60,
        "5m": 4 * 12,
        "15m": 4 * 4,
        "30m": 4 * 2,
        "60m": 4,
        "1h": 4,
        "1d": 1,
        "1wk": 1 / 5,
        "1mo": 1 / 22,
    }.get(interval, 1)

    return max(50, int(days * bars_per_day))


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------
class ITickSource(DataSource):
    """REST-first iTick adapter.

    Streaming via WebSocket is exposed via :meth:`stream_ticks` as a
    placeholder — add an async consumer when the scalping pipeline needs it.
    """

    name = "itick"
    typical_delay_minutes = 0
    supports_realtime = True

    BASE_URL = "https://api.itick.org"
    REGION = "ID"
    DEFAULT_TIMEOUT = 15.0

    def __init__(self, api_key: str | None = None, timeout: float | None = None) -> None:
        self._api_key = api_key if api_key is not None else settings.itick_api_key
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            timeout=timeout or self.DEFAULT_TIMEOUT,
            headers=self._build_headers(),
        )

    # ------ helpers ------
    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "saham-indonesia/0.1 (+itick-adapter)",
        }
        if self._api_key:
            headers["token"] = self._api_key
        return headers

    def _require_key(self) -> None:
        if not self._api_key:
            raise SourceError(
                "ITICK_API_KEY is empty. Set it in `.env` or pass `api_key=...`."
            )

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.5, max=4.0),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    )
    def _get(self, path: str, params: dict[str, Any]) -> dict:
        """GET wrapper with retries and uniform error handling."""
        resp = self._client.get(path, params=params)
        if resp.status_code == 429:
            # Convert to HTTPStatusError so tenacity retries
            resp.raise_for_status()
        if resp.status_code >= 400:
            raise SourceError(
                f"iTick HTTP {resp.status_code} for {path}: {resp.text[:200]}"
            )
        try:
            return resp.json()
        except Exception as exc:
            raise SourceError(f"iTick non-JSON response from {path}: {exc}") from exc

    # ------ DataSource API ------
    def get_quote(self, ticker: str) -> Quote:
        self._require_key()
        payload = self._get(
            "/stock/quote",
            {"region": self.REGION, "code": ticker.upper().removesuffix(".JK")},
        )
        data = self._extract_quote_payload(payload)
        if data is None:
            raise SourceError(f"iTick: no quote data for {ticker}")
        return self._parse_quote(ticker, data)

    def get_quotes(self, tickers: Iterable[str]) -> list[Quote]:
        self._require_key()
        symbols = [t.upper().removesuffix(".JK") for t in tickers]
        if not symbols:
            return []
        payload = self._get(
            "/stock/quotes",
            {"region": self.REGION, "code": ",".join(symbols)},
        )
        items = self._extract_list_payload(payload)
        out: list[Quote] = []
        for item in items:
            code = str(item.get("code") or item.get("symbol") or "").upper()
            if not code:
                continue
            try:
                out.append(self._parse_quote(code, item))
            except Exception:
                continue
        return out

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        self._require_key()
        ktype = _INTERVAL_TO_KTYPE.get(interval)
        if ktype is None:
            raise SourceError(
                f"iTick does not support interval={interval!r}. "
                f"Allowed: {sorted(_INTERVAL_TO_KTYPE)}"
            )
        limit = _period_to_bar_count(period, interval)
        payload = self._get(
            "/stock/kline",
            {
                "region": self.REGION,
                "code": ticker.upper().removesuffix(".JK"),
                "kType": ktype,
                "limit": limit,
            },
        )
        items = self._extract_list_payload(payload)
        if not items:
            raise SourceError(f"iTick: empty kline for {ticker}")
        return self._parse_kline(items)

    # ------ WebSocket (skeleton) ------
    def stream_ticks(self, tickers: list[str]):  # pragma: no cover - placeholder
        """Async generator yielding tick updates.

        TODO: implement using `websockets` or `httpx-ws`. The iTick docs
        describe `wss://api.itick.org/sstream` with a subscribe message of
        the form ``{"ac": "subscribe", "params": "ID:BBCA,ID:BBRI"}`` after
        authenticating with the token. See
        https://docs.itick.org/en/websocket/stocks for the most current shape.
        """
        raise NotImplementedForSource("iTick WebSocket streaming not yet implemented.")

    # ------ Lifecycle ------
    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Parsing helpers (kept separate so they can be unit-tested cleanly)
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_quote_payload(payload: dict) -> dict | None:
        """iTick responses are commonly wrapped as ``{"code": 0, "data": ...}``.

        Accept both a wrapper and a bare-dict payload.
        """
        if not isinstance(payload, dict):
            return None
        if "data" in payload:
            data = payload["data"]
            if isinstance(data, list):
                return data[0] if data else None
            if isinstance(data, dict):
                return data
            return None
        return payload or None

    @staticmethod
    def _extract_list_payload(payload: dict) -> list[dict]:
        if not isinstance(payload, dict):
            return []
        data = payload.get("data", payload)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Some endpoints nest the list under `klines`, `list`, etc.
            for key in ("klines", "list", "items", "records"):
                if key in data and isinstance(data[key], list):
                    return data[key]
        return []

    @classmethod
    def _parse_quote(cls, ticker: str, data: dict) -> Quote:
        """Normalize an iTick quote dict into our canonical `Quote` model.

        Keys vary by endpoint version; we probe a handful of common names.
        """
        def _first(*keys: str) -> Any:
            for k in keys:
                if k in data and data[k] not in (None, ""):
                    return data[k]
            return None

        last = _first("ld", "last", "lastPrice", "price", "p")
        if last is None:
            raise SourceError(f"iTick: missing last price field in quote for {ticker}")
        open_ = _first("o", "open")
        high = _first("h", "high")
        low = _first("l", "low")
        prev = _first("pc", "preClose", "previousClose")
        volume = _first("v", "volume")
        ts_raw = _first("t", "time", "ts", "timestamp")
        timestamp = cls._parse_timestamp(ts_raw)

        return Quote(
            ticker=ticker.upper().removesuffix(".JK"),
            timestamp=timestamp,
            last=Decimal(str(last)),
            open=Decimal(str(open_)) if open_ is not None else None,
            high=Decimal(str(high)) if high is not None else None,
            low=Decimal(str(low)) if low is not None else None,
            prev_close=Decimal(str(prev)) if prev is not None else None,
            volume=int(volume) if volume is not None else 0,
            delayed_minutes=0,
            source="itick",
        )

    @classmethod
    def _parse_kline(cls, items: list[dict]) -> pd.DataFrame:
        """Convert a list of iTick kline dicts to an OHLCV DataFrame."""
        rows: list[dict] = []
        for it in items:
            ts = it.get("t") or it.get("time") or it.get("ts")
            try:
                rows.append(
                    {
                        "timestamp": cls._parse_timestamp(ts),
                        "open": float(it.get("o") or it.get("open") or 0.0),
                        "high": float(it.get("h") or it.get("high") or 0.0),
                        "low": float(it.get("l") or it.get("low") or 0.0),
                        "close": float(it.get("c") or it.get("close") or 0.0),
                        "volume": int(it.get("v") or it.get("volume") or 0),
                    }
                )
            except Exception:
                continue
        if not rows:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        df = pd.DataFrame(rows).set_index("timestamp").sort_index()
        return df

    @staticmethod
    def _parse_timestamp(ts: Any) -> datetime:
        """Accept epoch seconds, epoch millis, or ISO strings."""
        if ts is None:
            return datetime.utcnow()
        if isinstance(ts, (int, float)):
            # Heuristic: >= 1e12 means milliseconds
            seconds = float(ts) / 1000.0 if float(ts) > 1e12 else float(ts)
            return datetime.utcfromtimestamp(seconds)
        if isinstance(ts, str):
            # Try ISO8601 first
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
            except ValueError:
                try:
                    return datetime.utcfromtimestamp(float(ts))
                except Exception:
                    return datetime.utcnow()
        return datetime.utcnow()
