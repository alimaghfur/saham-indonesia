"""Volume Profile — analyze volume distribution across price levels.

Shows where most trading activity occurred (Value Area), Point of Control,
and identifies high-volume nodes (support/resistance) vs low-volume nodes
(price likely to move quickly through).

Usage:
    from saham_id.analysis.volume_profile import volume_profile, VolumeProfile

    vp = volume_profile(df, bins=50)
    print(vp.poc)           # Point of Control (highest volume price)
    print(vp.value_area)    # (VAL, VAH) - 70% of volume between these
    print(vp.hvn)           # High Volume Nodes
    print(vp.lvn)           # Low Volume Nodes
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


@dataclass
class VolumeNode:
    """A price level with its volume."""
    price: float
    volume: float
    pct_of_total: float = 0.0


@dataclass
class VolumeProfile:
    """Volume profile analysis result."""

    ticker: str = ""
    period: str = ""
    bins: int = 50
    poc: float = 0.0  # Point of Control — price with most volume
    value_area_low: float = 0.0  # Value Area Low (70% volume starts here)
    value_area_high: float = 0.0  # Value Area High (70% volume ends here)
    profile: list[VolumeNode] = field(default_factory=list)
    total_volume: float = 0.0
    price_range: tuple[float, float] = (0.0, 0.0)

    @property
    def value_area(self) -> tuple[float, float]:
        """Value Area (VAL, VAH)."""
        return (self.value_area_low, self.value_area_high)

    @property
    def hvn(self) -> list[float]:
        """High Volume Nodes — prices with above-average volume.
        These act as support/resistance.
        """
        if not self.profile:
            return []
        avg_vol = self.total_volume / len(self.profile) if self.profile else 0
        return [n.price for n in self.profile if n.volume > avg_vol * 1.5]

    @property
    def lvn(self) -> list[float]:
        """Low Volume Nodes — prices with below-average volume.
        Price tends to move quickly through these levels.
        """
        if not self.profile:
            return []
        avg_vol = self.total_volume / len(self.profile) if self.profile else 0
        return [n.price for n in self.profile if n.volume < avg_vol * 0.5]

    def is_in_value_area(self, price: float) -> bool:
        """Check if a price is within the Value Area."""
        return self.value_area_low <= price <= self.value_area_high


def volume_profile(
    df: pd.DataFrame,
    bins: int = 50,
    value_area_pct: float = 0.70,
) -> VolumeProfile:
    """Compute volume profile from OHLCV data.

    Distributes volume across price bins based on where price traded.
    Uses the midpoint of each bar (H+L)/2 as the representative price.

    Parameters:
        df: OHLCV DataFrame with 'high', 'low', 'close', 'volume'
        bins: Number of price bins
        value_area_pct: Percentage of total volume for Value Area (default 70%)

    Returns:
        VolumeProfile with POC, Value Area, and per-level data
    """
    if df.empty or len(df) < 5:
        return VolumeProfile(bins=bins)

    # Get price range
    all_highs = [float(df["high"].iloc[i]) for i in range(len(df)) if df["high"].iloc[i] is not None]
    all_lows = [float(df["low"].iloc[i]) for i in range(len(df)) if df["low"].iloc[i] is not None]

    if not all_highs or not all_lows:
        return VolumeProfile(bins=bins)

    price_min = min(all_lows)
    price_max = max(all_highs)

    if price_max == price_min:
        return VolumeProfile(bins=bins, price_range=(price_min, price_max))

    # Create bins
    bin_width = (price_max - price_min) / bins
    bin_volumes: list[float] = [0.0] * bins
    bin_prices: list[float] = [price_min + (i + 0.5) * bin_width for i in range(bins)]

    # Distribute volume across bins
    # For each bar, distribute its volume proportionally across the bins it covers
    for i in range(len(df)):
        h = df["high"].iloc[i]
        l = df["low"].iloc[i]
        v = df["volume"].iloc[i]

        if h is None or l is None or v is None:
            continue

        bar_high = float(h)
        bar_low = float(l)
        bar_vol = float(v)

        if bar_vol <= 0 or bar_high <= bar_low:
            continue

        # Find which bins this bar spans
        low_bin = max(0, int((bar_low - price_min) / bin_width))
        high_bin = min(bins - 1, int((bar_high - price_min) / bin_width))

        # Distribute volume evenly across spanned bins
        span = high_bin - low_bin + 1
        vol_per_bin = bar_vol / span

        for b in range(low_bin, high_bin + 1):
            if 0 <= b < bins:
                bin_volumes[b] += vol_per_bin

    total_volume = sum(bin_volumes)
    if total_volume == 0:
        return VolumeProfile(bins=bins, price_range=(price_min, price_max))

    # Find POC (bin with highest volume)
    poc_idx = bin_volumes.index(max(bin_volumes))
    poc_price = bin_prices[poc_idx]

    # Compute Value Area (70% of volume around POC)
    # Start from POC and expand outward until 70% is captured
    va_volume = bin_volumes[poc_idx]
    va_low_idx = poc_idx
    va_high_idx = poc_idx

    target_volume = total_volume * value_area_pct

    while va_volume < target_volume and (va_low_idx > 0 or va_high_idx < bins - 1):
        # Look at next bar on each side, add the larger one
        expand_low = bin_volumes[va_low_idx - 1] if va_low_idx > 0 else 0
        expand_high = bin_volumes[va_high_idx + 1] if va_high_idx < bins - 1 else 0

        if expand_low >= expand_high and va_low_idx > 0:
            va_low_idx -= 1
            va_volume += expand_low
        elif va_high_idx < bins - 1:
            va_high_idx += 1
            va_volume += expand_high
        else:
            va_low_idx -= 1
            va_volume += expand_low

    # Build profile nodes
    profile_nodes: list[VolumeNode] = []
    for i in range(bins):
        if bin_volumes[i] > 0:
            profile_nodes.append(VolumeNode(
                price=round(bin_prices[i], 2),
                volume=bin_volumes[i],
                pct_of_total=bin_volumes[i] / total_volume * 100,
            ))

    return VolumeProfile(
        bins=bins,
        poc=round(poc_price, 2),
        value_area_low=round(bin_prices[va_low_idx], 2),
        value_area_high=round(bin_prices[va_high_idx], 2),
        profile=profile_nodes,
        total_volume=total_volume,
        price_range=(round(price_min, 2), round(price_max, 2)),
    )


def volume_profile_for_ticker(
    ticker: str,
    period: str = "6mo",
    bins: int = 50,
    source: Optional[object] = None,
) -> VolumeProfile:
    """Convenience function: fetch OHLC and compute volume profile."""
    from saham_id.data.sources import get_source

    src = source or get_source()
    df = src.get_ohlc(ticker, period=period, interval="1d")
    vp = volume_profile(df, bins=bins)
    vp.ticker = ticker
    vp.period = period
    return vp
