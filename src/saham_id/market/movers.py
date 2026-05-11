"""Top Gainer / Top Loser screener.

Computes % change over a given period using daily OHLC. Works with any
source implementing `get_ohlc` (default: yfinance).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Literal

import pandas as pd

from saham_id.data.models import Mover
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe

Period = Literal["1D", "1W", "1M", "3M", "YTD"]

_PERIOD_TO_YF = {
    "1D": "5d",    # fetch 5 business days, take last 2 closes
    "1W": "1mo",
    "1M": "3mo",
    "3M": "6mo",
    "YTD": "ytd",
}

_PERIOD_TO_BARS = {
    "1D": 2,
    "1W": 6,
    "1M": 22,
    "3M": 66,
    "YTD": None,  # handled separately — all YTD bars
}


def _compute_change(df: pd.DataFrame, period: Period) -> tuple[float, float, int, float]:
    """Return (last_close, change_pct, volume_last, value_last)."""
    if period == "YTD":
        # First close of year -> last close
        first_close = float(df["close"].iloc[0])
    else:
        bars = _PERIOD_TO_BARS[period] or 2
        if len(df) < bars:
            raise ValueError(f"not enough data for period={period}")
        first_close = float(df["close"].iloc[-bars])

    last_close = float(df["close"].iloc[-1])
    change_pct = (last_close - first_close) / first_close
    vol = int(df["volume"].iloc[-1]) if "volume" in df.columns else 0
    val = last_close * vol
    return last_close, change_pct, vol, val


def _build_movers_table(
    tickers: Iterable[str],
    period: Period,
    source: DataSource,
) -> pd.DataFrame:
    """Fetch OHLC for each ticker and compute change metrics."""
    yf_period = _PERIOD_TO_YF[period]
    rows: list[dict] = []
    for t in tickers:
        try:
            df = source.get_ohlc(t, period=yf_period, interval="1d")
            if df.empty:
                continue
            last, chg, vol, val = _compute_change(df, period)
            rows.append(
                {
                    "ticker": t,
                    "last": last,
                    "change_pct": chg,
                    "volume": vol,
                    "value": val,
                }
            )
        except Exception:
            continue
    return pd.DataFrame(rows)


def _apply_filters(
    df: pd.DataFrame,
    min_price: float,
    min_value: float,
) -> pd.DataFrame:
    if df.empty:
        return df
    return df[(df["last"] >= min_price) & (df["value"] >= min_value)].reset_index(drop=True)


def _to_movers(df: pd.DataFrame) -> list[Mover]:
    return [
        Mover(
            ticker=r["ticker"],
            last=Decimal(str(r["last"])),
            change=Decimal(str(r["last"] * r["change_pct"])),
            change_pct=float(r["change_pct"]),
            volume=int(r["volume"]),
            value=Decimal(str(r["value"])),
            rank=i + 1,
        )
        for i, r in df.iterrows()
    ]


def top_gainers(
    universe: str | Iterable[str] = "LQ45",
    period: Period = "1D",
    min_price: float = 50.0,
    min_value: float = 1_000_000_000.0,
    top_n: int = 20,
    source: DataSource | None = None,
) -> list[Mover]:
    """Return top-N gainers in a universe over the requested period."""
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    df = _build_movers_table(tickers, period, src)
    df = _apply_filters(df, min_price, min_value)
    df = df.sort_values("change_pct", ascending=False).head(top_n).reset_index(drop=True)
    return _to_movers(df)


def top_losers(
    universe: str | Iterable[str] = "LQ45",
    period: Period = "1D",
    min_price: float = 50.0,
    min_value: float = 1_000_000_000.0,
    top_n: int = 20,
    source: DataSource | None = None,
) -> list[Mover]:
    """Return top-N losers in a universe over the requested period."""
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    df = _build_movers_table(tickers, period, src)
    df = _apply_filters(df, min_price, min_value)
    df = df.sort_values("change_pct", ascending=True).head(top_n).reset_index(drop=True)
    return _to_movers(df)


def most_active(
    universe: str | Iterable[str] = "LQ45",
    by: Literal["volume", "value"] = "value",
    top_n: int = 20,
    source: DataSource | None = None,
) -> list[Mover]:
    """Return top-N most actively traded stocks (by volume or transaction value)."""
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    df = _build_movers_table(tickers, "1D", src)
    if df.empty:
        return []
    df = df.sort_values(by, ascending=False).head(top_n).reset_index(drop=True)
    return _to_movers(df)
