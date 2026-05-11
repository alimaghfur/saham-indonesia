"""Unusual volume / price anomaly detector.

Flags stocks whose volume or price movement today is statistically far
from their recent baseline (e.g. > 2.5 standard deviations).

Useful for spotting news-driven moves or bandar activity.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


def detect(
    universe: str | Iterable[str] = "LQ45",
    lookback: int = 60,
    volume_sigma: float = 2.5,
    price_sigma: float = 2.0,
    top_n: int = 30,
    source: DataSource | None = None,
) -> ScreenResult:
    """Detect unusual volume/price activity today."""
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    rows: list[ScreenRow] = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period="6mo", interval="1d")
        except Exception:
            continue
        if df.empty or len(df) < lookback + 1:
            continue

        df = df.copy().tail(lookback + 1)
        df["ret"] = df["close"].pct_change()

        vol_hist = df["volume"].iloc[:-1]
        ret_hist = df["ret"].iloc[:-1]

        vol_mean = float(vol_hist.mean())
        vol_std = float(vol_hist.std(ddof=0))
        ret_mean = float(ret_hist.mean())
        ret_std = float(ret_hist.std(ddof=0))

        if vol_std == 0 or ret_std == 0:
            continue

        vol_z = (float(df["volume"].iloc[-1]) - vol_mean) / vol_std
        ret_z = (float(df["ret"].iloc[-1]) - ret_mean) / ret_std

        if vol_z < volume_sigma and abs(ret_z) < price_sigma:
            continue

        # Score: combined absolute anomaly
        score = abs(vol_z) + abs(ret_z)
        rows.append(
            ScreenRow(
                ticker=ticker,
                score=score,
                metrics={
                    "volume_sigma": round(vol_z, 2),
                    "price_sigma": round(ret_z, 2),
                    "last_close": float(df["close"].iloc[-1]),
                    "last_return_pct": round(float(df["ret"].iloc[-1]), 4),
                    "last_volume": int(df["volume"].iloc[-1]),
                },
            )
        )

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(
        strategy="unusual_activity",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "lookback": lookback,
            "volume_sigma": volume_sigma,
            "price_sigma": price_sigma,
        },
    )
