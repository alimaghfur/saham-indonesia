"""Tests for data models."""
from datetime import date, datetime
from decimal import Decimal

from saham_id.data.models import (
    Bar,
    FundamentalSnapshot,
    MarketBoard,
    Mover,
    Quote,
    Sector,
    Stock,
)


class TestStock:
    def test_create_stock(self):
        s = Stock(ticker="BBCA", name="Bank Central Asia", sector="financials", board="main")
        assert s.ticker == "BBCA"
        assert s.name == "Bank Central Asia"
        assert s.sector == "financials"
        assert s.board == "main"

    def test_stock_defaults(self):
        s = Stock(ticker="TLKM")
        assert s.name == ""
        assert s.sector == "unknown"
        assert s.board == "unknown"
        assert s.listing_date is None
        assert s.shares_outstanding is None

    def test_stock_with_all_fields(self):
        s = Stock(
            ticker="BBRI",
            name="Bank Rakyat Indonesia",
            sector="financials",
            board="main",
            listing_date=date(2003, 11, 10),
            shares_outstanding=151_949_000_000,
        )
        assert s.listing_date == date(2003, 11, 10)
        assert s.shares_outstanding == 151_949_000_000


class TestQuote:
    def test_quote_change(self):
        q = Quote(
            ticker="BBCA",
            timestamp=datetime(2025, 1, 6, 10, 0),
            last=Decimal("9800"),
            prev_close=Decimal("9500"),
            volume=1_000_000,
            source="yahoo",
        )
        assert q.change == Decimal("300")
        assert abs(q.change_pct - 0.031578) < 0.001

    def test_quote_no_prev_close(self):
        q = Quote(ticker="BBRI", timestamp=datetime(2025, 1, 6), last=Decimal("5000"), source="test")
        assert q.change is None
        assert q.change_pct is None

    def test_quote_prev_close_zero(self):
        q = Quote(ticker="X", timestamp=datetime(2025, 1, 1), last=Decimal("100"), prev_close=Decimal("0"), source="t")
        assert q.change_pct is None

    def test_quote_delayed(self):
        q = Quote(ticker="BBCA", timestamp=datetime(2025, 1, 6), last=Decimal("9800"), delayed_minutes=15, source="yahoo")
        assert q.delayed_minutes == 15


class TestBar:
    def test_create_bar(self):
        b = Bar(
            ticker="BBCA",
            timestamp=datetime(2025, 1, 6),
            open=Decimal("9500"),
            high=Decimal("9900"),
            low=Decimal("9400"),
            close=Decimal("9800"),
            volume=5_000_000,
        )
        assert b.ticker == "BBCA"
        assert b.close == Decimal("9800")


class TestFundamentalSnapshot:
    def test_create_fundamental(self):
        f = FundamentalSnapshot(
            ticker="BBCA",
            as_of=date(2024, 12, 31),
            per=25.0,
            pbv=4.5,
            roe=0.21,
            der=0.5,
            dividend_yield=0.02,
        )
        assert f.per == 25.0
        assert f.roe == 0.21
        assert f.source == "unknown"


class TestMover:
    def test_create_mover(self):
        m = Mover(
            ticker="ANTM",
            last=Decimal("2350"),
            change=Decimal("100"),
            change_pct=0.0444,
            volume=50_000_000,
            rank=1,
        )
        assert m.ticker == "ANTM"
        assert m.rank == 1


class TestEnums:
    def test_market_boards(self):
        assert MarketBoard.MAIN == "main"
        assert MarketBoard.DEVELOPMENT == "development"

    def test_sectors(self):
        assert Sector.FINANCIALS == "financials"
        assert Sector.TECHNOLOGY == "technology"
        assert Sector.UNKNOWN == "unknown"
