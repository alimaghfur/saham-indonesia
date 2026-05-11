"""Tests for backtest report generator."""
import tempfile
from pathlib import Path
from datetime import datetime

import pandas as pd

from saham_id.backtest.engine import Backtester, Order
from saham_id.backtest.metrics import compute_metrics
from saham_id.backtest.report import generate_report


class TestGenerateReport:
    def _run_backtest(self):
        data = {
            "open": [100 + i for i in range(20)],
            "high": [103 + i for i in range(20)],
            "low": [98 + i for i in range(20)],
            "close": [102 + i for i in range(20)],
            "volume": [1000000] * 20,
        }
        index = [datetime(2025, 1, 6 + i, 0, 0) for i in range(20)]
        df = pd.DataFrame(data, index=index)

        def simple(bar, state):
            if state["position"] == 0:
                return [Order(side="buy", quantity=100)]
            return [Order(side="sell", quantity=state["position"])]

        bt = Backtester(strategy=simple, initial_capital=100_000_000)
        result = bt.run(df)
        metrics = compute_metrics(result)
        return result, metrics

    def test_creates_file(self):
        result, metrics = self._run_backtest()
        tmp = Path(tempfile.mkdtemp())
        path = generate_report(result, metrics, ticker="BBCA",
                              strategy_name="test", output_dir=tmp)
        assert path.exists()
        assert path.suffix == ".html"

    def test_html_content(self):
        result, metrics = self._run_backtest()
        tmp = Path(tempfile.mkdtemp())
        path = generate_report(result, metrics, ticker="BBCA",
                              strategy_name="BPJS", output_dir=tmp)
        content = path.read_text()
        assert "BBCA" in content
        assert "BPJS" in content
        assert "Total Return" in content
        assert "Trade Log" in content
