"""Tests for market summary report."""
from saham_id.market_summary import MarketSummaryReport, generate_daily_summary


class TestMarketSummaryReport:
    def test_create(self):
        report = MarketSummaryReport(
            headline="Pasar Menguat",
            market_status="bullish",
            advancers=30, decliners=10, ad_ratio=3.0,
            top_gainers=["BBCA", "BBRI"],
        )
        assert report.headline == "Pasar Menguat"
        assert report.market_status == "bullish"

    def test_to_text(self):
        report = MarketSummaryReport(
            market_status="bullish", advancers=30, decliners=10,
            ad_ratio=3.0, regime="TRENDING_UP",
            regime_recommendation="Momentum strategies favored",
            top_gainers=["BBCA"], top_losers=["GOTO"],
            trending_stocks=["ADRO"], leading_sectors=["financials"],
            lagging_sectors=["technology"],
        )
        text = report.to_text()
        assert "BULLISH" in text
        assert "BBCA" in text
        assert "TRENDING_UP" in text

    def test_to_markdown(self):
        report = MarketSummaryReport(
            market_status="bearish", advancers=10, decliners=30,
            ad_ratio=0.33, top_gainers=["A"], top_losers=["B"],
            trending_stocks=["C"], regime="TRENDING_DOWN",
        )
        md = report.to_markdown()
        assert "##" in md
        assert "TRENDING_DOWN" in md


class TestGenerateSummary:
    def test_returns_report(self):
        report = generate_daily_summary("LQ45")
        assert isinstance(report, MarketSummaryReport)
        assert report.timestamp is not None
