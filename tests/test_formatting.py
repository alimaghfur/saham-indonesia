"""Unit tests for formatting helpers."""

from __future__ import annotations

from decimal import Decimal

from saham_id.utils.formatting import format_large, format_pct, format_rupiah


class TestFormatRupiah:
    def test_basic(self):
        assert format_rupiah(1_234_567) == "Rp 1.234.567"

    def test_negative(self):
        assert format_rupiah(-1_000_000) == "-Rp 1.000.000"

    def test_zero(self):
        assert format_rupiah(0) == "Rp 0"

    def test_with_decimals_uses_indonesian_separators(self):
        # Indonesian convention: '.' thousands, ',' decimals
        assert format_rupiah(1234.5, decimals=2) == "Rp 1.234,50"

    def test_accepts_decimal_type(self):
        assert format_rupiah(Decimal("5000")) == "Rp 5.000"


class TestFormatPct:
    def test_positive_has_plus(self):
        assert format_pct(0.0321) == "+3.21%"

    def test_negative(self):
        assert format_pct(-0.045) == "-4.50%"

    def test_zero(self):
        assert format_pct(0.0) == "0.00%"

    def test_custom_decimals(self):
        assert format_pct(0.12345, decimals=3) == "+12.345%"


class TestFormatLarge:
    def test_trillion(self):
        assert format_large(1.5e12) == "1.50T"

    def test_billion(self):
        assert format_large(2.3e9) == "2.30B"

    def test_million(self):
        assert format_large(5_600_000) == "5.60M"

    def test_thousand(self):
        assert format_large(7_890) == "7.89K"

    def test_small_no_suffix(self):
        assert format_large(42) == "42.00"

    def test_negative(self):
        assert format_large(-1.5e12) == "-1.50T"
