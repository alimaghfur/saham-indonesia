"""Swing pullback screener — uptrend retracing to a moving average.

Setup:
    - Price in uptrend (close > MA_trend, e.g. MA50)
    - Current price has pulled back to or near MA_pullback (e.g. MA20)
    - RSI in neutral zone (not extremely oversold — that's a reversal setup)
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from saham_id.analysis.indicators import rsi as rsi_fn
from saham_id.analysis.indicators import sma
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


def screen(
    universe: str | Iterable[str] = "LQ45",
    trend_ma: int = 50,
    pullback_ma: int = 20,
    proximity_pct: float = 0.02,     # within 2% of pullback MA
    rsi_min: float = 40.0,
    rsi_max: float = 55.0,
    top_n: int = 15,
    source: DataSource | None = None,
) -> ScreenResult:
    """Screen for uptrend pullback candidates."""
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    rows: list[ScreenRow] = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period="6mo", interval="1d")
        except Exception:
            continue
        if df.empty or len(df) < trend_ma + 5:
            continue

        df = df.copy()
        df["ma_trend"] = sma(df["close"], trend_ma)
        df["ma_pull"] = sma(df["close"], pullback_ma)
        df["rsi"] = rsi_fn(df["close"], 14)
        last = df.iloc[-1]

        if any(
            v is None or pd_isna(v)
            for v in (last["ma_trend"], last["ma_pull"], last["rsi"])
        ):
            continue

        # Must be in uptrend
        if last["close"] <= last["ma_trend"]:
            continue
        # Proximity to pullback MA
        distance = abs(last["close"] - last["ma_pull"]) / last["ma_pull"]
        if distance > proximity_pct:
            continue
        # RSI neutral
        if not (rsi_min <= last["rsi"] <= rsi_max):
            continue

        # Score: closer to MA + healthier trend strength
        trend_strength = (last["close"] - last["ma_trend"]) / last["ma_trend"]
        score = (proximity_pct - distance) * 100 + trend_strength * 50
        rows.append(
            ScreenRow(
                ticker=ticker,
                score=score,
                metrics={
                    "close": float(last["close"]),
                    "ma_trend": round(float(last["ma_trend"]), 2),
                    "ma_pull": round(float(last["ma_pull"]), 2),
                    "rsi": round(float(last["rsi"]), 2),
                    "distance_to_pull_ma_pct": round(float(distance), 4),
                    "trend_strength_pct": round(float(trend_strength), 4),
                },
            )
        )

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(
        strategy="swing_pullback",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "trend_ma": trend_ma,
            "pullback_ma": pullback_ma,
            "proximity_pct": proximity_pct,
            "rsi_min": rsi_min,
            "rsi_max": rsi_max,
        },
    )


def pd_isna(x) -> bool:
    import pandas as pd
    return bool(pd.isna(x))
