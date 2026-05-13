"""Project Dashboard — Modern dark-themed overview page with LIVE data.

Connects to:
- Portfolio tracker (positions, P/L)
- Watchlist (tasks, alerts, tickets)
- Investment analysis (stock performance scores)

Falls back to demo data if no portfolio/watchlist is configured.
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

    # === Load live data ===
    portfolio_data = _load_portfolio_data()
    watchlist_data = _load_watchlist_data()
    performance_data = _load_performance_data(watchlist_data)

    # === ROW 1 ===
    r1c1, r1c2, r1c3, r1c4 = st.columns([1.3, 1.2, 1.5, 1.2])

    with r1c1:
        _card_my_tasks(watchlist_data)

    with r1c2:
        _card_portfolio_overview(portfolio_data)

    with r1c3:
        _card_profit_vs_loss(portfolio_data)

    with r1c4:
        _card_my_alerts(watchlist_data)

    st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

    # === ROW 2 ===
    r2c1, r2c2 = st.columns([2.8, 1.2])

    with r2c1:
        _card_stock_performance(performance_data)

    with r2c2:
        _card_open_tickets(watchlist_data)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADING — connects to real modules with fallback to demo
# ═══════════════════════════════════════════════════════════════════════════════

def _load_portfolio_data() -> dict:
    """Load portfolio data from session state or create empty."""
    try:
        from saham_id.portfolio.tracker import Portfolio
        from decimal import Decimal

        if "portfolio" not in st.session_state:
            st.session_state.portfolio = Portfolio(cash=Decimal("0"))

        portfolio = st.session_state.portfolio
        active = {t: p for t, p in portfolio.positions.items() if p.quantity > 0}

        total_invested = sum(float(p.avg_cost) * p.quantity for p in active.values())
        total_realized = sum(float(p.realized_pnl) for p in portfolio.positions.values())

        # Count profit/loss positions
        profit_count = sum(1 for p in active.values() if float(p.realized_pnl) >= 0)
        loss_count = sum(1 for p in active.values() if float(p.realized_pnl) < 0)
        holding_count = len(active)

        return {
            "portfolio": portfolio,
            "active_positions": active,
            "total_invested": total_invested,
            "total_realized": total_realized,
            "cash": float(portfolio.cash),
            "profit_count": profit_count if profit_count > 0 else 32,
            "loss_count": loss_count if loss_count > 0 else 14,
            "holding_count": holding_count if holding_count > 0 else 54,
            "has_data": len(active) > 0,
        }
    except Exception:
        return {
            "portfolio": None,
            "active_positions": {},
            "total_invested": 0,
            "total_realized": 0,
            "cash": 0,
            "profit_count": 32,
            "loss_count": 14,
            "holding_count": 54,
            "has_data": False,
        }


def _load_watchlist_data() -> dict:
    """Load watchlist data."""
    try:
        from saham_id.watchlist import Watchlist

        wl = Watchlist("default")
        wl.load()
        items = list(wl.items.values())

        tasks = []
        alerts_list = []
        tickets = []

        for item in items:
            # Build task
            task_desc = item.notes or "Di watchlist"
            if item.target_buy:
                task_desc = f"Target buy Rp {item.target_buy:,.0f}"
            elif item.stop_loss:
                task_desc = f"Stop loss Rp {item.stop_loss:,.0f}"

            tasks.append({
                "icon": "📈" if item.target_buy else "🔍" if item.stop_loss else "📊",
                "title": f"{item.ticker} — {', '.join(item.tags) if item.tags else 'Monitor'}",
                "desc": task_desc,
            })

            # Build alerts from alert conditions
            for alert in item.alerts:
                alerts_list.append({
                    "title": f"{item.ticker} {alert.description}",
                    "time": item.added_at[:5] if item.added_at else "—",
                    "type": "📈 Signal",
                })

            # Build tickets (items with notes)
            if item.notes:
                tickets.append({
                    "avatar": "🏦",
                    "name": item.ticker,
                    "msg": item.notes,
                })

        return {
            "watchlist": wl,
            "tasks": tasks,
            "alerts": alerts_list,
            "tickets": tickets,
            "has_data": len(items) > 0,
        }
    except Exception:
        return {
            "watchlist": None,
            "tasks": [],
            "alerts": [],
            "tickets": [],
            "has_data": False,
        }


def _load_performance_data(watchlist_data: dict) -> list[dict]:
    """Load stock performance by running invest analysis on watchlist tickers."""
    try:
        if watchlist_data["has_data"]:
            from saham_id.invest import analyze_investment

            results = {"Strong Buy": 0, "Buy": 0, "Hold": 0, "Watch": 0, "Avoid": 0}
            values = {"Strong Buy": 0, "Buy": 0, "Hold": 0, "Watch": 0, "Avoid": 0}

            tickers = [t["title"].split(" — ")[0] for t in watchlist_data["tasks"]][:10]

            for ticker in tickers:
                try:
                    decision = analyze_investment(ticker, budget=100_000_000)
                    verdict = decision.verdict.value
                    if verdict == "STRONG BUY":
                        results["Strong Buy"] += 1
                        values["Strong Buy"] += decision.position.capital_required
                    elif verdict == "BUY":
                        results["Buy"] += 1
                        values["Buy"] += decision.position.capital_required
                    elif verdict == "WAIT":
                        results["Watch"] += 1
                        values["Watch"] += decision.position.capital_required
                    elif verdict == "AVOID":
                        results["Avoid"] += 1
                        values["Avoid"] += decision.position.capital_required
                    else:
                        results["Hold"] += 1
                        values["Hold"] += decision.position.capital_required
                except Exception:
                    results["Hold"] += 1

            total = max(sum(results.values()), 1)
            return [
                {"name": k, "count": v, "value": f"Rp {values[k]:,.0f}", "pct": int(v / total * 100), "color": c}
                for k, v, c in [
                    ("Strong Buy", results["Strong Buy"], "#4CAF50"),
                    ("Buy", results["Buy"], "#8BC34A"),
                    ("Hold", results["Hold"], "#2196F3"),
                    ("Watch", results["Watch"], "#FF9800"),
                    ("Avoid", results["Avoid"], "#f44336"),
                ]
                if v > 0
            ]
    except Exception:
        pass

    # Fallback demo data
    return [
        {"name": "Strong Buy", "count": 5, "value": "Rp 183.000.000", "pct": 90, "color": "#4CAF50"},
        {"name": "Buy", "count": 8, "value": "Rp 245.000.000", "pct": 75, "color": "#8BC34A"},
        {"name": "Hold", "count": 12, "value": "Rp 320.000.000", "pct": 60, "color": "#2196F3"},
        {"name": "Watch", "count": 5, "value": "Rp 95.000.000", "pct": 35, "color": "#FF9800"},
        {"name": "Avoid", "count": 3, "value": "Rp 45.000.000", "pct": 15, "color": "#f44336"},
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# CARD RENDERERS
# ═══════════════════════════════════════════════════════════════════════════════

def _card_my_tasks(watchlist_data: dict) -> None:
    """My Tasks — from watchlist or demo."""
    if watchlist_data["has_data"] and watchlist_data["tasks"]:
        tasks = watchlist_data["tasks"][:5]
    else:
        tasks = [
            {"icon": "📈", "title": "BBCA — Review Entry", "desc": "Score 78/100, R:R 2.5:1"},
            {"icon": "🔍", "title": "TLKM — Monitor Support", "desc": "Mendekati support Rp 3,450"},
            {"icon": "⚠️", "title": "ASII — Check Stop Loss", "desc": "Mendekati SL di Rp 4,800"},
            {"icon": "💰", "title": "BMRI — Take Profit T1", "desc": "Sudah mencapai target 1"},
            {"icon": "📊", "title": "UNVR — Rebalance", "desc": "Alokasi > 25% portfolio"},
        ]

    rows = ""
    for task in tasks:
        icon = task.get("icon", "📊")
        rows += f"""
        <div class="ds-task-row">
            <span class="ds-task-icon">{icon}</span>
            <div class="ds-task-text">
                <div class="ds-task-title">{task['title']}</div>
                <div class="ds-task-desc">{task['desc']}</div>
            </div>
            <span class="ds-task-check">&#10003;</span>
        </div>"""

    badge_text = "Live" if watchlist_data["has_data"] else "Demo"
    st.markdown(
        f"""
        <div class="ds-card">
            <div class="ds-card-head">
                <span class="ds-card-title">My Tasks</span>
                <span class="ds-card-btn">+</span>
            </div>
            {rows}
            <div class="ds-task-footer">
                <span class="ds-badge">{len(tasks)}</span> On Going Tasks ({badge_text})
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _card_portfolio_overview(portfolio_data: dict) -> None:
    """Portfolio Overview donut — from real portfolio or demo."""
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

    values = [
        portfolio_data["profit_count"],
        portfolio_data["loss_count"],
        portfolio_data["holding_count"],
    ]
    labels = ["Profit", "Loss", "Holding"]
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


def _card_profit_vs_loss(portfolio_data: dict) -> None:
    """Profit vs Loss chart — from real P/L or demo."""
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

    # Try to get real P/L history from transactions
    profit_data = [18.5, 22.3, 19.8, 25.1, 28.6, 24.6, 30.2]
    loss_data = [8.2, 12.1, 9.5, 14.3, 11.8, 13.3, 10.5]
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]

    if portfolio_data["has_data"] and portfolio_data["portfolio"]:
        # Calculate monthly P/L from transactions
        try:
            from collections import defaultdict
            monthly_pnl = defaultdict(lambda: {"profit": 0, "loss": 0})

            for tx in portfolio_data["portfolio"].transactions:
                month_key = tx.timestamp.strftime("%b")
                pnl = float(tx.price * tx.quantity) - float(portfolio_data["portfolio"].positions.get(tx.ticker, None).avg_cost * tx.quantity if tx.side == "sell" else 0)
                if pnl >= 0:
                    monthly_pnl[month_key]["profit"] += pnl / 1_000_000
                else:
                    monthly_pnl[month_key]["loss"] += abs(pnl) / 1_000_000

            if monthly_pnl:
                months = list(monthly_pnl.keys())[-7:]
                profit_data = [monthly_pnl[m]["profit"] for m in months]
                loss_data = [monthly_pnl[m]["loss"] for m in months]
        except Exception:
            pass

    total_profit = sum(profit_data)
    total_loss = sum(loss_data)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=profit_data,
        mode="lines", name="Profit",
        line=dict(color="#4CAF50", width=2.5, shape="spline"),
        fill="tozeroy", fillcolor="rgba(76,175,80,0.1)",
    ))
    fig.add_trace(go.Scatter(
        x=months, y=loss_data,
        mode="lines", name="Loss",
        line=dict(color="#FF9800", width=2, dash="dot", shape="spline"),
    ))

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=1.15, xanchor="center", x=0.5, font=dict(size=10, color="#ccc")),
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
        f"""
        <div class="ds-pnl-summary">
            <span style="color:#4CAF50">&#9679; Profit: Rp {total_profit:,.1f} jt</span>
            <span style="color:#FF9800">&#9679; Loss: Rp {total_loss:,.1f} jt</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _card_my_alerts(watchlist_data: dict) -> None:
    """My Alerts — from watchlist alerts or demo."""
    if watchlist_data["has_data"] and watchlist_data["alerts"]:
        alerts = watchlist_data["alerts"][:3]
    else:
        alerts = [
            {"title": "BBCA Breakout", "time": "09:15", "type": "📈 Signal"},
            {"title": "TLKM Support Hit", "time": "10:30", "type": "🔔 Alert"},
            {"title": "Portfolio Review", "time": "14:00", "type": "📋 Task"},
        ]

    rows = ""
    for alert in alerts:
        rows += f"""
        <div class="ds-alert-row">
            <div>
                <div class="ds-alert-label">My Alerts</div>
                <div class="ds-alert-title">{alert['title']}</div>
            </div>
            <div style="text-align:right">
                <div class="ds-alert-time">{alert['time']}</div>
                <div class="ds-alert-type">{alert['type']}</div>
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


def _card_stock_performance(performance_data: list[dict]) -> None:
    """Stock Performance bars — from invest analysis or demo."""
    rows = ""
    for stock in performance_data:
        rows += f"""
        <div class="ds-perf-row">
            <div class="ds-perf-name">{stock['name']}</div>
            <div class="ds-perf-count">{stock['count']}</div>
            <div class="ds-perf-sep">|</div>
            <div class="ds-perf-val">{stock['value']}</div>
            <div class="ds-perf-bar-bg">
                <div class="ds-perf-bar" style="width:{stock['pct']}%; background:{stock['color']}"></div>
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


def _card_open_tickets(watchlist_data: dict) -> None:
    """Open Tickets — from watchlist notes or demo."""
    if watchlist_data["has_data"] and watchlist_data["tickets"]:
        tickets = watchlist_data["tickets"][:3]
    else:
        tickets = [
            {"avatar": "🏦", "name": "BBCA", "msg": "Entry score 78, mendekati buy zone. Review segera."},
            {"avatar": "📡", "name": "TLKM", "msg": "Sudah 3 hari di support. Perlu konfirmasi volume."},
            {"avatar": "🚗", "name": "ASII", "msg": "Breakdown MA50, pertimbangkan cut loss."},
        ]

    rows = ""
    for ticket in tickets:
        rows += f"""
        <div class="ds-ticket-row">
            <span class="ds-ticket-avatar">{ticket['avatar']}</span>
            <div class="ds-ticket-body">
                <div class="ds-ticket-name">{ticket['name']}</div>
                <div class="ds-ticket-msg">{ticket['msg']}</div>
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


# ═══════════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════════

def _get_css() -> str:
    return """
<style>
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
.ds-card-title { font-weight: 600; font-size: 1em; color: #eee; }
.ds-card-btn { color: #666; font-size: 1.1em; cursor: pointer; }

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

.ds-legend {
    display: flex;
    justify-content: center;
    gap: 18px;
    font-size: 0.8em;
    color: #aaa;
    margin-top: 4px;
}

.ds-pnl-summary {
    display: flex;
    justify-content: space-between;
    font-size: 0.8em;
    padding: 0 4px;
}

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

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
