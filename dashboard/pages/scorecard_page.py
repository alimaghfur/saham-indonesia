"""Score Card page — deep single-stock analysis in dashboard."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Stock Score Card")
    st.markdown("Analisis lengkap satu saham: Teknikal + Bandarmology + Foreign Flow + Patterns + S/R")

    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.text_input("Ticker", value="BBCA", max_chars=10).upper()
    with col2:
        source_name = st.selectbox("Source", ["yahoo", "itick", "goapi"], index=0)

    if st.button("Analisis Lengkap", type="primary"):
        try:
            from saham_id.data.sources import get_source
            from saham_id.scorecard import generate_scorecard
            from saham_id.analysis.bandarmology import bandar_score
            from saham_id.analysis.foreign_flow import estimate_foreign_flow
            from saham_id.analysis.patterns import detect_patterns
            from saham_id.analysis.support_resistance import find_nearest_levels
            from saham_id.signals import swing_buy_engine, swing_sell_engine, Action
            from saham_id.analysis.indicators.ichimoku import ichimoku

            src = get_source(source_name)

            with st.spinner(f"Menganalisis {ticker}..."):
                df = src.get_ohlc(ticker, period="6mo", interval="1d")

            if df.empty or len(df) < 30:
                st.error(f"Data tidak cukup untuk {ticker}")
                return

            # --- Score Card ---
            card = generate_scorecard(ticker, source=src)

            # Header
            score_color = "green" if card.overall_score >= 60 else ("red" if card.overall_score < 40 else "orange")
            st.markdown(f"## {ticker} — :{score_color}[{card.recommendation}] (Score: {card.overall_score:.0f}/100)")
            st.markdown(f"**Harga:** Rp {card.last_price:,.0f} | **Trend:** {card.trend}")

            st.markdown("---")

            # --- Scores ---
            st.subheader("Composite Score")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Overall", f"{card.overall_score:.0f}/100")
            m2.metric("Technical", f"{card.technical_score:.0f}/100")
            m3.metric("Bandarmology", f"{card.bandar_score:.0f}/100")
            m4.metric("Foreign Flow", f"{card.foreign_flow_score:.0f}/100")

            st.markdown("---")

            # --- Bandarmology ---
            st.subheader("Bandarmology")
            try:
                bs = bandar_score(ticker, source=src)
                bc1, bc2, bc3 = st.columns(3)
                phase_emoji = {"ACCUMULATION": "🟢", "MARKUP": "🚀", "DISTRIBUTION": "🟡", "MARKDOWN": "🔴", "NEUTRAL": "⚪"}
                bc1.metric("Phase", f"{phase_emoji.get(bs.phase.value, '')} {bs.phase.value}")
                bc2.metric("Score", f"{bs.score:.0f}/100")
                bc3.metric("Confidence", f"{bs.confidence:.0%}")
                st.info(bs.interpretation)
                if bs.smart_money:
                    st.caption(f"SMI: {bs.smart_money.smart_money_index:.0f} | "
                              f"Stealth Accumulation: {'Yes' if bs.smart_money.stealth_accumulation else 'No'} | "
                              f"Unusual Vol Days: {bs.smart_money.unusual_volume_days}")
            except Exception as e:
                st.warning(f"Bandarmology error: {e}")

            st.markdown("---")

            # --- Foreign Flow ---
            st.subheader("Foreign Flow (Asing)")
            try:
                ff = estimate_foreign_flow(df, ticker=ticker)
                fc1, fc2, fc3 = st.columns(3)
                act_emoji = {"HEAVY_BUYING": "🟢🟢", "BUYING": "🟢", "NEUTRAL": "⚪", "SELLING": "🔴", "HEAVY_SELLING": "🔴🔴"}
                fc1.metric("Activity", f"{act_emoji.get(ff.activity.value, '')} {ff.activity.value}")
                fc2.metric("Net 20D", f"Rp {ff.total_net_20d/1e9:.1f}B")
                fc3.metric("Consistency", f"{ff.flow_consistency:.0%}")
                st.caption(f"Akumulasi: {ff.accumulation_days} hari | Distribusi: {ff.distribution_days} hari")
            except Exception as e:
                st.warning(f"Foreign flow error: {e}")

            st.markdown("---")

            # --- Ichimoku ---
            st.subheader("Ichimoku Cloud")
            try:
                ichi = ichimoku(df["high"], df["low"], df["close"])
                ic1, ic2, ic3 = st.columns(3)
                ic1.metric("Cloud", f"{'🟢' if ichi.cloud_color == 'green' else '🔴'} {ichi.cloud_color.upper()}")
                ic2.metric("Price vs Cloud", ichi.price_vs_cloud.upper())
                ic3.metric("TK Cross", f"{'🟢' if ichi.tk_cross == 'bullish' else '🔴'} {ichi.tk_cross}")
            except Exception as e:
                st.warning(f"Ichimoku error: {e}")

            st.markdown("---")

            # --- Patterns ---
            st.subheader("Candlestick Patterns (Last 5 bars)")
            patterns = detect_patterns(df, lookback=5)
            if patterns:
                for p in patterns[:5]:
                    emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}[p.bias.value]
                    st.markdown(f"{emoji} **{p.name}** ({p.reliability.value}) — {p.description}")
            else:
                st.info("Tidak ada pola candlestick terdeteksi.")

            st.markdown("---")

            # --- Support & Resistance ---
            st.subheader("Support & Resistance")
            levels = find_nearest_levels(df, n=3)
            lc1, lc2 = st.columns(2)
            with lc1:
                st.markdown("**Resistance (atas):**")
                for r in levels.get("resistance", []):
                    st.markdown(f"- Rp {r:,.0f}")
            with lc2:
                st.markdown("**Support (bawah):**")
                for s in levels.get("support", []):
                    st.markdown(f"- Rp {s:,.0f}")

            st.markdown("---")

            # --- Signal Engines ---
            st.subheader("Signal Engine")
            buy_eng = swing_buy_engine()
            sell_eng = swing_sell_engine()
            buy_sig = buy_eng.evaluate(df, ticker=ticker)
            sell_sig = sell_eng.evaluate(df, ticker=ticker)

            sg1, sg2 = st.columns(2)
            with sg1:
                color = "green" if buy_sig.action == Action.BUY else "gray"
                st.markdown(f"**Buy Engine:** :{color}[{buy_sig.action.value}] ({buy_sig.confidence:.0%})")
                for r in buy_sig.reasons[:4]:
                    st.caption(f"  • {r}")
            with sg2:
                color = "red" if sell_sig.action == Action.SELL else "gray"
                st.markdown(f"**Sell Engine:** :{color}[{sell_sig.action.value}] ({sell_sig.confidence:.0%})")
                for r in sell_sig.reasons[:4]:
                    st.caption(f"  • {r}")

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            st.code(traceback.format_exc())
