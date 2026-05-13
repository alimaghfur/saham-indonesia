"""
saham-indonesia Streamlit Dashboard
====================================

Multi-page dashboard for IDX stock analytics.

Run with:
    cd saham-indonesia
    streamlit run dashboard/app.py

Pages:
    1. Market Overview — breadth, top movers, trending + quick chart
    2. Technical Chart — full interactive candlestick & indicator analysis
    3. Sinyal — BUY/SELL signal generation
    4. Screener — swing breakout/pullback/reversal, BPJS, BSJP
    5. Backtest — run strategies on historical data
    6. Portfolio — track positions, P/L, equity curve, drawdown
    7. Watchlist & Fee — watchlist + broker fee calculator
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so imports work regardless of CWD
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

import streamlit as st

st.set_page_config(
    page_title="Saham Indonesia",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar navigation ---
st.sidebar.title("Saham Indonesia")
st.sidebar.markdown("**IDX Analytics & Screener**")

page = st.sidebar.radio(
    "Navigasi",
    ["Market Overview", "Real-time", "Heatmap", "Technical Chart", "Compare", "Score Card", "Bandarmology", "Sinyal", "Screener", "Backtest", "Portfolio", "Watchlist & Fee"],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "Data: [yfinance](https://pypi.org/project/yfinance/) (delayed 15m)"
)
st.sidebar.markdown(
    "[GitHub](https://github.com/alimaghfur/saham-indonesia)"
)

# --- Route to pages ---
if page == "Market Overview":
    from dashboard.pages import overview
    overview.render()
elif page == "Real-time":
    from dashboard.pages import realtime
    realtime.render()
elif page == "Heatmap":
    from dashboard.pages import heatmap_page
    heatmap_page.render()
elif page == "Technical Chart":
    from dashboard.pages import chart
    chart.render()
elif page == "Compare":
    _render_compare_page()
elif page == "Score Card":
    from dashboard.pages import scorecard_page
    scorecard_page.render()
elif page == "Bandarmology":
    from dashboard.pages import bandarmology_page
    bandarmology_page.render()
elif page == "Sinyal":
    from dashboard.pages import signals
    signals.render()
elif page == "Screener":
    from dashboard.pages import screener
    screener.render()
elif page == "Backtest":
    from dashboard.pages import backtest
    backtest.render()
elif page == "Portfolio":
    from dashboard.pages import portfolio
    portfolio.render()
elif page == "Watchlist & Fee":
    from dashboard.pages import watchlist_page
    watchlist_page.render()


def _render_compare_page():
    """Inline comparison page."""
    st.title("Stock Comparison")
    st.markdown("Bandingkan performa 2-5 saham (rebased to 100).")

    tickers_input = st.text_input("Tickers (comma-separated)", value="BBCA, BBRI, BMRI")
    period = st.selectbox("Period", ["3mo", "6mo", "1y", "2y"], index=1)

    if st.button("Compare", type="primary"):
        try:
            from saham_id.data.sources import get_source
            from saham_id.charting.comparison import comparison_chart, drawdown_comparison

            ticker_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
            if len(ticker_list) < 2:
                st.warning("Masukkan minimal 2 ticker.")
                return

            src = get_source()
            dataframes = {}
            with st.spinner("Fetching data..."):
                for ticker in ticker_list:
                    try:
                        df = src.get_ohlc(ticker, period=period, interval="1d")
                        if not df.empty:
                            dataframes[ticker] = df
                    except Exception:
                        pass

            if len(dataframes) < 2:
                st.error("Tidak cukup data.")
                return

            fig = comparison_chart(dataframes, title=f"Comparison: {', '.join(dataframes.keys())}")
            st.plotly_chart(fig, use_container_width=True)

            fig_dd = drawdown_comparison(dataframes)
            st.plotly_chart(fig_dd, use_container_width=True)

            # Summary table
            st.subheader("Performance Summary")
            rows = []
            for ticker, df in dataframes.items():
                first = df["close"].iloc[0]
                last = df["close"].iloc[-1]
                ret = (last - first) / first * 100 if first else 0
                rows.append({"Ticker": ticker, "Start": f"Rp {first:,.0f}", "End": f"Rp {last:,.0f}", "Return": f"{ret:+.2f}%"})
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")
