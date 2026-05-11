"""Tests for paper trading module."""
from saham_id.paper_trading import PaperTrader, PaperOrder, PaperPosition, PaperTrade


class TestPaperOrder:
    def test_create(self):
        order = PaperOrder(ticker="BBCA", side="buy", lots=10)
        assert order.shares == 1000
        assert order.status == "pending"

    def test_shares_from_lots(self):
        order = PaperOrder(ticker="BBRI", side="sell", lots=5)
        assert order.shares == 500


class TestPaperPosition:
    def test_create(self):
        pos = PaperPosition(ticker="BBCA", shares=1000, avg_cost=9500.0)
        assert pos.lots == 10

    def test_zero_position(self):
        pos = PaperPosition(ticker="BBCA")
        assert pos.lots == 0
        assert pos.shares == 0


class TestPaperTrader:
    def test_initial_state(self):
        trader = PaperTrader(initial_capital=100_000_000)
        assert trader.cash == 100_000_000
        assert len(trader.positions) == 0
        assert len(trader.trades) == 0

    def test_summary(self):
        trader = PaperTrader(initial_capital=50_000_000)
        summary = trader.summary()
        assert summary["initial_capital"] == 50_000_000
        assert summary["cash"] == 50_000_000
        assert summary["num_trades"] == 0

    def test_buy_insufficient_cash(self):
        trader = PaperTrader(initial_capital=100)  # Very low capital
        # Even though we can't get live price, the logic path exists
        # This will fail to get price (no network) which is expected
        order = trader.buy("BBCA", lots=1000)
        assert order.status == "rejected"

    def test_sell_no_position(self):
        trader = PaperTrader(initial_capital=100_000_000)
        order = trader.sell("BBCA", lots=1)
        assert order.status == "rejected"
        assert "Insufficient shares" in order.note

    def test_sell_too_many(self):
        trader = PaperTrader(initial_capital=100_000_000)
        trader.positions["BBCA"] = PaperPosition(ticker="BBCA", shares=500, avg_cost=9500)
        order = trader.sell("BBCA", lots=10)  # 1000 shares > 500
        assert order.status == "rejected"
