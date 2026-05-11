"""Chart styling and theming for IDX-themed visualizations."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go
import plotly.io as pio

# IDX color palette
COLORS = {
    "green": "#26a69a",       # Bullish / up
    "red": "#ef5350",         # Bearish / down
    "blue": "#42a5f5",        # Primary accent
    "orange": "#ffa726",      # Warning / highlight
    "purple": "#ab47bc",      # Secondary accent
    "grey": "#78909c",        # Neutral
    "dark_bg": "#1e1e2e",     # Dark background
    "light_bg": "#ffffff",    # Light background
    "grid": "#2d2d3d",        # Grid lines (dark)
    "grid_light": "#e0e0e0",  # Grid lines (light)
    "text": "#cdd6f4",        # Text (dark theme)
    "text_light": "#333333",  # Text (light theme)
}

# Multi-line color sequence
LINE_COLORS = [
    "#42a5f5", "#ffa726", "#ab47bc", "#26a69a",
    "#ef5350", "#66bb6a", "#29b6f6", "#ff7043",
    "#ec407a", "#8d6e63",
]

# IDX Dark theme template
IDX_THEME: dict[str, Any] = {
    "layout": {
        "paper_bgcolor": COLORS["dark_bg"],
        "plot_bgcolor": COLORS["dark_bg"],
        "font": {"color": COLORS["text"], "family": "Inter, sans-serif"},
        "xaxis": {
            "gridcolor": COLORS["grid"],
            "zerolinecolor": COLORS["grid"],
            "showgrid": True,
            "gridwidth": 0.5,
        },
        "yaxis": {
            "gridcolor": COLORS["grid"],
            "zerolinecolor": COLORS["grid"],
            "showgrid": True,
            "gridwidth": 0.5,
        },
        "colorway": LINE_COLORS,
        "hoverlabel": {
            "bgcolor": "#2d2d3d",
            "font_size": 12,
            "font_family": "Inter, monospace",
        },
        "legend": {
            "bgcolor": "rgba(30,30,46,0.8)",
            "bordercolor": COLORS["grid"],
            "borderwidth": 1,
        },
    },
}


def apply_theme(fig: go.Figure, dark: bool = True) -> go.Figure:
    """Apply IDX theme to a plotly figure.

    Args:
        fig: Plotly figure to style.
        dark: If True, use dark theme; otherwise light theme.

    Returns:
        The styled figure (modified in-place).
    """
    if dark:
        fig.update_layout(
            paper_bgcolor=COLORS["dark_bg"],
            plot_bgcolor=COLORS["dark_bg"],
            font=dict(color=COLORS["text"], family="Inter, sans-serif"),
            xaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
            yaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
        )
    else:
        fig.update_layout(
            paper_bgcolor=COLORS["light_bg"],
            plot_bgcolor=COLORS["light_bg"],
            font=dict(color=COLORS["text_light"], family="Inter, sans-serif"),
            xaxis=dict(gridcolor=COLORS["grid_light"], zerolinecolor=COLORS["grid_light"]),
            yaxis=dict(gridcolor=COLORS["grid_light"], zerolinecolor=COLORS["grid_light"]),
        )

    fig.update_layout(
        hoverlabel=dict(bgcolor="#2d2d3d" if dark else "#f5f5f5", font_size=12),
        margin=dict(l=60, r=30, t=50, b=40),
    )
    return fig


def register_idx_template() -> None:
    """Register the IDX template in plotly so it can be used globally."""
    pio.templates["idx_dark"] = go.layout.Template(layout=go.Layout(**IDX_THEME["layout"]))
    pio.templates.default = "idx_dark"
