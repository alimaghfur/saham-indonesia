"""Tests for export utilities."""
import json
import os
from datetime import datetime
from pathlib import Path

from saham_id.export import to_csv, to_json, export_screen_result
from saham_id.screener.engine import ScreenResult, ScreenRow


class TestToCSV:
    def test_basic_export(self, tmp_path=None):
        import pandas as pd
        import tempfile

        tmp_dir = tmp_path or Path(tempfile.mkdtemp())
        filepath = tmp_dir / "test.csv"

        df = pd.DataFrame({
            "ticker": ["BBCA", "BBRI"],
            "score": [95.0, 85.0],
        })
        result = to_csv(df, filepath, index=False)
        assert result.exists()
        content = result.read_text()
        assert "BBCA" in content
        assert "BBRI" in content

    def test_creates_parent_dirs(self):
        import tempfile
        tmp = Path(tempfile.mkdtemp())
        filepath = tmp / "sub" / "dir" / "test.csv"

        import pandas as pd
        df = pd.DataFrame({"x": [1, 2, 3]})
        result = to_csv(df, filepath)
        assert result.exists()


class TestToJSON:
    def test_basic_export(self):
        import tempfile
        import pandas as pd

        tmp = Path(tempfile.mkdtemp())
        filepath = tmp / "test.json"

        df = pd.DataFrame({
            "ticker": ["BBCA", "BBRI"],
            "score": [95.0, 85.0],
        })
        result = to_json(df, filepath)
        assert result.exists()
        data = json.loads(result.read_text())
        assert isinstance(data, list)
        assert data[0]["ticker"] == "BBCA"


class TestExportScreenResult:
    def test_export_json(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        filepath = tmp / "screen.json"

        rows = [
            ScreenRow(ticker="BBCA", score=95.0, metrics={"rsi": 28}),
            ScreenRow(ticker="BBRI", score=85.0, metrics={"rsi": 32}),
        ]
        result = ScreenResult(
            strategy="test", universe="LQ45",
            as_of=datetime(2025, 1, 6), rows=rows,
            params={"lookback": 60},
        )

        path = export_screen_result(result, filepath, format="json")
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["strategy"] == "test"
        assert data["total_results"] == 2
        assert len(data["data"]) == 2

    def test_export_csv(self):
        import tempfile

        tmp = Path(tempfile.mkdtemp())
        filepath = tmp / "screen.csv"

        rows = [ScreenRow(ticker="BBCA", score=95.0)]
        result = ScreenResult(
            strategy="test", universe="LQ45",
            as_of=datetime(2025, 1, 6), rows=rows,
        )

        path = export_screen_result(result, filepath, format="csv")
        assert path.exists()
        assert "BBCA" in path.read_text()
