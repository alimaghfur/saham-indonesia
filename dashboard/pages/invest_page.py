"""Investment Advisor page — complete analysis before buy/sell decision."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Investment Advisor")
    st.markdown("Analisis komprehensif sebelum keputusan investasi. **Tujuan: jangan sampai loss.**")

    # --- Controls ---
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        ticker = st.text_input("Ticker", value="BBCA", max_chars=10).upper()
    with col2:
        budget = st.number_input("Budget (Rp)", value=50_000_000, step=10_000_000, min_value=1_000_000)
    with col3:
        risk_pct = st.selectbox("Risk/Trade", [1.0, 1.5, 2.0, 2.5, 3.0], index=2, format_func=lambda x: f"{x}%")

    if st.button("Analisis Investasi", type="primary"):
        try:
            from saham_id.invest import analyze_investment, Verdict, Conviction, MarketRegime

            with st.spinner(f"Menganalisis {ticker}..."):
                decision = analyze_investment(
                    ticker=ticker,
                    budget=budget,
                    risk_tolerance=risk_pct / 100,
                )

            # --- VERDICT BANNER ---
            verdict_colors = {
                "STRONG BUY": ("green", "background-color: #1a472a"),
                "BUY": ("green", "background-color: #2d4a2d"),
                "WAIT": ("orange", "background-color: #4a3a1a"),
                "AVOID": ("red", "background-color: #4a1a1a"),
                "SELL": ("red", "background-color: #5a1a1a"),
            }
            color, bg = verdict_colors.get(decision.verdict.value, ("gray", "background-color: #333"))

            st.markdown(
                f"<div style='{bg}; padding: 20px; border-radius: 10px; text-align: center; margin: 20px 0;'>"
                f"<h1 style='color: {color}; margin: 0;'>{decision.verdict.value}</h1>"
                f"<p style='font-size: 1.2em; margin: 5px 0;'>{decision.summary}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )

            # --- ENTRY SCORE GAUGE ---
            st.markdown("---")
            score_cols = st.columns(4)
            score_cols[0].metric("Entry Score", f"{decision.entry_score:.0f}/100")
            score_cols[1].metric("R:R Ratio", f"{decision.risk_reward.risk_reward_ratio:.1f}:1")
            score_cols[2].metric("Conviction", decision.conviction.value)
            score_cols[3].metric("Market", decision.market_regime.value)

            # --- COMPONENT SCORES ---
            st.markdown("---")
            st.subheader("Component Scores")

            comp_cols = st.columns(6)
            components = [
                ("Trend", decision.trend_score),
                ("Momentum", decision.momentum_score),
                ("Volume", decision.volume_score),
                ("Bandar", decision.bandar_score),
                ("Asing", decision.foreign_flow_score),
                ("S/R Position", decision.support_resistance_score),
            ]
            for i, (name, score) in enumerate(components):
                with comp_cols[i]:
                    bar_color = "green" if score >= 65 else "orange" if score >= 45 else "red"
                    st.metric(name, f"{score:.0f}")
                    st.progress(int(min(score, 100)))

            # --- RISK/REWARD ---
            st.markdown("---")
            st.subheader("Risk / Reward")

            rr = decision.risk_reward
            rr_cols = st.columns(4)
            rr_cols[0].metric("Entry Price", f"Rp {rr.entry_price:,.0f}")
            rr_cols[1].metric("Stop-Loss", f"Rp {rr.stop_loss:,.0f}", delta=f"-{rr.risk_pct:.1f}%")
            rr_cols[2].metric("Target 1", f"Rp {rr.target_1:,.0f}", delta=f"+{(rr.target_1-rr.entry_price)/rr.entry_price*100:.1f}%")
            rr_cols[3].metric("Target 2", f"Rp {rr.target_2:,.0f}", delta=f"+{rr.reward_pct:.1f}%")

            if rr.is_favorable:
                st.success(f"Risk:Reward FAVORABLE — {rr.risk_reward_ratio:.1f}:1 (risiko Rp {rr.risk_amount:,.0f}, potensi Rp {rr.reward_amount:,.0f})")
            else:
                st.warning(f"Risk:Reward KURANG IDEAL — {rr.risk_reward_ratio:.1f}:1 (butuh minimal 2:1)")

            # --- POSITION SIZING ---
            st.markdown("---")
            st.subheader("Position Sizing")

            pos = decision.position
            pos_cols = st.columns(4)
            pos_cols[0].metric("Beli", f"{pos.lots} lot ({pos.shares:,} lembar)")
            pos_cols[1].metric("Modal Dibutuhkan", f"Rp {pos.capital_required:,.0f}")
            pos_cols[2].metric("Max Loss", f"Rp {pos.max_loss:,.0f}")
            pos_cols[3].metric("% Portfolio", f"{pos.pct_of_portfolio:.1f}%")

            # --- EXIT PLAN ---
            st.markdown("---")
            st.subheader("Exit Plan (Aturan Keluar)")

            for condition in decision.exit_plan.exit_conditions:
                st.markdown(f"- {condition}")

            # --- REASONS ---
            st.markdown("---")
            col_bull, col_bear = st.columns(2)

            with col_bull:
                st.subheader("Alasan Bullish")
                if decision.bullish_reasons:
                    for reason in decision.bullish_reasons:
                        st.markdown(f"- :green[{reason}]")
                else:
                    st.caption("Tidak ada sinyal bullish signifikan.")

            with col_bear:
                st.subheader("Alasan Bearish")
                if decision.bearish_reasons:
                    for reason in decision.bearish_reasons:
                        st.markdown(f"- :red[{reason}]")
                else:
                    st.caption("Tidak ada sinyal bearish signifikan.")

            # --- WARNINGS ---
            if decision.warnings:
                st.markdown("---")
                st.subheader("Peringatan")
                for warning in decision.warnings:
                    st.warning(warning)

            # --- ACTION SUMMARY ---
            st.markdown("---")
            if decision.should_buy:
                st.success(
                    f"**REKOMENDASI: {decision.verdict.value} {ticker}**\n\n"
                    f"- Beli **{pos.lots} lot** di Rp {rr.entry_price:,.0f}\n"
                    f"- Stop-loss di Rp {rr.stop_loss:,.0f}\n"
                    f"- Target: Rp {rr.target_1:,.0f} → {rr.target_2:,.0f} → {rr.target_3:,.0f}\n"
                    f"- Max loss: Rp {pos.max_loss:,.0f} ({pos.risk_per_trade:.1f}% risk)"
                )
            else:
                st.info(
                    f"**{decision.verdict.value}** — Belum waktunya beli {ticker}. "
                    f"Tunggu kondisi lebih baik atau cari saham lain."
                )

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            with st.expander("Detail Error"):
                st.code(traceback.format_exc())
