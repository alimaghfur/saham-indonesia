"""Backtest page — run strategies on historical data and view performance."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Backtesting")
    st.markdown("Uji strategi trading pada data historis.")

    # --- Controls ---
    col1, col2, col3 = st.columns(3)
    with col1:
        ticker = st.text_input("Ticker", value="BBCA", max_chars=10).upper()
    with col2:
        strategy_name = st.selectbox(
            "Strategi",
            ["BPJS (Buy Open, Sell Close)", "Swing Pullback (MA20/MA50)"],
        )
    with col3:
        period = st.selectbox("Period", ["6mo", "1y", "2y", "5y"], index=1)

    col4, col5, col6 = st.columns(3)
    with col4:
        initial_capital = st.number_input(
            "Modal Awal (Rp)", value=100_000_000, step=10_000_000, format="%d"
        )
    with col5:
        commission_bps = st.slider("Komisi (bps per side)", 0, 50, 15)
    with col6:
        source_name = st.selectbox("Data Source", ["yahoo", "goapi", "itick"], index=0)

    # --- Run Backtest ---
    if st.button("Run Backtest", type="primary"):
        try:
            from saham_id.data.sources import get_source
            from saham_id.backtest.engine import Backtester
            from saham_id.backtest.metrics import compute_metrics
            from saham_id.backtest.strategies import bpjs_strategy, swing_pullback_strategy
            from saham_id.analysis.indicators import sma
            import pandas as pd

            src = get_source(source_name)

            with st.spinner(f"Fetching {ticker} data ({period})..."):
                df = src.get_ohlc(ticker, period=period, interval="1d")

            if df.empty or len(df) < 30:
                st.error(f"Data tidak cukup untuk {ticker} (hanya {len(df)} bars)")
                return

            # Add moving averages for swing pullback
            if "Swing" in strategy_name:
                df["ma_20"] = sma(df["close"], 20)
                df["ma_50"] = sma(df["close"], 50)
                strategy_fn = swing_pullback_strategy
            else:
                strategy_fn = bpjs_strategy

            with st.spinner("Running backtest..."):
                bt = Backtester(
                    strategy=strategy_fn,
                    initial_capital=float(initial_capital),
                    commission_bps=float(commission_bps),
                )
                result = bt.run(df)
                metrics = compute_metrics(result)

            # --- Display Results ---
            st.subheader("Hasil Backtest")

            # Key metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Return", f"{metrics.total_return*100:.2f}%")
            m2.metric("CAGR", f"{metrics.cagr*100:.2f}%")
            m3.metric("Sharpe Ratio", f"{metrics.sharpe:.2f}")
            m4.metric("Max Drawdown", f"{metrics.max_drawdown*100:.2f}%")

            m5, m6, m7, m8 = st.columns(4)
            m5.metric("Win Rate", f"{metrics.win_rate*100:.1f}%")
            m6.metric("Total Trades", metrics.num_trades)
            m7.metric("Profit Factor", f"{metrics.profit_factor:.2f}")
            m8.metric("Avg Trade", f"{metrics.avg_trade_pct*100:.3f}%")

            # Capital summary
            st.markdown(f"""
            | | Nilai |
            |---|---|
            | Modal Awal | Rp {initial_capital:,.0f} |
            | Modal Akhir | Rp {result.final_capital:,.0f} |
            | Profit/Loss | Rp {result.final_capital - initial_capital:,.0f} |
            """)

            # Equity curve
            st.subheader("Equity Curve")
            equity_data = pd.DataFrame({
                "Equity": result.equity_curve.values,
            }, index=result.equity_curve.index)
            st.line_chart(equity_data, use_container_width=True)

            # Trade log
            if result.trades:
                st.subheader(f"Trade Log ({len(result.trades)} trades)")
                trade_data = pd.DataFrame([
                    {
                        "Entry Time": t.entry_time,
                        "Exit Time": t.exit_time,
                        "Entry Price": f"{t.entry_price:,.0f}",
                        "Exit Price": f"{t.exit_price:,.0f}" if t.exit_price else "-",
                        "Qty": t.quantity,
                        "P/L": f"Rp {t.pnl:,.0f}",
                        "P/L %": f"{t.pnl_pct*100:.2f}%",
                    }
                    for t in result.trades
                ])
                st.dataframe(trade_data, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())
