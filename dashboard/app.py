"""
saham-indonesia Streamlit Dashboard
====================================

Multi-page dashboard for IDX stock analytics.

Run with:
    cd saham-indonesia
    streamlit run dashboard/app.py

Pages:
    1. Market Overview — breadth, top movers, trending
    2. Sinyal — BUY/SELL signal generation
    3. Screener — swing breakout/pullback/reversal, BPJS, BSJP
    4. Backtest — run strategies on historical data
    5. Portfolio — track positions and P/L
    6. Watchlist & Fee — watchlist + broker fee calculator
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
    ["Market Overview", "Sinyal", "Screener", "Backtest", "Portfolio", "Watchlist & Fee"],
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
elif page == "Watchlist & Fee":
    from dashboard.pages import watchlist_page
    watchlist_page.render()
