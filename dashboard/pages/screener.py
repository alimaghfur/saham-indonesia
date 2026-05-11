"""Screener page — run swing/intraday screeners interactively."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Stock Screener")
    st.markdown("Filter saham berdasarkan strategi teknikal.")

    # --- Strategy selection ---
    strategy = st.selectbox(
        "Pilih Strategi",
        [
            "Swing Breakout",
            "Swing Pullback",
            "Swing Reversal",
            "BPJS (Beli Pagi Jual Sore)",
            "BSJP (Beli Sore Jual Pagi)",
            "Scalping",
        ],
    )

    # --- Common controls ---
    col1, col2, col3 = st.columns(3)
    with col1:
        universe = st.selectbox("Universe", ["LQ45", "IDX30", "IDX80", "KOMPAS100"])
    with col2:
        top_n = st.slider("Top N results", 5, 30, 15)
    with col3:
        source_name = st.selectbox("Data Source", ["yahoo", "rti", "goapi", "itick", "sectors"])

    # --- Strategy-specific parameters ---
    params = {}

    if strategy == "Swing Breakout":
        params["resistance_window"] = st.slider("Resistance Window (days)", 10, 60, 20)
        params["min_consolidation_days"] = st.slider("Min Consolidation Days", 5, 30, 10)
        params["min_rvol"] = st.slider("Min RVOL", 1.0, 5.0, 1.5, 0.1)

    elif strategy == "Swing Pullback":
        params["trend_ma"] = st.slider("Trend MA", 20, 100, 50)
        params["pullback_ma"] = st.slider("Pullback MA", 5, 50, 20)
        params["proximity_pct"] = st.slider("Proximity %", 0.005, 0.05, 0.02, 0.005)

    elif strategy == "Swing Reversal":
        params["rsi_oversold"] = st.slider("RSI Oversold", 15.0, 40.0, 30.0, 1.0)
        params["rsi_exit"] = st.slider("RSI Exit Zone", 30.0, 60.0, 40.0, 1.0)

    elif strategy in ("BPJS (Beli Pagi Jual Sore)", "BSJP (Beli Sore Jual Pagi)"):
        params["lookback_days"] = st.slider("Lookback Days", 20, 120, 60)
        params["min_win_rate"] = st.slider("Min Win Rate", 0.40, 0.70, 0.55, 0.01)

    elif strategy == "Scalping":
        params["min_atr_pct"] = st.slider("Min ATR %", 0.005, 0.05, 0.015, 0.001)
        params["min_rvol"] = st.slider("Min RVOL", 1.0, 5.0, 2.0, 0.1)

    # --- Run button ---
    if st.button("Run Screener", type="primary"):
        try:
            from saham_id.data.sources import get_source

            src = get_source(source_name)

            with st.spinner(f"Running {strategy}..."):
                result = _run_strategy(strategy, universe, top_n, params, src)

            if result and result.rows:
                st.success(f"Ditemukan {len(result.rows)} kandidat!")

                # Display results
                df = result.to_dataframe()
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Show parameters used
                with st.expander("Parameters"):
                    st.json(result.params)
            else:
                st.warning("Tidak ada saham yang memenuhi kriteria.")

        except Exception as e:
            st.error(f"Error: {e}")


def _run_strategy(strategy: str, universe: str, top_n: int, params: dict, source):
    """Dispatch to the appropriate screener function."""
    if strategy == "Swing Breakout":
        from saham_id.screener.swing.breakout import screen
        return screen(universe=universe, top_n=top_n, source=source, **params)

    elif strategy == "Swing Pullback":
        from saham_id.screener.swing.pullback import screen
        return screen(universe=universe, top_n=top_n, source=source, **params)

    elif strategy == "Swing Reversal":
        from saham_id.screener.swing.reversal import screen
        return screen(universe=universe, top_n=top_n, source=source, **params)

    elif strategy == "BPJS (Beli Pagi Jual Sore)":
        from saham_id.screener.intraday.bpjs import screen
        return screen(universe=universe, top_n=top_n, source=source, **params)

    elif strategy == "BSJP (Beli Sore Jual Pagi)":
        from saham_id.screener.intraday.bsjp import screen
        return screen(universe=universe, top_n=top_n, source=source, **params)

    elif strategy == "Scalping":
        from saham_id.screener.intraday.scalping import screen
        return screen(universe=universe, top_n=top_n, source=source, **params)

    return None
