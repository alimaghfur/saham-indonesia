"""Scalping screener — high-frequency momentum scanner.

Requires tick or 1-minute bar data — NOT available from yfinance in bulk.
Recommended sources: iTick (free tier, realtime WS) or premium providers.

This module is a SKELETON; core loop is sketched so you can fill in once
your realtime source is implemented.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource, NotImplementedForSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


def screen(
    universe: str | Iterable[str] = "LQ45",
    min_avg_volume: int = 10_000_000,
    min_transaction_value: float = 50_000_000_000,
    min_atr_pct: float = 0.015,
    min_rvol: float = 2.0,
    top_n: int = 10,
    source: DataSource | None = None,
) -> ScreenResult:
    """Screen for scalping candidates using intraday (1m/5m) data.

    TODO(impl):
        1. Pull 1m bars (last 1–2 trading days) per ticker
        2. Compute: RVOL (rolling 20-period), ATR%, bid-ask spread if available
        3. Filter by liquidity, volatility, and recent momentum
        4. Rank by a composite scalping score
    """
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    rows: list[ScreenRow] = []
    for ticker in tickers:
        try:
            # 1m data — yfinance only supports last 7 days; realtime sources preferred
            df = src.get_ohlc(ticker, period="5d", interval="1m")
        except NotImplementedForSource:
            # Source does not support intraday — bail out entirely
            raise
        except Exception:
            continue
        if df.empty:
            continue

        # TODO: real scalping logic. For now, trivial placeholder so
        # the pipeline is exercisable end-to-end without crashing.
        rows.append(
            ScreenRow(
                ticker=ticker,
                score=0.0,
                metrics={"note": "scalping screener is a skeleton"},
            )
        )

    return ScreenResult(
        strategy="scalping",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "min_avg_volume": min_avg_volume,
            "min_transaction_value": min_transaction_value,
            "min_atr_pct": min_atr_pct,
            "min_rvol": min_rvol,
        },
    )
