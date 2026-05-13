"""Comparison chart — relative performance overlay for 2+ tickers.

Visualize multiple stocks on a single chart with:
- Normalized price (rebased to 100)
- Relative performance overlay
- Volume comparison
"""

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from saham_id.charting.styles import COLORS, LINE_COLORS, apply_theme


def comparison_chart(
    dataframes: dict[str, pd.DataFrame],
    title: str = "Stock Comparison",
    normalize: bool = True,
    show_volume: bool = False,
    height: int = 600,
    dark: bool = True,
) -> go.Figure:
    """Create a relative performance comparison chart.

    Args:
        dataframes: Dict of {ticker: DataFrame} with 'close' column.
        title: Chart title.
        normalize: If True, rebase all prices to 100 at start.
        show_volume: Show volume comparison subplot.
        height: Chart height.
        dark: Dark theme.

    Returns:
        Plotly Figure.
    """
    rows = 2 if show_volume else 1
    row_heights = [0.7, 0.3] if show_volume else [1.0]

    fig = make_subplots(
        rows=rows, cols=1, shared_xaxes=True,
        vertical_spacing=0.05, row_heights=row_heights,
    )

    for i, (ticker, df) in enumerate(dataframes.items()):
        if df.empty or "close" not in df.columns:
            continue

        close = df["close"]
        if normalize:
            first_val = close.iloc[0]
            if first_val and float(first_val) != 0:
                y_data = close / first_val * 100
                y_title = "Performance (rebased to 100)"
            else:
                y_data = close
                y_title = "Price"
        else:
            y_data = close
            y_title = "Price (IDR)"

        color = LINE_COLORS[i % len(LINE_COLORS)]
        fig.add_trace(
            go.Scatter(
                x=df.index, y=y_data,
                mode="lines", name=ticker,
                line=dict(color=color, width=2),
            ),
            row=1, col=1,
        )

        # Volume subplot
        if show_volume and "volume" in df.columns:
            fig.add_trace(
                go.Bar(
                    x=df.index, y=df["volume"],
                    name=f"{ticker} Vol",
                    marker_color=color, opacity=0.4,
                    showlegend=False,
                ),
                row=2, col=1,
            )

    # Reference line at 100 for normalized
    if normalize:
        fig.add_hline(y=100, line_dash="dash", line_color=COLORS["grey"], opacity=0.4, row=1, col=1)

    fig.update_layout(
        title=dict(text=title, x=0.5),
        height=height,
        yaxis_title=y_title if not normalize else "Performance (rebased to 100)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    if show_volume:
        fig.update_yaxes(title_text="Volume", row=2, col=1)

    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    apply_theme(fig, dark=dark)
    return fig


def drawdown_comparison(
    dataframes: dict[str, pd.DataFrame],
    title: str = "Drawdown Comparison",
    height: int = 400,
    dark: bool = True,
) -> go.Figure:
    """Compare drawdown profiles of multiple stocks.

    Args:
        dataframes: Dict of {ticker: DataFrame} with 'close' column.
        title: Chart title.
        height: Chart height.
        dark: Dark theme.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()

    for i, (ticker, df) in enumerate(dataframes.items()):
        if df.empty or "close" not in df.columns:
            continue

        close = df["close"]
        cummax = close.cummax()
        drawdown = (close - cummax) / cummax * 100

        color = LINE_COLORS[i % len(LINE_COLORS)]
        fig.add_trace(
            go.Scatter(
                x=df.index, y=drawdown,
                mode="lines", name=ticker,
                line=dict(color=color, width=1.5),
            )
        )

    fig.add_hline(y=0, line_color=COLORS["grey"], opacity=0.3)

    fig.update_layout(
        title=dict(text=title, x=0.5),
        height=height,
        yaxis_title="Drawdown (%)",
        hovermode="x unified",
    )

    apply_theme(fig, dark=dark)
    return fig
