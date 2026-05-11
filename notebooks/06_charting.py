"""
# 06 - Charting & Visualisasi Saham Indonesia
# =============================================
# Notebook ini mendemonstrasikan penggunaan charting module
# untuk analisis teknikal saham-saham IDX.
#
# Fitur:
# - Candlestick chart dengan Moving Average overlay
# - Support/Resistance lines
# - Indicator charts (RSI, MACD, Bollinger, Stochastic, ATR)
# - Multi-indicator panel
# - Portfolio dashboard (equity curve, drawdown, alokasi)
# - Export ke HTML/PNG
#
# Jalankan: python notebooks/06_charting.py
# Atau buka di Jupyter/IPython untuk interaktif.
"""

# %% [markdown]
# ## Setup

# %%
import numpy as np
import pandas as pd

from saham_id.data import get_source
from saham_id.charting import (
    candlestick_chart,
    indicator_chart,
    multi_indicator_chart,
    equity_curve,
    drawdown_chart,
    allocation_pie,
    portfolio_dashboard,
)
from saham_id.charting.candlestick import ohlc_chart
from saham_id.charting.styles import register_idx_template

# Register IDX theme sebagai default plotly template
register_idx_template()

# %% [markdown]
# ## 1. Ambil Data Saham
# Data otomatis di-cache sehingga request berikutnya lebih cepat.

# %%
src = get_source("yahoo")

# Ambil data BBCA 6 bulan terakhir
bbca = src.get_ohlc("BBCA", period="6mo", interval="1d")
print(f"BBCA: {len(bbca)} bars, dari {bbca.index[0]} s/d {bbca.index[-1]}")
print(bbca.tail())

# %%
# Ambil data BBRI juga untuk perbandingan
bbri = src.get_ohlc("BBRI", period="6mo", interval="1d")
print(f"BBRI: {len(bbri)} bars")

# %% [markdown]
# ## 2. Candlestick Chart
# Chart paling dasar — candlestick + volume bars.

# %%
fig = candlestick_chart(bbca, ticker="BBCA")
fig.show()

# %% [markdown]
# ### 2.1 Dengan Moving Average Overlay
# Tambahkan MA20, MA50, MA200 untuk melihat trend.

# %%
fig = candlestick_chart(
    bbca,
    ticker="BBCA",
    ma_periods=[20, 50, 200],
    show_volume=True,
    height=700,
)
fig.show()

# %% [markdown]
# ### 2.2 Dengan Support & Resistance
# Tambahkan level S/R yang sudah diidentifikasi.

# %%
# Hitung level S/R sederhana dari data
recent_high = float(bbca["high"].tail(20).max())
recent_low = float(bbca["low"].tail(20).min())
mid_level = (recent_high + recent_low) / 2

fig = candlestick_chart(
    bbca,
    ticker="BBCA",
    ma_periods=[20, 50],
    support_levels=[recent_low, recent_low * 0.97],
    resistance_levels=[recent_high, recent_high * 1.03],
    height=700,
)
fig.show()
print(f"Support: {recent_low:,.0f} | Resistance: {recent_high:,.0f}")

# %% [markdown]
# ### 2.3 OHLC Bar Chart (alternatif candlestick)

# %%
fig = ohlc_chart(bbca, ticker="BBCA", height=500)
fig.show()

# %% [markdown]
# ## 3. Indicator Charts
# Setiap indikator bisa ditampilkan terpisah.

# %% [markdown]
# ### 3.1 RSI (Relative Strength Index)
# - Di atas 70 = overbought
# - Di bawah 30 = oversold

# %%
fig = indicator_chart(bbca, indicator="rsi", ticker="BBCA", period=14)
fig.show()

# %% [markdown]
# ### 3.2 MACD (Moving Average Convergence Divergence)
# - MACD cross di atas Signal = bullish
# - Histogram hijau makin besar = momentum naik

# %%
fig = indicator_chart(bbca, indicator="macd", ticker="BBCA")
fig.show()

# %% [markdown]
# ### 3.3 Bollinger Bands
# - Harga menyentuh upper band = potensi overbought
# - Harga menyentuh lower band = potensi oversold
# - Band menyempit = volatilitas rendah, siap breakout

# %%
fig = indicator_chart(bbca, indicator="bollinger", ticker="BBCA", period=20)
fig.show()

# %% [markdown]
# ### 3.4 Stochastic Oscillator
# - %K di atas 80 = overbought
# - %K di bawah 20 = oversold
# - %K cross %D dari bawah = buy signal

# %%
fig = indicator_chart(bbca, indicator="stochastic", ticker="BBCA", period=14)
fig.show()

# %% [markdown]
# ### 3.5 ATR (Average True Range)
# Mengukur volatilitas harga. Semakin tinggi ATR = semakin volatile.

# %%
fig = indicator_chart(bbca, indicator="atr", ticker="BBCA", period=14)
fig.show()

# %% [markdown]
# ## 4. Multi-Indicator Panel
# Gabungan candlestick + beberapa indikator dalam satu view.

# %%
# Price + RSI + MACD
fig = multi_indicator_chart(
    bbca,
    indicators=["rsi", "macd"],
    ticker="BBCA",
    height=800,
)
fig.show()

# %%
# Price + RSI + MACD + Volume
fig = multi_indicator_chart(
    bbca,
    indicators=["rsi", "macd", "volume"],
    ticker="BBCA",
    height=900,
)
fig.show()

# %%
# Price + ATR + Volume (untuk analisis volatility)
fig = multi_indicator_chart(
    bbri,
    indicators=["atr", "volume"],
    ticker="BBRI",
    height=750,
)
fig.show()

# %% [markdown]
# ## 5. Portfolio Visualization
# Simulasi portfolio dengan beberapa saham.

# %%
# Simulasi daily returns (realistis untuk saham IDX)
np.random.seed(42)
n_days = 120
dates = pd.bdate_range(end=pd.Timestamp.today(), periods=n_days)

# Simulasi returns portfolio dengan slight positive drift
daily_returns = pd.Series(
    np.random.normal(0.0008, 0.015, n_days),  # mean 0.08%/hari, std 1.5%
    index=dates,
    name="portfolio_returns",
)

# Simulasi benchmark (IHSG-like)
benchmark_returns = pd.Series(
    np.random.normal(0.0005, 0.012, n_days),
    index=dates,
    name="benchmark_returns",
)

print(f"Simulated portfolio: {n_days} hari")
print(f"Total return portfolio: {((1 + daily_returns).prod() - 1) * 100:.1f}%")
print(f"Total return benchmark: {((1 + benchmark_returns).prod() - 1) * 100:.1f}%")

# %% [markdown]
# ### 5.1 Equity Curve

# %%
fig = equity_curve(
    daily_returns,
    benchmark=benchmark_returns,
    title="Portfolio vs IHSG",
    initial_capital=100_000_000,  # Rp 100 juta
)
fig.show()

# %% [markdown]
# ### 5.2 Drawdown Chart

# %%
fig = drawdown_chart(daily_returns, title="Drawdown Portfolio")
fig.show()

# %% [markdown]
# ### 5.3 Alokasi Portfolio (Pie/Donut)

# %%
holdings = {
    "BBCA": 35_000_000,
    "BBRI": 25_000_000,
    "TLKM": 15_000_000,
    "ASII": 12_000_000,
    "UNVR": 8_000_000,
    "BMRI": 5_000_000,
}

fig = allocation_pie(holdings, title="Alokasi Portfolio Saya")
fig.show()

# %% [markdown]
# ### 5.4 Portfolio Dashboard (All-in-One)
# Gabungan equity curve + drawdown + alokasi + monthly returns.

# %%
fig = portfolio_dashboard(
    returns=daily_returns,
    holdings=holdings,
    benchmark=benchmark_returns,
    title="Dashboard Portfolio Saham IDX",
    initial_capital=100_000_000,
    height=1000,
)
fig.show()

# %% [markdown]
# ## 6. Dark vs Light Theme
# Semua chart mendukung mode terang.

# %%
# Light mode
fig = candlestick_chart(
    bbca,
    ticker="BBCA",
    ma_periods=[20, 50],
    dark=False,  # Light theme
    height=500,
)
fig.show()

# %%
fig = indicator_chart(bbca, indicator="macd", ticker="BBCA", dark=False)
fig.show()

# %% [markdown]
# ## 7. Export Charts
# Simpan chart ke file untuk sharing atau reporting.

# %%
# Export sebagai HTML interaktif (bisa dibuka di browser)
fig = multi_indicator_chart(bbca, indicators=["rsi", "macd"], ticker="BBCA")
fig.write_html("output/chart_bbca_analysis.html")
print("Saved: output/chart_bbca_analysis.html")

# %%
# Export sebagai PNG (perlu kaleido terinstall)
try:
    fig.write_image("output/chart_bbca_analysis.png", width=1400, height=800, scale=2)
    print("Saved: output/chart_bbca_analysis.png")
except Exception as e:
    print(f"PNG export gagal (install kaleido): {e}")

# %% [markdown]
# ## 8. Tips & Tricks
#
# ### Zoom & Pan
# - Scroll mouse untuk zoom in/out
# - Drag untuk pan (geser)
# - Double-click untuk reset view
#
# ### Hover Info
# - Hover di candle untuk lihat OHLCV
# - Hover di indikator untuk lihat value
#
# ### Custom Indicator
# Jika punya kolom custom di DataFrame, bisa langsung diplot:
# ```python
# df["custom_signal"] = ...  # kalkulasi sendiri
# fig = indicator_chart(df, indicator="custom_signal", ticker="BBCA")
# ```
#
# ### Combine dengan Analysis Module
# ```python
# from saham_id.analysis import support_resistance
# levels = support_resistance.find_levels(df)
# fig = candlestick_chart(df, ticker="BBCA",
#     support_levels=levels["support"],
#     resistance_levels=levels["resistance"])
# ```
#
# ### Performance
# - Data di-cache otomatis (TTL 1 jam untuk daily OHLC)
# - Panggil `src.clear_cache("BBCA")` untuk refresh paksa
# - Set `SAHAM_ID_CACHE_ENABLED=false` di .env untuk disable

# %% [markdown]
# ---
# **Happy charting!** 📈
