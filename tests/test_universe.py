"""Tests for stock universe module."""
from saham_id.data.universe import (
    IDX30,
    IDX80,
    KOMPAS100,
    LQ45,
    get_universe,
    list_universes,
    to_yahoo_symbols,
)


class TestGetUniverse:
    def test_idx30(self):
        u = get_universe("IDX30")
        assert len(u) == len(IDX30)
        assert "BBCA" in u

    def test_lq45(self):
        u = get_universe("LQ45")
        assert len(u) == len(LQ45)

    def test_case_insensitive(self):
        u1 = get_universe("idx30")
        u2 = get_universe("IDX30")
        assert u1 == u2

    def test_invalid_universe(self):
        try:
            get_universe("INVALID")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown universe" in str(e)


class TestListUniverses:
    def test_lists_all(self):
        names = list(list_universes())
        assert "IDX30" in names
        assert "LQ45" in names
        assert "IDX80" in names
        assert "KOMPAS100" in names


class TestToYahooSymbols:
    def test_basic_conversion(self):
        result = to_yahoo_symbols(["BBCA", "BBRI", "TLKM"])
        assert result == ["BBCA.JK", "BBRI.JK", "TLKM.JK"]

    def test_already_suffixed(self):
        result = to_yahoo_symbols(["BBCA.JK"])
        assert result == ["BBCA.JK"]

    def test_lowercase_input(self):
        result = to_yahoo_symbols(["bbca"])
        assert result == ["BBCA.JK"]

    def test_empty(self):
        result = to_yahoo_symbols([])
        assert result == []


class TestUniverseData:
    def test_idx30_subset_of_lq45(self):
        for ticker in IDX30:
            assert ticker in LQ45

    def test_lq45_subset_of_idx80(self):
        for ticker in LQ45:
            assert ticker in IDX80

    def test_idx80_subset_of_kompas100(self):
        for ticker in IDX80:
            assert ticker in KOMPAS100

    def test_no_duplicates_in_idx30(self):
        assert len(IDX30) == len(set(IDX30))
