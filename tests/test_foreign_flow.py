"""Tests for foreign flow tracker."""
import pandas as pd
from datetime import date
from saham_id.analysis.foreign_flow import (
    ForeignFlowData, ForeignFlowSummary, ForeignActivity,
    estimate_foreign_flow, foreign_scan, foreign_trend,
    compute_foreign_dominance, classify_foreign_activity,
)


def _accumulation_data(n=30):
    close = [1000 + i * 5 for i in range(n)]
    return pd.DataFrame({
        "open": [c - 7 for c in close], "high": [c + 3 for c in close],
        "low": [c - 10 for c in close], "close": close,
        "volume": [5000000 + i * 200000 for i in range(n)],
    })


def _distribution_data(n=30):
    close = [2000 - i * 5 for i in range(n)]
    return pd.DataFrame({
        "open": [c + 7 for c in close], "high": [c + 10 for c in close],
        "low": [c - 3 for c in close], "close": close,
        "volume": [5000000 + i * 200000 for i in range(n)],
    })


class TestForeignFlowData:
    def test_create(self):
        flow = ForeignFlowData(ticker="BBCA", date=date(2025, 1, 6),
                              net_foreign=5_000_000_000, foreign_buy_value=15_000_000_000,
                              foreign_sell_value=10_000_000_000)
        assert flow.ticker == "BBCA"
        assert flow.is_net_buy is True

    def test_is_net_sell(self):
        flow = ForeignFlowData(ticker="X", date=date(2025, 1, 6),
                              net_foreign=-1_000_000_000,
                              foreign_buy_value=5_000_000_000, foreign_sell_value=6_000_000_000)
        assert flow.is_net_buy is False


class TestEstimateForeignFlow:
    def test_accumulation_positive_net(self):
        df = _accumulation_data(30)
        summary = estimate_foreign_flow(df, ticker="BBCA")
        assert summary.total_net_20d > 0
        assert summary.accumulation_days > summary.distribution_days

    def test_distribution_negative_net(self):
        df = _distribution_data(30)
        summary = estimate_foreign_flow(df, ticker="X")
        assert summary.total_net_20d < 0
        assert summary.distribution_days > summary.accumulation_days

    def test_empty(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        summary = estimate_foreign_flow(df, ticker="X")
        assert summary.total_net_20d == 0.0


class TestClassifyActivity:
    def test_heavy_buying(self):
        result = classify_foreign_activity(net_flow_20d=10_000_000_000,
                                          flow_consistency=0.8, avg_daily_net=500_000_000)
        assert result == ForeignActivity.HEAVY_BUYING

    def test_heavy_selling(self):
        result = classify_foreign_activity(net_flow_20d=-10_000_000_000,
                                          flow_consistency=0.8, avg_daily_net=-500_000_000)
        assert result == ForeignActivity.HEAVY_SELLING

    def test_neutral(self):
        result = classify_foreign_activity(net_flow_20d=100_000,
                                          flow_consistency=0.3, avg_daily_net=10_000)
        assert result == ForeignActivity.NEUTRAL


class TestComputeDominance:
    def test_high_dominance(self):
        dom = compute_foreign_dominance(foreign_value=50_000_000_000, total_value=100_000_000_000)
        assert dom == 0.5

    def test_zero_total(self):
        dom = compute_foreign_dominance(foreign_value=0, total_value=0)
        assert dom == 0.0


class TestForeignTrend:
    def test_basic(self):
        df = _accumulation_data(30)
        result = foreign_trend(df, ticker="BBCA", lookback=20)
        assert "trend" in result
        assert result["trend"] in ("increasing", "decreasing", "stable")

    def test_empty(self):
        df = pd.DataFrame({"open": [], "high": [], "low": [], "close": [], "volume": []})
        result = foreign_trend(df, ticker="X")
        assert result["trend"] == "stable"


class TestActivityEnum:
    def test_all_have_descriptions(self):
        from saham_id.analysis.foreign_flow import ACTIVITY_DESCRIPTIONS
        for activity in ForeignActivity:
            assert activity in ACTIVITY_DESCRIPTIONS
