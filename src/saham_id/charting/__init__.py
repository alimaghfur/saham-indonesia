"""Charting module for saham-indonesia.

Plotly-based interactive charts for:
- Candlestick / OHLC with volume
- Technical indicators overlay
- Portfolio performance
- Comparison / relative strength
- Screener heatmaps
"""

from saham_id.charting.candlestick import candlestick_chart, ohlc_chart
from saham_id.charting.indicators import indicator_chart, multi_indicator_chart
from saham_id.charting.portfolio import (
    allocation_pie,
    drawdown_chart,
    equity_curve,
    portfolio_dashboard,
)
from saham_id.charting.styles import IDX_THEME, apply_theme

__all__ = [
    "candlestick_chart",
    "ohlc_chart",
    "indicator_chart",
    "multi_indicator_chart",
    "equity_curve",
    "drawdown_chart",
    "allocation_pie",
    "portfolio_dashboard",
    "apply_theme",
    "IDX_THEME",
]
