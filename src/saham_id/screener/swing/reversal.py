"""Swing reversal screener — oversold bounce setup.

Setup:
    - RSI crosses up from oversold zone (< 30)
    - Price near lower Bollinger Band
    - Bullish candle (close > open)
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from saham_id.analysis.indicators import bollinger_bands, rsi as rsi_fn
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


def screen(
    universe: str | Iterable[str] = "LQ45",
    rsi_oversold: float = 30.0,
    rsi_exit: float = 40.0,
    require_bullish_candle: bool = True,
    top_n: int = 15,
    source: DataSource | None = None,
) -> ScreenResult:
    """Screen for oversold bounce candidates."""
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    rows: list[ScreenRow] = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period="6mo", interval="1d")
        except Exception:
            continue
        if df.empty or len(df) < 30:
            continue

        df = df.copy()
        df["rsi"] = rsi_fn(df["close"], 14)
        bb = bollinger_bands(df["close"], 20, 2.0)
        df["bb_lower"] = bb["lower"]
        df["bb_percent_b"] = bb["percent_b"]

        last = df.iloc[-1]
        prev = df.iloc[-2]

        # Cross up from oversold
        crossed_up = prev["rsi"] < rsi_oversold and rsi_oversold <= last["rsi"] <= rsi_exit
        if not crossed_up:
            continue
        # Near lower BB
        if last["bb_percent_b"] is None or last["bb_percent_b"] > 0.25:
            continue
        if require_bullish_candle and last["close"] <= last["open"]:
            continue

        score = (rsi_exit - last["rsi"]) + (0.25 - float(last["bb_percent_b"])) * 100
        rows.append(
            ScreenRow(
                ticker=ticker,
                score=score,
                metrics={
                    "close": float(last["close"]),
                    "rsi": round(float(last["rsi"]), 2),
                    "percent_b": round(float(last["bb_percent_b"]), 3),
                    "prev_rsi": round(float(prev["rsi"]), 2),
                },
            )
        )

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(
        strategy="swing_reversal",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "rsi_oversold": rsi_oversold,
            "rsi_exit": rsi_exit,
            "require_bullish_candle": require_bullish_candle,
        },
    )
