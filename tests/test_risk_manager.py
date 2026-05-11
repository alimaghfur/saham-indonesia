"""Tests for risk manager module."""
from datetime import date, timedelta

from saham_id.risk_manager import (
    RiskManager, StopRule, StopTrigger,
)


class TestStopRule:
    def test_create(self):
        rule = StopRule(ticker="BBCA", entry_price=9500, stop_price=9000)
        assert rule.ticker == "BBCA"
        assert rule.current_stop == 9000
        assert rule.risk_pct > 0

    def test_trailing_stop(self):
        rule = StopRule(
            ticker="BBCA", entry_price=9500, stop_price=9000,
            trailing_pct=0.05, highest_since_entry=10000,
        )
        # Trailing stop = 10000 * (1 - 0.05) = 9500
        # Should be max(9000, 9500) = 9500
        assert rule.current_stop == 9500

    def test_trailing_not_below_initial(self):
        rule = StopRule(
            ticker="BBCA", entry_price=9500, stop_price=9000,
            trailing_pct=0.05, highest_since_entry=9300,
        )
        # Trailing = 9300 * 0.95 = 8835 — below initial stop
        # Should use initial stop of 9000
        assert rule.current_stop == 9000

    def test_risk_pct(self):
        rule = StopRule(ticker="BBCA", entry_price=10000, stop_price=9000)
        assert abs(rule.risk_pct - 0.10) < 0.001  # 10% risk

    def test_days_held(self):
        rule = StopRule(
            ticker="BBCA", entry_price=9500, stop_price=9000,
            entry_date=date.today() - timedelta(days=5),
        )
        assert rule.days_held == 5

    def test_time_limit(self):
        rule = StopRule(
            ticker="BBCA", entry_price=9500, stop_price=9000,
            time_limit_days=30, entry_date=date.today() - timedelta(days=31),
        )
        assert rule.days_held >= 30


class TestRiskManager:
    def test_add_remove_stop(self):
        rm = RiskManager()
        rm.add_stop(StopRule(ticker="BBCA", entry_price=9500, stop_price=9000))
        assert "BBCA" in rm.stops
        rm.remove_stop("BBCA")
        assert "BBCA" not in rm.stops

    def test_update_high(self):
        rm = RiskManager()
        rm.add_stop(StopRule(ticker="BBCA", entry_price=9500, stop_price=9000))
        rm.update_high("BBCA", 10000)
        assert rm.stops["BBCA"].highest_since_entry == 10000

    def test_circuit_breaker(self):
        rm = RiskManager(max_portfolio_drawdown=0.10)
        rm.peak_portfolio_value = 100_000_000
        # 15% drawdown -> should trigger
        assert rm.check_circuit_breaker(85_000_000) is True
        assert rm.is_halted is True

    def test_circuit_breaker_not_triggered(self):
        rm = RiskManager(max_portfolio_drawdown=0.10)
        rm.peak_portfolio_value = 100_000_000
        # 5% drawdown -> should NOT trigger
        assert rm.check_circuit_breaker(95_000_000) is False
        assert rm.is_halted is False

    def test_daily_limit(self):
        rm = RiskManager(daily_loss_limit=0.03)
        # 4% daily loss -> should stop
        assert rm.check_daily_limit(-4_000_000, 100_000_000) is True
        # 1% daily loss -> OK
        assert rm.check_daily_limit(-1_000_000, 100_000_000) is False

    def test_reset_circuit_breaker(self):
        rm = RiskManager()
        rm.is_halted = True
        rm.reset_circuit_breaker()
        assert rm.is_halted is False

    def test_summary(self):
        rm = RiskManager()
        rm.add_stop(StopRule(ticker="BBCA", entry_price=9500, stop_price=9000))
        summary = rm.summary()
        assert summary["active_stops"] == 1
        assert "BBCA" in summary["stops"]
        assert summary["is_halted"] is False
