"""Investment Advisor — Professional analysis page."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    # --- Header ---
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h2 style="margin:0; color:#f1f5f9;">Investment Advisor</h2>
            <p style="color:#94a3b8; margin:4px 0 0 0; font-size:0.9em;">
                Analisis komprehensif sebelum keputusan investasi — <strong>tujuan: jangan sampai loss.</strong>
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Input Controls ---
    with st.container():
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1.5])
        with col1:
            ticker = st.text_input("Ticker", value="BBCA", max_chars=10, placeholder="Masukkan ticker").upper()
        with col2:
            budget = st.number_input("Budget (Rp)", value=50_000_000, step=10_000_000, min_value=1_000_000)
        with col3:
            risk_pct = st.selectbox("Risk/Trade", [1.0, 1.5, 2.0, 2.5, 3.0], index=2, format_func=lambda x: f"{x}%")
        with col4:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            analyze_btn = st.button("Analisis Sekarang", type="primary", use_container_width=True)

    if not analyze_btn:
        # Show placeholder
        st.markdown(
            """
            <div style="text-align:center; padding: 60px 20px; color: #64748b;">
                <div style="font-size: 1.1em; font-weight: 500;">Masukkan ticker dan klik "Analisis Sekarang"</div>
                <div style="font-size: 0.85em; margin-top: 8px;">
                    Sistem akan menganalisis trend, momentum, bandar, foreign flow, dan risk/reward
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # --- Run Analysis ---
    try:
        from saham_id.invest import analyze_investment

        with st.spinner(f"Menganalisis {ticker}..."):
            decision = analyze_investment(
                ticker=ticker,
                budget=budget,
                risk_tolerance=risk_pct / 100,
            )

        # === VERDICT BANNER ===
        verdict_config = {
            "STRONG BUY": ("#22c55e", "rgba(34,197,94,0.1)", "border-color: #22c55e"),
            "BUY": ("#4ade80", "rgba(74,222,128,0.08)", "border-color: #4ade80"),
            "WAIT": ("#f59e0b", "rgba(245,158,11,0.08)", "border-color: #f59e0b"),
            "AVOID": ("#ef4444", "rgba(239,68,68,0.08)", "border-color: #ef4444"),
            "SELL": ("#dc2626", "rgba(220,38,38,0.1)", "border-color: #dc2626"),
        }
        color, bg, border = verdict_config.get(
            decision.verdict.value, ("#94a3b8", "rgba(148,163,184,0.08)", "border-color: #475569")
        )

        st.markdown(
            f"""
            <div style="background:{bg}; border: 2px solid {color}; border-radius:14px;
                        padding:24px; text-align:center; margin:16px 0 24px 0;">
                <div style="font-size:2.2em; font-weight:800; color:{color}; letter-spacing:1px;">
                    {decision.verdict.value}
                </div>
                <div style="font-size:0.95em; color:#94a3b8; margin-top:8px;">
                    {decision.summary}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # === KEY METRICS ROW ===
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Entry Score", f"{decision.entry_score:.0f}/100")
        m2.metric("R:R Ratio", f"{decision.risk_reward.risk_reward_ratio:.1f}:1")
        m3.metric("Conviction", decision.conviction.value)
        m4.metric("Market", decision.market_regime.value)

        st.markdown("")

        # === COMPONENT SCORES ===
        st.markdown("##### Component Scores")
        components = [
            ("Trend", decision.trend_score, "T"),
            ("Momentum", decision.momentum_score, "M"),
            ("Volume", decision.volume_score, "V"),
            ("Bandar", decision.bandar_score, "B"),
            ("Foreign Flow", decision.foreign_flow_score, "F"),
            ("S/R Position", decision.support_resistance_score, "S"),
        ]

        cols = st.columns(6)
        for i, (name, score, icon) in enumerate(components):
            with cols[i]:
                score_color = "#22c55e" if score >= 65 else "#f59e0b" if score >= 45 else "#ef4444"
                st.markdown(
                    f"""
                    <div style="text-align:center; padding:12px 8px; background:#1a1f2e;
                                border-radius:10px; border:1px solid #2a3040;">
                        <div style="font-size:1.3em;">{icon}</div>
                        <div style="font-size:0.75em; color:#94a3b8; margin:4px 0;">{name}</div>
                        <div style="font-size:1.2em; font-weight:700; color:{score_color};">{score:.0f}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("")

        # === RISK / REWARD ===
        st.markdown("##### Risk / Reward")
        rr = decision.risk_reward

        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Entry Price", f"Rp {rr.entry_price:,.0f}")
        r2.metric("Stop-Loss", f"Rp {rr.stop_loss:,.0f}", delta=f"-{rr.risk_pct:.1f}%")
        r3.metric("Target 1", f"Rp {rr.target_1:,.0f}", delta=f"+{(rr.target_1-rr.entry_price)/rr.entry_price*100:.1f}%")
        r4.metric("Target 2", f"Rp {rr.target_2:,.0f}", delta=f"+{rr.reward_pct:.1f}%")

        if rr.is_favorable:
            st.success(f"Risk:Reward FAVORABLE — {rr.risk_reward_ratio:.1f}:1 (risiko Rp {rr.risk_amount:,.0f}, potensi Rp {rr.reward_amount:,.0f})")
        else:
            st.warning(f"Risk:Reward KURANG IDEAL — {rr.risk_reward_ratio:.1f}:1 (butuh minimal 2:1)")

        st.markdown("")

        # === POSITION SIZING ===
        st.markdown("##### Position Sizing")
        pos = decision.position
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Beli", f"{pos.lots} lot ({pos.shares:,} lbr)")
        p2.metric("Modal", f"Rp {pos.capital_required:,.0f}")
        p3.metric("Max Loss", f"Rp {pos.max_loss:,.0f}")
        p4.metric("% Portfolio", f"{pos.pct_of_portfolio:.1f}%")

        st.markdown("")

        # === EXIT PLAN ===
        with st.expander("Exit Plan (Aturan Keluar)", expanded=False):
            for condition in decision.exit_plan.exit_conditions:
                st.markdown(f"- {condition}")

        # === REASONS ===
        col_bull, col_bear = st.columns(2)

        with col_bull:
            with st.expander("Alasan Bullish", expanded=True):
                if decision.bullish_reasons:
                    for reason in decision.bullish_reasons:
                        st.markdown(f"- {reason}")
                else:
                    st.caption("Tidak ada sinyal bullish signifikan.")

        with col_bear:
            with st.expander("Alasan Bearish", expanded=True):
                if decision.bearish_reasons:
                    for reason in decision.bearish_reasons:
                        st.markdown(f"- {reason}")
                else:
                    st.caption("Tidak ada sinyal bearish signifikan.")

        # === WARNINGS ===
        if decision.warnings:
            st.markdown("##### Peringatan")
            for warning in decision.warnings:
                st.warning(warning)

        # === ACTION SUMMARY ===
        st.markdown("---")
        if decision.should_buy:
            st.success(
                f"**REKOMENDASI: {decision.verdict.value} {ticker}**\n\n"
                f"- Beli **{pos.lots} lot** di Rp {rr.entry_price:,.0f}\n"
                f"- Stop-loss di Rp {rr.stop_loss:,.0f}\n"
                f"- Target: Rp {rr.target_1:,.0f} > {rr.target_2:,.0f} > {rr.target_3:,.0f}\n"
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
