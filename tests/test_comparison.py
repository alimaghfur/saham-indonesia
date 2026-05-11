"""Tests for stock comparison module."""
from saham_id.analysis.comparison import ComparisonResult, StockMetrics, compare_stocks


class TestStockMetrics:
    def test_create(self):
        m = StockMetrics(ticker="BBCA", period_return=0.15, volatility=0.20, sharpe=1.5)
        assert m.ticker == "BBCA"
        assert m.period_return == 0.15


class TestComparisonResult:
    def test_winner(self):
        metrics = {
            "BBCA": StockMetrics(ticker="BBCA", period_return=0.15),
            "BBRI": StockMetrics(ticker="BBRI", period_return=0.25),
            "TLKM": StockMetrics(ticker="TLKM", period_return=0.05),
        }
        result = ComparisonResult(tickers=["BBCA", "BBRI", "TLKM"], period="1y", metrics=metrics)
        assert result.winner == "BBRI"

    def test_lowest_risk(self):
        metrics = {
            "BBCA": StockMetrics(ticker="BBCA", volatility=0.15),
            "BBRI": StockMetrics(ticker="BBRI", volatility=0.25),
            "TLKM": StockMetrics(ticker="TLKM", volatility=0.10),
        }
        result = ComparisonResult(tickers=["BBCA", "BBRI", "TLKM"], period="1y", metrics=metrics)
        assert result.lowest_risk == "TLKM"

    def test_best_risk_adjusted(self):
        metrics = {
            "BBCA": StockMetrics(ticker="BBCA", sharpe=1.8),
            "BBRI": StockMetrics(ticker="BBRI", sharpe=1.2),
        }
        result = ComparisonResult(tickers=["BBCA", "BBRI"], period="1y", metrics=metrics)
        assert result.best_risk_adjusted == "BBCA"

    def test_ranking(self):
        metrics = {
            "A": StockMetrics(ticker="A", period_return=0.10),
            "B": StockMetrics(ticker="B", period_return=0.30),
            "C": StockMetrics(ticker="C", period_return=0.20),
        }
        result = ComparisonResult(tickers=["A", "B", "C"], period="1y", metrics=metrics)
        ranking = result.ranking(by="period_return")
        assert ranking[0][0] == "B"
        assert ranking[-1][0] == "A"

    def test_to_dataframe(self):
        metrics = {
            "BBCA": StockMetrics(ticker="BBCA", period_return=0.15, volatility=0.2, sharpe=1.5,
                                max_drawdown=-0.1, avg_volume=5000000, last_price=9800),
        }
        result = ComparisonResult(tickers=["BBCA"], period="1y", metrics=metrics)
        df = result.to_dataframe()
        assert len(df) == 1
        assert "ticker" in df.columns

    def test_empty(self):
        result = ComparisonResult(tickers=[], period="1y", metrics={})
        assert result.winner == ""
        assert result.lowest_risk == ""
