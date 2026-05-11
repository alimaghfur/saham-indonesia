"""Tests for valuation module."""
import math

from saham_id.analysis.valuation import DCFInputs, dcf_fair_value, graham_number


class TestDCF:
    def test_dcf_basic(self):
        inputs = DCFInputs(
            fcf_last=1_000_000,
            growth_high=0.10,
            growth_terminal=0.03,
            discount_rate=0.10,
            years_high=5,
            shares_outstanding=1000,
        )
        fv = dcf_fair_value(inputs)
        assert fv > 0
        # Should be roughly 19714 per share
        assert 15000 < fv < 25000

    def test_dcf_higher_growth_gives_higher_value(self):
        base = DCFInputs(fcf_last=1_000_000, growth_high=0.10, discount_rate=0.12, shares_outstanding=100)
        high = DCFInputs(fcf_last=1_000_000, growth_high=0.20, discount_rate=0.12, shares_outstanding=100)
        assert dcf_fair_value(high) > dcf_fair_value(base)

    def test_dcf_invalid_discount_rate(self):
        inputs = DCFInputs(fcf_last=1000, growth_terminal=0.10, discount_rate=0.05)
        try:
            dcf_fair_value(inputs)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "discount_rate must exceed growth_terminal" in str(e)

    def test_dcf_equal_discount_terminal(self):
        inputs = DCFInputs(fcf_last=1000, growth_terminal=0.10, discount_rate=0.10)
        try:
            dcf_fair_value(inputs)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestGrahamNumber:
    def test_graham_basic(self):
        gn = graham_number(eps=500, bvps=3000)
        expected = math.sqrt(22.5 * 500 * 3000)
        assert abs(gn - expected) < 0.01

    def test_graham_negative_eps(self):
        assert graham_number(eps=-100, bvps=3000) == 0.0

    def test_graham_negative_bvps(self):
        assert graham_number(eps=500, bvps=-100) == 0.0

    def test_graham_both_negative(self):
        assert graham_number(eps=-100, bvps=-500) == 0.0

    def test_graham_zero_eps(self):
        assert graham_number(eps=0, bvps=3000) == 0.0
