"""Project Dashboard — Modern dark-themed overview page.

All HTML rendered as single complete blocks per st.markdown() call
to prevent Streamlit from displaying raw HTML tags.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go


def render() -> None:
    """Render the modern Project Dashboard."""

    # --- Inject CSS ---
    st.markdown(_get_css(), unsafe_allow_html=True)

    # --- Header ---
    st.markdown(
        """
        <div style="margin-bottom: 8px;">
            <span style="color: #aaa; font-size: 0.9em;">Manage and track your investments</span>
            <h1 style="color: #FF8C00; margin: 0; font-size: 1.8em; font-weight: 700;">Investment Dashboard</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Time Filter + Search ---
    fcol1, fcol2, fcol3, fcol4, _, scol = st.columns([0.8, 0.8, 0.9, 0.8, 1, 2.5])
    with fcol1:
        st.button("Today", use_container_width=True, type="secondary")
    with fcol2:
        st.button("This Week", use_container_width=True, type="secondary")
    with fcol3:
        st.button("This Month", use_container_width=True, type="primary")
    with fcol4:
        st.button("Reports", use_container_width=True, type="secondary")
    with scol:
        st.text_input("search", placeholder="Search Stock, Signal, Portfolio...", label_visibility="collapsed")

    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

    # === ROW 1 ===
    r1c1, r1c2, r1c3, r1c4 = st.columns([1.3, 1.2, 1.5, 1.2])

    with r1c1:
        _card_my_tasks()

    with r1c2:
        _card_portfolio_overview()

    with r1c3:
        _card_profit_vs_loss()

    with r1c4:
        _card_my_alerts()

    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

    # === ROW 2 ===
    r2c1, r2c2 = st.columns([2.8, 1.2])

    with r2c1:
        _card_stock_performance()

    with r2c2:
        _card_open_tickets()


# ─── CARD: MY TASKS ──────────────────────────────────────────────────────────

def _card_my_tasks() -> None:
    tasks = [
        ("📈", "BBCA — Review Entry", "Score 78/100, R:R 2.5:1"),
        ("🔍", "TLKM — Monitor Support", "Mendekati support Rp 3,450"),
        ("⚠️", "ASII — Check Stop Loss", "Mendekati SL di Rp 4,800"),
        ("💰", "BMRI — Take Profit T1", "Sudah mencapai target 1"),
        ("📊", "UNVR — Rebalance", "Alokasi > 25% portfolio"),
    ]

    rows = ""
    for icon, title, desc in tasks:
        rows += f"""
        <div class="ds-task-row">
            <span class="ds-task-icon">{icon}</span>
            <div class="ds-task-text">
                <div class="ds-task-title">{title}</div>
                <div class="ds-task-desc">{desc}</div>
            </div>
            <span class="ds-task-check">&#10003;</span>
        </div>"""

    st.markdown(
        f"""
        <div class="ds-card">
            <div class="ds-card-head">
                <span class="ds-card-title">My Tasks</span>
                <span class="ds-card-btn">+</span>
            </div>
            {rows}
            <div class="ds-task-footer">
                <span class="ds-badge">{len(tasks)}</span> On Going Tasks
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── CARD: PORTFOLIO OVERVIEW ────────────────────────────────────────────────

def _card_portfolio_overview() -> None:
    st.markdown(
        """
        <div class="ds-card">
            <div class="ds-card-head">
                <span class="ds-card-title">Portfolio Overview</span>
                <span class="ds-card-btn">&#8599;</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    labels = ["Profit", "Loss", "Holding"]
    values = [32, 14, 54]
    colors = ["#4CAF50", "#FF9800", "#555555"]

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
        height=200,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        annotations=[dict(
            text=f"<b>{sum(values)}</b><br><span style='font-size:11px'>Stocks</span>",
            x=0.5, y=0.5,
            font_size=20,
            showarrow=False,
            font=dict(color="white"),
        )],
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        f"""
        <div class="ds-legend">
            <span><span style="color:#FF9800">&#9679;</span> Loss: {values[1]}</span>
            <span><span style="color:#4CAF50">&#9679;</span> Profit: {values[0]}</span>
        </div>
        <div class="ds-legend" style="justify-content:center">
            <span><span style="color:#666">&#9679;</span> Holding: {values[2]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── CARD: PROFIT VS LOSS ────────────────────────────────────────────────────

def _card_profit_vs_loss() -> None:
    st.markdown(
        """
        <div class="ds-card">
            <div class="ds-card-head">
                <span class="ds-card-title">Profit VS Loss</span>
                <span class="ds-card-btn">&#9881; &#8599;</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
    profit = [18.5, 22.3, 19.8, 25.1, 28.6, 24.6, 30.2]
    loss = [8.2, 12.1, 9.5, 14.3, 11.8, 13.3, 10.5]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=months, y=profit,
        mode="lines",
        name="Profit",
        line=dict(color="#4CAF50", width=2.5, shape="spline"),
        fill="tozeroy",
        fillcolor="rgba(76,175,80,0.1)",
    ))

    fig.add_trace(go.Scatter(
        x=months, y=loss,
        mode="lines",
        name="Loss",
        line=dict(color="#FF9800", width=2, dash="dot", shape="spline"),
    ))

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5,
            font=dict(size=10, color="#ccc"),
        ),
        margin=dict(l=0, r=0, t=25, b=0),
        height=200,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, showline=False, tickfont=dict(size=10, color="#888")),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", showline=False, tickfont=dict(size=10, color="#888")),
        hovermode="x unified",
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        """
        <div class="ds-pnl-summary">
            <span style="color:#4CAF50">&#9679; Profit: Rp 24.600.000</span>
            <span style="color:#FF9800">&#9679; Loss: Rp 13.290.000</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── CARD: MY ALERTS ─────────────────────────────────────────────────────────

def _card_my_alerts() -> None:
    alerts = [
        ("BBCA Breakout", "09:15", "📈 Signal"),
        ("TLKM Support Hit", "10:30", "🔔 Alert"),
        ("Portfolio Review", "14:00", "📋 Task"),
    ]

    rows = ""
    for title, time, atype in alerts:
        rows += f"""
        <div class="ds-alert-row">
            <div>
                <div class="ds-alert-label">My Alerts</div>
                <div class="ds-alert-title">{title}</div>
            </div>
            <div style="text-align:right">
                <div class="ds-alert-time">{time}</div>
                <div class="ds-alert-type">{atype}</div>
            </div>
            <span class="ds-alert-arrow">&#8599;</span>
        </div>"""

    st.markdown(
        f"""
        <div class="ds-card">
            <div class="ds-card-head">
                <span class="ds-card-title">My Alerts</span>
                <span class="ds-card-btn">&#128197;</span>
            </div>
            {rows}
            <div class="ds-see-all">See All Alerts &gt;</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── CARD: STOCK PERFORMANCE ─────────────────────────────────────────────────

def _card_stock_performance() -> None:
    stocks = [
        ("Strong Buy", 5, "Rp 183.000.000", 90, "#4CAF50"),
        ("Buy", 8, "Rp 245.000.000", 75, "#8BC34A"),
        ("Hold", 12, "Rp 320.000.000", 60, "#2196F3"),
        ("Watch", 5, "Rp 95.000.000", 35, "#FF9800"),
        ("Avoid", 3, "Rp 45.000.000", 15, "#f44336"),
    ]

    rows = ""
    for name, count, value, pct, color in stocks:
        rows += f"""
        <div class="ds-perf-row">
            <div class="ds-perf-name">{name}</div>
            <div class="ds-perf-count">{count}</div>
            <div class="ds-perf-sep">|</div>
            <div class="ds-perf-val">{value}</div>
            <div class="ds-perf-bar-bg">
                <div class="ds-perf-bar" style="width:{pct}%; background:{color}"></div>
            </div>
        </div>"""

    st.markdown(
        f"""
        <div class="ds-card">
            <div class="ds-card-head">
                <span class="ds-card-title">Stock Performance</span>
                <span class="ds-card-btn">&#9881;</span>
            </div>
            {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── CARD: OPEN TICKETS ──────────────────────────────────────────────────────

def _card_open_tickets() -> None:
    tickets = [
        ("🏦", "BBCA", "Entry score 78, mendekati buy zone. Review segera."),
        ("📡", "TLKM", "Sudah 3 hari di support. Perlu konfirmasi volume."),
        ("🚗", "ASII", "Breakdown MA50, pertimbangkan cut loss."),
    ]

    rows = ""
    for avatar, name, msg in tickets:
        rows += f"""
        <div class="ds-ticket-row">
            <span class="ds-ticket-avatar">{avatar}</span>
            <div class="ds-ticket-body">
                <div class="ds-ticket-name">{name}</div>
                <div class="ds-ticket-msg">{msg}</div>
            </div>
            <span class="ds-ticket-action">Check &gt;</span>
        </div>"""

    st.markdown(
        f"""
        <div class="ds-card">
            <div class="ds-card-head">
                <span class="ds-card-title">Open Tickets</span>
                <span class="ds-card-btn">&#9881;</span>
            </div>
            {rows}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─── CSS ──────────────────────────────────────────────────────────────────────

def _get_css() -> str:
    return """
<style>
/* ── Card container ── */
.ds-card {
    background: #1e1e2e;
    border: 1px solid #2a2a3e;
    border-radius: 16px;
    padding: 18px 20px;
    margin-bottom: 10px;
}
.ds-card-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
}
.ds-card-title {
    font-weight: 600;
    font-size: 1em;
    color: #eee;
}
.ds-card-btn {
    color: #666;
    font-size: 1.1em;
    cursor: pointer;
}

/* ── Task rows ── */
.ds-task-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 0;
    border-bottom: 1px solid #2a2a3e;
}
.ds-task-icon { font-size: 1.2em; }
.ds-task-text { flex: 1; }
.ds-task-title { font-weight: 600; font-size: 0.85em; color: #ddd; }
.ds-task-desc { font-size: 0.75em; color: #888; margin-top: 2px; }
.ds-task-check { color: #4CAF50; opacity: 0.6; }
.ds-task-footer {
    margin-top: 12px;
    padding: 6px 12px;
    background: #252535;
    border-radius: 16px;
    font-size: 0.8em;
    color: #aaa;
    display: inline-block;
}
.ds-badge {
    background: #4CAF50;
    color: white;
    padding: 2px 8px;
    border-radius: 8px;
    font-size: 0.85em;
    margin-right: 5px;
}

/* ── Legend ── */
.ds-legend {
    display: flex;
    justify-content: center;
    gap: 18px;
    font-size: 0.8em;
    color: #aaa;
    margin-top: 4px;
}

/* ── P&L Summary ── */
.ds-pnl-summary {
    display: flex;
    justify-content: space-between;
    font-size: 0.8em;
    padding: 0 4px;
}

/* ── Alert rows ── */
.ds-alert-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    background: #252535;
    border-radius: 12px;
    margin-bottom: 8px;
}
.ds-alert-label { font-size: 0.65em; color: #666; }
.ds-alert-title { font-weight: 600; font-size: 0.85em; color: #ddd; }
.ds-alert-time { font-weight: 700; font-size: 0.85em; color: #eee; }
.ds-alert-type { font-size: 0.7em; color: #888; }
.ds-alert-arrow { color: #555; font-size: 0.9em; margin-left: auto; }
.ds-see-all { text-align: center; font-size: 0.8em; color: #666; padding: 8px 0; }

/* ── Performance rows ── */
.ds-perf-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 0;
    border-bottom: 1px solid #2a2a3e;
}
.ds-perf-name { font-weight: 600; font-size: 0.9em; color: #ddd; min-width: 90px; }
.ds-perf-count { font-size: 0.85em; color: #888; min-width: 24px; }
.ds-perf-sep { color: #333; }
.ds-perf-val { font-size: 0.85em; color: #aaa; min-width: 140px; }
.ds-perf-bar-bg {
    flex: 1;
    background: #2a2a3e;
    border-radius: 6px;
    height: 10px;
    overflow: hidden;
}
.ds-perf-bar {
    height: 100%;
    border-radius: 6px;
    transition: width 0.6s ease;
}

/* ── Ticket rows ── */
.ds-ticket-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 12px 0;
    border-bottom: 1px solid #2a2a3e;
}
.ds-ticket-avatar {
    width: 38px; height: 38px;
    background: #252535;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2em;
}
.ds-ticket-body { flex: 1; }
.ds-ticket-name { font-weight: 700; font-size: 0.88em; color: #ddd; }
.ds-ticket-msg { font-size: 0.75em; color: #888; margin-top: 3px; line-height: 1.3; }
.ds-ticket-action { font-size: 0.78em; color: #666; cursor: pointer; }

/* ── Hide Streamlit chrome ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
