"""Real-time Streaming page — live price ticker via polling.

Displays live-updating prices for selected tickers using auto-refresh.
Uses iTick REST API (or any configured source) with periodic polling
since Streamlit doesn't natively support WebSocket push.

Features:
- Live price table with color-coded changes
- Auto-refresh every N seconds
- Configurable ticker watchlist
- Mini sparkline of recent prices
- Volume bar indicator
"""

from __future__ import annotations

import time
from datetime import datetime

import streamlit as st


def render() -> None:
    st.title("Real-time Streaming")
    st.markdown("Live price updates untuk saham IDX (auto-refresh).")

    # --- Controls ---
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        tickers_input = st.text_input(
            "Tickers (comma-separated)",
            value="BBCA, BBRI, TLKM, ASII, BMRI",
            help="Masukkan ticker dipisah koma",
        )
    with col2:
        refresh_interval = st.selectbox(
            "Refresh (detik)",
            [5, 10, 15, 30, 60],
            index=1,
        )
    with col3:
        source_name = st.selectbox(
            "Source",
            ["yahoo", "itick", "goapi"],
            index=0,
        )

    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    if not tickers:
        st.warning("Masukkan minimal satu ticker.")
        return

    # --- Auto-refresh toggle ---
    auto_refresh = st.checkbox("Auto-Refresh", value=True)

    st.markdown("---")

    # --- Fetch & Display ---
    _fetch_and_display(tickers, source_name)

    # --- Auto-refresh logic ---
    if auto_refresh:
        time.sleep(0.1)  # Small delay to prevent immediate re-run
        st.markdown(
            f"<meta http-equiv='refresh' content='{refresh_interval}'>",
            unsafe_allow_html=True,
        )
        st.caption(
            f"Auto-refresh setiap {refresh_interval} detik. "
            f"Terakhir update: {datetime.now().strftime('%H:%M:%S')}"
        )


def _fetch_and_display(tickers: list[str], source_name: str) -> None:
    """Fetch quotes and display as a live table."""
    try:
        from saham_id.data.sources import get_source
        from saham_id.errors import error_boundary, ErrorCollector

        src = get_source(source_name)
        collector = ErrorCollector()
        quotes = []

        with st.spinner(f"Fetching {len(tickers)} quotes dari {source_name}..."):
            for ticker in tickers:
                with collector.catch(ticker):
                    q = src.get_quote(ticker)
                    quotes.append(q)

        if collector.has_errors:
            st.warning(f"Gagal fetch: {collector.error_count} ticker(s)")

        if not quotes:
            st.error("Tidak ada data yang berhasil diambil.")
            return

        # --- Price Table ---
        st.subheader("Live Prices")

        # Header
        cols = st.columns([2, 2, 2, 2, 2, 3])
        cols[0].markdown("**Ticker**")
        cols[1].markdown("**Last**")
        cols[2].markdown("**Change**")
        cols[3].markdown("**Change %**")
        cols[4].markdown("**Volume**")
        cols[5].markdown("**Bid / Ask**")

        # Rows
        for q in quotes:
            cols = st.columns([2, 2, 2, 2, 2, 3])

            # Determine color
            change = float(q.last - q.prev_close) if q.prev_close else 0
            change_pct = (change / float(q.prev_close) * 100) if q.prev_close and float(q.prev_close) != 0 else 0

            if change > 0:
                color = "green"
                arrow = "+"
            elif change < 0:
                color = "red"
                arrow = ""
            else:
                color = "gray"
                arrow = ""

            cols[0].markdown(f"**{q.ticker}**")
            cols[1].markdown(f"Rp {float(q.last):,.0f}")
            cols[2].markdown(f":{color}[{arrow}{change:,.0f}]")
            cols[3].markdown(f":{color}[{arrow}{change_pct:.2f}%]")
            cols[4].markdown(f"{q.volume:,}")

            bid_str = f"Rp {float(q.bid):,.0f}" if q.bid else "-"
            ask_str = f"Rp {float(q.ask):,.0f}" if q.ask else "-"
            cols[5].markdown(f"{bid_str} / {ask_str}")

        # --- Summary Stats ---
        st.markdown("---")
        st.subheader("Ringkasan")

        gainers = [q for q in quotes if q.prev_close and q.last > q.prev_close]
        losers = [q for q in quotes if q.prev_close and q.last < q.prev_close]
        unchanged = [q for q in quotes if q.prev_close and q.last == q.prev_close]

        sum_cols = st.columns(4)
        sum_cols[0].metric("Total Tickers", len(quotes))
        sum_cols[1].metric("Gainers", len(gainers))
        sum_cols[2].metric("Losers", len(losers))
        sum_cols[3].metric("Unchanged", len(unchanged))

        # Top mover
        if quotes:
            best = max(
                quotes,
                key=lambda q: (float(q.last) - float(q.prev_close)) / float(q.prev_close) * 100
                if q.prev_close and float(q.prev_close) != 0 else 0,
            )
            worst = min(
                quotes,
                key=lambda q: (float(q.last) - float(q.prev_close)) / float(q.prev_close) * 100
                if q.prev_close and float(q.prev_close) != 0 else 0,
            )

            best_pct = (float(best.last) - float(best.prev_close)) / float(best.prev_close) * 100 if best.prev_close else 0
            worst_pct = (float(worst.last) - float(worst.prev_close)) / float(worst.prev_close) * 100 if worst.prev_close else 0

            mover_cols = st.columns(2)
            mover_cols[0].metric(
                f"Best: {best.ticker}",
                f"Rp {float(best.last):,.0f}",
                delta=f"{best_pct:+.2f}%",
            )
            mover_cols[1].metric(
                f"Worst: {worst.ticker}",
                f"Rp {float(worst.last):,.0f}",
                delta=f"{worst_pct:+.2f}%",
            )

        # --- WebSocket info ---
        with st.expander("WebSocket Streaming (Advanced)"):
            st.markdown("""
            Untuk streaming real-time via WebSocket (tanpa polling), gunakan Python API:

            ```python
            import asyncio
            from saham_id.data.sources.itick import ITickSource

            async def main():
                src = ITickSource()
                async for tick in await src.stream_ticks(["BBCA", "BBRI"]):
                    print(f"{tick}")

            asyncio.run(main())
            ```

            Requires: `pip install websockets` dan `ITICK_API_KEY` set di `.env`.
            """)

    except ImportError as e:
        st.error(f"Module tidak ditemukan: {e}")
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        with st.expander("Detail Error"):
            st.code(traceback.format_exc())
