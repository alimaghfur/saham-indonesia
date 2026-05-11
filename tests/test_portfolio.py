"""Tests for portfolio tracker."""
from datetime import datetime
from decimal import Decimal

from saham_id.portfolio.tracker import Portfolio, Position, Transaction


class TestPosition:
    def test_buy(self):
        pos = Position(ticker="BBCA")
        tx = Transaction(
            ticker="BBCA", side="buy", quantity=100,
            price=Decimal("9500"), timestamp=datetime(2025, 1, 6, 9, 30),
        )
        pos.apply(tx)
        assert pos.quantity == 100
        assert pos.avg_cost == Decimal("9500")

    def test_buy_twice_avg_cost(self):
        pos = Position(ticker="BBCA")
        tx1 = Transaction(ticker="BBCA", side="buy", quantity=100, price=Decimal("9500"), timestamp=datetime(2025, 1, 6))
        tx2 = Transaction(ticker="BBCA", side="buy", quantity=100, price=Decimal("10500"), timestamp=datetime(2025, 1, 7))
        pos.apply(tx1)
        pos.apply(tx2)
        assert pos.quantity == 200
        assert pos.avg_cost == Decimal("10000")  # (9500*100 + 10500*100) / 200

    def test_sell_partial(self):
        pos = Position(ticker="BBCA", quantity=200, avg_cost=Decimal("9500"))
        tx = Transaction(ticker="BBCA", side="sell", quantity=100, price=Decimal("10000"), timestamp=datetime(2025, 1, 7))
        pos.apply(tx)
        assert pos.quantity == 100
        assert pos.realized_pnl == Decimal("50000")  # (10000-9500)*100

    def test_sell_all(self):
        pos = Position(ticker="BBCA", quantity=100, avg_cost=Decimal("9500"))
        tx = Transaction(ticker="BBCA", side="sell", quantity=100, price=Decimal("10000"), timestamp=datetime(2025, 1, 7))
        pos.apply(tx)
        assert pos.quantity == 0
        assert pos.avg_cost == Decimal("0")

    def test_oversell_raises(self):
        pos = Position(ticker="BBCA", quantity=50, avg_cost=Decimal("9500"))
        tx = Transaction(ticker="BBCA", side="sell", quantity=100, price=Decimal("10000"), timestamp=datetime(2025, 1, 7))
        try:
            pos.apply(tx)
            assert False, "Should raise ValueError"
        except ValueError:
            pass


class TestPortfolio:
    def test_buy_reduces_cash(self):
        p = Portfolio(cash=Decimal("100000000"))
        tx = Transaction(
            ticker="BBCA", side="buy", quantity=100,
            price=Decimal("9500"), timestamp=datetime(2025, 1, 6),
            fee=Decimal("1425"),
        )
        p.record(tx)
        expected_cash = Decimal("100000000") - Decimal("9500") * 100 - Decimal("1425")
        assert p.cash == expected_cash

    def test_sell_increases_cash(self):
        p = Portfolio(cash=Decimal("0"))
        p.positions["BBCA"] = Position(ticker="BBCA", quantity=100, avg_cost=Decimal("9500"))
        tx = Transaction(
            ticker="BBCA", side="sell", quantity=100,
            price=Decimal("10000"), timestamp=datetime(2025, 1, 7),
            fee=Decimal("1500"),
        )
        p.record(tx)
        expected_cash = Decimal("10000") * 100 - Decimal("1500")
        assert p.cash == expected_cash

    def test_multiple_stocks(self):
        p = Portfolio(cash=Decimal("200000000"))
        tx1 = Transaction(ticker="BBCA", side="buy", quantity=100, price=Decimal("9500"), timestamp=datetime(2025, 1, 6))
        tx2 = Transaction(ticker="BBRI", side="buy", quantity=200, price=Decimal("5000"), timestamp=datetime(2025, 1, 6))
        p.record(tx1)
        p.record(tx2)
        assert "BBCA" in p.positions
        assert "BBRI" in p.positions
        assert p.positions["BBCA"].quantity == 100
        assert p.positions["BBRI"].quantity == 200

    def test_transactions_recorded(self):
        p = Portfolio(cash=Decimal("100000000"))
        tx = Transaction(ticker="BBCA", side="buy", quantity=100, price=Decimal("9500"), timestamp=datetime(2025, 1, 6))
        p.record(tx)
        assert len(p.transactions) == 1
        assert p.transactions[0].ticker == "BBCA"
