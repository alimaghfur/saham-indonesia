"""Tests for fundamental analysis."""
from datetime import date

from saham_id.analysis.fundamental import quality_score, value_score
from saham_id.data.models import FundamentalSnapshot


class TestValueScore:
    def test_value_score_range(self):
        snap = FundamentalSnapshot(
            ticker="BBCA",
            as_of=date(2024, 12, 31),
            per=15.0,
            pbv=2.0,
            dividend_yield=0.03,
        )
        vs = value_score(snap)
        assert 0 <= vs <= 100

    def test_value_score_cheap_stock(self):
        snap = FundamentalSnapshot(
            ticker="CHEAP",
            as_of=date(2024, 12, 31),
            per=5.0,
            pbv=0.5,
            dividend_yield=0.08,
        )
        vs = value_score(snap)
        assert vs > 60  # Should score high

    def test_value_score_expensive_stock(self):
        snap = FundamentalSnapshot(
            ticker="EXPENSIVE",
            as_of=date(2024, 12, 31),
            per=50.0,
            pbv=8.0,
            dividend_yield=0.005,
        )
        vs = value_score(snap)
        assert vs < 40  # Should score low

    def test_value_score_no_data(self):
        snap = FundamentalSnapshot(ticker="EMPTY", as_of=date(2024, 1, 1))
        vs = value_score(snap)
        assert vs == 50.0  # Default base score


class TestQualityScore:
    def test_quality_score_range(self):
        snap = FundamentalSnapshot(
            ticker="BBCA",
            as_of=date(2024, 12, 31),
            roe=0.20,
            net_margin=0.30,
            der=0.5,
        )
        qs = quality_score(snap)
        assert 0 <= qs <= 100

    def test_quality_score_high_quality(self):
        snap = FundamentalSnapshot(
            ticker="HQ",
            as_of=date(2024, 12, 31),
            roe=0.30,
            net_margin=0.40,
            der=0.3,
        )
        qs = quality_score(snap)
        assert qs > 60

    def test_quality_score_low_quality(self):
        snap = FundamentalSnapshot(
            ticker="LQ",
            as_of=date(2024, 12, 31),
            roe=0.02,
            net_margin=0.01,
            der=3.0,
        )
        qs = quality_score(snap)
        assert qs < 55

    def test_quality_score_no_data(self):
        snap = FundamentalSnapshot(ticker="EMPTY", as_of=date(2024, 1, 1))
        qs = quality_score(snap)
        assert qs == 50.0
