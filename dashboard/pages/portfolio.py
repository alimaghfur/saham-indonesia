"""Portfolio page — track positions, P/L, and allocation."""

from __future__ import annotations

import streamlit as st
from datetime import datetime
from decimal import Decimal


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
