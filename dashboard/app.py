"""
Saham Indonesia — Professional IDX Analytics Dashboard
======================================================

Run:  streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))
if str(_project_root / "src") not in sys.path:
    sys.path.insert(0, str(_project_root / "src"))

import streamlit as st

st.set_page_config(
    page_title="Saham Indonesia",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Inject global professional CSS ---
from dashboard.styles import inject_global_css
st.markdown(inject_global_css(), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    # Logo / Brand
    st.markdown(
        """
        <div style="padding: 16px 0 24px 0;">
            <div style="font-size: 1.2em; font-weight: 700; color: #f1f5f9; letter-spacing: -0.3px;">
                Saham Indonesia
            </div>
            <div style="font-size: 0.7em; color: #64748b; margin-top: 4px; letter-spacing: 1px; text-transform: uppercase;">
                IDX Analytics Platform
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation — grouped sections
    PAGES = [
        ("Investment Advisor", "Investment Advisor"),
        ("Market Overview", "Market Overview"),
        ("Real-time", "Real-time"),
        ("Heatmap", "Heatmap"),
        ("Technical Chart", "Technical Chart"),
        ("Compare", "Compare"),
        ("Score Card", "Score Card"),
        ("Bandarmology", "Bandarmology"),
        ("Sinyal", "Sinyal"),
        ("Screener", "Screener"),
        ("Backtest", "Backtest"),
        ("Portfolio", "Portfolio"),
        ("Watchlist & Fee", "Watchlist & Fee"),
    ]

    page_labels = [p[0] for p in PAGES]

    # Section: Analysis
    st.markdown(
        '<p style="font-size:0.7em; color:#475569; text-transform:uppercase; letter-spacing:1px; margin:12px 0 4px 0; font-weight:600;">Analysis</p>',
        unsafe_allow_html=True,
    )
    selected_idx = None
    analysis_pages = page_labels[:4]
    for i, label in enumerate(analysis_pages):
        if st.button(label, key=f"nav_{i}", use_container_width=True, type="secondary"):
            selected_idx = i

    # Section: Charts
    st.markdown(
        '<p style="font-size:0.7em; color:#475569; text-transform:uppercase; letter-spacing:1px; margin:16px 0 4px 0; font-weight:600;">Charts</p>',
        unsafe_allow_html=True,
    )
    chart_pages = page_labels[4:7]
    for i, label in enumerate(chart_pages, start=4):
        if st.button(label, key=f"nav_{i}", use_container_width=True, type="secondary"):
            selected_idx = i

    # Section: Signals & Screening
    st.markdown(
        '<p style="font-size:0.7em; color:#475569; text-transform:uppercase; letter-spacing:1px; margin:16px 0 4px 0; font-weight:600;">Signals & Screening</p>',
        unsafe_allow_html=True,
    )
    signal_pages = page_labels[7:11]
    for i, label in enumerate(signal_pages, start=7):
        if st.button(label, key=f"nav_{i}", use_container_width=True, type="secondary"):
            selected_idx = i

    # Section: Portfolio
    st.markdown(
        '<p style="font-size:0.7em; color:#475569; text-transform:uppercase; letter-spacing:1px; margin:16px 0 4px 0; font-weight:600;">Portfolio</p>',
        unsafe_allow_html=True,
    )
    portfolio_pages = page_labels[11:]
    for i, label in enumerate(portfolio_pages, start=11):
        if st.button(label, key=f"nav_{i}", use_container_width=True, type="secondary"):
            selected_idx = i

    # Handle navigation state
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0

    if selected_idx is not None:
        st.session_state.current_page = selected_idx
        st.rerun()

    # Footer
    st.markdown("<div style='height:40px'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size:0.7em; color:#475569; padding:12px 0; border-top:1px solid #2a3040;">
            <div>Data: yfinance (delayed 15m)</div>
            <div style="margin-top:4px;">
                <a href="https://github.com/alimaghfur/saham-indonesia" style="color:#60a5fa; text-decoration:none;">GitHub</a>
                &middot; v0.1.0
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Get current page
selected_page = PAGES[st.session_state.current_page][1]


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARE PAGE (inline)
# ═══════════════════════════════════════════════════════════════════════════════

def _render_compare_page():
    st.markdown("## 📈 Stock Comparison")
    st.caption("Bandingkan performa 2-5 saham (rebased to 100)")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        tickers_input = st.text_input("Tickers", value="BBCA, BBRI, BMRI", label_visibility="collapsed", placeholder="BBCA, BBRI, BMRI")
    with col2:
        period = st.selectbox("Period", ["3mo", "6mo", "1y", "2y"], index=1, label_visibility="collapsed")
    with col3:
        run_compare = st.button("Compare", type="primary", use_container_width=True)

    if run_compare:
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

            st.subheader("Performance Summary")
            rows = []
            for ticker, df in dataframes.items():
                first = df["close"].iloc[0]
                last = df["close"].iloc[-1]
                ret = (last - first) / first * 100 if first else 0
                rows.append({"Ticker": ticker, "Start": f"Rp {first:,.0f}", "End": f"Rp {last:,.0f}", "Return": f"{ret:+.2f}%"})
            import pandas as pd
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE ROUTING
# ═══════════════════════════════════════════════════════════════════════════════

if selected_page == "Investment Advisor":
    from dashboard.pages import invest_page
    invest_page.render()
elif selected_page == "Market Overview":
    from dashboard.pages import overview
    overview.render()
elif selected_page == "Real-time":
    from dashboard.pages import realtime
    realtime.render()
elif selected_page == "Heatmap":
    from dashboard.pages import heatmap_page
    heatmap_page.render()
elif selected_page == "Technical Chart":
    from dashboard.pages import chart
    chart.render()
elif selected_page == "Compare":
    _render_compare_page()
elif selected_page == "Score Card":
    from dashboard.pages import scorecard_page
    scorecard_page.render()
elif selected_page == "Bandarmology":
    from dashboard.pages import bandarmology_page
    bandarmology_page.render()
elif selected_page == "Sinyal":
    from dashboard.pages import signals
    signals.render()
elif selected_page == "Screener":
    from dashboard.pages import screener
    screener.render()
elif selected_page == "Backtest":
    from dashboard.pages import backtest
    backtest.render()
elif selected_page == "Portfolio":
    from dashboard.pages import portfolio
    portfolio.render()
elif selected_page == "Watchlist & Fee":
    from dashboard.pages import watchlist_page
    watchlist_page.render()
