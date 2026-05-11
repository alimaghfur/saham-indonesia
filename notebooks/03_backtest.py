"""
# 03 — Backtesting
#
# Contoh menjalankan backtest strategi pada data historis.
"""

# %% [markdown]
# ## Setup Data

# %%
from saham_id.data.sources import get_source
from saham_id.analysis.indicators import sma

src = get_source("yahoo")

# Ambil 2 tahun data BBCA
df = src.get_ohlc("BBCA", period="2y", interval="1d")
print(f"Data: {len(df)} bars ({df.index[0]} to {df.index[-1]})")

# Tambah moving averages untuk swing pullback strategy
df["ma_20"] = sma(df["close"], 20)
df["ma_50"] = sma(df["close"], 50)

# %% [markdown]
# ## Backtest BPJS Strategy

# %%
from saham_id.backtest.engine import Backtester
from saham_id.backtest.strategies import bpjs_strategy
from saham_id.backtest.metrics import compute_metrics

bt = Backtester(
    strategy=bpjs_strategy,
    initial_capital=100_000_000,  # Rp 100 juta
    commission_bps=15,            # 0.15% per side (total ~0.3% round-trip)
)

result = bt.run(df)
metrics = compute_metrics(result)

print("=" * 50)
print("BPJS Strategy — BBCA (2Y)")
print("=" * 50)
print(f"  Total Return:  {metrics.total_return:.2%}")
print(f"  CAGR:          {metrics.cagr:.2%}")
print(f"  Sharpe Ratio:  {metrics.sharpe:.2f}")
print(f"  Sortino Ratio: {metrics.sortino:.2f}")
print(f"  Max Drawdown:  {metrics.max_drawdown:.2%}")
print(f"  Win Rate:      {metrics.win_rate:.1%}")
print(f"  Num Trades:    {metrics.num_trades}")
print(f"  Avg Trade:     {metrics.avg_trade_pct:.3%}")
print(f"  Profit Factor: {metrics.profit_factor:.2f}")
print(f"  Final Capital: Rp {result.final_capital:,.0f}")

# %% [markdown]
# ## Backtest Swing Pullback Strategy

# %%
from saham_id.backtest.strategies import swing_pullback_strategy

bt2 = Backtester(
    strategy=swing_pullback_strategy,
    initial_capital=100_000_000,
    commission_bps=15,
)

result2 = bt2.run(df)
metrics2 = compute_metrics(result2)

print("\n" + "=" * 50)
print("Swing Pullback — BBCA (2Y)")
print("=" * 50)
print(f"  Total Return:  {metrics2.total_return:.2%}")
print(f"  CAGR:          {metrics2.cagr:.2%}")
print(f"  Sharpe Ratio:  {metrics2.sharpe:.2f}")
print(f"  Max Drawdown:  {metrics2.max_drawdown:.2%}")
print(f"  Win Rate:      {metrics2.win_rate:.1%}")
print(f"  Num Trades:    {metrics2.num_trades}")
print(f"  Profit Factor: {metrics2.profit_factor:.2f}")
print(f"  Final Capital: Rp {result2.final_capital:,.0f}")

# %% [markdown]
# ## Custom Strategy
# Buat strategi sendiri — cukup satu fungsi: (bar, state) -> [Order]

# %%
from saham_id.backtest.engine import Order

def rsi_mean_reversion(bar, state):
    """Buy when RSI < 30, sell when RSI > 70."""
    rsi_val = bar.get("RSI_14") or bar.get("rsi")
    position = state["position"]

    if rsi_val is None:
        return []

    # Entry: RSI < 30 (oversold)
    if position == 0 and rsi_val < 30:
        return [Order(side="buy", quantity=100, note="rsi_oversold")]

    # Exit: RSI > 70 (overbought)
    if position > 0 and rsi_val > 70:
        return [Order(side="sell", quantity=position, note="rsi_overbought")]

    return []


# Enrich data with RSI
from saham_id.analysis.indicators import rsi
df["RSI_14"] = rsi(df["close"], 14)

bt3 = Backtester(
    strategy=rsi_mean_reversion,
    initial_capital=100_000_000,
    commission_bps=15,
)
result3 = bt3.run(df)
metrics3 = compute_metrics(result3)

print("\n" + "=" * 50)
print("RSI Mean Reversion — BBCA (2Y)")
print("=" * 50)
print(f"  Total Return:  {metrics3.total_return:.2%}")
print(f"  Sharpe Ratio:  {metrics3.sharpe:.2f}")
print(f"  Win Rate:      {metrics3.win_rate:.1%}")
print(f"  Num Trades:    {metrics3.num_trades}")
print(f"  Final Capital: Rp {result3.final_capital:,.0f}")
