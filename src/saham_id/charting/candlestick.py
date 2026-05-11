"""Candlestick and OHLC chart builders.

Supports:
- Classic candlestick with volume bars
- OHLC bar chart variant
- Moving average overlays
- Volume profile sidebar
- Support/resistance lines
"""

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from saham_id.charting.styles import COLORS, LINE_COLORS, apply_theme


def candlestick_chart(
    df: pd.DataFrame,
    ticker: str = "",
    title: Optional[str] = None,
    ma_periods: Optional[Sequence[int]] = None,
    show_volume: bool = True,
    support_levels: Optional[Sequence[float]] = None,
    resistance_levels: Optional[Sequence[float]] = None,
    height: int = 600,
    dark: bool = True,
) -> go.Figure:
    """Create an interactive candlestick chart with optional overlays.

    Args:
        df: DataFrame with columns: open, high, low, close, volume.
            Index should be datetime.
        ticker: Stock ticker for display.
        title: Chart title (defaults to ticker).
        ma_periods: Moving average periods to overlay (e.g., [20, 50, 200]).
        show_volume: Whether to show volume subplot.
        support_levels: Horizontal support lines.
        resistance_levels: Horizontal resistance lines.
        height: Chart height in pixels.
        dark: Use dark theme.

    Returns:
        Plotly Figure object.
    """
    if title is None:
        title = f"{ticker} - Candlestick" if ticker else "Candlestick Chart"

    row_heights = [0.7, 0.3] if show_volume else [1.0]
    rows = 2 if show_volume else 1

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            increasing_line_color=COLORS["green"],
            decreasing_line_color=COLORS["red"],
            increasing_fillcolor=COLORS["green"],
            decreasing_fillcolor=COLORS["red"],
            name="Price",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    # Moving averages
    if ma_periods:
        for i, period in enumerate(ma_periods):
            ma = df["close"].rolling(window=period).mean()
            color = LINE_COLORS[i % len(LINE_COLORS)]
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=ma,
                    mode="lines",
                    name=f"MA{period}",
                    line=dict(color=color, width=1.5),
                    opacity=0.8,
                ),
                row=1,
                col=1,
            )

    # Support/Resistance lines
    if support_levels:
        for level in support_levels:
            fig.add_hline(
                y=level,
                line_dash="dash",
                line_color=COLORS["green"],
                opacity=0.5,
                annotation_text=f"S: {level:,.0f}",
                row=1,
                col=1,
            )

    if resistance_levels:
        for level in resistance_levels:
            fig.add_hline(
                y=level,
                line_dash="dash",
                line_color=COLORS["red"],
                opacity=0.5,
                annotation_text=f"R: {level:,.0f}",
                row=1,
                col=1,
            )

    # Volume bars
    if show_volume and "volume" in df.columns:
        colors = [
            COLORS["green"] if c >= o else COLORS["red"]
            for c, o in zip(df["close"], df["open"])
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["volume"],
                marker_color=colors,
                opacity=0.6,
                name="Volume",
                showlegend=False,
            ),
            row=2,
            col=1,
        )
        fig.update_yaxes(title_text="Volume", row=2, col=1)

    # Layout
    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis_rangeslider_visible=False,
        height=height,
        yaxis_title="Price (IDR)",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    # Hide weekends/holidays gaps
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # weekends
        ]
    )

    apply_theme(fig, dark=dark)
    return fig


def ohlc_chart(
    df: pd.DataFrame,
    ticker: str = "",
    title: Optional[str] = None,
    show_volume: bool = True,
    height: int = 600,
    dark: bool = True,
) -> go.Figure:
    """Create an OHLC bar chart (alternative to candlestick).

    Args:
        df: DataFrame with OHLCV columns.
        ticker: Stock ticker for display.
        title: Chart title.
        show_volume: Whether to show volume subplot.
        height: Chart height in pixels.
        dark: Use dark theme.

    Returns:
        Plotly Figure object.
    """
    if title is None:
        title = f"{ticker} - OHLC" if ticker else "OHLC Chart"

    row_heights = [0.7, 0.3] if show_volume else [1.0]
    rows = 2 if show_volume else 1

    fig = make_subplots(
        rows=rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    fig.add_trace(
        go.Ohlc(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            increasing_line_color=COLORS["green"],
            decreasing_line_color=COLORS["red"],
            name="OHLC",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    if show_volume and "volume" in df.columns:
        colors = [
            COLORS["green"] if c >= o else COLORS["red"]
            for c, o in zip(df["close"], df["open"])
        ]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["volume"],
                marker_color=colors,
                opacity=0.6,
                name="Volume",
                showlegend=False,
            ),
            row=2,
            col=1,
        )

    fig.update_layout(
        title=dict(text=title, x=0.5),
        xaxis_rangeslider_visible=False,
        height=height,
        yaxis_title="Price (IDR)",
    )

    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    apply_theme(fig, dark=dark)
    return fig
