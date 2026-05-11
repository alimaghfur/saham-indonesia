"""
# 02 — Strategy Screeners
#
# Contoh penggunaan semua screener yang tersedia.
"""

# %% [markdown]
# ## Swing Breakout
# Cari saham yang breakout di atas resistance N-day high.

# %%
from saham_id.screener.swing.breakout import screen as breakout_screen
from saham_id.data.sources import get_source

src = get_source("yahoo")

result = breakout_screen(
    universe="IDX30",
    resistance_window=20,
    min_consolidation_days=10,
    volume_confirmation=True,
    min_rvol=1.5,
    top_n=10,
    source=src,
)
print(f"Swing Breakout — {len(result)} results")
print(result.to_dataframe())

# %% [markdown]
# ## Swing Pullback
# Cari saham uptrend yang retrace ke moving average.

# %%
from saham_id.screener.swing.pullback import screen as pullback_screen

result = pullback_screen(
    universe="LQ45",
    trend_ma=50,
    pullback_ma=20,
    proximity_pct=0.02,
    rsi_min=40.0,
    rsi_max=55.0,
    top_n=10,
    source=src,
)
print(f"\nSwing Pullback — {len(result)} results")
print(result.to_dataframe())

# %% [markdown]
# ## Swing Reversal
# Cari saham oversold yang mulai bounce (RSI cross up dari < 30).

# %%
from saham_id.screener.swing.reversal import screen as reversal_screen

result = reversal_screen(
    universe="LQ45",
    rsi_oversold=30.0,
    rsi_exit=40.0,
    require_bullish_candle=True,
    top_n=10,
    source=src,
)
print(f"\nSwing Reversal — {len(result)} results")
print(result.to_dataframe())

# %% [markdown]
# ## BPJS (Beli Pagi Jual Sore)
# Ranking saham berdasarkan statistik intraday return (close - open).

# %%
from saham_id.screener.intraday.bpjs import screen as bpjs_screen

result = bpjs_screen(
    universe="LQ45",
    lookback_days=60,
    min_win_rate=0.55,
    min_avg_return=0.003,
    top_n=10,
    source=src,
)
print(f"\nBPJS — {len(result)} results")
print(result.to_dataframe())

# %% [markdown]
# ## BSJP (Beli Sore Jual Pagi)
# Ranking saham berdasarkan overnight gap (open hari berikutnya vs close hari ini).

# %%
from saham_id.screener.intraday.bsjp import screen as bsjp_screen

result = bsjp_screen(
    universe="LQ45",
    lookback_days=60,
    min_gap_up_rate=0.55,
    min_avg_gap=0.002,
    top_n=10,
    source=src,
)
print(f"\nBSJP — {len(result)} results")
print(result.to_dataframe())

# %% [markdown]
# ## Scalping Screener
# Cari saham dengan volatilitas dan likuiditas tinggi untuk scalping.

# %%
from saham_id.screener.intraday.scalping import screen as scalping_screen

result = scalping_screen(
    universe="IDX30",
    min_atr_pct=0.015,
    min_rvol=2.0,
    top_n=10,
    source=src,
)
print(f"\nScalping — {len(result)} results")
print(result.to_dataframe())
