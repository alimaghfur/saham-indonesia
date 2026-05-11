"""Tests for data sources module."""
from saham_id.data.sources import get_source, list_sources
from saham_id.data.sources.base import DataSource, NotImplementedForSource, SourceError


class TestSourceRegistry:
    def test_list_sources(self):
        sources = list_sources()
        assert "yahoo" in sources
        assert "rti" in sources
        assert "itick" in sources
        assert "goapi" in sources
        assert "sectors" in sources

    def test_get_yahoo(self):
        src = get_source("yahoo")
        assert isinstance(src, DataSource)
        assert src.name == "yahoo"
        assert src.typical_delay_minutes == 15
        assert src.supports_realtime is False

    def test_get_yfinance_alias(self):
        src = get_source("yfinance")
        assert src.name == "yahoo"

    def test_get_rti(self):
        src = get_source("rti")
        assert src.name == "rti"
        assert src.supports_realtime is False

    def test_get_itick(self):
        src = get_source("itick")
        assert src.name == "itick"
        assert src.supports_realtime is True

    def test_get_goapi(self):
        src = get_source("goapi")
        assert src.name == "goapi"

    def test_get_sectors(self):
        src = get_source("sectors")
        assert src.name == "sectors"

    def test_get_default(self):
        src = get_source()
        assert src.name == "yahoo"  # Default chain starts with yahoo

    def test_get_invalid(self):
        try:
            get_source("nonexistent")
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "Unknown data source" in str(e)

    def test_pasardana_alias(self):
        src = get_source("pasardana")
        assert src.name == "rti"


class TestSkeletonSources:
    def test_rti_get_quote_raises(self):
        src = get_source("rti")
        try:
            src.get_quote("BBCA")
            assert False, "Should raise NotImplementedForSource"
        except NotImplementedForSource:
            pass

    def test_rti_get_ohlc_raises(self):
        src = get_source("rti")
        try:
            src.get_ohlc("BBCA")
            assert False, "Should raise NotImplementedForSource"
        except NotImplementedForSource:
            pass

    def test_itick_no_key_get_quote_raises(self):
        src = get_source("itick")
        try:
            src.get_quote("BBCA")
            assert False
        except (SourceError, NotImplementedForSource):
            pass

    def test_goapi_no_key_get_quote_raises(self):
        src = get_source("goapi")
        try:
            src.get_quote("BBCA")
            assert False
        except (SourceError, NotImplementedForSource):
            pass

    def test_sectors_no_key_get_quote_raises(self):
        src = get_source("sectors")
        try:
            src.get_quote("BBCA")
            assert False
        except (SourceError, NotImplementedForSource):
            pass


class TestDataSourceInterface:
    def test_repr(self):
        src = get_source("yahoo")
        r = repr(src)
        assert "yahoo" in r
        assert "15" in r

    def test_context_manager(self):
        src = get_source("yahoo")
        with src as s:
            assert s.name == "yahoo"
