"""Market Overview page — breadth, movers, trending stocks."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    st.title("Market Overview")
    st.markdown("Ringkasan pasar IDX hari ini.")

    # --- Controls ---
    col1, col2, col3 = st.columns(3)
    with col1:
        universe = st.selectbox("Universe", ["LQ45", "IDX30", "IDX80", "KOMPAS100"], index=0)
    with col2:
        period = st.selectbox("Period", ["1D", "1W", "1M", "3M"], index=0)
    with col3:
        top_n = st.slider("Top N", 5, 30, 10)

    # --- Market Breadth ---
    st.subheader("Market Breadth")
    try:
        from saham_id.market.breadth import snapshot
        from saham_id.data.sources import get_source

        src = get_source()

        with st.spinner("Mengambil data breadth..."):
            snap = snapshot(universe=universe, source=src)

        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
        b_col1.metric("Advancers", snap.advancers)
        b_col2.metric("Decliners", snap.decliners)
        b_col3.metric("Unchanged", snap.unchanged)
        b_col4.metric("A/D Ratio", f"{snap.ad_ratio:.2f}")

        col_nh, col_nl = st.columns(2)
        col_nh.metric("New 52w Highs", snap.new_highs_52w)
        col_nl.metric("New 52w Lows", snap.new_lows_52w)

    except Exception as e:
        st.error(f"Error fetching breadth: {e}")

    st.markdown("---")

    # --- Top Movers ---
    col_gain, col_lose = st.columns(2)

    with col_gain:
        st.subheader("Top Gainers")
        try:
            from saham_id.market.movers import top_gainers

            with st.spinner("Loading gainers..."):
                gainers = top_gainers(universe=universe, period=period, top_n=top_n, source=src)

            if gainers:
                import pandas as pd
                df = pd.DataFrame([
                    {
                        "Ticker": m.ticker,
                        "Last": float(m.last),
                        "Change %": f"{m.change_pct*100:.2f}%",
                        "Volume": f"{m.volume:,}",
                    }
                    for m in gainers
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No gainers found.")
        except Exception as e:
            st.error(f"Error: {e}")

    with col_lose:
        st.subheader("Top Losers")
        try:
            from saham_id.market.movers import top_losers

            with st.spinner("Loading losers..."):
                losers = top_losers(universe=universe, period=period, top_n=top_n, source=src)

            if losers:
                import pandas as pd
                df = pd.DataFrame([
                    {
                        "Ticker": m.ticker,
                        "Last": float(m.last),
                        "Change %": f"{m.change_pct*100:.2f}%",
                        "Volume": f"{m.volume:,}",
                    }
                    for m in losers
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No losers found.")
        except Exception as e:
            st.error(f"Error: {e}")

    st.markdown("---")

    # --- Trending Stocks ---
    st.subheader("Trending Stocks")
    try:
        from saham_id.market.trending import detect

        timeframe_map = {"1D": "1D", "1W": "1W", "1M": "1M", "3M": "1M"}
        tf = timeframe_map.get(period, "1D")

        with st.spinner("Detecting trending stocks..."):
            result = detect(universe=universe, timeframe=tf, top_n=top_n, source=src)

        if result.rows:
            df = result.to_dataframe()
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No trending stocks detected.")
    except Exception as e:
        st.error(f"Error: {e}")

    # --- Unusual Activity ---
    st.subheader("Unusual Activity")
    try:
        from saham_id.market.unusual_activity import detect as detect_unusual

        with st.spinner("Detecting unusual activity..."):
            unusual = detect_unusual(universe=universe, top_n=top_n, source=src)

        if unusual.rows:
            df = unusual.to_dataframe()
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No unusual activity detected.")
    except Exception as e:
        st.error(f"Error: {e}")

    st.markdown("---")

    # --- Quick Chart: Top Gainer / Selected Stock ---
    st.subheader("Quick Chart")
    chart_col1, chart_col2 = st.columns([1, 3])

    with chart_col1:
        chart_ticker = st.text_input("Ticker untuk chart", value="BBCA", max_chars=10).upper()
        chart_period = st.selectbox("Chart Period", ["1mo", "3mo", "6mo", "1y"], index=2, key="ov_chart_period")
        chart_indicators = st.multiselect(
            "Indicators",
            ["RSI", "MACD", "Volume"],
            default=["RSI"],
            key="ov_chart_ind",
        )

    with chart_col2:
        try:
            from saham_id.data.sources import get_source as _get_source
            from saham_id.charting.candlestick import candlestick_chart
            from saham_id.charting.indicators import multi_indicator_chart

            _src = _get_source()
            with st.spinner(f"Loading chart {chart_ticker}..."):
                ohlc_df = _src.get_ohlc(chart_ticker, period=chart_period, interval="1d")

            if ohlc_df is not None and not ohlc_df.empty:
                # Candlestick with MA
                fig_candle = candlestick_chart(
                    ohlc_df,
                    ticker=chart_ticker,
                    ma_periods=[20, 50],
                    show_volume=True,
                    height=450,
                    dark=True,
                )
                st.plotly_chart(fig_candle, use_container_width=True)

                # Indicators panel below
                ind_map = {"RSI": "rsi", "MACD": "macd", "Volume": "volume"}
                ind_list = [ind_map[i] for i in chart_indicators if i in ind_map]

                if ind_list:
                    fig_ind = multi_indicator_chart(
                        ohlc_df,
                        indicators=ind_list,
                        ticker=chart_ticker,
                        height=200 + 180 * len(ind_list),
                        dark=True,
                    )
                    st.plotly_chart(fig_ind, use_container_width=True)
            else:
                st.warning(f"Tidak ada data untuk {chart_ticker}.")
        except Exception as e:
            st.error(f"Chart error: {e}")

    # --- Market News ---
    st.markdown("---")
    st.subheader("Berita Pasar Terkini")
    _render_market_news()



def _render_market_news() -> None:
    """Display latest market news feed in the overview page."""
    try:
        from saham_id.news import get_news

        with st.spinner("Mengambil berita terkini..."):
            articles = get_news(limit=10)

        if articles:
            for article in articles:
                col_content, col_info = st.columns([5, 1])
                with col_content:
                    st.markdown(f"**[{article.title}]({article.url})**")
                    if article.summary:
                        summary_display = article.summary[:200] + "..." if len(article.summary) > 200 else article.summary
                        st.caption(summary_display)
                with col_info:
                    st.caption(f"📰 {article.source.value}")
                    st.caption(f"🕐 {article.age_display}")
                    if article.tickers:
                        st.caption(f"🏷️ {', '.join(article.tickers[:4])}")
                st.markdown("---")
        else:
            st.info("Tidak dapat mengambil berita saat ini. Cek koneksi internet.")

    except ImportError:
        st.warning("Module `feedparser` belum terinstall. Run: `pip install feedparser`")
    except Exception as e:
        st.warning(f"Gagal mengambil berita: {e}")
