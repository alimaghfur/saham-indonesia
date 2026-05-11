"""Intraday session stats — performance by time of day.

Analyzes morning vs afternoon return patterns from daily OHLC.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


@dataclass
class SessionStats:
    """Intraday session performance statistics."""

    ticker: str
    period: str
    sample_days: int = 0
    morning_avg_return: float = 0.0
    morning_win_rate: float = 0.0
    afternoon_avg_return: float = 0.0
    afternoon_win_rate: float = 0.0
    avg_gap: float = 0.0
    gap_up_rate: float = 0.0
    last_hour_avg_return: float = 0.0
    last_hour_win_rate: float = 0.0
    full_day_avg_return: float = 0.0
    full_day_win_rate: float = 0.0

    @property
    def best_session(self) -> str:
        if self.morning_avg_return > self.afternoon_avg_return:
            return "morning"
        elif self.afternoon_avg_return > self.morning_avg_return:
            return "afternoon"
        return "neutral"


def session_stats(
    ticker: str,
    period: str = "3mo",
    source: Optional[DataSource] = None,
) -> SessionStats:
    """Compute session stats from daily OHLC (approximation)."""
    src = source or get_source()

    try:
        df = src.get_ohlc(ticker, period=period, interval="1d")
    except Exception:
        return SessionStats(ticker=ticker, period=period)

    if df.empty or len(df) < 10:
        return SessionStats(ticker=ticker, period=period)

    morning_returns = []
    afternoon_returns = []
    gaps = []
    full_day_returns = []

    for i in range(1, len(df)):
        o = df["open"].iloc[i]
        h = df["high"].iloc[i]
        l = df["low"].iloc[i]
        c = df["close"].iloc[i]
        prev_c = df["close"].iloc[i - 1]

        if any(v is None for v in (o, h, l, c, prev_c)):
            continue
        o_f, h_f, l_f, c_f, pc_f = float(o), float(h), float(l), float(c), float(prev_c)
        if o_f == 0 or pc_f == 0:
            continue

        gaps.append((o_f - pc_f) / pc_f)
        full_day_returns.append((c_f - o_f) / o_f)
        midpoint = (h_f + l_f) / 2
        morning_returns.append((midpoint - o_f) / o_f)
        afternoon_returns.append((c_f - midpoint) / midpoint if midpoint > 0 else 0)

    n = len(full_day_returns)
    if n == 0:
        return SessionStats(ticker=ticker, period=period)

    return SessionStats(
        ticker=ticker, period=period, sample_days=n,
        morning_avg_return=sum(morning_returns) / n,
        morning_win_rate=sum(1 for r in morning_returns if r > 0) / n,
        afternoon_avg_return=sum(afternoon_returns) / n,
        afternoon_win_rate=sum(1 for r in afternoon_returns if r > 0) / n,
        avg_gap=sum(gaps) / len(gaps) if gaps else 0,
        gap_up_rate=sum(1 for g in gaps if g > 0) / len(gaps) if gaps else 0,
        last_hour_avg_return=sum(afternoon_returns[-20:]) / min(20, len(afternoon_returns)) if afternoon_returns else 0,
        last_hour_win_rate=sum(1 for r in afternoon_returns[-20:] if r > 0) / min(20, len(afternoon_returns)) if afternoon_returns else 0,
        full_day_avg_return=sum(full_day_returns) / n,
        full_day_win_rate=sum(1 for r in full_day_returns if r > 0) / n,
    )
