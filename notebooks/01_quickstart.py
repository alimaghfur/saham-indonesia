"""
# 01 — Quickstart: saham-indonesia
#
# Notebook ini menunjukkan cara memulai menggunakan library saham-indonesia.
# Jalankan di Jupyter / IPython / VS Code Interactive:
#   %run notebooks/01_quickstart.py
#
# Atau langsung:
#   python notebooks/01_quickstart.py
"""

# %% [markdown]
# ## Setup
# Pastikan sudah `pip install -e .` dari root project.

# %%
from saham_id import __version__
print(f"saham-indonesia v{__version__}")

# %% [markdown]
# ## 1. Data Sources

# %%
from saham_id.data.sources import list_sources, get_source

print("Available sources:", list_sources())

# Yahoo Finance — gratis, tanpa API key
src = get_source("yahoo")
print(f"Using: {src}")

# %% [markdown]
# ## 2. Ambil Quote

# %%
quote = src.get_quote("BBCA")
print(f"{quote.ticker}: Rp {quote.last:,}")
print(f"  Change: {quote.change} ({quote.change_pct:.2%})" if quote.change_pct else "")
print(f"  Volume: {quote.volume:,}")
print(f"  Source: {quote.source}, delay: {quote.delayed_minutes}m")

# %% [markdown]
# ## 3. Ambil OHLC Historis

# %%
df = src.get_ohlc("BBRI", period="6mo", interval="1d")
print(f"BBRI - {len(df)} bars:")
print(df.tail(5))

# %% [markdown]
# ## 4. Indikator Teknikal

# %%
from saham_id.analysis.indicators import sma, ema, rsi, macd, bollinger_bands

df["SMA_20"] = sma(df["close"], 20)
df["EMA_12"] = ema(df["close"], 12)
df["RSI_14"] = rsi(df["close"], 14)

macd_df = macd(df["close"])
df["MACD"] = macd_df["macd"]
df["Signal"] = macd_df["signal"]

bb = bollinger_bands(df["close"], 20, 2.0)
df["BB_Upper"] = bb["upper"]
df["BB_Lower"] = bb["lower"]

print("\nLast 5 rows with indicators:")
print(df[["close", "SMA_20", "RSI_14", "MACD"]].tail(5))

# %% [markdown]
# ## 5. Stock Universe

# %%
from saham_id.data.universe import get_universe, list_universes

print("Universes:", list(list_universes()))
lq45 = get_universe("LQ45")
print(f"LQ45 ({len(lq45)} saham): {lq45[:10]}...")

# %% [markdown]
# ## 6. Formatting Helpers

# %%
from saham_id.utils.formatting import format_rupiah, format_pct, format_large

print(format_rupiah(9_800))          # Rp 9.800
print(format_pct(0.0315))            # +3.15%
print(format_large(425_000_000_000)) # 425.00B

# %% [markdown]
# ## Selesai!
# Lihat notebook berikutnya untuk screener, backtest, dan portfolio.
