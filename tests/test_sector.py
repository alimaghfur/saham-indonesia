"""Tests for sector analysis module."""
from saham_id.analysis.sector import (
    SECTOR_REPRESENTATIVES,
    SectorPerformance,
    SectorRotationResult,
)


class TestSectorRepresentatives:
    def test_all_sectors_defined(self):
        expected_sectors = [
            "financials", "energy", "basic_materials",
            "consumer_cyclicals", "consumer_non_cyclicals",
            "technology", "infrastructure", "property_real_estate",
            "industrials", "healthcare", "transportation_logistic",
        ]
        for sector in expected_sectors:
            assert sector in SECTOR_REPRESENTATIVES, f"Missing sector: {sector}"

    def test_each_sector_has_stocks(self):
        for sector, stocks in SECTOR_REPRESENTATIVES.items():
            assert len(stocks) >= 2, f"Sector {sector} needs at least 2 representative stocks"

    def test_bluechip_banks_in_financials(self):
        fin = SECTOR_REPRESENTATIVES["financials"]
        assert "BBCA" in fin
        assert "BBRI" in fin
        assert "BMRI" in fin


class TestSectorPerformance:
    def test_create(self):
        sp = SectorPerformance(
            sector="financials",
            return_pct=0.05,
            avg_return_pct=0.05,
            num_advancing=4,
            num_declining=1,
            top_stock="BBCA",
            top_stock_return=0.08,
            bottom_stock="BRIS",
            bottom_stock_return=-0.02,
        )
        assert sp.sector == "financials"
        assert sp.return_pct == 0.05
        assert sp.num_advancing == 4


class TestSectorRotationResult:
    def test_to_dataframe(self):
        sectors = [
            SectorPerformance(sector="financials", return_pct=0.05, avg_return_pct=0.05),
            SectorPerformance(sector="energy", return_pct=-0.02, avg_return_pct=-0.02),
        ]
        result = SectorRotationResult(
            timeframe="1M",
            as_of=None,
            sectors=sectors,
            leading_sectors=["financials"],
            lagging_sectors=["energy"],
        )
        df = result.to_dataframe()
        assert len(df) == 2
        assert "sector" in df.columns
