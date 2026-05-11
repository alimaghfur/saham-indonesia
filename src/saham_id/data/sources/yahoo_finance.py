"""Yahoo Finance adapter (via `yfinance`).

- Free, no API key.
- Delayed ~15 minutes for quotes.
- Best-in-class daily OHLC; limited intraday (7 days for 1m).
- Tickers are suffixed with `.JK` for IDX (e.g. `BBCA.JK`).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Iterable

import pandas as pd

from saham_id.data.models import Quote
from saham_id.data.sources.base import DataSource, Interval, Period, SourceError


def _to_yahoo(ticker: str) -> str:
    t = ticker.upper()
    return t if t.endswith(".JK") else f"{t}.JK"


def _from_yahoo(symbol: str) -> str:
    return symbol.upper().removesuffix(".JK")


class YahooFinanceSource(DataSource):
    """`yfinance` backed implementation. Functional out of the box."""

    name = "yahoo"
    typical_delay_minutes = 15
    supports_realtime = False

    def __init__(self) -> None:
        try:
            import yfinance  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise SourceError(
                "yfinance not installed. Run `pip install yfinance`."
            ) from exc

    # ------------------------------------------------------------------
    # Quotes
    # ------------------------------------------------------------------
    def get_quote(self, ticker: str) -> Quote:
        import yfinance as yf

        symbol = _to_yahoo(ticker)
        tk = yf.Ticker(symbol)
        # `fast_info` is the cheapest path; avoid `info` (slow & heavy).
        try:
            fi = tk.fast_info
            last = fi.get("last_price")
            prev = fi.get("previous_close")
            open_ = fi.get("open")
            high = fi.get("day_high")
            low = fi.get("day_low")
            volume = fi.get("last_volume") or 0
        except Exception as exc:
            raise SourceError(f"yfinance quote failed for {ticker}: {exc}") from exc

        if last is None:
            raise SourceError(f"No quote returned for {ticker}")

        return Quote(
            ticker=_from_yahoo(symbol),
            timestamp=datetime.utcnow(),
            last=Decimal(str(last)),
            open=Decimal(str(open_)) if open_ else None,
            high=Decimal(str(high)) if high else None,
            low=Decimal(str(low)) if low else None,
            prev_close=Decimal(str(prev)) if prev else None,
            volume=int(volume) if volume else 0,
            delayed_minutes=self.typical_delay_minutes,
            source=self.name,
        )

    def get_quotes(self, tickers: Iterable[str]) -> list[Quote]:
        # yfinance.Tickers batch is more efficient than loop.
        import yfinance as yf

        symbols = [_to_yahoo(t) for t in tickers]
        if not symbols:
            return []
        tks = yf.Tickers(" ".join(symbols))
        quotes: list[Quote] = []
        for sym in symbols:
            tk = tks.tickers.get(sym)
            if tk is None:
                continue
            try:
                fi = tk.fast_info
                last = fi.get("last_price")
                if last is None:
                    continue
                quotes.append(
                    Quote(
                        ticker=_from_yahoo(sym),
                        timestamp=datetime.utcnow(),
                        last=Decimal(str(last)),
                        open=Decimal(str(fi.get("open"))) if fi.get("open") else None,
                        high=Decimal(str(fi.get("day_high"))) if fi.get("day_high") else None,
                        low=Decimal(str(fi.get("day_low"))) if fi.get("day_low") else None,
                        prev_close=(
                            Decimal(str(fi.get("previous_close")))
                            if fi.get("previous_close")
                            else None
                        ),
                        volume=int(fi.get("last_volume") or 0),
                        delayed_minutes=self.typical_delay_minutes,
                        source=self.name,
                    )
                )
            except Exception:
                # Best-effort batch: skip ticker on failure, continue others.
                continue
        return quotes

    # ------------------------------------------------------------------
    # OHLC
    # ------------------------------------------------------------------
    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        import yfinance as yf

        symbol = _to_yahoo(ticker)
        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            threads=False,
        )
        if df is None or df.empty:
            raise SourceError(f"No OHLC for {ticker} (period={period}, interval={interval})")
        # Flatten multi-index columns yfinance sometimes returns.
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
        df = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )
        df.index.name = "timestamp"
        return df
