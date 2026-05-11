"""BSJP screener — Beli Sore, Jual Pagi (overnight gap).

Logic:
    overnight_return[t] = (open[t+1] - close[t]) / close[t]
    Rank tickers with consistent positive overnight gaps.

Data requirement:
    Daily OHLC only (yfinance is sufficient).
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


def screen(
    universe: str | Iterable[str] = "LQ45",
    lookback_days: int = 60,
    min_gap_up_rate: float = 0.55,
    min_avg_gap: float = 0.002,
    min_avg_value: float = 1_000_000_000,
    top_n: int = 10,
    source: DataSource | None = None,
) -> ScreenResult:
    """Screen for BSJP (Beli Sore Jual Pagi) candidates."""
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    rows: list[ScreenRow] = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period=f"{max(lookback_days + 10, 90)}d", interval="1d")
        except Exception:
            continue
        if df.empty or len(df) < lookback_days + 1:
            continue

        df = df.tail(lookback_days + 1).copy()
        # overnight gap = next_open - prev_close, so shift open back by 1
        df["overnight_gap"] = (df["open"].shift(-1) - df["close"]) / df["close"]
        df = df.iloc[:-1]  # drop final row (no next day)

        df["daily_value"] = df["close"] * df["volume"]
        gap_up_rate = float((df["overnight_gap"] > 0).mean())
        avg_gap = float(df["overnight_gap"].mean())
        avg_value = float(df["daily_value"].mean())

        if gap_up_rate < min_gap_up_rate:
            continue
        if avg_gap < min_avg_gap:
            continue
        if avg_value < min_avg_value:
            continue

        score = gap_up_rate * 100 + avg_gap * 1000
        rows.append(
            ScreenRow(
                ticker=ticker,
                score=score,
                metrics={
                    "gap_up_rate": round(gap_up_rate, 4),
                    "avg_overnight_gap": round(avg_gap, 5),
                    "avg_daily_value": round(avg_value, 0),
                    "sample_days": int(len(df)),
                },
            )
        )

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(
        strategy="bsjp",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "lookback_days": lookback_days,
            "min_gap_up_rate": min_gap_up_rate,
            "min_avg_gap": min_avg_gap,
            "min_avg_value": min_avg_value,
        },
    )
