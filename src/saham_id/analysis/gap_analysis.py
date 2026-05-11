"""Gap analysis — detect and classify price gaps."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
import pandas as pd

GapDirection = Literal["up", "down"]

@dataclass
class Gap:
    bar_index: int
    direction: GapDirection
    gap_pct: float
    gap_size: float
    open_price: float
    prev_close: float
    gap_type: str = "common"
    is_filled: bool = False
    fill_bars: int = 0
    volume_ratio: float = 0.0

    @property
    def is_significant(self) -> bool:
        return abs(self.gap_pct) > 0.02


def detect_gaps(df: pd.DataFrame, min_gap_pct: float = 0.005, lookback_for_fill: int = 20) -> list[Gap]:
    gaps: list[Gap] = []
    n = len(df)
    if n < 2:
        return gaps
    volumes = [float(df["volume"].iloc[i]) for i in range(n) if df["volume"].iloc[i] is not None]
    avg_volume = sum(volumes) / len(volumes) if volumes else 1.0

    for i in range(1, n):
        open_i, high_prev, low_prev, close_prev = df["open"].iloc[i], df["high"].iloc[i-1], df["low"].iloc[i-1], df["close"].iloc[i-1]
        volume_i = df["volume"].iloc[i]
        if any(v is None for v in (open_i, high_prev, low_prev, close_prev)):
            continue
        o, hp, lp, cp = float(open_i), float(high_prev), float(low_prev), float(close_prev)
        vol = float(volume_i) if volume_i is not None else 0
        if cp == 0:
            continue
        vol_ratio = vol / avg_volume if avg_volume > 0 else 1.0

        if o > hp:
            gap_pct = (o - cp) / cp
            if gap_pct >= min_gap_pct:
                is_filled, fill_bars = _check_fill(df, i, cp, "up", lookback_for_fill)
                gaps.append(Gap(bar_index=i, direction="up", gap_pct=gap_pct, gap_size=o-cp,
                               open_price=o, prev_close=cp, gap_type=_classify(gap_pct, vol_ratio),
                               is_filled=is_filled, fill_bars=fill_bars, volume_ratio=vol_ratio))
        elif o < lp:
            gap_pct = (o - cp) / cp
            if abs(gap_pct) >= min_gap_pct:
                is_filled, fill_bars = _check_fill(df, i, cp, "down", lookback_for_fill)
                gaps.append(Gap(bar_index=i, direction="down", gap_pct=gap_pct, gap_size=o-cp,
                               open_price=o, prev_close=cp, gap_type=_classify(gap_pct, vol_ratio),
                               is_filled=is_filled, fill_bars=fill_bars, volume_ratio=vol_ratio))
    gaps.sort(key=lambda g: g.bar_index, reverse=True)
    return gaps


def gap_fill_rate(df: pd.DataFrame, min_gap_pct: float = 0.01) -> dict:
    gaps = detect_gaps(df, min_gap_pct=min_gap_pct)
    if not gaps:
        return {"total_gaps": 0, "gaps_filled": 0, "fill_rate": 0.0, "avg_fill_bars": 0.0,
                "gap_up_fill_rate": 0.0, "gap_down_fill_rate": 0.0}
    filled = [g for g in gaps if g.is_filled]
    up_gaps = [g for g in gaps if g.direction == "up"]
    down_gaps = [g for g in gaps if g.direction == "down"]
    return {
        "total_gaps": len(gaps), "gaps_filled": len(filled),
        "fill_rate": len(filled) / len(gaps),
        "avg_fill_bars": sum(g.fill_bars for g in filled) / len(filled) if filled else 0.0,
        "gap_up_fill_rate": sum(1 for g in up_gaps if g.is_filled) / len(up_gaps) if up_gaps else 0.0,
        "gap_down_fill_rate": sum(1 for g in down_gaps if g.is_filled) / len(down_gaps) if down_gaps else 0.0,
    }


def _classify(gap_pct: float, vol_ratio: float) -> str:
    if abs(gap_pct) > 0.03 and vol_ratio > 2.0:
        return "breakaway"
    if abs(gap_pct) > 0.015 and vol_ratio > 1.2:
        return "runaway"
    return "common"


def _check_fill(df, gap_idx: int, prev_close: float, direction: str, max_bars: int) -> tuple[bool, int]:
    n = len(df)
    for j in range(1, min(max_bars + 1, n - gap_idx)):
        idx = gap_idx + j
        if direction == "up":
            low_j = df["low"].iloc[idx]
            if low_j is not None and float(low_j) <= prev_close:
                return True, j
        else:
            high_j = df["high"].iloc[idx]
            if high_j is not None and float(high_j) >= prev_close:
                return True, j
    return False, 0
