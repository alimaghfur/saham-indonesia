"""Market heatmap — generate performance data for visual display."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Optional
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe

_SECTOR_MAP = {
    "BBCA": "financials", "BBRI": "financials", "BMRI": "financials",
    "BBNI": "financials", "ADRO": "energy", "ITMG": "energy",
    "PTBA": "energy", "TLKM": "infrastructure", "ASII": "consumer",
    "GOTO": "technology", "UNVR": "consumer", "ICBP": "consumer",
}


@dataclass
class HeatmapCell:
    ticker: str
    change_pct: float
    volume: int = 0
    sector: str = ""
    last_price: float = 0.0


@dataclass
class HeatmapData:
    universe: str
    period: str
    cells: list[HeatmapCell] = field(default_factory=list)

    @property
    def gainers(self) -> list[HeatmapCell]:
        return sorted([c for c in self.cells if c.change_pct > 0], key=lambda c: c.change_pct, reverse=True)

    @property
    def losers(self) -> list[HeatmapCell]:
        return sorted([c for c in self.cells if c.change_pct < 0], key=lambda c: c.change_pct)

    @property
    def avg_change(self) -> float:
        return sum(c.change_pct for c in self.cells) / len(self.cells) if self.cells else 0.0

    def by_sector(self) -> dict[str, list[HeatmapCell]]:
        sectors: dict[str, list[HeatmapCell]] = {}
        for cell in self.cells:
            sectors.setdefault(cell.sector or "unknown", []).append(cell)
        return sectors

    def to_dataframe(self):
        import pandas as pd
        rows = [{"ticker": c.ticker, "change_pct": round(c.change_pct * 100, 2),
                 "volume": c.volume, "sector": c.sector, "last_price": c.last_price}
                for c in self.cells]
        return pd.DataFrame(rows)


def generate_heatmap(universe: str | Iterable[str] = "LQ45", period: str = "1D",
                     source: Optional[DataSource] = None) -> HeatmapData:
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    bars_map = {"1D": 2, "1W": 6, "1M": 22}
    period_map = {"1D": "5d", "1W": "1mo", "1M": "3mo"}
    bars = bars_map.get(period, 2)
    yf_period = period_map.get(period, "5d")
    cells = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period=yf_period, interval="1d")
            if df.empty or len(df) < bars:
                continue
            last = float(df["close"].iloc[-1])
            prev = float(df["close"].iloc[-bars]) if len(df) >= bars else float(df["close"].iloc[0])
            if prev == 0:
                continue
            cells.append(HeatmapCell(
                ticker=ticker, change_pct=(last - prev) / prev,
                volume=int(df["volume"].iloc[-1]) if df["volume"].iloc[-1] else 0,
                sector=_SECTOR_MAP.get(ticker, ""), last_price=last,
            ))
        except Exception:
            continue
    return HeatmapData(universe=universe if isinstance(universe, str) else "custom", period=period, cells=cells)
