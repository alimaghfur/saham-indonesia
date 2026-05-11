"""Signals page — real-time buy/sell signals from composite indicator engine."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Sinyal Trading")
    st.markdown("Sinyal BUY/SELL dari composite indicator engine (RSI + MACD + BB + SMA + Volume).")

    # --- Controls ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        universe = st.selectbox("Universe", ["IDX30", "LQ45", "IDX80", "KOMPAS100"], index=0)
    with col2:
        engine_type = st.selectbox("Engine", ["Swing Buy", "Swing Sell", "Scalping"], index=0)
    with col3:
        min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.3, 0.05)
    with col4:
        source_name = st.selectbox("Source", ["yahoo", "itick", "goapi"], index=0)

    engine_map = {"Swing Buy": "swing_buy", "Swing Sell": "swing_sell", "Scalping": "scalping"}
    engine_key = engine_map[engine_type]

    if st.button("Generate Sinyal", type="primary"):
        try:
            from saham_id.signals import (
                generate_signals, swing_buy_engine, swing_sell_engine,
                scalping_engine, Action,
            )
            from saham_id.data.sources import get_source
            from saham_id.data.universe import get_universe

            src = get_source(source_name)
            tickers = get_universe(universe)
            engines = {"swing_buy": swing_buy_engine, "swing_sell": swing_sell_engine, "scalping": scalping_engine}
            engine = engines[engine_key]()

            with st.spinner(f"Scanning {len(tickers)} saham..."):
                signals = generate_signals(tickers, engine=engine, source=src)

            actionable = [s for s in signals if s.action != Action.HOLD and s.confidence >= min_confidence]
            buy_signals = [s for s in actionable if s.action == Action.BUY]
            sell_signals = [s for s in actionable if s.action == Action.SELL]

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Scanned", len(signals))
            m2.metric("BUY Signals", len(buy_signals))
            m3.metric("SELL Signals", len(sell_signals))
            m4.metric("HOLD", len(signals) - len(actionable))

            if buy_signals:
                st.subheader(f"BUY Signals ({len(buy_signals)})")
                import pandas as pd
                df = pd.DataFrame([{
                    "Ticker": s.ticker, "Confidence": f"{s.confidence:.0%}",
                    "Score": f"{s.score:+.3f}", "RSI": f"{s.indicators.get('rsi',0):.1f}",
                    "RVOL": f"{s.indicators.get('rvol',0):.2f}",
                    "Close": f"{s.indicators.get('close',0):,.0f}",
                    "Reasons": "; ".join(s.reasons[:3]),
                } for s in buy_signals[:20]])
                st.dataframe(df, use_container_width=True, hide_index=True)

            if sell_signals:
                st.subheader(f"SELL Signals ({len(sell_signals)})")
                import pandas as pd
                df = pd.DataFrame([{
                    "Ticker": s.ticker, "Confidence": f"{s.confidence:.0%}",
                    "Score": f"{s.score:+.3f}", "RSI": f"{s.indicators.get('rsi',0):.1f}",
                    "Close": f"{s.indicators.get('close',0):,.0f}",
                    "Reasons": "; ".join(s.reasons[:3]),
                } for s in sell_signals[:20]])
                st.dataframe(df, use_container_width=True, hide_index=True)

            if not actionable:
                st.info("Tidak ada sinyal yang memenuhi kriteria.")

        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")

    # --- Single Stock Detail ---
    st.subheader("Detail Sinyal Per Saham")
    detail_ticker = st.text_input("Ticker", value="BBCA", max_chars=10).upper()

    if st.button("Analisis Detail"):
        try:
            from saham_id.signals import swing_buy_engine, swing_sell_engine, Action, _extract_indicators
            from saham_id.data.sources import get_source
            from saham_id.analysis.patterns import detect_patterns
            from saham_id.analysis.support_resistance import find_nearest_levels

            src = get_source(source_name)
            with st.spinner(f"Menganalisis {detail_ticker}..."):
                df = src.get_ohlc(detail_ticker, period="6mo", interval="1d")

            if df.empty or len(df) < 30:
                st.error(f"Data tidak cukup untuk {detail_ticker}")
                return

            indicators = _extract_indicators(df)

            st.markdown("#### Indikator Teknikal")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("RSI", f"{indicators.get('rsi',0):.1f}")
            c2.metric("MACD", "Bullish" if indicators.get("macd_bullish") == 1 else "Bearish")
            c3.metric("RVOL", f"{indicators.get('rvol',0):.2f}x")
            c4.metric("ATR%", f"{indicators.get('atr_pct',0)*100:.2f}%")

            # Signal from engines
            buy_engine = swing_buy_engine()
            sell_engine = swing_sell_engine()
            buy_sig = buy_engine.evaluate(df, ticker=detail_ticker)
            sell_sig = sell_engine.evaluate(df, ticker=detail_ticker)

            st.markdown("#### Hasil Engine")
            sc1, sc2 = st.columns(2)
            with sc1:
                color = "green" if buy_sig.action == Action.BUY else "gray"
                st.markdown(f"**Buy Engine:** :{color}[{buy_sig.action.value}] ({buy_sig.confidence:.0%})")
                for r in buy_sig.reasons[:3]:
                    st.caption(f"  - {r}")
            with sc2:
                color = "red" if sell_sig.action == Action.SELL else "gray"
                st.markdown(f"**Sell Engine:** :{color}[{sell_sig.action.value}] ({sell_sig.confidence:.0%})")
                for r in sell_sig.reasons[:3]:
                    st.caption(f"  - {r}")

            # Patterns
            patterns = detect_patterns(df, lookback=5)
            if patterns:
                st.markdown("#### Candlestick Patterns")
                for p in patterns[:5]:
                    emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}[p.bias.value]
                    st.markdown(f"{emoji} **{p.name}** — {p.description}")

            # S/R Levels
            levels = find_nearest_levels(df, n=3)
            st.markdown("#### Support & Resistance")
            lr1, lr2 = st.columns(2)
            with lr1:
                st.markdown(f"**Resistance:** {', '.join(f'Rp {r:,.0f}' for r in levels.get('resistance', []))}")
            with lr2:
                st.markdown(f"**Support:** {', '.join(f'Rp {s:,.0f}' for s in levels.get('support', []))}")

        except Exception as e:
            st.error(f"Error: {e}")
