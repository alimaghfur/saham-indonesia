"""Project Dashboard — Modern overview page inspired by Panze Studio design.

Displays:
- Time filter tabs (Today, This Week, This Month)
- My Tasks (watchlist actions)
- Portfolio Overview (donut chart)
- Profit vs Loss (line chart)
- My Alerts (upcoming signals)
- Stock Performance (progress bars)
- Open Tickets (watchlist items needing attention)
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def render() -> None:
    """Render the modern Project Dashboard."""

    # --- Custom CSS for modern look ---
    st.markdown(_get_custom_css(), unsafe_allow_html=True)

    # --- Header ---
    st.markdown(
        """
        <div class="dashboard-header">
            <div>
                <p class="subtitle">Manage and track your investments</p>
                <h1 class="main-title">Investment Dashboard</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Time Filter Tabs ---
    col_filters, col_search = st.columns([3, 2])
    with col_filters:
        time_filter = st.radio(
            "Period",
            ["Today", "This Week", "This Month", "Reports"],
            horizontal=True,
            index=2,
            label_visibility="collapsed",
        )
    with col_search:
        st.text_input(
            "Search",
            placeholder="Search Stock, Signal, Portfolio...",
            label_visibility="collapsed",
        )

    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # --- Main Layout: 3 columns + right panel ---
    main_col, right_col = st.columns([3, 1])

    with main_col:
        # --- Row 1: My Tasks | Projects Overview | Income vs Expense ---
        row1_col1, row1_col2, row1_col3 = st.columns([1, 1.2, 1.3])

        with row1_col1:
            _render_my_tasks(time_filter)

        with row1_col2:
            _render_portfolio_overview()

        with row1_col3:
            _render_profit_vs_loss(time_filter)

        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

        # --- Row 2: Stock Performance (Invoice-like progress bars) ---
        _render_stock_performance()

    with right_col:
        _render_my_alerts()
        st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
        _render_open_tickets()


def _render_my_tasks(time_filter: str) -> None:
    """My Tasks card — watchlist actions pending."""
    st.markdown(
        """
        <div class="card">
            <div class="card-header">
                <span class="card-title">My Tasks</span>
                <span class="card-action">+</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Task items
    tasks = [
        {"icon": "📈", "title": "BBCA — Review Entry", "desc": "Score 78/100, R:R 2.5:1", "color": "#4CAF50"},
        {"icon": "🔍", "title": "TLKM — Monitor Support", "desc": "Mendekati support Rp 3,450", "color": "#FF9800"},
        {"icon": "⚠️", "title": "ASII — Check Stop Loss", "desc": "Mendekati SL di Rp 4,800", "color": "#f44336"},
        {"icon": "💰", "title": "BMRI — Take Profit T1", "desc": "Sudah mencapai target 1", "color": "#2196F3"},
        {"icon": "📊", "title": "UNVR — Rebalance", "desc": "Alokasi > 25% portfolio", "color": "#9C27B0"},
    ]

    for task in tasks:
        st.markdown(
            f"""
            <div class="task-item">
                <div class="task-icon" style="background: {task['color']}20; color: {task['color']}">{task['icon']}</div>
                <div class="task-content">
                    <div class="task-title">{task['title']}</div>
                    <div class="task-desc">{task['desc']}</div>
                </div>
                <div class="task-check">&#10003;</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div class="task-counter">
            <span class="counter-badge">{len(tasks)}</span> On Going Tasks
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_portfolio_overview() -> None:
    """Portfolio Overview — donut chart showing status of investments."""
    st.markdown(
        """
        <div class="card">
            <div class="card-header">
                <span class="card-title">Portfolio Overview</span>
                <span class="card-action">&#8599;</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Donut chart data
    labels = ["Profit", "Loss", "Holding"]
    values = [32, 14, 54]
    colors = ["#4CAF50", "#FF9800", "#E0E0E0"]

    import plotly.graph_objects as go

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.65,
        marker=dict(colors=colors),
        textinfo="none",
        hovertemplate="<b>%{label}</b><br>%{value} positions<br>%{percent}<extra></extra>",
    )])

    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=200,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b>{sum(values)}</b><br>Stocks",
            x=0.5, y=0.5,
            font_size=16,
            showarrow=False,
            font=dict(color="#333"),
        )],
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Legend below chart
    st.markdown(
        f"""
        <div class="donut-legend">
            <span class="legend-item"><span class="legend-dot" style="background: #FF9800"></span> Loss: {values[1]}</span>
            <span class="legend-item"><span class="legend-dot" style="background: #4CAF50"></span> Profit: {values[0]}</span>
        </div>
        <div class="donut-legend" style="justify-content: center;">
            <span class="legend-item"><span class="legend-dot" style="background: #E0E0E0"></span> Holding: {values[2]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_profit_vs_loss(time_filter: str) -> None:
    """Profit vs Loss line chart — like Income vs Expense."""
    st.markdown(
        """
        <div class="card">
            <div class="card-header">
                <span class="card-title">Profit VS Loss</span>
                <span class="card-action">&#9881; &#8599;</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    import plotly.graph_objects as go

    # Generate sample data
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
    profit = [18.5, 22.3, 19.8, 25.1, 28.6, 24.6, 30.2]
    loss = [8.2, 12.1, 9.5, 14.3, 11.8, 13.3, 10.5]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=months, y=profit,
        mode="lines",
        name="Profit",
        line=dict(color="#4CAF50", width=2, shape="spline"),
        fill="tonexty" if False else None,
    ))

    fig.add_trace(go.Scatter(
        x=months, y=loss,
        mode="lines",
        name="Loss",
        line=dict(color="#FF9800", width=2, dash="dot", shape="spline"),
    ))

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5, font=dict(size=10)),
        margin=dict(l=10, r=10, t=30, b=10),
        height=200,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0", showline=False),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Summary metrics
    st.markdown(
        """
        <div class="profit-summary">
            <span class="profit-value">&#9679; Profit: Rp 24.600.000</span>
            <span class="loss-value">&#9679; Loss: Rp 13.290.000</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_stock_performance() -> None:
    """Stock Performance section — progress bars like Invoice Overview."""
    st.markdown(
        """
        <div class="card">
            <div class="card-header">
                <span class="card-title">Stock Performance</span>
                <span class="card-action">&#9881;</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    stocks = [
        {"name": "Strong Buy", "count": 5, "value": "Rp 183.000.000", "pct": 90, "color": "#4CAF50"},
        {"name": "Buy", "count": 8, "value": "Rp 245.000.000", "pct": 75, "color": "#8BC34A"},
        {"name": "Hold", "count": 12, "value": "Rp 320.000.000", "pct": 60, "color": "#2196F3"},
        {"name": "Watch", "count": 5, "value": "Rp 95.000.000", "pct": 35, "color": "#FF9800"},
        {"name": "Avoid", "count": 3, "value": "Rp 45.000.000", "pct": 15, "color": "#f44336"},
    ]

    for stock in stocks:
        st.markdown(
            f"""
            <div class="perf-row">
                <div class="perf-label">{stock['name']}</div>
                <div class="perf-count">{stock['count']}</div>
                <div class="perf-separator">|</div>
                <div class="perf-value">{stock['value']}</div>
                <div class="perf-bar-container">
                    <div class="perf-bar" style="width: {stock['pct']}%; background: {stock['color']}"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_my_alerts() -> None:
    """My Alerts section — like My Meetings."""
    st.markdown(
        """
        <div class="card">
            <div class="card-header">
                <span class="card-title">My Alerts</span>
                <span class="card-action">&#128197;</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    alerts = [
        {"title": "BBCA Breakout", "time": "09:15", "type": "Signal", "icon": "📈"},
        {"title": "TLKM Support Hit", "time": "10:30", "type": "Alert", "icon": "🔔"},
        {"title": "Portfolio Review", "time": "14:00", "type": "Task", "icon": "📋"},
    ]

    for alert in alerts:
        st.markdown(
            f"""
            <div class="alert-item">
                <div class="alert-left">
                    <div class="alert-label">My Alerts</div>
                    <div class="alert-title">{alert['title']}</div>
                </div>
                <div class="alert-right">
                    <div class="alert-time">{alert['time']}</div>
                    <div class="alert-type">{alert['icon']} {alert['type']}</div>
                </div>
                <span class="alert-arrow">&#8599;</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """<div class="see-all">See All Alerts &gt;</div>""",
        unsafe_allow_html=True,
    )


def _render_open_tickets() -> None:
    """Open Tickets — watchlist items needing attention."""
    st.markdown(
        """
        <div class="card">
            <div class="card-header">
                <span class="card-title">Open Tickets</span>
                <span class="card-action">&#9881;</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tickets = [
        {"name": "BBCA", "message": "Entry score 78, mendekati buy zone. Review segera.", "avatar": "🏦"},
        {"name": "TLKM", "message": "Sudah 3 hari di support. Perlu konfirmasi volume.", "avatar": "📡"},
        {"name": "ASII", "message": "Breakdown MA50, pertimbangkan cut loss.", "avatar": "🚗"},
    ]

    for ticket in tickets:
        st.markdown(
            f"""
            <div class="ticket-item">
                <div class="ticket-avatar">{ticket['avatar']}</div>
                <div class="ticket-content">
                    <div class="ticket-name">{ticket['name']}</div>
                    <div class="ticket-msg">{ticket['message']}</div>
                </div>
                <div class="ticket-action">Check &gt;</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _get_custom_css() -> str:
    """Return custom CSS for the modern dashboard look."""
    return """
    <style>
    /* Main container */
    .block-container {
        padding-top: 1rem !important;
        max-width: 1400px;
    }

    /* Dashboard Header */
    .dashboard-header {
        margin-bottom: 10px;
    }
    .dashboard-header .subtitle {
        color: #888;
        font-size: 0.9em;
        margin: 0;
    }
    .dashboard-header .main-title {
        font-size: 2em;
        font-weight: 700;
        color: #1a1a2e;
        margin: 0;
    }

    /* Cards */
    .card {
        background: #ffffff;
        border-radius: 16px;
        padding: 0px;
        margin-bottom: 5px;
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
    }
    .card-title {
        font-weight: 600;
        font-size: 1.05em;
        color: #1a1a2e;
    }
    .card-action {
        color: #aaa;
        cursor: pointer;
        font-size: 1.2em;
    }

    /* Task Items */
    .task-item {
        display: flex;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #f5f5f5;
        gap: 10px;
    }
    .task-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1em;
        flex-shrink: 0;
    }
    .task-content {
        flex: 1;
    }
    .task-title {
        font-weight: 600;
        font-size: 0.85em;
        color: #1a1a2e;
    }
    .task-desc {
        font-size: 0.75em;
        color: #888;
        margin-top: 2px;
    }
    .task-check {
        color: #4CAF50;
        font-size: 1.1em;
        opacity: 0.5;
    }
    .task-counter {
        margin-top: 10px;
        padding: 8px 12px;
        background: #f8f9fa;
        border-radius: 20px;
        font-size: 0.85em;
        color: #555;
        display: inline-block;
    }
    .counter-badge {
        background: #1a1a2e;
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 0.85em;
        margin-right: 5px;
    }

    /* Donut Legend */
    .donut-legend {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 5px;
    }
    .legend-item {
        font-size: 0.8em;
        color: #555;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .legend-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
    }

    /* Profit Summary */
    .profit-summary {
        display: flex;
        justify-content: space-between;
        font-size: 0.8em;
        margin-top: 5px;
    }
    .profit-value { color: #4CAF50; }
    .loss-value { color: #FF9800; }

    /* Performance Rows (Invoice-like) */
    .perf-row {
        display: flex;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #f5f5f5;
        gap: 12px;
    }
    .perf-label {
        font-weight: 600;
        font-size: 0.9em;
        color: #1a1a2e;
        min-width: 90px;
    }
    .perf-count {
        font-size: 0.85em;
        color: #888;
        min-width: 20px;
    }
    .perf-separator {
        color: #ddd;
    }
    .perf-value {
        font-size: 0.85em;
        color: #555;
        min-width: 130px;
    }
    .perf-bar-container {
        flex: 1;
        background: #f0f0f0;
        border-radius: 6px;
        height: 8px;
        overflow: hidden;
    }
    .perf-bar {
        height: 100%;
        border-radius: 6px;
        transition: width 0.5s ease;
    }

    /* Alert Items */
    .alert-item {
        display: flex;
        align-items: center;
        padding: 12px;
        background: #fafafa;
        border-radius: 12px;
        margin-bottom: 8px;
        gap: 10px;
        position: relative;
    }
    .alert-left {
        flex: 1;
    }
    .alert-label {
        font-size: 0.7em;
        color: #aaa;
    }
    .alert-title {
        font-weight: 600;
        font-size: 0.9em;
        color: #1a1a2e;
    }
    .alert-right {
        text-align: right;
    }
    .alert-time {
        font-weight: 600;
        font-size: 0.85em;
        color: #1a1a2e;
    }
    .alert-type {
        font-size: 0.75em;
        color: #888;
    }
    .alert-arrow {
        color: #aaa;
        font-size: 1em;
    }
    .see-all {
        text-align: center;
        font-size: 0.85em;
        color: #888;
        padding: 8px;
        cursor: pointer;
    }

    /* Ticket Items */
    .ticket-item {
        display: flex;
        align-items: flex-start;
        padding: 12px 0;
        border-bottom: 1px solid #f5f5f5;
        gap: 10px;
    }
    .ticket-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3em;
        flex-shrink: 0;
    }
    .ticket-content {
        flex: 1;
    }
    .ticket-name {
        font-weight: 700;
        font-size: 0.9em;
        color: #1a1a2e;
    }
    .ticket-msg {
        font-size: 0.78em;
        color: #888;
        margin-top: 2px;
        line-height: 1.3;
    }
    .ticket-action {
        font-size: 0.8em;
        color: #888;
        cursor: pointer;
        white-space: nowrap;
        padding-top: 2px;
    }

    /* Radio buttons styled as tabs */
    div[data-testid="stHorizontalBlock"] div[role="radiogroup"] {
        gap: 0;
    }
    div[data-testid="stHorizontalBlock"] div[role="radiogroup"] label {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 20px;
        padding: 6px 16px;
        margin-right: 8px;
        font-size: 0.85em;
    }
    div[data-testid="stHorizontalBlock"] div[role="radiogroup"] label[data-checked="true"] {
        background: #1a1a2e;
        color: white;
        border-color: #1a1a2e;
    }

    /* Hide default Streamlit elements for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
