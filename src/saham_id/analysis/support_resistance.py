"""Support & Resistance detection — auto-detect key price levels.

Methods:
    1. Pivot Points (classic, Fibonacci, Camarilla)
    2. Swing High/Low clustering
    3. Fibonacci retracement from recent swing

Usage:
    from saham_id.analysis.support_resistance import (
        detect_levels, pivot_points, fibonacci_retracement, find_nearest_levels
    )

    levels = detect_levels(df)
    print(levels.support)   # [9000, 8750, 8500]
    print(levels.resistance)  # [9800, 10000, 10500]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class PriceLevel:
    """A single support or resistance level."""
    price: float
    strength: int = 1
    level_type: str = ""
    method: str = ""


@dataclass
class SRLevels:
    """Support and Resistance levels for a stock."""
    ticker: str = ""
    support: list[float] = field(default_factory=list)
    resistance: list[float] = field(default_factory=list)
    current_price: float = 0.0
    details: list[PriceLevel] = field(default_factory=list)

    @property
    def nearest_support(self) -> Optional[float]:
        below = [s for s in self.support if s < self.current_price]
        return max(below) if below else None

    @property
    def nearest_resistance(self) -> Optional[float]:
        above = [r for r in self.resistance if r > self.current_price]
        return min(above) if above else None


@dataclass
class FibonacciLevels:
    """Fibonacci retracement levels."""
    swing_high: float
    swing_low: float
    direction: str
    levels: dict[float, float] = field(default_factory=dict)


def pivot_points(high: float, low: float, close: float, method: str = "classic") -> dict[str, float]:
    """Calculate pivot points from previous session's H/L/C."""
    if method == "classic":
        p = (high + low + close) / 3
        s1 = 2 * p - high
        s2 = p - (high - low)
        s3 = low - 2 * (high - p)
        r1 = 2 * p - low
        r2 = p + (high - low)
        r3 = high + 2 * (p - low)
    elif method == "fibonacci":
        p = (high + low + close) / 3
        diff = high - low
        s1 = p - 0.382 * diff
        s2 = p - 0.618 * diff
        s3 = p - 1.000 * diff
        r1 = p + 0.382 * diff
        r2 = p + 0.618 * diff
        r3 = p + 1.000 * diff
    elif method == "camarilla":
        p = (high + low + close) / 3
        diff = high - low
        s1 = close - diff * 1.1 / 12
        s2 = close - diff * 1.1 / 6
        s3 = close - diff * 1.1 / 4
        r1 = close + diff * 1.1 / 12
        r2 = close + diff * 1.1 / 6
        r3 = close + diff * 1.1 / 4
    else:
        raise ValueError(f"Unknown method: {method}")
    return {"P": p, "S1": s1, "S2": s2, "S3": s3, "R1": r1, "R2": r2, "R3": r3}


def fibonacci_retracement(df: pd.DataFrame, lookback: int = 60) -> FibonacciLevels:
    """Calculate Fibonacci retracement from recent swing."""
    if len(df) < lookback:
        lookback = len(df)
    recent = df.tail(lookback)
    highs = recent["high"]
    lows = recent["low"]
    swing_high = float(highs.max())
    swing_low = float(lows.min())
    if swing_high == swing_low:
        return FibonacciLevels(swing_high=swing_high, swing_low=swing_low, direction="up", levels={})
    high_idx = highs._data.index(swing_high) if swing_high in highs._data else 0
    low_idx = lows._data.index(swing_low) if swing_low in lows._data else 0
    diff = swing_high - swing_low
    fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
    if high_idx > low_idx:
        direction = "up"
        levels = {r: swing_high - diff * r for r in fib_ratios}
    else:
        direction = "down"
        levels = {r: swing_low + diff * r for r in fib_ratios}
    return FibonacciLevels(swing_high=swing_high, swing_low=swing_low, direction=direction, levels=levels)


def _find_swing_points(df: pd.DataFrame, window: int = 5) -> tuple[list[float], list[float]]:
    """Find swing highs and lows."""
    swing_highs: list[float] = []
    swing_lows: list[float] = []
    highs = df["high"]
    lows = df["low"]
    n = len(df)
    for i in range(window, n - window):
        h = float(highs.iloc[i])
        is_swing_high = all(
            h > float(highs.iloc[i - j]) and h > float(highs.iloc[i + j])
            for j in range(1, window + 1)
            if highs.iloc[i - j] is not None and highs.iloc[i + j] is not None
        )
        if is_swing_high:
            swing_highs.append(h)
        l_val = float(lows.iloc[i])
        is_swing_low = all(
            l_val < float(lows.iloc[i - j]) and l_val < float(lows.iloc[i + j])
            for j in range(1, window + 1)
            if lows.iloc[i - j] is not None and lows.iloc[i + j] is not None
        )
        if is_swing_low:
            swing_lows.append(l_val)
    return swing_highs, swing_lows


def _cluster_levels(prices: list[float], tolerance_pct: float = 0.02) -> list[tuple[float, int]]:
    """Cluster nearby levels."""
    if not prices:
        return []
    sorted_prices = sorted(prices)
    clusters: list[tuple[float, int]] = []
    used = [False] * len(sorted_prices)
    for i, price in enumerate(sorted_prices):
        if used[i]:
            continue
        cluster = [price]
        used[i] = True
        for j in range(i + 1, len(sorted_prices)):
            if used[j]:
                continue
            if abs(sorted_prices[j] - price) / max(price, 1) < tolerance_pct:
                cluster.append(sorted_prices[j])
                used[j] = True
        clusters.append((round(sum(cluster) / len(cluster), 0), len(cluster)))
    clusters.sort(key=lambda x: x[1], reverse=True)
    return clusters


def detect_levels(df: pd.DataFrame, swing_window: int = 5, cluster_tolerance: float = 0.02, max_levels: int = 5) -> SRLevels:
    """Auto-detect support and resistance levels."""
    if df.empty or len(df) < swing_window * 2 + 1:
        return SRLevels()
    current_price = float(df["close"].iloc[-1]) if df["close"].iloc[-1] is not None else 0.0
    swing_highs, swing_lows = _find_swing_points(df, window=swing_window)
    resistance_clusters = _cluster_levels(swing_highs, cluster_tolerance)
    support_clusters = _cluster_levels(swing_lows, cluster_tolerance)
    resistance = sorted([p for p, _ in resistance_clusters if p > current_price])[:max_levels]
    support = sorted([p for p, _ in support_clusters if p < current_price], reverse=True)[:max_levels]
    details = []
    for price, strength in resistance_clusters:
        if price > current_price:
            details.append(PriceLevel(price=price, strength=strength, level_type="resistance", method="swing_cluster"))
    for price, strength in support_clusters:
        if price < current_price:
            details.append(PriceLevel(price=price, strength=strength, level_type="support", method="swing_cluster"))
    return SRLevels(support=support, resistance=resistance, current_price=current_price, details=sorted(details, key=lambda d: d.strength, reverse=True))


def find_nearest_levels(df: pd.DataFrame, n: int = 3) -> dict[str, list[float]]:
    """Find N nearest support and resistance levels."""
    levels = detect_levels(df, max_levels=n)
    return {"support": levels.support[:n], "resistance": levels.resistance[:n], "current": levels.current_price}
