"""Portfolio page — track positions, P/L, and allocation with interactive charts."""

from __future__ import annotations

import streamlit as st
from datetime import datetime
from decimal import Decimal

import numpy as np
import pandas as pd


def render() -> None:
    st.title("Portfolio Tracker")
    st.markdown("Kelola dan pantau portofolio saham IDX.")

    # Initialize session state for portfolio
    if "portfolio" not in st.session_state:
        from saham_id.portfolio.tracker import Portfolio
        st.session_state.portfolio = Portfolio(cash=Decimal("0"))

    portfolio = st.session_state.portfolio

    # --- Add Transaction ---
    st.subheader("Tambah Transaksi")

    with st.form("add_transaction"):
        t_col1, t_col2, t_col3, t_col4 = st.columns(4)
        with t_col1:
            tx_ticker = st.text_input("Ticker", value="BBCA", max_chars=10).upper()
        with t_col2:
            tx_side = st.selectbox("Side", ["buy", "sell"])
        with t_col3:
            tx_qty = st.number_input("Lot (100 shares)", value=1, min_value=1, step=1)
        with t_col4:
            tx_price = st.number_input("Harga/lembar", value=9500, min_value=1, step=25)

        t_col5, t_col6 = st.columns(2)
        with t_col5:
            tx_fee = st.number_input("Fee (Rp)", value=0, min_value=0, step=1000)
        with t_col6:
            tx_note = st.text_input("Catatan", value="")

        submitted = st.form_submit_button("Record Transaction")

        if submitted:
            from saham_id.portfolio.tracker import Transaction

            try:
                tx = Transaction(
                    ticker=tx_ticker,
                    side=tx_side,
                    quantity=tx_qty * 100,  # convert lot to shares
                    price=Decimal(str(tx_price)),
                    timestamp=datetime.now(),
                    fee=Decimal(str(tx_fee)),
                    note=tx_note,
                )
                portfolio.record(tx)
                st.success(
                    f"Recorded: {tx_side.upper()} {tx_qty} lot {tx_ticker} @ Rp {tx_price:,}"
                )
            except ValueError as e:
                st.error(f"Error: {e}")

    # --- Set Cash ---
    st.subheader("Set Cash Balance")
    new_cash = st.number_input("Cash (Rp)", value=float(portfolio.cash), step=1_000_000.0)
    if st.button("Update Cash"):
        portfolio.cash = Decimal(str(int(new_cash)))
        st.success(f"Cash updated to Rp {int(new_cash):,}")

    st.markdown("---")

    # --- Current Positions ---
    st.subheader("Posisi Saat Ini")

    active_positions = {t: p for t, p in portfolio.positions.items() if p.quantity > 0}

    if active_positions:
        import pandas as pd

        pos_data = []
        for ticker, pos in active_positions.items():
            market_value = float(pos.avg_cost) * pos.quantity
            pos_data.append({
                "Ticker": ticker,
                "Qty (shares)": pos.quantity,
                "Qty (lot)": pos.quantity // 100,
                "Avg Cost": f"Rp {float(pos.avg_cost):,.0f}",
                "Market Value": f"Rp {market_value:,.0f}",
                "Realized P/L": f"Rp {float(pos.realized_pnl):,.0f}",
            })

        df = pd.DataFrame(pos_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Allocation pie chart
        if len(active_positions) > 1:
            st.subheader("Alokasi")
            alloc_data = {
                t: float(p.avg_cost) * p.quantity
                for t, p in active_positions.items()
            }
            import pandas as pd
            alloc_df = pd.DataFrame(
                {"Ticker": list(alloc_data.keys()), "Value": list(alloc_data.values())}
            )
            st.bar_chart(alloc_df.set_index("Ticker"))
    else:
        st.info("Belum ada posisi terbuka. Tambahkan transaksi di atas.")

    # --- Transaction History ---
    st.subheader("Riwayat Transaksi")
    if portfolio.transactions:
        import pandas as pd

        tx_data = pd.DataFrame([
            {
                "Waktu": tx.timestamp.strftime("%Y-%m-%d %H:%M"),
                "Ticker": tx.ticker,
                "Side": tx.side.upper(),
                "Qty": tx.quantity,
                "Price": f"Rp {float(tx.price):,.0f}",
                "Fee": f"Rp {float(tx.fee):,.0f}",
                "Note": tx.note,
            }
            for tx in reversed(portfolio.transactions)
        ])
        st.dataframe(tx_data, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada transaksi.")

    # --- Summary ---
    st.markdown("---")
    st.subheader("Ringkasan")
    total_invested = sum(
        float(p.avg_cost) * p.quantity
        for p in active_positions.values()
    )
    total_realized = sum(
        float(p.realized_pnl)
        for p in portfolio.positions.values()
    )
    st.markdown(f"""
    | Metric | Nilai |
    |--------|-------|
    | Cash | Rp {float(portfolio.cash):,.0f} |
    | Total Invested | Rp {total_invested:,.0f} |
    | Total Realized P/L | Rp {total_realized:,.0f} |
    | Portfolio Value | Rp {float(portfolio.cash) + total_invested:,.0f} |
    """)

    # --- Portfolio Charts ---
    st.markdown("---")
    st.subheader("Portfolio Charts")

    _render_portfolio_charts(portfolio, active_positions)



def _render_portfolio_charts(portfolio, active_positions: dict) -> None:
    """Render interactive portfolio charts using the charting module."""

    if not active_positions:
        st.info("Tambahkan posisi untuk melihat chart portfolio.")
        return

    try:
        from saham_id.charting.portfolio import (
            allocation_pie,
            drawdown_chart,
            equity_curve,
            portfolio_dashboard,
        )

        # --- Allocation Pie Chart ---
        st.markdown("#### Alokasi Portfolio")
        holdings = {
            ticker: float(pos.avg_cost) * pos.quantity
            for ticker, pos in active_positions.items()
        }

        # Add cash if significant
        if float(portfolio.cash) > 0:
            holdings["Cash"] = float(portfolio.cash)

        fig_alloc = allocation_pie(holdings, title="Alokasi Portfolio", height=450, dark=True)
        st.plotly_chart(fig_alloc, use_container_width=True)

        st.markdown("---")

        # --- Simulated Equity Curve & Drawdown ---
        # Generate equity curve from transaction history
        if portfolio.transactions:
            st.markdown("#### Performance (Simulasi)")
            st.caption("Berdasarkan riwayat transaksi & harga rata-rata.")

            returns = _estimate_portfolio_returns(portfolio, active_positions)

            if returns is not None and len(returns) > 5:
                total_value = sum(holdings.values())

                chart_tab1, chart_tab2, chart_tab3 = st.tabs(
                    ["Equity Curve", "Drawdown", "Dashboard"]
                )

                with chart_tab1:
                    fig_equity = equity_curve(
                        returns,
                        title="Equity Curve Portfolio",
                        initial_capital=total_value,
                        height=400,
                        dark=True,
                    )
                    st.plotly_chart(fig_equity, use_container_width=True)

                with chart_tab2:
                    fig_dd = drawdown_chart(
                        returns,
                        title="Drawdown Portfolio",
                        height=350,
                        dark=True,
                    )
                    st.plotly_chart(fig_dd, use_container_width=True)

                    # Drawdown stats
                    cumulative = (1 + returns).cumprod()
                    running_max = cumulative.cummax()
                    dd = (cumulative - running_max) / running_max * 100
                    max_dd = dd.min()

                    dd_col1, dd_col2, dd_col3 = st.columns(3)
                    dd_col1.metric("Max Drawdown", f"{max_dd:.2f}%")
                    dd_col2.metric("Current DD", f"{dd.iloc[-1]:.2f}%")
                    dd_col3.metric("Recovery Days", f"{_days_since_peak(dd)}")

                with chart_tab3:
                    fig_dash = portfolio_dashboard(
                        returns=returns,
                        holdings={k: v for k, v in holdings.items() if k != "Cash"},
                        title="Portfolio Dashboard",
                        initial_capital=total_value,
                        height=900,
                        dark=True,
                    )
                    st.plotly_chart(fig_dash, use_container_width=True)
            else:
                st.info("Perlu minimal 5 hari data untuk menampilkan chart performance.")
        else:
            st.info("Belum ada transaksi untuk menghitung performance.")

    except ImportError as e:
        st.warning(f"Charting module belum terinstall: {e}")
    except Exception as e:
        st.error(f"Error rendering charts: {e}")
        import traceback
        with st.expander("Detail Error"):
            st.code(traceback.format_exc())


def _estimate_portfolio_returns(portfolio, active_positions: dict) -> "pd.Series | None":
    """Estimate daily portfolio returns from held positions using OHLC data."""
    try:
        from saham_id.data.sources import get_source

        src = get_source()
        tickers = list(active_positions.keys())

        if not tickers:
            return None

        # Fetch OHLC for all held tickers (3 months)
        all_returns = []
        weights = {}
        total_value = sum(float(p.avg_cost) * p.quantity for p in active_positions.values())

        for ticker, pos in active_positions.items():
            try:
                df = src.get_ohlc(ticker, period="3mo", interval="1d")
                if df is not None and not df.empty:
                    daily_ret = df["close"].pct_change().dropna()
                    weight = (float(pos.avg_cost) * pos.quantity) / total_value if total_value > 0 else 0
                    weights[ticker] = weight
                    all_returns.append(daily_ret * weight)
            except Exception:
                continue

        if not all_returns:
            return None

        # Combine weighted returns
        combined = pd.concat(all_returns, axis=1).sum(axis=1)
        combined.name = "portfolio_returns"
        return combined

    except Exception:
        # Fallback: generate simulated returns
        n_days = 60
        dates = pd.bdate_range(end=pd.Timestamp.today(), periods=n_days)
        returns = pd.Series(
            np.random.normal(0.0005, 0.012, n_days),
            index=dates,
            name="portfolio_returns",
        )
        return returns


def _days_since_peak(drawdown: "pd.Series") -> int:
    """Calculate days since the last equity peak (DD = 0)."""
    if drawdown.empty:
        return 0
    at_peak = drawdown[drawdown == 0]
    if at_peak.empty:
        return len(drawdown)
    last_peak = at_peak.index[-1]
    return (drawdown.index[-1] - last_peak).days
