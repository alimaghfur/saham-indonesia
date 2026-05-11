"""Tests for screener engine."""
from datetime import datetime

from saham_id.screener.engine import ScreenResult, ScreenRow


class TestScreenRow:
    def test_create(self):
        row = ScreenRow(ticker="BBCA", score=95.0, metrics={"rsi": 28.0})
        assert row.ticker == "BBCA"
        assert row.score == 95.0
        assert row.metrics["rsi"] == 28.0

    def test_default_metrics(self):
        row = ScreenRow(ticker="BBRI", score=50.0)
        assert row.metrics == {}


class TestScreenResult:
    def test_create(self):
        rows = [
            ScreenRow(ticker="BBCA", score=95.0),
            ScreenRow(ticker="BBRI", score=85.0),
            ScreenRow(ticker="TLKM", score=70.0),
        ]
        result = ScreenResult(
            strategy="test", universe="LQ45",
            as_of=datetime(2025, 1, 6), rows=rows,
        )
        assert len(result) == 3
        assert result.strategy == "test"

    def test_to_dataframe(self):
        rows = [
            ScreenRow(ticker="A", score=50.0, metrics={"vol": 100}),
            ScreenRow(ticker="B", score=80.0, metrics={"vol": 200}),
        ]
        result = ScreenResult(strategy="x", universe="LQ45", as_of=datetime(2025, 1, 6), rows=rows)
        df = result.to_dataframe()
        assert len(df) == 2
        assert "ticker" in df.columns
        assert "score" in df.columns

    def test_to_dataframe_empty(self):
        result = ScreenResult(strategy="x", universe="LQ45", as_of=datetime(2025, 1, 6), rows=[])
        df = result.to_dataframe()
        assert len(df) == 0

    def test_top(self):
        rows = [ScreenRow(ticker=f"T{i}", score=float(i)) for i in range(20)]
        result = ScreenResult(strategy="x", universe="LQ45", as_of=datetime(2025, 1, 6), rows=rows)
        top5 = result.top(5)
        assert len(top5) == 5
