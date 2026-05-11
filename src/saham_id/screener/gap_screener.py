"""Gap screener — find stocks that gapped today."""
from __future__ import annotations
from datetime import datetime
from typing import Iterable, Optional
from saham_id.analysis.gap_analysis import detect_gaps
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


def screen_gaps(universe: str | Iterable[str] = "LQ45", min_gap_pct: float = 0.02,
                direction: Optional[str] = None, top_n: int = 20,
                source: Optional[DataSource] = None) -> ScreenResult:
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"
    rows: list[ScreenRow] = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period="5d", interval="1d")
            if df.empty or len(df) < 2:
                continue
            gaps = detect_gaps(df, min_gap_pct=min_gap_pct)
            if not gaps:
                continue
            latest = gaps[0]
            if latest.bar_index != len(df) - 1:
                continue
            if direction and latest.direction != direction:
                continue
            score = abs(latest.gap_pct) * 100 + latest.volume_ratio * 5
            rows.append(ScreenRow(ticker=ticker, score=round(score, 2), metrics={
                "direction": latest.direction, "gap_pct": round(latest.gap_pct*100, 2),
                "gap_type": latest.gap_type, "volume_ratio": round(latest.volume_ratio, 2),
            }))
        except Exception:
            continue
    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(strategy="gap_screener", universe=universe_name, as_of=datetime.utcnow(),
                       rows=rows[:top_n], params={"min_gap_pct": min_gap_pct, "direction": direction})
