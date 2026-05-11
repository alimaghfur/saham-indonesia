"""Tests for position sizing module."""
from saham_id.portfolio.sizing import (
    PositionSize, kelly_size, fixed_fractional, risk_based,
    max_shares_for_capital, portfolio_heat,
)


class TestKellySize:
    def test_positive_edge(self):
        # 60% win rate, 5% avg win, 3% avg loss
        size = kelly_size(win_rate=0.6, avg_win=0.05, avg_loss=0.03)
        assert size > 0
        assert size <= 0.25  # capped

    def test_negative_edge(self):
        # 30% win rate, 2% avg win, 5% avg loss -> no edge
        size = kelly_size(win_rate=0.3, avg_win=0.02, avg_loss=0.05)
        assert size == 0.0

    def test_breakeven(self):
        # 50% win, equal win/loss -> edge = 0
        size = kelly_size(win_rate=0.5, avg_win=0.05, avg_loss=0.05)
        assert size == 0.0

    def test_half_kelly(self):
        full = kelly_size(win_rate=0.6, avg_win=0.05, avg_loss=0.03, fraction=1.0)
        half = kelly_size(win_rate=0.6, avg_win=0.05, avg_loss=0.03, fraction=0.5)
        assert half < full or (half == full == 0.25)  # both may be capped

    def test_invalid_inputs(self):
        assert kelly_size(win_rate=0, avg_win=0.05, avg_loss=0.03) == 0.0
        assert kelly_size(win_rate=0.6, avg_win=0.05, avg_loss=0) == 0.0
        assert kelly_size(win_rate=1.0, avg_win=0.05, avg_loss=0.03) == 0.0


class TestFixedFractional:
    def test_basic(self):
        result = fixed_fractional(
            capital=100_000_000,
            risk_pct=0.02,
            entry_price=9500,
            stop_loss_price=9000,
        )
        assert result.shares > 0
        assert result.lots > 0
        assert result.shares == result.lots * 100
        assert result.risk_amount > 0
        assert result.risk_pct_of_capital <= 0.021  # approximately 2%

    def test_tight_stop(self):
        # Tight stop -> more shares
        tight = fixed_fractional(100_000_000, 0.02, 9500, 9400)
        wide = fixed_fractional(100_000_000, 0.02, 9500, 8500)
        assert tight.shares >= wide.shares

    def test_zero_risk_per_share(self):
        # Stop = entry -> no risk per share -> 0 shares
        result = fixed_fractional(100_000_000, 0.02, 9500, 9500)
        assert result.shares == 0

    def test_expensive_stock_small_capital(self):
        # Cannot afford even 1 lot
        result = fixed_fractional(1_000_000, 0.02, 50000, 45000)
        # With 20k risk, entry 50k, risk/share = 5000, max shares = 4 -> 0 lots
        assert result.lots == 0 or result.shares < 100


class TestRiskBased:
    def test_basic(self):
        result = risk_based(
            capital=100_000_000,
            risk_pct=0.02,
            entry_price=9500,
            atr=200,
            atr_multiplier=2.0,
        )
        assert result.shares > 0
        assert result.stop_loss_price == 9500 - (200 * 2.0)
        assert result.method == "risk_based_atr"

    def test_high_atr_fewer_shares(self):
        low_atr = risk_based(100_000_000, 0.02, 9500, atr=100, atr_multiplier=2.0)
        high_atr = risk_based(100_000_000, 0.02, 9500, atr=500, atr_multiplier=2.0)
        assert low_atr.shares >= high_atr.shares


class TestMaxSharesForCapital:
    def test_basic(self):
        result = max_shares_for_capital(
            capital=100_000_000, price=9500, max_allocation_pct=0.20
        )
        assert result.shares > 0
        assert result.capital_required <= 100_000_000 * 0.201  # within 20%+commission

    def test_zero_price(self):
        result = max_shares_for_capital(100_000_000, 0)
        assert result.shares == 0


class TestPortfolioHeat:
    def test_single_position(self):
        positions = [{"shares": 1000, "entry": 9500, "stop_loss": 9000}]
        heat = portfolio_heat(positions, capital=100_000_000)
        # Risk = 1000 * (9500 - 9000) = 500,000 / 100M = 0.5%
        assert abs(heat - 0.005) < 0.001

    def test_multiple_positions(self):
        positions = [
            {"shares": 1000, "entry": 9500, "stop_loss": 9000},
            {"shares": 2000, "entry": 5000, "stop_loss": 4700},
        ]
        heat = portfolio_heat(positions, capital=100_000_000)
        # Risk1 = 500k, Risk2 = 600k, total = 1.1M / 100M = 1.1%
        assert abs(heat - 0.011) < 0.001

    def test_empty_portfolio(self):
        heat = portfolio_heat([], capital=100_000_000)
        assert heat == 0.0
