"""Portfolio visualization charts.

Supports:
- Equity curve
- Drawdown chart
- Allocation pie/donut
- Portfolio dashboard (combined)
"""

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from saham_id.charting.styles import COLORS, LINE_COLORS, apply_theme


def equity_curve(
    returns: pd.Series,
    benchmark: Optional[pd.Series] = None,
    title: str = "Equity Curve",
    initial_capital: float = 100_000_000,
    height: int = 400,
    dark: bool = True,
) -> go.Figure:
    """Plot cumulative portfolio equity curve.

    Args:
        returns: Daily returns series (decimal, e.g., 0.01 = 1%).
        benchmark: Optional benchmark returns for comparison.
        title: Chart title.
        initial_capital: Starting capital in IDR.
        height: Chart height.
        dark: Use dark theme.

    Returns:
        Plotly Figure.
    """
    equity = (1 + returns).cumprod() * initial_capital

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=equity.index,
        y=equity,
        mode="lines",
        name="Portfolio",
        line=dict(color=COLORS["blue"], width=2),
        fill="tozeroy",
        fillcolor="rgba(66,165,245,0.1)",
    ))

    if benchmark is not None:
        bench_equity = (1 + benchmark).cumprod() * initial_capital
        fig.add_trace(go.Scatter(
            x=bench_equity.index,
            y=bench_equity,
            mode="lines",
            name="Benchmark",
            line=dict(color=COLORS["grey"], width=1.5, dash="dash"),
        ))

    fig.update_layout(
        title=dict(text=title, x=0.5),
        height=height,
        yaxis_title="Equity (IDR)",
        xaxis_title="Date",
        hovermode="x unified",
    )

    apply_theme(fig, dark=dark)
    return fig


def drawdown_chart(
    returns: pd.Series,
    title: str = "Drawdown",
    height: int = 300,
    dark: bool = True,
) -> go.Figure:
    """Plot underwater / drawdown chart.

    Args:
        returns: Daily returns series (decimal).
        title: Chart title.
        height: Chart height.
        dark: Use dark theme.

    Returns:
        Plotly Figure.
    """
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max * 100  # As percentage

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=drawdown.index,
        y=drawdown,
        mode="lines",
        name="Drawdown",
        line=dict(color=COLORS["red"], width=1.5),
        fill="tozeroy",
        fillcolor="rgba(239,83,80,0.2)",
    ))

    # Max drawdown annotation
    max_dd = drawdown.min()
    max_dd_date = drawdown.idxmin()
    fig.add_annotation(
        x=max_dd_date,
        y=max_dd,
        text=f"Max DD: {max_dd:.1f}%",
        showarrow=True,
        arrowhead=2,
        font=dict(color=COLORS["red"]),
    )

    fig.update_layout(
        title=dict(text=title, x=0.5),
        height=height,
        yaxis_title="Drawdown (%)",
        xaxis_title="Date",
        hovermode="x unified",
    )

    apply_theme(fig, dark=dark)
    return fig


def allocation_pie(
    holdings: dict[str, float],
    title: str = "Portfolio Allocation",
    height: int = 400,
    dark: bool = True,
) -> go.Figure:
    """Create a donut chart showing portfolio allocation.

    Args:
        holdings: Dict of {ticker: value_in_idr}.
        title: Chart title.
        height: Chart height.
        dark: Use dark theme.

    Returns:
        Plotly Figure.
    """
    tickers = list(holdings.keys())
    values = list(holdings.values())
    total = sum(values)
    percentages = [v / total * 100 for v in values]

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=tickers,
        values=values,
        hole=0.4,
        marker=dict(colors=LINE_COLORS[:len(tickers)]),
        textinfo="label+percent",
        textposition="outside",
        hovertemplate="<b>%{label}</b><br>Value: Rp %{value:,.0f}<br>Weight: %{percent}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(text=title, x=0.5),
        height=height,
        annotations=[dict(
            text=f"Rp {total:,.0f}",
            x=0.5, y=0.5,
            font_size=14,
            showarrow=False,
            font_color=COLORS["text"] if dark else COLORS["text_light"],
        )],
    )

    apply_theme(fig, dark=dark)
    return fig


def portfolio_dashboard(
    returns: pd.Series,
    holdings: dict[str, float],
    benchmark: Optional[pd.Series] = None,
    title: str = "Portfolio Dashboard",
    initial_capital: float = 100_000_000,
    height: int = 900,
    dark: bool = True,
) -> go.Figure:
    """Create a comprehensive portfolio dashboard with multiple panels.

    Panels:
    1. Equity curve (with optional benchmark)
    2. Drawdown chart
    3. Allocation pie
    4. Monthly returns heatmap

    Args:
        returns: Daily returns series.
        holdings: Current holdings {ticker: value}.
        benchmark: Optional benchmark returns.
        title: Dashboard title.
        initial_capital: Starting capital.
        height: Total height.
        dark: Use dark theme.

    Returns:
        Plotly Figure.
    """
    fig = make_subplots(
        rows=3,
        cols=2,
        specs=[
            [{"colspan": 2}, None],
            [{"colspan": 2}, None],
            [{"type": "domain"}, {"type": "xy"}],
        ],
        row_heights=[0.4, 0.25, 0.35],
        vertical_spacing=0.08,
        subplot_titles=["Equity Curve", "Drawdown", "Allocation", "Monthly Returns (%)"],
    )

    # 1. Equity curve
    equity = (1 + returns).cumprod() * initial_capital
    fig.add_trace(go.Scatter(
        x=equity.index, y=equity, mode="lines", name="Portfolio",
        line=dict(color=COLORS["blue"], width=2),
    ), row=1, col=1)

    if benchmark is not None:
        bench_equity = (1 + benchmark).cumprod() * initial_capital
        fig.add_trace(go.Scatter(
            x=bench_equity.index, y=bench_equity, mode="lines", name="Benchmark",
            line=dict(color=COLORS["grey"], width=1.5, dash="dash"),
        ), row=1, col=1)

    # 2. Drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max * 100
    fig.add_trace(go.Scatter(
        x=drawdown.index, y=drawdown, mode="lines", name="Drawdown",
        line=dict(color=COLORS["red"], width=1.5),
        fill="tozeroy", fillcolor="rgba(239,83,80,0.15)",
        showlegend=False,
    ), row=2, col=1)

    # 3. Allocation pie
    tickers = list(holdings.keys())
    values = list(holdings.values())
    fig.add_trace(go.Pie(
        labels=tickers, values=values, hole=0.4,
        marker=dict(colors=LINE_COLORS[:len(tickers)]),
        textinfo="label+percent", textposition="inside",
        showlegend=False,
    ), row=3, col=1)

    # 4. Monthly returns bar
    monthly = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1) * 100
    colors = [COLORS["green"] if v >= 0 else COLORS["red"] for v in monthly]
    fig.add_trace(go.Bar(
        x=monthly.index, y=monthly, marker_color=colors,
        name="Monthly %", showlegend=False,
    ), row=3, col=2)

    fig.update_layout(
        title=dict(text=title, x=0.5),
        height=height,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    apply_theme(fig, dark=dark)
    return fig
