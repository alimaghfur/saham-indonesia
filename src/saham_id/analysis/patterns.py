"""Candlestick pattern recognition — detect classic chart patterns.

Detects single-bar and multi-bar candlestick patterns commonly used
in IDX trading:
    - Doji (indecision)
    - Hammer / Inverted Hammer (reversal)
    - Engulfing (bullish/bearish)
    - Morning Star / Evening Star (reversal)
    - Three White Soldiers / Three Black Crows (continuation)
    - Marubozu (strong conviction)
    - Harami (inside bar)

Usage:
    from saham_id.analysis.patterns import detect_patterns, PatternResult

    patterns = detect_patterns(df)  # returns list of PatternResult
    for p in patterns:
        print(f"{p.name} on bar {p.bar_index} — {p.bias} ({p.reliability})")
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal, Optional

import pandas as pd


class PatternBias(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class PatternReliability(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


@dataclass
class PatternResult:
    """A detected candlestick pattern."""

    name: str
    bias: PatternBias
    reliability: PatternReliability
    bar_index: int  # index of the triggering bar
    description: str = ""

    @property
    def is_bullish(self) -> bool:
        return self.bias == PatternBias.BULLISH

    @property
    def is_bearish(self) -> bool:
        return self.bias == PatternBias.BEARISH


def _body(open_val: float, close_val: float) -> float:
    """Absolute body size."""
    return abs(close_val - open_val)


def _upper_shadow(high: float, open_val: float, close_val: float) -> float:
    return high - max(open_val, close_val)


def _lower_shadow(low: float, open_val: float, close_val: float) -> float:
    return min(open_val, close_val) - low


def _range(high: float, low: float) -> float:
    return high - low


def _is_bullish_bar(open_val: float, close_val: float) -> bool:
    return close_val > open_val


def _is_bearish_bar(open_val: float, close_val: float) -> bool:
    return close_val < open_val


def detect_doji(o: float, h: float, l: float, c: float, threshold: float = 0.1) -> bool:
    """Doji: very small body relative to range."""
    rng = _range(h, l)
    if rng == 0:
        return False
    return _body(o, c) / rng < threshold


def detect_hammer(o: float, h: float, l: float, c: float) -> bool:
    """Hammer: small body at top, long lower shadow (2x+ body)."""
    body = _body(o, c)
    lower = _lower_shadow(l, o, c)
    upper = _upper_shadow(h, o, c)
    rng = _range(h, l)
    if rng == 0 or body == 0:
        return False
    return (lower >= 2 * body) and (upper <= body * 0.5) and (body / rng < 0.4)


def detect_inverted_hammer(o: float, h: float, l: float, c: float) -> bool:
    """Inverted Hammer: small body at bottom, long upper shadow."""
    body = _body(o, c)
    lower = _lower_shadow(l, o, c)
    upper = _upper_shadow(h, o, c)
    rng = _range(h, l)
    if rng == 0 or body == 0:
        return False
    return (upper >= 2 * body) and (lower <= body * 0.5) and (body / rng < 0.4)


def detect_marubozu(o: float, h: float, l: float, c: float, threshold: float = 0.05) -> Optional[str]:
    """Marubozu: full-body candle with minimal shadows. Returns 'bullish'/'bearish' or None."""
    rng = _range(h, l)
    if rng == 0:
        return None
    upper = _upper_shadow(h, o, c)
    lower = _lower_shadow(l, o, c)
    body = _body(o, c)
    if body / rng > 0.85 and upper / rng < threshold and lower / rng < threshold:
        return "bullish" if _is_bullish_bar(o, c) else "bearish"
    return None


def detect_engulfing(
    o1: float, h1: float, l1: float, c1: float,
    o2: float, h2: float, l2: float, c2: float,
) -> Optional[str]:
    """Engulfing pattern (2-bar). Returns 'bullish'/'bearish' or None."""
    body1 = _body(o1, c1)
    body2 = _body(o2, c2)

    # Bullish engulfing: bar1 bearish, bar2 bullish and engulfs bar1
    if _is_bearish_bar(o1, c1) and _is_bullish_bar(o2, c2):
        if o2 <= c1 and c2 >= o1:
            return "bullish"

    # Bearish engulfing: bar1 bullish, bar2 bearish and engulfs bar1
    if _is_bullish_bar(o1, c1) and _is_bearish_bar(o2, c2):
        if o2 >= c1 and c2 <= o1:
            return "bearish"

    return None


def detect_harami(
    o1: float, h1: float, l1: float, c1: float,
    o2: float, h2: float, l2: float, c2: float,
) -> Optional[str]:
    """Harami (inside bar). Returns 'bullish'/'bearish' or None."""
    # Bar2 body is inside bar1 body
    body1_high = max(o1, c1)
    body1_low = min(o1, c1)
    body2_high = max(o2, c2)
    body2_low = min(o2, c2)

    if body2_high <= body1_high and body2_low >= body1_low:
        # Bullish harami: bar1 bearish, bar2 bullish (smaller)
        if _is_bearish_bar(o1, c1) and _is_bullish_bar(o2, c2):
            return "bullish"
        # Bearish harami: bar1 bullish, bar2 bearish (smaller)
        if _is_bullish_bar(o1, c1) and _is_bearish_bar(o2, c2):
            return "bearish"

    return None


def detect_three_white_soldiers(
    bars: list[tuple[float, float, float, float]],
) -> bool:
    """Three White Soldiers: 3 consecutive bullish bars with higher closes."""
    if len(bars) < 3:
        return False
    for i in range(3):
        o, h, l, c = bars[i]
        if not _is_bullish_bar(o, c):
            return False
    # Each close higher than previous
    if bars[1][3] <= bars[0][3] or bars[2][3] <= bars[1][3]:
        return False
    # Each open within previous body
    for i in range(1, 3):
        prev_o, _, _, prev_c = bars[i - 1]
        curr_o = bars[i][0]
        if not (min(prev_o, prev_c) <= curr_o <= max(prev_o, prev_c)):
            return False
    return True


def detect_three_black_crows(
    bars: list[tuple[float, float, float, float]],
) -> bool:
    """Three Black Crows: 3 consecutive bearish bars with lower closes."""
    if len(bars) < 3:
        return False
    for i in range(3):
        o, h, l, c = bars[i]
        if not _is_bearish_bar(o, c):
            return False
    if bars[1][3] >= bars[0][3] or bars[2][3] >= bars[1][3]:
        return False
    return True


def detect_patterns(
    df: pd.DataFrame,
    lookback: int = 5,
) -> list[PatternResult]:
    """Scan the last N bars for candlestick patterns.

    Parameters:
        df: OHLCV DataFrame with 'open', 'high', 'low', 'close' columns
        lookback: How many recent bars to scan

    Returns:
        List of detected patterns, sorted by bar_index descending (newest first)
    """
    patterns: list[PatternResult] = []
    n = len(df)

    if n < 3:
        return patterns

    start = max(0, n - lookback)

    for i in range(start, n):
        o = float(df["open"].iloc[i])
        h = float(df["high"].iloc[i])
        l = float(df["low"].iloc[i])
        c = float(df["close"].iloc[i])

        if o is None or h is None or l is None or c is None:
            continue

        # Single-bar patterns
        if detect_doji(o, h, l, c):
            patterns.append(PatternResult(
                name="Doji", bias=PatternBias.NEUTRAL, reliability=PatternReliability.MODERATE,
                bar_index=i, description="Indecision — equal buying/selling pressure",
            ))

        if detect_hammer(o, h, l, c):
            patterns.append(PatternResult(
                name="Hammer", bias=PatternBias.BULLISH, reliability=PatternReliability.MODERATE,
                bar_index=i, description="Potential reversal — buyers stepping in at lows",
            ))

        if detect_inverted_hammer(o, h, l, c):
            patterns.append(PatternResult(
                name="Inverted Hammer", bias=PatternBias.BULLISH, reliability=PatternReliability.LOW,
                bar_index=i, description="Potential reversal — buying attempt from below",
            ))

        marubozu = detect_marubozu(o, h, l, c)
        if marubozu:
            bias = PatternBias.BULLISH if marubozu == "bullish" else PatternBias.BEARISH
            patterns.append(PatternResult(
                name=f"Marubozu ({marubozu})", bias=bias, reliability=PatternReliability.HIGH,
                bar_index=i, description="Strong conviction — dominated by one side",
            ))

        # Two-bar patterns
        if i >= 1:
            o1 = float(df["open"].iloc[i - 1])
            h1 = float(df["high"].iloc[i - 1])
            l1 = float(df["low"].iloc[i - 1])
            c1 = float(df["close"].iloc[i - 1])

            engulfing = detect_engulfing(o1, h1, l1, c1, o, h, l, c)
            if engulfing:
                bias = PatternBias.BULLISH if engulfing == "bullish" else PatternBias.BEARISH
                patterns.append(PatternResult(
                    name=f"Engulfing ({engulfing})", bias=bias, reliability=PatternReliability.HIGH,
                    bar_index=i, description="Strong reversal — new bar completely engulfs previous",
                ))

            harami = detect_harami(o1, h1, l1, c1, o, h, l, c)
            if harami:
                bias = PatternBias.BULLISH if harami == "bullish" else PatternBias.BEARISH
                patterns.append(PatternResult(
                    name=f"Harami ({harami})", bias=bias, reliability=PatternReliability.MODERATE,
                    bar_index=i, description="Inside bar — momentum slowing, potential reversal",
                ))

        # Three-bar patterns
        if i >= 2:
            bars_3 = [
                (float(df["open"].iloc[i - 2]), float(df["high"].iloc[i - 2]),
                 float(df["low"].iloc[i - 2]), float(df["close"].iloc[i - 2])),
                (float(df["open"].iloc[i - 1]), float(df["high"].iloc[i - 1]),
                 float(df["low"].iloc[i - 1]), float(df["close"].iloc[i - 1])),
                (o, h, l, c),
            ]

            if detect_three_white_soldiers(bars_3):
                patterns.append(PatternResult(
                    name="Three White Soldiers", bias=PatternBias.BULLISH,
                    reliability=PatternReliability.HIGH, bar_index=i,
                    description="Strong bullish continuation — 3 consecutive higher closes",
                ))

            if detect_three_black_crows(bars_3):
                patterns.append(PatternResult(
                    name="Three Black Crows", bias=PatternBias.BEARISH,
                    reliability=PatternReliability.HIGH, bar_index=i,
                    description="Strong bearish continuation — 3 consecutive lower closes",
                ))

    # Sort newest first
    patterns.sort(key=lambda p: p.bar_index, reverse=True)
    return patterns


def pattern_summary(df: pd.DataFrame, lookback: int = 10) -> dict[str, Any]:
    """Get a summary of recent patterns and overall bias.

    Returns:
        {
            "patterns": [...],
            "bullish_count": int,
            "bearish_count": int,
            "neutral_count": int,
            "overall_bias": "bullish"/"bearish"/"neutral",
        }
    """
    from typing import Any

    patterns = detect_patterns(df, lookback=lookback)

    bullish = sum(1 for p in patterns if p.is_bullish)
    bearish = sum(1 for p in patterns if p.is_bearish)
    neutral = sum(1 for p in patterns if p.bias == PatternBias.NEUTRAL)

    # Weight by reliability
    bull_score = sum(
        {"high": 3, "moderate": 2, "low": 1}[p.reliability.value]
        for p in patterns if p.is_bullish
    )
    bear_score = sum(
        {"high": 3, "moderate": 2, "low": 1}[p.reliability.value]
        for p in patterns if p.is_bearish
    )

    if bull_score > bear_score * 1.5:
        overall = "bullish"
    elif bear_score > bull_score * 1.5:
        overall = "bearish"
    else:
        overall = "neutral"

    return {
        "patterns": patterns,
        "bullish_count": bullish,
        "bearish_count": bearish,
        "neutral_count": neutral,
        "bull_score": bull_score,
        "bear_score": bear_score,
        "overall_bias": overall,
    }
