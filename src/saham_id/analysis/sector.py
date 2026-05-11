"""Sector rotation analysis — track sector performance over time.

Identifies which sectors are leading/lagging and detects rotation patterns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Literal, Optional

from saham_id.data.models import Sector
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe


# Map sector names to representative ETFs or stock groups
SECTOR_REPRESENTATIVES: dict[str, list[str]] = {
    "financials": ["BBCA", "BBRI", "BMRI", "BBNI", "BRIS"],
    "energy": ["ADRO", "ITMG", "PTBA", "MEDC", "PGAS"],
    "basic_materials": ["ANTM", "INCO", "INKP", "TKIM", "BRPT"],
    "consumer_cyclicals": ["ASII", "MAPI", "ERAA", "LPPF", "ACES"],
    "consumer_non_cyclicals": ["ICBP", "INDF", "UNVR", "KLBF", "SIDO"],
    "technology": ["GOTO", "BUKA", "EMTK"],
    "infrastructure": ["TLKM", "TOWR", "TBIG", "MTEL", "EXCL"],
    "property_real_estate": ["BSDE", "CTRA", "PWON", "SMRA"],
    "industrials": ["SMGR", "INTP", "WIKA", "CPIN"],
    "healthcare": ["KLBF", "SIDO", "MIKA"],
    "transportation_logistic": ["JSMR", "AVIA", "BIRD"],
}

Timeframe = Literal["1W", "1M", "3M", "6M", "1Y"]

_TIMEFRAME_TO_PERIOD = {
    "1W": "1mo",
    "1M": "3mo",
    "3M": "6mo",
    "6M": "1y",
    "1Y": "2y",
}

_TIMEFRAME_TO_BARS = {
    "1W": 5,
    "1M": 22,
    "3M": 66,
    "6M": 132,
    "1Y": 252,
}


@dataclass
class SectorPerformance:
    """Performance metrics for one sector."""

    sector: str
    return_pct: float
    avg_return_pct: float  # average of representative stocks
    num_advancing: int = 0
    num_declining: int = 0
    top_stock: str = ""
    top_stock_return: float = 0.0
    bottom_stock: str = ""
    bottom_stock_return: float = 0.0


@dataclass
class SectorRotationResult:
    """Result of sector rotation analysis."""

    timeframe: str
    as_of: datetime
    sectors: list[SectorPerformance]
    leading_sectors: list[str] = field(default_factory=list)
    lagging_sectors: list[str] = field(default_factory=list)

    def to_dataframe(self):
        """Convert to pandas DataFrame for display."""
        import pandas as pd
        rows = [
            {
                "sector": s.sector,
                "return_pct": round(s.return_pct * 100, 2),
                "avg_return_pct": round(s.avg_return_pct * 100, 2),
                "advancing": s.num_advancing,
                "declining": s.num_declining,
                "top_stock": f"{s.top_stock} ({s.top_stock_return*100:.1f}%)",
                "bottom_stock": f"{s.bottom_stock} ({s.bottom_stock_return*100:.1f}%)",
            }
            for s in self.sectors
        ]
        return pd.DataFrame(rows).sort_values("return_pct", ascending=False).reset_index(drop=True)


def sector_performance(
    timeframe: Timeframe = "1M",
    source: Optional[DataSource] = None,
) -> SectorRotationResult:
    """Analyze performance by sector over a given timeframe.

    Computes average return of representative stocks per sector,
    identifies leaders and laggards.
    """
    src = source or get_source()
    period = _TIMEFRAME_TO_PERIOD.get(timeframe, "3mo")
    bars = _TIMEFRAME_TO_BARS.get(timeframe, 22)

    sector_results: list[SectorPerformance] = []

    for sector_name, reps in SECTOR_REPRESENTATIVES.items():
        returns: list[tuple[str, float]] = []
        adv = dec = 0

        for ticker in reps:
            try:
                df = src.get_ohlc(ticker, period=period, interval="1d")
                if df.empty or len(df) < bars:
                    continue

                # Compute return over the timeframe
                close_now = float(df["close"].iloc[-1])
                close_prev = float(df["close"].iloc[-bars]) if len(df) >= bars else float(df["close"].iloc[0])

                if close_prev == 0:
                    continue

                ret = (close_now - close_prev) / close_prev
                returns.append((ticker, ret))

                if ret > 0:
                    adv += 1
                else:
                    dec += 1
            except Exception:
                continue

        if not returns:
            continue

        avg_ret = sum(r for _, r in returns) / len(returns)
        returns.sort(key=lambda x: x[1], reverse=True)

        sector_results.append(SectorPerformance(
            sector=sector_name,
            return_pct=avg_ret,
            avg_return_pct=avg_ret,
            num_advancing=adv,
            num_declining=dec,
            top_stock=returns[0][0] if returns else "",
            top_stock_return=returns[0][1] if returns else 0.0,
            bottom_stock=returns[-1][0] if returns else "",
            bottom_stock_return=returns[-1][1] if returns else 0.0,
        ))

    # Sort by performance
    sector_results.sort(key=lambda s: s.return_pct, reverse=True)

    # Identify leaders (top 3) and laggards (bottom 3)
    leaders = [s.sector for s in sector_results[:3]]
    laggards = [s.sector for s in sector_results[-3:]]

    return SectorRotationResult(
        timeframe=timeframe,
        as_of=datetime.utcnow(),
        sectors=sector_results,
        leading_sectors=leaders,
        lagging_sectors=laggards,
    )


def compare_timeframes(
    source: Optional[DataSource] = None,
) -> dict[str, SectorRotationResult]:
    """Compare sector performance across multiple timeframes.

    Returns dict keyed by timeframe (1W, 1M, 3M, 6M, 1Y).
    Useful for detecting rotation (e.g. sector strong short-term but weak long-term).
    """
    src = source or get_source()
    results: dict[str, SectorRotationResult] = {}

    for tf in ["1W", "1M", "3M"]:
        try:
            results[tf] = sector_performance(timeframe=tf, source=src)  # type: ignore
        except Exception:
            continue

    return results
