"""Swing breakout screener — price tembus resistance N-day high."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from saham_id.analysis.indicators import rvol
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


def screen(
    universe: str | Iterable[str] = "LQ45",
    resistance_window: int = 20,
    min_consolidation_days: int = 10,
    volume_confirmation: bool = True,
    min_rvol: float = 1.5,
    top_n: int = 20,
    source: DataSource | None = None,
) -> ScreenResult:
    """Screen for stocks breaking out above their N-day high."""
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    rows: list[ScreenRow] = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period="6mo", interval="1d")
        except Exception:
            continue
        if df.empty or len(df) < resistance_window + min_consolidation_days:
            continue

        df = df.copy()
        resistance = df["high"].rolling(resistance_window).max().shift(1)
        last = df.iloc[-1]

        breakout_triggered = bool(last["close"] > resistance.iloc[-1])
        if not breakout_triggered:
            continue

        # Confirm consolidation: price within a tight band for N days prior
        recent = df.iloc[-min_consolidation_days - 1 : -1]
        range_pct = (recent["high"].max() - recent["low"].min()) / recent["close"].mean()
        if range_pct > 0.15:  # >15% range = not consolidating
            continue

        vol_score = 1.0
        if volume_confirmation:
            rv = rvol(df["volume"], window=20).iloc[-1]
            if rv is None or rv < min_rvol:
                continue
            vol_score = float(rv)

        breakout_pct = float((last["close"] - resistance.iloc[-1]) / resistance.iloc[-1])
        score = breakout_pct * 100 + vol_score * 10
        rows.append(
            ScreenRow(
                ticker=ticker,
                score=score,
                metrics={
                    "close": float(last["close"]),
                    "resistance_n": resistance_window,
                    "breakout_pct": round(breakout_pct, 4),
                    "rvol": round(vol_score, 2),
                    "consolidation_range_pct": round(float(range_pct), 4),
                },
            )
        )

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(
        strategy="swing_breakout",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "resistance_window": resistance_window,
            "min_consolidation_days": min_consolidation_days,
            "volume_confirmation": volume_confirmation,
            "min_rvol": min_rvol,
        },
    )
