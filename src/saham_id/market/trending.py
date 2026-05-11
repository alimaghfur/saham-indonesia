"""Trending detector — combines volume, momentum, and breakout signals.

`trending` = "something unusual is going on". Unlike raw top-gainer, this
ranks stocks by a composite score:

    score = w_rvol * zscore(rvol)
          + w_mom  * zscore(price_return)
          + w_brk  * breakout_score

Defaults pick stocks with elevated volume AND price action — filters out
dead cat bounces on low volume.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Literal

import numpy as np

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow

Timeframe = Literal["1D", "1W", "1M"]

_TIMEFRAME_TO_PERIOD = {"1D": "3mo", "1W": "6mo", "1M": "1y"}
_TIMEFRAME_TO_BARS = {"1D": 1, "1W": 5, "1M": 20}


@dataclass
class TrendingWeights:
    rvol: float = 0.4
    momentum: float = 0.4
    breakout: float = 0.2


def _zscore_last(series, window: int = 60) -> float:
    """Last value's z-score vs a rolling window."""
    tail = series.dropna().tail(window)
    if len(tail) < 10:
        return 0.0
    mean = float(tail.mean())
    std = float(tail.std(ddof=0))
    if std == 0:
        return 0.0
    return (float(series.iloc[-1]) - mean) / std


def detect(
    universe: str | Iterable[str] = "LQ45",
    timeframe: Timeframe = "1D",
    min_rvol: float = 2.0,
    min_avg_value: float = 1_000_000_000.0,
    weights: TrendingWeights | None = None,
    top_n: int = 30,
    source: DataSource | None = None,
) -> ScreenResult:
    """Detect trending stocks by composite rvol + momentum + breakout score."""
    src = source or get_source()
    w = weights or TrendingWeights()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"
    period = _TIMEFRAME_TO_PERIOD[timeframe]
    bars = _TIMEFRAME_TO_BARS[timeframe]

    rows: list[ScreenRow] = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period=period, interval="1d")
        except Exception:
            continue
        if df.empty or len(df) < 30:
            continue
        df = df.copy()

        # Liquidity filter
        df["daily_value"] = df["close"] * df["volume"]
        avg_value = float(df["daily_value"].tail(20).mean())
        if avg_value < min_avg_value:
            continue

        # 1) Relative volume (current vs 20-day average)
        avg_vol = df["volume"].rolling(20).mean()
        rvol_now = float(df["volume"].iloc[-1] / avg_vol.iloc[-1]) if avg_vol.iloc[-1] else 0.0
        if rvol_now < min_rvol:
            continue

        # 2) Momentum — return over the requested bars, z-scored
        df["ret"] = df["close"].pct_change(bars)
        mom_z = _zscore_last(df["ret"], window=60)

        # 3) Breakout — distance above 20-day high, z-scored
        rolling_high = df["high"].rolling(20).max().shift(1)
        df["brk"] = (df["close"] - rolling_high) / rolling_high
        brk_z = _zscore_last(df["brk"], window=60)

        rvol_z = max(0.0, (rvol_now - 1.0))  # rvol=1 is "normal"; >1 contributes

        score = w.rvol * rvol_z + w.momentum * mom_z + w.breakout * brk_z
        if np.isnan(score):
            continue

        rows.append(
            ScreenRow(
                ticker=ticker,
                score=float(score),
                metrics={
                    "rvol": round(rvol_now, 2),
                    "momentum_z": round(mom_z, 3),
                    "breakout_z": round(brk_z, 3),
                    "avg_daily_value": round(avg_value, 0),
                    "last_close": float(df["close"].iloc[-1]),
                },
            )
        )

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(
        strategy=f"trending_{timeframe}",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "timeframe": timeframe,
            "min_rvol": min_rvol,
            "min_avg_value": min_avg_value,
            "weights": w.__dict__,
        },
    )
