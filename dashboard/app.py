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
    page_icon="📈",
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
        <div style="text-align:center; padding: 10px 0 20px 0;">
            <div style="font-size: 2em;">📈</div>
            <div style="font-size: 1.3em; font-weight: 700; color: #f1f5f9; margin-top: 4px;">
                Saham Indonesia
            </div>
            <div style="font-size: 0.75em; color: #64748b; margin-top: 2px;">
                IDX Analytics Platform
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Navigation with icons
    PAGES = {
        "💡 Investment Advisor": "Investment Advisor",
        "🌐 Market Overview": "Market Overview",
        "⚡ Real-time": "Real-time",
        "🗺️ Heatmap": "Heatmap",
        "📊 Technical Chart": "Technical Chart",
        "📈 Compare": "Compare",
        "🏆 Score Card": "Score Card",
        "🎯 Bandarmology": "Bandarmology",
        "🔔 Sinyal": "Sinyal",
        "🔍 Screener": "Screener",
        "🧪 Backtest": "Backtest",
        "💼 Portfolio": "Portfolio",
        "⭐ Watchlist & Fee": "Watchlist & Fee",
    }

    page = st.radio(
        "Menu",
        list(PAGES.keys()),
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Footer info
    st.markdown(
        """
        <div style="padding: 10px 0; font-size: 0.75em; color: #64748b; text-align: center;">
            <div>Data: <a href="https://pypi.org/project/yfinance/" style="color:#60a5fa; text-decoration:none;">yfinance</a> (delayed 15m)</div>
            <div style="margin-top: 6px;">
                <a href="https://github.com/alimaghfur/saham-indonesia" style="color:#60a5fa; text-decoration:none;">
                    GitHub Repository
                </a>
            </div>
            <div style="margin-top: 8px; color: #475569;">v0.1.0</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Get the actual page name
selected_page = PAGES[page]


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
