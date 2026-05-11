"""Unit tests for the portfolio tracker."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from saham_id.portfolio import Portfolio, Position, Transaction


def _tx(ticker: str, side: str, qty: int, price: float, fee: float = 0.0) -> Transaction:
    return Transaction(
        ticker=ticker,
        side=side,  # type: ignore[arg-type]
        quantity=qty,
        price=Decimal(str(price)),
        fee=Decimal(str(fee)),
        timestamp=datetime(2024, 6, 17, 10, 0),
    )


class TestPosition:
    def test_buy_sets_avg_cost(self):
        pos = Position(ticker="BBCA")
        pos.apply(_tx("BBCA", "buy", 100, 9000))
        assert pos.quantity == 100
        assert pos.avg_cost == Decimal("9000")

    def test_buy_twice_averages_cost(self):
        pos = Position(ticker="BBCA")
        pos.apply(_tx("BBCA", "buy", 100, 9000))
        pos.apply(_tx("BBCA", "buy", 100, 11000))
        assert pos.quantity == 200
        # (100*9000 + 100*11000) / 200 = 10000
        assert pos.avg_cost == Decimal("10000")

    def test_buy_with_fee_included_in_avg_cost(self):
        pos = Position(ticker="BBCA")
        pos.apply(_tx("BBCA", "buy", 100, 9000, fee=1000))
        # (100*9000 + 1000) / 100 = 9010
        assert pos.avg_cost == Decimal("9010")

    def test_partial_sell_updates_realized(self):
        pos = Position(ticker="BBCA")
        pos.apply(_tx("BBCA", "buy", 100, 9000))
        pos.apply(_tx("BBCA", "sell", 50, 10000))
        assert pos.quantity == 50
        # Realized on 50 shares @ 10000 vs cost 9000 = 50 * 1000 = 50000
        assert pos.realized_pnl == Decimal("50000")

    def test_full_sell_resets_avg_cost(self):
        pos = Position(ticker="BBCA")
        pos.apply(_tx("BBCA", "buy", 100, 9000))
        pos.apply(_tx("BBCA", "sell", 100, 10000))
        assert pos.quantity == 0
        assert pos.avg_cost == Decimal(0)

    def test_oversell_raises(self):
        pos = Position(ticker="BBCA")
        pos.apply(_tx("BBCA", "buy", 50, 9000))
        with pytest.raises(ValueError):
            pos.apply(_tx("BBCA", "sell", 100, 9500))


class TestPortfolio:
    def test_record_updates_cash_and_position(self):
        p = Portfolio(cash=Decimal("10000000"))
        p.record(_tx("BBCA", "buy", 100, 9000))
        assert p.cash == Decimal("9100000")  # 10M - 100*9000
        assert p.positions["BBCA"].quantity == 100
        assert len(p.transactions) == 1

    def test_sell_increases_cash(self):
        p = Portfolio(cash=Decimal("10000000"))
        p.record(_tx("BBCA", "buy", 100, 9000))
        p.record(_tx("BBCA", "sell", 100, 10000))
        # Cash = 10M - 100*9000 + 100*10000 = 10.1M
        assert p.cash == Decimal("10100000")
        assert p.positions["BBCA"].quantity == 0

    def test_snapshot_uses_source_quote(self, populated_fake_source):
        """Snapshot should fetch current price via the provided DataSource."""
        p = Portfolio(cash=Decimal("10000000"))
        p.record(_tx("BBCA", "buy", 100, 9000))
        snap = p.snapshot(source=populated_fake_source)
        assert not snap.empty
        assert snap.iloc[0]["ticker"] == "BBCA"
        assert snap.iloc[0]["quantity"] == 100
        # `weight` column present when portfolio non-empty
        assert "weight" in snap.columns
        assert snap.iloc[0]["weight"] == pytest.approx(1.0)

    def test_snapshot_skips_zero_positions(self, populated_fake_source):
        p = Portfolio(cash=Decimal("10000000"))
        p.record(_tx("BBCA", "buy", 100, 9000))
        p.record(_tx("BBCA", "sell", 100, 9500))
        snap = p.snapshot(source=populated_fake_source)
        assert snap.empty

    def test_total_value_with_no_positions(self, populated_fake_source):
        p = Portfolio(cash=Decimal("5000000"))
        assert p.total_value(source=populated_fake_source) == Decimal("5000000")

    def test_unrealized_pnl_sign(self, populated_fake_source):
        """If quote > avg_cost, unrealized PnL is positive; else negative."""
        p = Portfolio(cash=Decimal("100000000"))
        # Buy at an artificially low price so the live quote exceeds it
        p.record(_tx("BBCA", "buy", 100, 1))
        snap = p.snapshot(source=populated_fake_source)
        assert snap.iloc[0]["unrealized_pnl"] > 0
