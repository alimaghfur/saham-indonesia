"""Tests for volume profile analysis."""
import pandas as pd

from saham_id.analysis.volume_profile import (
    VolumeProfile, VolumeNode, volume_profile,
)


def _make_ohlcv(n=100, base=1000, amplitude=50):
    """Create OHLCV data with price oscillating in a range."""
    import math
    close = [base + amplitude * math.sin(i * 0.1) for i in range(n)]
    return pd.DataFrame({
        "open": [c - 5 for c in close],
        "high": [c + 10 for c in close],
        "low": [c - 10 for c in close],
        "close": close,
        "volume": [1000000 + i * 10000 for i in range(n)],
    })


class TestVolumeNode:
    def test_create(self):
        node = VolumeNode(price=9500, volume=1000000, pct_of_total=5.2)
        assert node.price == 9500
        assert node.volume == 1000000


class TestVolumeProfile:
    def test_basic(self):
        df = _make_ohlcv(100)
        vp = volume_profile(df, bins=20)
        assert vp.poc > 0
        assert vp.value_area_low <= vp.poc <= vp.value_area_high
        assert vp.total_volume > 0
        assert len(vp.profile) > 0

    def test_poc_is_highest_volume(self):
        df = _make_ohlcv(100)
        vp = volume_profile(df, bins=30)
        if vp.profile:
            max_vol_node = max(vp.profile, key=lambda n: n.volume)
            assert abs(vp.poc - max_vol_node.price) < (vp.price_range[1] - vp.price_range[0]) / 10

    def test_value_area_contains_poc(self):
        df = _make_ohlcv(100)
        vp = volume_profile(df, bins=25)
        assert vp.is_in_value_area(vp.poc)

    def test_hvn_lvn(self):
        df = _make_ohlcv(100)
        vp = volume_profile(df, bins=20)
        # HVN and LVN should not overlap
        hvn_set = set(vp.hvn)
        lvn_set = set(vp.lvn)
        assert len(hvn_set & lvn_set) == 0

    def test_empty_df(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        vp = volume_profile(df)
        assert vp.poc == 0
        assert vp.total_volume == 0

    def test_value_area_percentage(self):
        df = _make_ohlcv(200)
        vp = volume_profile(df, bins=50, value_area_pct=0.70)
        # Volume within VA should be roughly 70% of total
        if vp.profile:
            va_vol = sum(
                n.volume for n in vp.profile
                if vp.value_area_low <= n.price <= vp.value_area_high
            )
            pct = va_vol / vp.total_volume if vp.total_volume > 0 else 0
            assert pct >= 0.60  # at least 60% (may be slightly more due to binning)

    def test_price_range(self):
        df = _make_ohlcv(50, base=5000, amplitude=200)
        vp = volume_profile(df, bins=30)
        assert vp.price_range[0] < vp.price_range[1]
        assert vp.price_range[0] > 0
