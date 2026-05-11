"""Market breadth — advancers vs decliners, new highs / new lows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe


@dataclass
class BreadthSnapshot:
    universe: str
    advancers: int = 0
    decliners: int = 0
    unchanged: int = 0
    new_highs_52w: int = 0
    new_lows_52w: int = 0
    ad_ratio: float = 0.0        # advancers / decliners
    advancing_pct: float = 0.0   # advancers / total

    @property
    def total(self) -> int:
        return self.advancers + self.decliners + self.unchanged


def snapshot(
    universe: str | Iterable[str] = "LQ45",
    source: DataSource | None = None,
) -> BreadthSnapshot:
    """Snapshot today's market breadth across a universe."""
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    adv = dec = unch = 0
    nh = nl = 0

    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period="1y", interval="1d")
        except Exception:
            continue
        if df.empty or len(df) < 2:
            continue

        last = float(df["close"].iloc[-1])
        prev = float(df["close"].iloc[-2])
        if last > prev:
            adv += 1
        elif last < prev:
            dec += 1
        else:
            unch += 1

        hi52 = float(df["high"].tail(252).max())
        lo52 = float(df["low"].tail(252).min())
        if last >= hi52:
            nh += 1
        elif last <= lo52:
            nl += 1

    total = max(1, adv + dec + unch)
    return BreadthSnapshot(
        universe=universe_name,
        advancers=adv,
        decliners=dec,
        unchanged=unch,
        new_highs_52w=nh,
        new_lows_52w=nl,
        ad_ratio=adv / max(1, dec),
        advancing_pct=adv / total,
    )
