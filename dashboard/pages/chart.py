"""Technical Chart page — interactive charting with indicators.

Dedicated page for full technical analysis:
- Candlestick / OHLC with MA overlay
- Single & multi-indicator panels
- Support/Resistance visualization
- Customizable timeframe & indicators
"""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Technical Chart")
    st.markdown("Analisis teknikal interaktif untuk saham IDX.")

    # --- Controls ---
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        ticker = st.text_input("Ticker", value="BBCA", max_chars=10).upper()
    with col2:
        period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2)
    with col3:
        interval = st.selectbox("Interval", ["1d", "1wk", "1mo"], index=0)

    # --- Chart type & options ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("Chart Options")
    chart_type = st.sidebar.radio("Chart Type", ["Candlestick", "OHLC"], index=0)
    dark_mode = st.sidebar.checkbox("Dark Mode", value=True)
    show_volume = st.sidebar.checkbox("Show Volume", value=True)

    # Moving Averages
    st.sidebar.subheader("Moving Averages")
    ma_20 = st.sidebar.checkbox("MA 20", value=True)
    ma_50 = st.sidebar.checkbox("MA 50", value=True)
    ma_200 = st.sidebar.checkbox("MA 200", value=False)

    ma_periods = []
    if ma_20:
        ma_periods.append(20)
    if ma_50:
        ma_periods.append(50)
    if ma_200:
        ma_periods.append(200)

    # Indicators
    st.sidebar.subheader("Indicators")
    available_indicators = ["RSI", "MACD", "Bollinger Bands", "Stochastic", "ATR", "Volume"]
    selected_indicators = st.sidebar.multiselect(
        "Pilih Indikator",
        available_indicators,
        default=["RSI", "MACD"],
    )

    # Map display names to internal names
    indicator_map = {
        "RSI": "rsi",
        "MACD": "macd",
        "Bollinger Bands": "bollinger",
        "Stochastic": "stochastic",
        "ATR": "atr",
        "Volume": "volume",
    }

    # Support/Resistance
    st.sidebar.subheader("Support / Resistance")
    show_sr = st.sidebar.checkbox("Auto S/R Levels", value=False)

    # --- Fetch data & render chart ---
    if st.button("Generate Chart", type="primary") or "chart_data" in st.session_state:
        try:
            from saham_id.data.sources import get_source
            from saham_id.charting.candlestick import candlestick_chart, ohlc_chart
            from saham_id.charting.indicators import indicator_chart, multi_indicator_chart

            with st.spinner(f"Mengambil data {ticker}..."):
                src = get_source()
                df = src.get_ohlc(ticker, period=period, interval=interval)
                st.session_state["chart_data"] = df
                st.session_state["chart_ticker"] = ticker

            if df.empty:
                st.warning(f"Tidak ada data untuk {ticker}.")
                return

            # Info bar
            last_price = df["close"].iloc[-1]
            prev_price = df["close"].iloc[-2] if len(df) > 1 else last_price
            change = last_price - prev_price
            change_pct = (change / prev_price) * 100

            info_col1, info_col2, info_col3, info_col4 = st.columns(4)
            info_col1.metric("Last Price", f"Rp {last_price:,.0f}")
            info_col2.metric("Change", f"Rp {change:,.0f}", delta=f"{change_pct:.2f}%")
            info_col3.metric("High", f"Rp {df['high'].iloc[-1]:,.0f}")
            info_col4.metric("Low", f"Rp {df['low'].iloc[-1]:,.0f}")

            st.markdown("---")

            # --- Main Chart (Candlestick / OHLC) ---
            st.subheader(f"{ticker} - {chart_type}")

            # Calculate S/R levels if enabled
            support_levels = None
            resistance_levels = None
            if show_sr:
                support_levels, resistance_levels = _auto_sr_levels(df)

            if chart_type == "Candlestick":
                fig = candlestick_chart(
                    df,
                    ticker=ticker,
                    ma_periods=ma_periods if ma_periods else None,
                    show_volume=show_volume,
                    support_levels=support_levels,
                    resistance_levels=resistance_levels,
                    height=600,
                    dark=dark_mode,
                )
            else:
                fig = ohlc_chart(
                    df,
                    ticker=ticker,
                    show_volume=show_volume,
                    height=600,
                    dark=dark_mode,
                )

            st.plotly_chart(fig, use_container_width=True)

            # --- Indicator Charts ---
            if selected_indicators:
                st.markdown("---")
                st.subheader("Technical Indicators")

                # Multi-indicator panel view
                indicators_internal = [
                    indicator_map[ind] for ind in selected_indicators
                    if ind != "Bollinger Bands"  # BB shown separately as overlay
                ]

                # Bollinger Bands as overlay chart
                if "Bollinger Bands" in selected_indicators:
                    st.markdown("#### Bollinger Bands")
                    fig_bb = indicator_chart(
                        df, indicator="bollinger", ticker=ticker,
                        period=20, height=400, dark=dark_mode,
                    )
                    st.plotly_chart(fig_bb, use_container_width=True)

                # Other indicators in multi-panel
                if indicators_internal:
                    fig_multi = multi_indicator_chart(
                        df,
                        indicators=indicators_internal,
                        ticker=ticker,
                        height=250 + 200 * len(indicators_internal),
                        dark=dark_mode,
                    )
                    st.plotly_chart(fig_multi, use_container_width=True)

            # --- Data table ---
            with st.expander("Raw Data (OHLCV)"):
                st.dataframe(
                    df.tail(20).sort_index(ascending=False),
                    use_container_width=True,
                )

        except Exception as e:
            st.error(f"Error: {e}")
            import traceback
            with st.expander("Detail Error"):
                st.code(traceback.format_exc())


def _auto_sr_levels(df, lookback: int = 60) -> tuple[list[float], list[float]]:
    """Calculate simple support/resistance levels from recent price action."""
    recent = df.tail(lookback)

    # Simple pivot-based S/R
    high = float(recent["high"].max())
    low = float(recent["low"].min())
    close = float(recent["close"].iloc[-1])

    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    r2 = pivot + (high - low)
    s1 = 2 * pivot - high
    s2 = pivot - (high - low)

    support_levels = [round(s1, 0), round(s2, 0)]
    resistance_levels = [round(r1, 0), round(r2, 0)]

    # Filter out levels too far from current price (>15%)
    support_levels = [s for s in support_levels if s > close * 0.85]
    resistance_levels = [r for r in resistance_levels if r < close * 1.15]

    return support_levels, resistance_levels
