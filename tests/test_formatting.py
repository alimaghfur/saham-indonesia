"""Tests for formatting utilities."""
from decimal import Decimal

from saham_id.utils.formatting import format_large, format_pct, format_rupiah


class TestFormatRupiah:
    def test_basic(self):
        assert format_rupiah(1234567) == "Rp 1.234.567"

    def test_zero(self):
        assert format_rupiah(0) == "Rp 0"

    def test_negative(self):
        assert format_rupiah(-500000) == "-Rp 500.000"

    def test_decimal_places(self):
        result = format_rupiah(1500.50, decimals=2)
        assert "1.500" in result
        assert "50" in result

    def test_from_decimal(self):
        result = format_rupiah(Decimal("9800"))
        assert "9.800" in result

    def test_small_value(self):
        assert format_rupiah(50) == "Rp 50"


class TestFormatPct:
    def test_positive(self):
        assert format_pct(0.0321) == "+3.21%"

    def test_negative(self):
        assert format_pct(-0.05) == "-5.00%"

    def test_zero(self):
        assert format_pct(0) == "0.00%"

    def test_custom_decimals(self):
        result = format_pct(0.12345, decimals=3)
        assert "12.345%" in result

    def test_large_positive(self):
        result = format_pct(1.5)
        assert "+150.00%" == result


class TestFormatLarge:
    def test_trillion(self):
        assert format_large(1_500_000_000_000) == "1.50T"

    def test_billion(self):
        assert format_large(2_300_000_000) == "2.30B"

    def test_million(self):
        assert format_large(5_600_000) == "5.60M"

    def test_thousand(self):
        assert format_large(1234) == "1.23K"

    def test_small(self):
        assert format_large(50) == "50.00"

    def test_negative_billion(self):
        assert format_large(-3_000_000_000) == "-3.00B"

    def test_from_decimal(self):
        result = format_large(Decimal("1500000000"))
        assert "1.50B" == result
