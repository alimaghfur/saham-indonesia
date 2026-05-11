"""Tests for market heatmap."""
from saham_id.market.heatmap import HeatmapCell, HeatmapData, generate_heatmap, _SECTOR_MAP


class TestHeatmapCell:
    def test_create(self):
        cell = HeatmapCell(ticker="BBCA", change_pct=0.03, volume=5000000, sector="financials")
        assert cell.ticker == "BBCA"
        assert cell.change_pct == 0.03


class TestHeatmapData:
    def test_gainers_losers(self):
        cells = [
            HeatmapCell(ticker="A", change_pct=0.05),
            HeatmapCell(ticker="B", change_pct=-0.03),
            HeatmapCell(ticker="C", change_pct=0.02),
        ]
        data = HeatmapData(universe="TEST", period="1D", cells=cells)
        assert len(data.gainers) == 2
        assert len(data.losers) == 1
        assert data.gainers[0].ticker == "A"  # highest first

    def test_avg_change(self):
        cells = [HeatmapCell(ticker="A", change_pct=0.04), HeatmapCell(ticker="B", change_pct=-0.02)]
        data = HeatmapData(universe="TEST", period="1D", cells=cells)
        assert abs(data.avg_change - 0.01) < 0.001

    def test_by_sector(self):
        cells = [
            HeatmapCell(ticker="BBCA", change_pct=0.03, sector="financials"),
            HeatmapCell(ticker="BBRI", change_pct=0.01, sector="financials"),
            HeatmapCell(ticker="TLKM", change_pct=-0.01, sector="infrastructure"),
        ]
        data = HeatmapData(universe="TEST", period="1D", cells=cells)
        sectors = data.by_sector()
        assert len(sectors["financials"]) == 2
        assert len(sectors["infrastructure"]) == 1

    def test_empty(self):
        data = HeatmapData(universe="TEST", period="1D")
        assert data.avg_change == 0.0
        assert data.gainers == []


class TestSectorMap:
    def test_has_blue_chips(self):
        assert "BBCA" in _SECTOR_MAP
        assert "TLKM" in _SECTOR_MAP
        assert _SECTOR_MAP["BBCA"] == "financials"
