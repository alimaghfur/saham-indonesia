"""Project Dashboard — Modern overview page inspired by Panze Studio design.

Uses Streamlit native components properly with targeted CSS enhancements
for a clean, card-based modern dashboard look.
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def render() -> None:
    """Render the modern Project Dashboard."""

    # --- Custom CSS ---
    st.markdown(_get_custom_css(), unsafe_allow_html=True)

    # --- Header Section ---
    header_left, header_right = st.columns([3, 2])
    with header_left:
        st.caption("Manage and track your investments")
        st.markdown("## Investment Dashboard")
    with header_right:
        time_filter = st.radio(
            "Period",
            ["Today", "This Week", "This Month", "Reports"],
            horizontal=True,
            index=2,
            label_visibility="collapsed",
        )

    st.divider()

    # === ROW 1: Tasks | Portfolio Overview | Profit vs Loss ===
    col_tasks, col_overview, col_pnl = st.columns([1, 1.2, 1.5])

    with col_tasks:
        _render_my_tasks()

    with col_overview:
        _render_portfolio_overview()

    with col_pnl:
        _render_profit_vs_loss()

    st.divider()

    # === ROW 2: Stock Performance | Alerts & Tickets ===
    col_perf, col_side = st.columns([2.5, 1])

    with col_perf:
        _render_stock_performance()

    with col_side:
        _render_my_alerts()
        st.markdown("")
        _render_open_tickets()


def _render_my_tasks() -> None:
    """My Tasks card — watchlist actions pending."""
    st.markdown("#### My Tasks")

    tasks = [
        {"icon": "📈", "title": "BBCA — Review Entry", "desc": "Score 78/100, R:R 2.5:1", "status": "urgent"},
        {"icon": "🔍", "title": "TLKM — Monitor Support", "desc": "Mendekati support Rp 3,450", "status": "warning"},
        {"icon": "⚠️", "title": "ASII — Check Stop Loss", "desc": "Mendekati SL di Rp 4,800", "status": "danger"},
        {"icon": "💰", "title": "BMRI — Take Profit T1", "desc": "Sudah mencapai target 1", "status": "success"},
        {"icon": "📊", "title": "UNVR — Rebalance", "desc": "Alokasi > 25% portfolio", "status": "info"},
    ]

    for task in tasks:
        with st.container():
            st.markdown(
                f"""<div class="dash-task-item">
                    <span class="dash-task-icon">{task['icon']}</span>
                    <div>
                        <strong>{task['title']}</strong><br>
                        <small style="color:#888">{task['desc']}</small>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown(
        f"""<div class="dash-task-badge">
            <span class="dash-badge-num">{len(tasks)}</span> On Going Tasks
        </div>""",
        unsafe_allow_html=True,
    )


def _render_portfolio_overview() -> None:
    """Portfolio Overview — donut chart."""
    st.markdown("#### Portfolio Overview")

    import plotly.graph_objects as go

    labels = ["Profit", "Loss", "Holding"]
    values = [32, 14, 54]
    colors = ["#4CAF50", "#FF9800", "#E0E0E0"]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.7,
        marker=dict(colors=colors, line=dict(width=0)),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>%{value} stocks<br>%{percent}<extra></extra>",
    )])

    fig.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=220,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b>{sum(values)}</b><br><span style='font-size:11px'>Stocks</span>",
            x=0.5, y=0.5,
            font_size=20,
            showarrow=False,
            font=dict(color="#333"),
        )],
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Legend
    leg1, leg2, leg3 = st.columns(3)
    leg1.markdown(f"<span style='color:#FF9800'>&#9679;</span> Loss: **{values[1]}**", unsafe_allow_html=True)
    leg2.markdown(f"<span style='color:#4CAF50'>&#9679;</span> Profit: **{values[0]}**", unsafe_allow_html=True)
    leg3.markdown(f"<span style='color:#bbb'>&#9679;</span> Hold: **{values[2]}**", unsafe_allow_html=True)


def _render_profit_vs_loss() -> None:
    """Profit vs Loss line chart."""
    st.markdown("#### Profit VS Loss")

    import plotly.graph_objects as go

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
    profit = [18.5, 22.3, 19.8, 25.1, 28.6, 24.6, 30.2]
    loss = [8.2, 12.1, 9.5, 14.3, 11.8, 13.3, 10.5]

    fig = go.Figure()

    # Profit area
    fig.add_trace(go.Scatter(
        x=months, y=profit,
        mode="lines",
        name="Profit",
        line=dict(color="#4CAF50", width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(76, 175, 80, 0.08)",
    ))

    # Loss line
    fig.add_trace(go.Scatter(
        x=months, y=loss,
        mode="lines",
        name="Loss",
        line=dict(color="#FF9800", width=2, dash="dot", shape="spline"),
    ))

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=1.12, xanchor="center", x=0.5, font=dict(size=10)),
        margin=dict(l=0, r=0, t=25, b=0),
        height=220,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10)),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)", showline=False, tickfont=dict(size=10)),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Summary
    m1, m2 = st.columns(2)
    m1.markdown("<span style='color:#4CAF50; font-size:0.85em'>&#9679; Profit: **Rp 24,6 jt**</span>", unsafe_allow_html=True)
    m2.markdown("<span style='color:#FF9800; font-size:0.85em'>&#9679; Loss: **Rp 13,3 jt**</span>", unsafe_allow_html=True)


def _render_stock_performance() -> None:
    """Stock Performance — progress bars like Invoice Overview."""
    st.markdown("#### Stock Performance")

    stocks = [
        {"name": "Strong Buy", "count": 5, "value": "Rp 183 jt", "pct": 90, "color": "#4CAF50"},
        {"name": "Buy", "count": 8, "value": "Rp 245 jt", "pct": 75, "color": "#8BC34A"},
        {"name": "Hold", "count": 12, "value": "Rp 320 jt", "pct": 60, "color": "#2196F3"},
        {"name": "Watch", "count": 5, "value": "Rp 95 jt", "pct": 35, "color": "#FF9800"},
        {"name": "Avoid", "count": 3, "value": "Rp 45 jt", "pct": 15, "color": "#f44336"},
    ]

    for stock in stocks:
        c1, c2, c3, c4 = st.columns([1.2, 0.4, 1, 3])
        with c1:
            st.markdown(f"**{stock['name']}**")
        with c2:
            st.caption(f"{stock['count']}")
        with c3:
            st.caption(stock['value'])
        with c4:
            st.markdown(
                f"""<div style="background:#f0f0f0; border-radius:6px; height:12px; margin-top:8px; overflow:hidden;">
                    <div style="width:{stock['pct']}%; background:{stock['color']}; height:100%; border-radius:6px; transition: width 0.5s;"></div>
                </div>""",
                unsafe_allow_html=True,
            )


def _render_my_alerts() -> None:
    """My Alerts section."""
    st.markdown("#### My Alerts")

    alerts = [
        {"title": "BBCA Breakout", "time": "09:15", "type": "Signal"},
        {"title": "TLKM Support Hit", "time": "10:30", "type": "Alert"},
        {"title": "Portfolio Review", "time": "14:00", "type": "Task"},
    ]

    for alert in alerts:
        st.markdown(
            f"""<div class="dash-alert-card">
                <div>
                    <small style="color:#aaa">Alert</small><br>
                    <strong style="font-size:0.9em">{alert['title']}</strong>
                </div>
                <div style="text-align:right">
                    <strong style="font-size:0.85em">{alert['time']}</strong><br>
                    <small style="color:#888">{alert['type']}</small>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.caption("See All Alerts >")


def _render_open_tickets() -> None:
    """Open Tickets — watchlist items needing attention."""
    st.markdown("#### Open Tickets")

    tickets = [
        {"name": "BBCA", "msg": "Entry score 78, mendekati buy zone.", "avatar": "🏦"},
        {"name": "TLKM", "msg": "3 hari di support, perlu konfirmasi.", "avatar": "📡"},
        {"name": "ASII", "msg": "Breakdown MA50, review cut loss.", "avatar": "🚗"},
    ]

    for ticket in tickets:
        st.markdown(
            f"""<div class="dash-ticket-card">
                <span style="font-size:1.5em">{ticket['avatar']}</span>
                <div style="flex:1">
                    <strong>{ticket['name']}</strong>
                    <br><small style="color:#888">{ticket['msg']}</small>
                </div>
                <small style="color:#aaa; cursor:pointer">Check ></small>
            </div>""",
            unsafe_allow_html=True,
        )


def _get_custom_css() -> str:
    """Targeted CSS that works with Streamlit's DOM structure."""
    return """
    <style>
    /* Page background */
    .stApp {
        background: linear-gradient(135deg, #fdf6ee 0%, #f8f9ff 50%, #f0f4ff 100%);
    }

    /* Remove default padding */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }

    /* Task items */
    .dash-task-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 12px;
        background: white;
        border-radius: 12px;
        margin-bottom: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #f0f0f0;
    }
    .dash-task-icon {
        font-size: 1.3em;
    }
    .dash-task-badge {
        display: inline-block;
        margin-top: 10px;
        padding: 6px 14px;
        background: #f8f9fa;
        border-radius: 20px;
        font-size: 0.85em;
        color: #555;
        border: 1px solid #eee;
    }
    .dash-badge-num {
        background: #1a1a2e;
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.85em;
        margin-right: 6px;
    }

    /* Alert cards */
    .dash-alert-card {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 14px;
        background: white;
        border-radius: 12px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #f0f0f0;
    }

    /* Ticket cards */
    .dash-ticket-card {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 14px;
        background: white;
        border-radius: 12px;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #f0f0f0;
    }

    /* Metrics - make them more compact */
    [data-testid="stMetric"] {
        background: white;
        padding: 12px 16px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #f0f0f0;
    }

    /* Hide hamburger menu & footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
