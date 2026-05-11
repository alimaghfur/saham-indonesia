"""BPJS screener — Beli Pagi, Jual Sore (intraday long).

Logic:
    For each ticker, compute daily intraday return = (close - open) / open.
    Rank tickers that historically have:
      - high win rate (close > open)
      - positive average intraday return
      - enough liquidity to actually trade

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
    min_win_rate: float = 0.55,
    min_avg_return: float = 0.003,
    min_avg_value: float = 1_000_000_000,
    top_n: int = 10,
    source: DataSource | None = None,
) -> ScreenResult:
    """Screen for BPJS (Beli Pagi Jual Sore) candidates."""
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    rows: list[ScreenRow] = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period=f"{max(lookback_days + 10, 90)}d", interval="1d")
        except Exception:
            continue
        if df.empty or len(df) < lookback_days:
            continue

        df = df.tail(lookback_days).copy()
        df["intraday_ret"] = (df["close"] - df["open"]) / df["open"]
        df["daily_value"] = df["close"] * df["volume"]  # rough transaction value proxy

        win_rate = float((df["intraday_ret"] > 0).mean())
        avg_ret = float(df["intraday_ret"].mean())
        avg_value = float(df["daily_value"].mean())

        if win_rate < min_win_rate:
            continue
        if avg_ret < min_avg_return:
            continue
        if avg_value < min_avg_value:
            continue

        score = win_rate * 100 + avg_ret * 1000  # simple composite
        rows.append(
            ScreenRow(
                ticker=ticker,
                score=score,
                metrics={
                    "win_rate": round(win_rate, 4),
                    "avg_intraday_ret": round(avg_ret, 5),
                    "avg_daily_value": round(avg_value, 0),
                    "sample_days": int(len(df)),
                },
            )
        )

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(
        strategy="bpjs",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "lookback_days": lookback_days,
            "min_win_rate": min_win_rate,
            "min_avg_return": min_avg_return,
            "min_avg_value": min_avg_value,
        },
    )
