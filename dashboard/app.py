"""Streamlit dashboard for saham-indonesia.

Run:
    pip install -e ".[dashboard]"
    streamlit run dashboard/app.py

Tabs:
    Overview   — pick a universe + data source, see market breadth
    Movers     — Top Gainers / Losers / Most Active
    Trending   — composite trending detector + unusual activity
    Screeners  — BPJS / BSJP / Swing / Scalping
    Quote      — single-ticker drill-down with chart
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from saham_id.analysis.indicators import bollinger_bands, ema, rsi, sma
from saham_id.data.sources import get_source, list_sources
from saham_id.data.universe import list_universes
from saham_id.market import breadth, movers, trending, unusual_activity
from saham_id.screener.intraday import bpjs, bsjp, scalping
from saham_id.screener.swing import breakout, pullback, reversal
from saham_id.utils.formatting import format_large, format_pct, format_rupiah


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="saham-indonesia",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Cached data access — reduces latency when users flip tabs
# ---------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def _cached_source(source_name: str):
    return get_source(source_name)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_top_gainers(source_name: str, universe: str, period: str, top: int):
    src = _cached_source(source_name)
    return movers.top_gainers(universe=universe, period=period, top_n=top, source=src)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_top_losers(source_name: str, universe: str, period: str, top: int):
    src = _cached_source(source_name)
    return movers.top_losers(universe=universe, period=period, top_n=top, source=src)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_most_active(source_name: str, universe: str, by: str, top: int):
    src = _cached_source(source_name)
    return movers.most_active(universe=universe, by=by, top_n=top, source=src)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_trending(source_name: str, universe: str, timeframe: str, top: int):
    src = _cached_source(source_name)
    return trending.detect(
        universe=universe, timeframe=timeframe, top_n=top, source=src
    ).to_dataframe()


@st.cache_data(ttl=300, show_spinner=False)
def _cached_unusual(source_name: str, universe: str, top: int):
    src = _cached_source(source_name)
    return unusual_activity.detect(universe=universe, top_n=top, source=src).to_dataframe()


@st.cache_data(ttl=600, show_spinner=False)
def _cached_breadth(source_name: str, universe: str):
    src = _cached_source(source_name)
    return breadth.snapshot(universe=universe, source=src)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_ohlc(source_name: str, ticker: str, period: str, interval: str):
    src = _cached_source(source_name)
    return src.get_ohlc(ticker, period=period, interval=interval)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _movers_to_df(movers_list) -> pd.DataFrame:
    if not movers_list:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "Ticker": m.ticker,
                "Last": float(m.last),
                "Change %": float(m.change_pct),
                "Volume": int(m.volume),
                "Value (Rp)": float(m.value),
            }
            for m in movers_list
        ]
    )


def _style_movers_df(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    display = df.copy()
    display["Last"] = display["Last"].map(lambda v: format_rupiah(v))
    display["Change %"] = display["Change %"].map(lambda v: format_pct(v))
    display["Volume"] = display["Volume"].map(lambda v: f"{v:,}")
    display["Value (Rp)"] = display["Value (Rp)"].map(lambda v: format_large(v))
    return display


def _candlestick_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    close = df["close"]
    ma20 = sma(close, 20)
    ma50 = sma(close, 50)
    ema20 = ema(close, 20)

    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=ticker,
        )
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=ma20, name="MA20", line=dict(color="#ff9800", width=1.2))
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=ma50, name="MA50", line=dict(color="#2196f3", width=1.2))
    )
    fig.add_trace(
        go.Scatter(x=df.index, y=ema20, name="EMA20", line=dict(color="#9c27b0", width=1, dash="dot"))
    )
    fig.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def _rsi_chart(df: pd.DataFrame) -> go.Figure:
    rsi_series = rsi(df["close"], 14)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=rsi_series, name="RSI(14)", line=dict(color="#4caf50")))
    fig.add_hline(y=70, line_dash="dot", line_color="red")
    fig.add_hline(y=30, line_dash="dot", line_color="green")
    fig.update_layout(
        height=200, margin=dict(l=10, r=10, t=10, b=10),
        yaxis=dict(range=[0, 100]),
    )
    return fig


def _render_screener_result(result) -> None:
    if not result.rows:
        st.info("No matches for the current filters. Try relaxing thresholds.")
        return
    df = result.to_dataframe()
    st.dataframe(df, use_container_width=True, hide_index=True)
    with st.expander("Parameters"):
        st.json(result.params)


# ---------------------------------------------------------------------------
# Sidebar — global controls
# ---------------------------------------------------------------------------
st.sidebar.title("📈 saham-indonesia")
st.sidebar.caption("IDX analytics & screener toolkit")

available_sources = list_sources()
default_idx = available_sources.index("yahoo") if "yahoo" in available_sources else 0
source_name = st.sidebar.selectbox(
    "Data source",
    available_sources,
    index=default_idx,
    help="yfinance is free & default. Others need API keys in `.env`.",
)
universe = st.sidebar.selectbox("Universe", list(list_universes()), index=1)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data is delayed unless you use a realtime source (iTick, Sectors, etc). "
    "For educational use only — not investment advice."
)


# ---------------------------------------------------------------------------
# Main — tabs
# ---------------------------------------------------------------------------
st.title(f"Dashboard — {universe}")
st.caption(f"Source: **{source_name}** · Last refreshed {datetime.now():%Y-%m-%d %H:%M}")

tab_overview, tab_movers, tab_trending, tab_screeners, tab_quote = st.tabs(
    ["Overview", "Movers", "Trending", "Screeners", "Quote"]
)


# ------------------- Overview -------------------
with tab_overview:
    st.subheader("Market Breadth")
    with st.spinner("Computing breadth..."):
        try:
            snap = _cached_breadth(source_name, universe)
        except Exception as exc:
            st.error(f"Failed to compute breadth: {exc}")
            snap = None

    if snap is not None:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Advancers", snap.advancers)
        c2.metric("Decliners", snap.decliners)
        c3.metric("A/D Ratio", f"{snap.ad_ratio:.2f}")
        c4.metric("Advancing %", format_pct(snap.advancing_pct - 0.5))  # delta vs 50/50

        c5, c6, c7 = st.columns(3)
        c5.metric("Unchanged", snap.unchanged)
        c6.metric("New Highs (52w)", snap.new_highs_52w)
        c7.metric("New Lows (52w)", snap.new_lows_52w)

    st.markdown("---")
    st.markdown(
        "Tips:\n\n"
        "- **A/D > 1.5** suggests broad strength; **< 0.7** suggests broad weakness.\n"
        "- Many **new 52-week highs** with rising breadth = healthy uptrend.\n"
        "- Many **new 52-week lows** during a rally = warning sign (internal weakness)."
    )


# ------------------- Movers -------------------
with tab_movers:
    c1, c2, c3 = st.columns([1, 1, 1])
    period = c1.selectbox("Period", ["1D", "1W", "1M", "3M", "YTD"], index=0)
    top = c2.slider("Top N", 5, 50, 10)
    mover_kind = c3.radio("Kind", ["Gainers", "Losers", "Most Active"], horizontal=True)

    with st.spinner("Loading movers..."):
        if mover_kind == "Gainers":
            data = _cached_top_gainers(source_name, universe, period, top)
        elif mover_kind == "Losers":
            data = _cached_top_losers(source_name, universe, period, top)
        else:
            data = _cached_most_active(source_name, universe, "value", top)

    raw_df = _movers_to_df(data)
    if raw_df.empty:
        st.info("No data returned. Try a larger universe or different period.")
    else:
        st.dataframe(_style_movers_df(raw_df), use_container_width=True, hide_index=True)
        with st.expander("Raw numeric data"):
            st.dataframe(raw_df, use_container_width=True, hide_index=True)


# ------------------- Trending -------------------
with tab_trending:
    c1, c2 = st.columns([1, 1])
    timeframe = c1.selectbox("Timeframe", ["1D", "1W", "1M"], index=0)
    trending_top = c2.slider("Top N (trending)", 5, 50, 20, key="trending_top")

    st.subheader("Trending stocks (rvol + momentum + breakout)")
    with st.spinner("Detecting trending..."):
        trending_df = _cached_trending(source_name, universe, timeframe, trending_top)
    if trending_df.empty:
        st.info("No trending candidates right now.")
    else:
        st.dataframe(trending_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Unusual activity (volume / price anomalies)")
    unusual_top = st.slider("Top N (unusual)", 5, 50, 20, key="unusual_top")
    with st.spinner("Detecting anomalies..."):
        unusual_df = _cached_unusual(source_name, universe, unusual_top)
    if unusual_df.empty:
        st.info("Nothing anomalous today.")
    else:
        st.dataframe(unusual_df, use_container_width=True, hide_index=True)


# ------------------- Screeners -------------------
with tab_screeners:
    screener = st.selectbox(
        "Strategy",
        [
            "BPJS (Beli Pagi Jual Sore)",
            "BSJP (Beli Sore Jual Pagi)",
            "Swing — Breakout",
            "Swing — Pullback",
            "Swing — Reversal",
            "Scalping (intraday)",
        ],
    )
    src = _cached_source(source_name)

    if screener.startswith("BPJS"):
        c1, c2, c3 = st.columns(3)
        lookback = c1.slider("Lookback days", 20, 180, 60)
        min_win = c2.slider("Min win rate", 0.0, 1.0, 0.55, 0.01)
        top_s = c3.slider("Top N", 5, 30, 10, key="bpjs_top")
        if st.button("Run BPJS screener"):
            with st.spinner("Screening..."):
                result = bpjs.screen(
                    universe=universe, lookback_days=lookback,
                    min_win_rate=min_win, top_n=top_s, source=src,
                )
            _render_screener_result(result)

    elif screener.startswith("BSJP"):
        c1, c2, c3 = st.columns(3)
        lookback = c1.slider("Lookback days", 20, 180, 60, key="bsjp_lb")
        min_gap = c2.slider("Min gap-up rate", 0.0, 1.0, 0.55, 0.01)
        top_s = c3.slider("Top N", 5, 30, 10, key="bsjp_top")
        if st.button("Run BSJP screener"):
            with st.spinner("Screening..."):
                result = bsjp.screen(
                    universe=universe, lookback_days=lookback,
                    min_gap_up_rate=min_gap, top_n=top_s, source=src,
                )
            _render_screener_result(result)

    elif screener == "Swing — Breakout":
        c1, c2, c3 = st.columns(3)
        win = c1.slider("Resistance window (days)", 10, 60, 20)
        rvol_min = c2.slider("Min RVOL", 1.0, 5.0, 1.5, 0.1)
        top_s = c3.slider("Top N", 5, 40, 20, key="brk_top")
        if st.button("Run breakout screener"):
            with st.spinner("Screening..."):
                result = breakout.screen(
                    universe=universe, resistance_window=win,
                    min_rvol=rvol_min, top_n=top_s, source=src,
                )
            _render_screener_result(result)

    elif screener == "Swing — Pullback":
        c1, c2, c3 = st.columns(3)
        trend_ma = c1.slider("Trend MA", 20, 200, 50, step=10)
        pull_ma = c2.slider("Pullback MA", 5, 50, 20)
        top_s = c3.slider("Top N", 5, 30, 15, key="pull_top")
        if st.button("Run pullback screener"):
            with st.spinner("Screening..."):
                result = pullback.screen(
                    universe=universe, trend_ma=trend_ma,
                    pullback_ma=pull_ma, top_n=top_s, source=src,
                )
            _render_screener_result(result)

    elif screener == "Swing — Reversal":
        c1, c2 = st.columns(2)
        rsi_os = c1.slider("RSI oversold threshold", 10.0, 40.0, 30.0)
        top_s = c2.slider("Top N", 5, 30, 15, key="rev_top")
        if st.button("Run reversal screener"):
            with st.spinner("Screening..."):
                result = reversal.screen(
                    universe=universe, rsi_oversold=rsi_os,
                    top_n=top_s, source=src,
                )
            _render_screener_result(result)

    else:  # Scalping
        st.warning(
            "Scalping needs intraday bars. yfinance gives 1-minute bars for the "
            "last ~7 days only; for production use iTick or a paid provider."
        )
        c1, c2, c3 = st.columns(3)
        interval = c1.selectbox("Interval", ["1m", "5m"], index=1)
        min_rvol_s = c2.slider("Min RVOL", 1.0, 5.0, 1.2, 0.1, key="scalp_rvol")
        top_s = c3.slider("Top N", 5, 30, 10, key="scalp_top")
        if st.button("Run scalping screener"):
            with st.spinner("Screening (may be slow for large universes)..."):
                try:
                    result = scalping.screen(
                        universe=universe, interval=interval,
                        min_rvol=min_rvol_s, top_n=top_s, source=src,
                    )
                    _render_screener_result(result)
                except Exception as exc:
                    st.error(f"Scalping screen failed: {exc}")


# ------------------- Quote -------------------
with tab_quote:
    c1, c2, c3 = st.columns([2, 1, 1])
    ticker = c1.text_input("Ticker (e.g. BBCA)", value="BBCA")
    period = c2.selectbox("Period", ["3mo", "6mo", "1y", "2y", "5y", "ytd", "max"], index=2)
    interval = c3.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)

    if ticker:
        with st.spinner(f"Loading {ticker.upper()}..."):
            try:
                df = _cached_ohlc(source_name, ticker.upper(), period, interval)
                src = _cached_source(source_name)
                quote = src.get_quote(ticker.upper())
            except Exception as exc:
                st.error(f"Failed to load data: {exc}")
                df = pd.DataFrame()
                quote = None

        if quote is not None:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Last", format_rupiah(quote.last))
            if quote.change_pct is not None:
                col2.metric("Change", format_pct(quote.change_pct))
            col3.metric(
                "Volume",
                f"{quote.volume:,}" if quote.volume else "—",
            )
            col4.metric("Delay", f"{quote.delayed_minutes} min")

        if not df.empty:
            st.plotly_chart(_candlestick_chart(df, ticker.upper()), use_container_width=True)
            st.plotly_chart(_rsi_chart(df), use_container_width=True)

            with st.expander("Bollinger Bands"):
                bb = bollinger_bands(df["close"], 20, 2.0)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df.index, y=df["close"], name="Close"))
                fig.add_trace(go.Scatter(x=df.index, y=bb["upper"], name="Upper", line=dict(dash="dot")))
                fig.add_trace(go.Scatter(x=df.index, y=bb["lower"], name="Lower", line=dict(dash="dot")))
                fig.add_trace(go.Scatter(x=df.index, y=bb["middle"], name="Middle"))
                fig.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig, use_container_width=True)

            with st.expander("Raw OHLC data (last 60 rows)"):
                st.dataframe(df.tail(60), use_container_width=True)
