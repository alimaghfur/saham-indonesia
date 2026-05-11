"""Display formatters for Indonesian financial data."""

from __future__ import annotations

from decimal import Decimal


def format_rupiah(value: float | Decimal | int, decimals: int = 0) -> str:
    """Format number as `Rp 1.234.567` with Indonesian thousands separator."""
    v = float(value)
    sign = "-" if v < 0 else ""
    v = abs(v)
    # Use Indonesian convention: '.' as thousands separator.
    formatted = f"{v:,.{decimals}f}".replace(",", ".")
    return f"{sign}Rp {formatted}"


def format_pct(value: float, decimals: int = 2) -> str:
    """Format a fraction as percentage with sign (e.g. 0.0321 -> '+3.21%')."""
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.{decimals}f}%"


def format_large(value: float | Decimal | int) -> str:
    """Short form: 1.2M, 3.4B, 5.6T for readable market caps."""
    v = float(value)
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1e12:
        return f"{sign}{v / 1e12:.2f}T"
    if v >= 1e9:
        return f"{sign}{v / 1e9:.2f}B"
    if v >= 1e6:
        return f"{sign}{v / 1e6:.2f}M"
    if v >= 1e3:
        return f"{sign}{v / 1e3:.2f}K"
    return f"{sign}{v:.2f}"
