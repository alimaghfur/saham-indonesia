"""Technical indicator chart builders.

Supports:
- Single indicator overlay (RSI, MACD, Bollinger, etc.)
- Multi-panel indicator dashboard
- Custom indicator combinations
"""

from __future__ import annotations

from typing import Optional, Sequence

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from saham_id.charting.styles import COLORS, LINE_COLORS, apply_theme


def indicator_chart(
    df: pd.DataFrame,
    indicator: str = "rsi",
    ticker: str = "",
    period: int = 14,
    height: int = 400,
    dark: bool = True,
) -> go.Figure:
    """Create a single indicator chart.

    Args:
        df: DataFrame with OHLCV + indicator columns.
        indicator: Indicator type ("rsi", "macd", "bollinger", "stochastic", "atr").
        ticker: Stock ticker for title.
        period: Indicator period (for calculation if not pre-computed).
        height: Chart height.
        dark: Use dark theme.

    Returns:
        Plotly Figure.
    """
    title = f"{ticker} - {indicator.upper()}" if ticker else indicator.upper()

    if indicator.lower() == "rsi":
        return _rsi_chart(df, title, period, height, dark)
    elif indicator.lower() == "macd":
        return _macd_chart(df, title, height, dark)
    elif indicator.lower() in ("bb", "bollinger"):
        return _bollinger_chart(df, title, period, height, dark)
    elif indicator.lower() == "stochastic":
        return _stochastic_chart(df, title, period, height, dark)
    elif indicator.lower() == "atr":
        return _atr_chart(df, title, period, height, dark)
    else:
        # Generic line chart for custom indicators
        return _generic_indicator(df, indicator, title, height, dark)


def multi_indicator_chart(
    df: pd.DataFrame,
    indicators: Sequence[str] = ("rsi", "macd"),
    ticker: str = "",
    height: int = 800,
    dark: bool = True,
) -> go.Figure:
    """Create a multi-panel chart with price + multiple indicators.

    Args:
        df: DataFrame with OHLCV data.
        indicators: List of indicator names to plot.
        ticker: Stock ticker for title.
        height: Total chart height.
        dark: Use dark theme.

    Returns:
        Plotly Figure with subplots.
    """
    n_panels = 1 + len(indicators)  # Price + indicators
    row_heights = [0.4] + [0.6 / len(indicators)] * len(indicators)

    fig = make_subplots(
        rows=n_panels,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=row_heights,
        subplot_titles=[f"{ticker} Price"] + [ind.upper() for ind in indicators],
    )

    # Price panel (candlestick)
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            increasing_line_color=COLORS["green"],
            decreasing_line_color=COLORS["red"],
            name="Price",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    # Indicator panels
    for i, indicator in enumerate(indicators):
        row = i + 2
        _add_indicator_panel(fig, df, indicator, row)

    fig.update_layout(
        title=dict(text=f"{ticker} Technical Analysis" if ticker else "Technical Analysis", x=0.5),
        height=height,
        xaxis_rangeslider_visible=False,
        showlegend=True,
    )

    fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
    apply_theme(fig, dark=dark)
    return fig


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def _compute_bollinger(close: pd.Series, period: int = 20, std_dev: float = 2.0):
    sma = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return upper, sma, lower


def _compute_stochastic(df: pd.DataFrame, period: int = 14):
    low_min = df["low"].rolling(window=period).min()
    high_max = df["high"].rolling(window=period).max()
    k = 100 * (df["close"] - low_min) / (high_max - low_min)
    d = k.rolling(window=3).mean()
    return k, d


def _compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def _rsi_chart(df: pd.DataFrame, title: str, period: int, height: int, dark: bool) -> go.Figure:
    rsi = _compute_rsi(df["close"], period)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=rsi, mode="lines", name=f"RSI({period})",
                             line=dict(color=COLORS["blue"], width=1.5)))

    # Overbought/Oversold zones
    fig.add_hline(y=70, line_dash="dash", line_color=COLORS["red"], opacity=0.5)
    fig.add_hline(y=30, line_dash="dash", line_color=COLORS["green"], opacity=0.5)
    fig.add_hrect(y0=70, y1=100, fillcolor=COLORS["red"], opacity=0.05)
    fig.add_hrect(y0=0, y1=30, fillcolor=COLORS["green"], opacity=0.05)

    fig.update_layout(title=dict(text=title, x=0.5), height=height,
                      yaxis=dict(range=[0, 100], title="RSI"))
    apply_theme(fig, dark=dark)
    return fig


def _macd_chart(df: pd.DataFrame, title: str, height: int, dark: bool) -> go.Figure:
    macd_line, signal_line, histogram = _compute_macd(df["close"])

    fig = go.Figure()
    # Histogram
    colors = [COLORS["green"] if v >= 0 else COLORS["red"] for v in histogram]
    fig.add_trace(go.Bar(x=df.index, y=histogram, marker_color=colors,
                         opacity=0.6, name="Histogram"))
    # MACD line
    fig.add_trace(go.Scatter(x=df.index, y=macd_line, mode="lines",
                             name="MACD", line=dict(color=COLORS["blue"], width=1.5)))
    # Signal line
    fig.add_trace(go.Scatter(x=df.index, y=signal_line, mode="lines",
                             name="Signal", line=dict(color=COLORS["orange"], width=1.5)))

    fig.update_layout(title=dict(text=title, x=0.5), height=height, yaxis_title="MACD")
    apply_theme(fig, dark=dark)
    return fig


def _bollinger_chart(df: pd.DataFrame, title: str, period: int, height: int, dark: bool) -> go.Figure:
    upper, sma, lower = _compute_bollinger(df["close"], period)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df["close"], mode="lines",
                             name="Close", line=dict(color=COLORS["blue"], width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=upper, mode="lines",
                             name="Upper BB", line=dict(color=COLORS["red"], width=1, dash="dash")))
    fig.add_trace(go.Scatter(x=df.index, y=sma, mode="lines",
                             name=f"SMA({period})", line=dict(color=COLORS["orange"], width=1)))
    fig.add_trace(go.Scatter(x=df.index, y=lower, mode="lines",
                             name="Lower BB", line=dict(color=COLORS["green"], width=1, dash="dash"),
                             fill="tonexty", fillcolor="rgba(66,165,245,0.05)"))

    fig.update_layout(title=dict(text=title, x=0.5), height=height, yaxis_title="Price (IDR)")
    apply_theme(fig, dark=dark)
    return fig


def _stochastic_chart(df: pd.DataFrame, title: str, period: int, height: int, dark: bool) -> go.Figure:
    k, d = _compute_stochastic(df, period)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=k, mode="lines", name=f"%K({period})",
                             line=dict(color=COLORS["blue"], width=1.5)))
    fig.add_trace(go.Scatter(x=df.index, y=d, mode="lines", name="%D",
                             line=dict(color=COLORS["orange"], width=1.5)))

    fig.add_hline(y=80, line_dash="dash", line_color=COLORS["red"], opacity=0.5)
    fig.add_hline(y=20, line_dash="dash", line_color=COLORS["green"], opacity=0.5)

    fig.update_layout(title=dict(text=title, x=0.5), height=height,
                      yaxis=dict(range=[0, 100], title="Stochastic"))
    apply_theme(fig, dark=dark)
    return fig


def _atr_chart(df: pd.DataFrame, title: str, period: int, height: int, dark: bool) -> go.Figure:
    atr = _compute_atr(df, period)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=atr, mode="lines", name=f"ATR({period})",
                             line=dict(color=COLORS["orange"], width=1.5),
                             fill="tozeroy", fillcolor="rgba(255,167,38,0.1)"))

    fig.update_layout(title=dict(text=title, x=0.5), height=height, yaxis_title="ATR")
    apply_theme(fig, dark=dark)
    return fig


def _generic_indicator(df: pd.DataFrame, col: str, title: str, height: int, dark: bool) -> go.Figure:
    """Plot a generic column as a line chart."""
    fig = go.Figure()
    if col in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], mode="lines",
                                 name=col, line=dict(color=COLORS["blue"], width=1.5)))
    fig.update_layout(title=dict(text=title, x=0.5), height=height, yaxis_title=col)
    apply_theme(fig, dark=dark)
    return fig


def _add_indicator_panel(fig: go.Figure, df: pd.DataFrame, indicator: str, row: int) -> None:
    """Add an indicator to an existing subplot figure."""
    if indicator.lower() == "rsi":
        rsi = _compute_rsi(df["close"])
        fig.add_trace(go.Scatter(x=df.index, y=rsi, mode="lines", name="RSI(14)",
                                 line=dict(color=COLORS["blue"], width=1.5)), row=row, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color=COLORS["red"], opacity=0.3, row=row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color=COLORS["green"], opacity=0.3, row=row, col=1)

    elif indicator.lower() == "macd":
        macd_line, signal_line, histogram = _compute_macd(df["close"])
        colors = [COLORS["green"] if v >= 0 else COLORS["red"] for v in histogram]
        fig.add_trace(go.Bar(x=df.index, y=histogram, marker_color=colors,
                             opacity=0.5, name="Hist", showlegend=False), row=row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=macd_line, mode="lines", name="MACD",
                                 line=dict(color=COLORS["blue"], width=1.2)), row=row, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=signal_line, mode="lines", name="Signal",
                                 line=dict(color=COLORS["orange"], width=1.2)), row=row, col=1)

    elif indicator.lower() == "volume":
        if "volume" in df.columns:
            colors = [COLORS["green"] if c >= o else COLORS["red"]
                      for c, o in zip(df["close"], df["open"])]
            fig.add_trace(go.Bar(x=df.index, y=df["volume"], marker_color=colors,
                                 opacity=0.6, name="Vol", showlegend=False), row=row, col=1)

    elif indicator.lower() == "atr":
        atr = _compute_atr(df)
        fig.add_trace(go.Scatter(x=df.index, y=atr, mode="lines", name="ATR(14)",
                                 line=dict(color=COLORS["orange"], width=1.2)), row=row, col=1)
