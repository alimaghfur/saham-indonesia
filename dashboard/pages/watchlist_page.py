"""Watchlist page — manage watchlist + check alerts interactively."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Watchlist & Alerts")
    st.markdown("Kelola daftar pantau saham + kondisi alert.")

    # --- Add to watchlist ---
    st.subheader("Tambah ke Watchlist")
    with st.form("add_watchlist"):
        col1, col2 = st.columns(2)
        with col1:
            ticker = st.text_input("Ticker", value="BBCA", max_chars=10).upper()
            notes = st.text_input("Catatan", value="")
        with col2:
            target_buy = st.number_input("Target Beli (Rp)", value=0, step=25)
            target_sell = st.number_input("Target Jual (Rp)", value=0, step=25)
            stop_loss = st.number_input("Stop Loss (Rp)", value=0, step=25)

        tags_input = st.text_input("Tags (pisahkan koma)", value="")
        submitted = st.form_submit_button("Tambah")

        if submitted and ticker:
            from saham_id.watchlist import Watchlist
            wl = Watchlist.load("dashboard")
            tags = [t.strip() for t in tags_input.split(",") if t.strip()]
            wl.add(ticker, notes=notes, tags=tags,
                  target_buy=target_buy if target_buy > 0 else None,
                  target_sell=target_sell if target_sell > 0 else None,
                  stop_loss=stop_loss if stop_loss > 0 else None)
            wl.save("dashboard")
            st.success(f"{ticker} ditambahkan ke watchlist!")

    st.markdown("---")

    # --- Current watchlist ---
    st.subheader("Watchlist Saat Ini")
    try:
        from saham_id.watchlist import Watchlist
        wl = Watchlist.load("dashboard")

        if wl.tickers:
            import pandas as pd
            rows = []
            for t in wl.tickers:
                item = wl.get(t)
                rows.append({
                    "Ticker": t,
                    "Notes": item.notes,
                    "Tags": ", ".join(item.tags),
                    "Target Buy": f"Rp {item.target_buy:,.0f}" if item.target_buy else "-",
                    "Target Sell": f"Rp {item.target_sell:,.0f}" if item.target_sell else "-",
                    "Stop Loss": f"Rp {item.stop_loss:,.0f}" if item.stop_loss else "-",
                    "Alerts": len(item.alerts),
                })
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Remove button
            remove_ticker = st.selectbox("Hapus ticker:", [""] + wl.tickers)
            if st.button("Hapus") and remove_ticker:
                wl.remove(remove_ticker)
                wl.save("dashboard")
                st.success(f"{remove_ticker} dihapus!")
                st.rerun()
        else:
            st.info("Watchlist kosong. Tambahkan saham di atas.")
    except Exception as e:
        st.error(f"Error: {e}")

    st.markdown("---")

    # --- Fee Calculator ---
    st.subheader("Kalkulator Fee & Lot")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        calc_price = st.number_input("Harga (Rp)", value=9500, step=25)
    with fc2:
        calc_budget = st.number_input("Budget (Rp)", value=10_000_000, step=1_000_000)
    with fc3:
        calc_broker = st.selectbox("Broker", ["bca_sekuritas", "stockbit", "indo_premier", "mirae_asset", "ajaib"])

    if st.button("Hitung"):
        from saham_id.lot_calculator import calculate_lots
        from saham_id.broker_fees import calculate_fees

        lot_result = calculate_lots(budget=calc_budget, price=calc_price)
        fee_result = calculate_fees(price=calc_price, lots=lot_result.lots, broker=calc_broker)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Lot", f"{lot_result.lots}")
        c2.metric("Total Cost", f"Rp {fee_result.total_buy_cost:,.0f}")
        c3.metric("Round-trip Fee", f"Rp {fee_result.round_trip_fee:,.0f}")
        c4.metric("Breakeven", f"Rp {fee_result.breakeven_price:,.0f}")

        st.markdown(f"""
        | Detail | Nilai |
        |--------|-------|
        | Shares | {fee_result.shares:,} |
        | Buy Commission | Rp {fee_result.buy_commission:,.0f} |
        | Sell Commission | Rp {fee_result.sell_commission:,.0f} |
        | Sell Tax (0.1%) | Rp {fee_result.sell_tax:,.0f} |
        | Round-trip % | {fee_result.round_trip_fee_pct*100:.3f}% |
        | Breakeven Ticks | {fee_result.breakeven_ticks} tick |
        | Sisa Cash | Rp {lot_result.remaining_cash:,.0f} |
        """)
