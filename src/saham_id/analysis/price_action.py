"""Price action analysis — bar characteristics and compression detection."""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd


@dataclass
class BarAnalysis:
    consecutive_up: int = 0
    consecutive_down: int = 0
    avg_body_ratio: float = 0.0
    avg_range_pct: float = 0.0
    inside_bars: int = 0
    outside_bars: int = 0
    last_bar_type: str = ""
    trend_strength: float = 0.0


@dataclass
class CompressionResult:
    is_compressed: bool = False
    compression_bars: int = 0
    current_range_pct: float = 0.0
    avg_range_pct: float = 0.0
    compression_ratio: float = 0.0
    breakout_potential: str = "low"


def bar_analysis(df: pd.DataFrame, lookback: int = 10) -> BarAnalysis:
    if df.empty or len(df) < 3:
        return BarAnalysis()
    n = len(df)
    start = max(0, n - lookback)
    consecutive_up = consecutive_down = 0
    body_ratios, range_pcts = [], []
    inside_count = outside_count = 0

    for i in range(n - 1, start - 1, -1):
        c, o = df["close"].iloc[i], df["open"].iloc[i]
        if c is None or o is None:
            break
        if float(c) > float(o):
            if consecutive_down == 0: consecutive_up += 1
            else: break
        elif float(c) < float(o):
            if consecutive_up == 0: consecutive_down += 1
            else: break
        else: break

    for i in range(start, n):
        o, h, l, c = df["open"].iloc[i], df["high"].iloc[i], df["low"].iloc[i], df["close"].iloc[i]
        if any(v is None for v in (o, h, l, c)):
            continue
        o_f, h_f, l_f, c_f = float(o), float(h), float(l), float(c)
        bar_range = h_f - l_f
        if bar_range > 0:
            body_ratios.append(abs(c_f - o_f) / bar_range)
            if c_f > 0: range_pcts.append(bar_range / c_f)
        if i > start:
            ph, pl = df["high"].iloc[i-1], df["low"].iloc[i-1]
            if ph is not None and pl is not None:
                if h_f <= float(ph) and l_f >= float(pl): inside_count += 1
                elif h_f > float(ph) and l_f < float(pl): outside_count += 1

    last_o, last_c, last_h, last_l = df["open"].iloc[-1], df["close"].iloc[-1], df["high"].iloc[-1], df["low"].iloc[-1]
    last_type = ""
    if all(v is not None for v in (last_o, last_c, last_h, last_l)):
        body = abs(float(last_c) - float(last_o))
        rng = float(last_h) - float(last_l)
        if rng > 0 and body / rng < 0.1: last_type = "doji"
        elif float(last_c) > float(last_o): last_type = "bullish"
        else: last_type = "bearish"

    return BarAnalysis(
        consecutive_up=consecutive_up, consecutive_down=consecutive_down,
        avg_body_ratio=sum(body_ratios)/len(body_ratios) if body_ratios else 0,
        avg_range_pct=sum(range_pcts)/len(range_pcts) if range_pcts else 0,
        inside_bars=inside_count, outside_bars=outside_count,
        last_bar_type=last_type,
        trend_strength=max(-1.0, min(1.0, (consecutive_up - consecutive_down) / max(lookback, 1))),
    )


def compression_detection(df: pd.DataFrame, lookback: int = 20, threshold: float = 0.5) -> CompressionResult:
    if df.empty or len(df) < lookback:
        return CompressionResult()
    n = len(df)
    ranges = []
    for i in range(max(0, n - lookback), n):
        h, l, c = df["high"].iloc[i], df["low"].iloc[i], df["close"].iloc[i]
        if h is not None and l is not None and c is not None and float(c) > 0:
            ranges.append((float(h) - float(l)) / float(c))
    if len(ranges) < 5:
        return CompressionResult()
    avg_range = sum(ranges) / len(ranges)
    current_range = ranges[-1]
    if avg_range == 0:
        return CompressionResult()
    ratio = current_range / avg_range
    compression_bars = 0
    for i in range(len(ranges) - 1, 0, -1):
        if ranges[i] < avg_range * 0.75: compression_bars += 1
        else: break
    is_compressed = ratio < threshold and compression_bars >= 3
    potential = "high" if is_compressed and compression_bars >= 5 else ("moderate" if is_compressed else "low")
    return CompressionResult(is_compressed=is_compressed, compression_bars=compression_bars,
                            current_range_pct=current_range, avg_range_pct=avg_range,
                            compression_ratio=ratio, breakout_potential=potential)
