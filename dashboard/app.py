"""
saham-indonesia Streamlit Dashboard
====================================

Multi-page dashboard for IDX stock analytics.

Run with:
    streamlit run dashboard/app.py

Pages:
    1. Market Overview — breadth, top movers, trending
    2. Screener — swing breakout/pullback/reversal, BPJS, BSJP
    3. Backtest — run strategies on historical data
    4. Portfolio — track positions and P/L
"""

from __future__ import annotations

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
    ["Market Overview", "Sinyal", "Screener", "Backtest", "Portfolio"],
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
