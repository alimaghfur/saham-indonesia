"""Sector Heatmap page — visual performance grid by sector and stock."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Sector Heatmap")
    st.markdown("Visualisasi performa saham per sektor IDX.")

    # --- Controls ---
    col1, col2 = st.columns(2)
    with col1:
        universe = st.selectbox("Universe", ["LQ45", "IDX30", "IDX80", "KOMPAS100"], index=0)
    with col2:
        period = st.selectbox("Period", ["1D", "1W", "1M", "3M"], index=0)

    st.markdown("---")

    if st.button("Generate Heatmap", type="primary") or "heatmap_data" in st.session_state:
        try:
            from saham_id.market.heatmap import generate_heatmap
            from saham_id.data.sources import get_source

            src = get_source()

            with st.spinner("Mengambil data heatmap..."):
                heatmap = generate_heatmap(universe=universe, period=period, source=src)
                st.session_state["heatmap_data"] = heatmap

            if not heatmap.cells:
                st.warning("Tidak ada data.")
                return

            # --- Summary ---
            avg_change = heatmap.avg_change
            n_gain = len(heatmap.gainers)
            n_lose = len(heatmap.losers)

            sum_cols = st.columns(4)
            sum_cols[0].metric("Total Stocks", len(heatmap.cells))
            sum_cols[1].metric("Avg Change", f"{avg_change * 100:+.2f}%")
            sum_cols[2].metric("Gainers", n_gain)
            sum_cols[3].metric("Losers", n_lose)

            st.markdown("---")

            # --- Heatmap by Sector ---
            st.subheader("Per Sector")
            sectors = heatmap.by_sector()

            for sector_name, cells in sorted(sectors.items()):
                sector_avg = sum(c.change_pct for c in cells) / len(cells) if cells else 0
                color = "green" if sector_avg > 0 else "red" if sector_avg < 0 else "gray"

                with st.expander(f"{sector_name.upper()} ({len(cells)} stocks, avg: {sector_avg * 100:+.2f}%)", expanded=True):
                    # Grid display
                    cols_per_row = 5
                    sorted_cells = sorted(cells, key=lambda c: c.change_pct, reverse=True)

                    for row_start in range(0, len(sorted_cells), cols_per_row):
                        row_cells = sorted_cells[row_start:row_start + cols_per_row]
                        cols = st.columns(cols_per_row)
                        for idx, cell in enumerate(row_cells):
                            with cols[idx]:
                                cell_color = "green" if cell.change_pct > 0 else "red" if cell.change_pct < 0 else "gray"
                                pct_str = f"{cell.change_pct * 100:+.2f}%"
                                st.markdown(
                                    f"<div style='text-align:center; padding:8px; "
                                    f"background-color:{'#1a472a' if cell.change_pct > 0 else '#4a1a1a' if cell.change_pct < 0 else '#333'}; "
                                    f"border-radius:6px; margin:2px;'>"
                                    f"<b>{cell.ticker}</b><br>"
                                    f"<span style='color:{cell_color}'>{pct_str}</span><br>"
                                    f"<small>Rp {cell.last_price:,.0f}</small>"
                                    f"</div>",
                                    unsafe_allow_html=True,
                                )

            # --- Data Table ---
            st.markdown("---")
            with st.expander("Raw Data"):
                df = heatmap.to_dataframe()
                st.dataframe(df.sort_values("change_pct", ascending=False), use_container_width=True)

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            with st.expander("Detail Error"):
                st.code(traceback.format_exc())
