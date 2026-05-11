"""Bandarmology + Foreign Flow page — scan aktivitas bandar & asing."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Bandarmology & Foreign Flow")
    st.markdown("Deteksi aktivitas smart money (bandar) dan investor asing.")

    col1, col2, col3 = st.columns(3)
    with col1:
        universe = st.selectbox("Universe", ["IDX30", "LQ45", "IDX80"], index=1)
    with col2:
        min_score = st.slider("Min Bandar Score", 40, 90, 60)
    with col3:
        source_name = st.selectbox("Source", ["yahoo", "goapi", "itick"], index=0)

    tab1, tab2 = st.tabs(["Bandarmology", "Foreign Flow"])

    with tab1:
        if st.button("Scan Bandar Activity", key="bandar_btn"):
            try:
                from saham_id.analysis.bandarmology import bandar_scan
                from saham_id.data.sources import get_source
                import pandas as pd

                src = get_source(source_name)
                with st.spinner(f"Scanning {universe} untuk aktivitas bandar..."):
                    results = bandar_scan(universe=universe, min_score=min_score, top_n=15, source=src)

                if results:
                    st.success(f"Ditemukan {len(results)} saham dengan indikasi bandar activity!")
                    data = pd.DataFrame([{
                        "Ticker": r.ticker,
                        "Phase": r.phase.value,
                        "Score": f"{r.score:.0f}",
                        "Confidence": f"{r.confidence:.0%}",
                        "Interpretation": r.interpretation[:50],
                    } for r in results])
                    st.dataframe(data, use_container_width=True, hide_index=True)

                    st.markdown("### Detail")
                    for r in results[:5]:
                        emoji = {"ACCUMULATION": "🟢", "MARKUP": "🚀", "DISTRIBUTION": "🟡", "MARKDOWN": "🔴", "NEUTRAL": "⚪"}
                        with st.expander(f"{emoji.get(r.phase.value, '')} {r.ticker} — {r.phase.value} ({r.score:.0f})"):
                            st.write(r.interpretation)
                            if r.money_flow:
                                st.caption(f"Flow Ratio: {r.money_flow.flow_ratio:.2f} | "
                                          f"Buy/Sell Ratio: {r.money_flow.buy_sell_ratio:.2f}")
                            if r.smart_money:
                                st.caption(f"SMI: {r.smart_money.smart_money_index:.0f} | "
                                          f"Stealth: {'Acc' if r.smart_money.stealth_accumulation else 'Dist' if r.smart_money.stealth_distribution else 'None'}")
                else:
                    st.info(f"Tidak ada saham dengan bandar score >= {min_score}")
            except Exception as e:
                st.error(f"Error: {e}")

    with tab2:
        if st.button("Scan Foreign Flow", key="foreign_btn"):
            try:
                from saham_id.analysis.foreign_flow import foreign_net_buy_top, foreign_net_sell_top
                from saham_id.data.sources import get_source
                import pandas as pd

                src = get_source(source_name)
                with st.spinner(f"Scanning foreign flow di {universe}..."):
                    top_buys = foreign_net_buy_top(universe=universe, days=20, top_n=10, source=src)
                    top_sells = foreign_net_sell_top(universe=universe, days=20, top_n=10, source=src)

                buy_col, sell_col = st.columns(2)
                with buy_col:
                    st.markdown("### 🟢 Asing Masuk (Net Buy)")
                    if top_buys:
                        data = pd.DataFrame([{
                            "Ticker": r.ticker,
                            "Net 20D": f"Rp {r.total_net_20d/1e9:.1f}B",
                            "Activity": r.activity.value,
                            "Consistency": f"{r.flow_consistency:.0%}",
                        } for r in top_buys])
                        st.dataframe(data, use_container_width=True, hide_index=True)
                    else:
                        st.info("Tidak ada data")

                with sell_col:
                    st.markdown("### 🔴 Asing Keluar (Net Sell)")
                    if top_sells:
                        data = pd.DataFrame([{
                            "Ticker": r.ticker,
                            "Net 20D": f"Rp {r.total_net_20d/1e9:.1f}B",
                            "Activity": r.activity.value,
                            "Consistency": f"{r.flow_consistency:.0%}",
                        } for r in top_sells])
                        st.dataframe(data, use_container_width=True, hide_index=True)
                    else:
                        st.info("Tidak ada data")
            except Exception as e:
                st.error(f"Error: {e}")
