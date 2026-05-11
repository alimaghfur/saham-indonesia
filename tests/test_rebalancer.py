"""Tests for auto-rebalancing."""
from saham_id.portfolio.rebalancer import RebalanceOrder, RebalanceResult, rebalance


class TestRebalanceOrder:
    def test_actionable_buy(self):
        order = RebalanceOrder(ticker="BBCA", action="buy", shares=500, lots=5,
                              price=9500, current_weight=0.2, target_weight=0.4, deviation=0.2)
        assert order.is_actionable is True

    def test_not_actionable_hold(self):
        order = RebalanceOrder(ticker="BBCA", action="hold", shares=0, lots=0,
                              price=9500, current_weight=0.39, target_weight=0.40, deviation=0.01)
        assert order.is_actionable is False


class TestRebalanceResult:
    def test_actionable_orders(self):
        orders = [
            RebalanceOrder(ticker="A", action="buy", shares=100, lots=1, price=100,
                          current_weight=0.2, target_weight=0.4, deviation=0.2),
            RebalanceOrder(ticker="B", action="hold", shares=0, lots=0, price=200,
                          current_weight=0.3, target_weight=0.3, deviation=0.0),
            RebalanceOrder(ticker="C", action="sell", shares=200, lots=2, price=150,
                          current_weight=0.5, target_weight=0.3, deviation=-0.2),
        ]
        result = RebalanceResult(orders=orders)
        assert result.num_buys == 1
        assert result.num_sells == 1
        assert len(result.actionable_orders) == 2

    def test_empty(self):
        result = RebalanceResult()
        assert result.num_buys == 0


class TestRebalance:
    def test_empty_positions(self):
        result = rebalance({}, {"BBCA": 1.0}, total_capital=100_000_000)
        assert isinstance(result, RebalanceResult)
