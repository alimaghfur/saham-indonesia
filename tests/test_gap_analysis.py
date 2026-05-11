"""Tests for gap analysis."""
import pandas as pd
from saham_id.analysis.gap_analysis import detect_gaps, gap_fill_rate, Gap


def _make_gapped_data():
    return pd.DataFrame({
        "open": [100, 102, 104, 115, 114, 113, 112, 100, 101, 102],
        "high": [103, 105, 106, 118, 116, 115, 114, 103, 104, 105],
        "low": [99, 101, 102, 113, 112, 111, 110, 98, 99, 100],
        "close": [102, 104, 105, 116, 113, 112, 111, 101, 102, 104],
        "volume": [1000000] * 10,
    })


class TestDetectGaps:
    def test_gap_up(self):
        df = _make_gapped_data()
        gaps = detect_gaps(df, min_gap_pct=0.01)
        up_gaps = [g for g in gaps if g.direction == "up"]
        assert len(up_gaps) >= 1

    def test_gap_down(self):
        df = _make_gapped_data()
        gaps = detect_gaps(df, min_gap_pct=0.01)
        down_gaps = [g for g in gaps if g.direction == "down"]
        assert len(down_gaps) >= 1

    def test_no_gaps_smooth(self):
        df = pd.DataFrame({
            "open": [100 + i * 0.5 for i in range(20)],
            "high": [101 + i * 0.5 for i in range(20)],
            "low": [99 + i * 0.5 for i in range(20)],
            "close": [100.5 + i * 0.5 for i in range(20)],
            "volume": [1000000] * 20,
        })
        gaps = detect_gaps(df, min_gap_pct=0.02)
        assert len(gaps) == 0

    def test_significant(self):
        gap = Gap(bar_index=5, direction="up", gap_pct=0.03, gap_size=300, open_price=10300, prev_close=10000)
        assert gap.is_significant is True
        small = Gap(bar_index=5, direction="up", gap_pct=0.005, gap_size=50, open_price=10050, prev_close=10000)
        assert small.is_significant is False

    def test_empty(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        assert detect_gaps(df) == []


class TestGapFillRate:
    def test_basic(self):
        df = _make_gapped_data()
        stats = gap_fill_rate(df, min_gap_pct=0.01)
        assert "total_gaps" in stats
        assert "fill_rate" in stats

    def test_no_gaps(self):
        df = pd.DataFrame({"open": [100]*10, "high": [101]*10, "low": [99]*10, "close": [100.5]*10, "volume": [1000]*10})
        stats = gap_fill_rate(df, min_gap_pct=0.05)
        assert stats["total_gaps"] == 0
