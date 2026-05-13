"""
# 07 - Alerts, Notifications & Real-time Monitoring
# ===================================================
# Notebook ini mendemonstrasikan:
# - Setup price alerts (watchlist-based)
# - Telegram/Discord notification backends
# - Real-time polling for live prices
# - Backtest parameter optimization
#
# Jalankan: python notebooks/07_alerts_realtime.py
# Atau buka di Jupyter/IPython untuk interaktif.
"""

# %% [markdown]
# ## Setup

# %%
from saham_id.data import get_source
from saham_id.watchlist import Watchlist, AlertCondition
from saham_id.notifications import (
    NotificationManager,
    TelegramBackend,
    DiscordBackend,
    ConsoleBackend,
    Notification,
)

# %% [markdown]
# ## 1. Price Alerts — Watchlist-Based
#
# Buat watchlist dengan alert conditions.
# Alert bisa berdasarkan harga, RSI, volume, dll.

# %%
# Create or load a watchlist
wl = Watchlist("demo_alerts")

# Add tickers with alert conditions
wl.add("BBCA", target_buy=9000, stop_loss=8500, alerts=[
    AlertCondition(field="last", op="<", value=9100, message="BBCA mendekati target buy!"),
    AlertCondition(field="rsi", op="<", value=30, message="BBCA RSI oversold!"),
])

wl.add("BBRI", target_buy=4500, target_sell=5500, alerts=[
    AlertCondition(field="last", op=">", value=5400, message="BBRI mendekati target sell!"),
])

wl.add("TLKM", alerts=[
    AlertCondition(field="volume", op=">", value=100_000_000, message="TLKM unusual volume!"),
])

# Save watchlist
wl.save()
print(f"Watchlist saved: {len(wl.tickers)} tickers")

# %% [markdown]
# ## 2. Check Alerts Against Live Data
#
# Cek apakah ada alert yang terpicu berdasarkan data real-time.

# %%
# Check alerts (requires active data source)
try:
    src = get_source()
    triggered = wl.check_alerts(source=src)

    if triggered:
        print(f"\n{len(triggered)} alert(s) triggered!")
        for result in triggered:
            print(f"  {result.ticker}: {result.triggered_alerts}")
    else:
        print("No alerts triggered at this time.")
except Exception as e:
    print(f"Skipped live check (no data source available): {e}")

# %% [markdown]
# ## 3. Notification Backends
#
# Kirim notifikasi ke berbagai channel: Console, Telegram, Discord.

# %%
# Console backend (always works)
manager = NotificationManager()
manager.add_backend(ConsoleBackend())

# Telegram (uncomment and fill in credentials)
# manager.add_backend(TelegramBackend(
#     bot_token="YOUR_BOT_TOKEN",
#     chat_id="YOUR_CHAT_ID",
# ))

# Discord (uncomment and fill in webhook URL)
# manager.add_backend(DiscordBackend(
#     webhook_url="https://discord.com/api/webhooks/..."
# ))

# Send a test notification
notif = Notification(
    title="Test Alert",
    message="BBCA mendekati target buy Rp 9,000",
    level="alert",
    ticker="BBCA",
    extra={"price": "Rp 9,150", "target": "Rp 9,000"},
)

results = manager.send_all(notif)
print(f"\nNotification sent to {len(results)} backend(s)")
for backend, success in results.items():
    print(f"  {backend}: {'OK' if success else 'FAILED'}")

# %% [markdown]
# ## 4. Custom Notification for Triggered Alerts
#
# Pattern: check alerts -> notify ke Telegram jika terpicu.

# %%
def alert_and_notify(watchlist_name: str = "demo_alerts"):
    """Check alerts and send notifications for triggered ones."""
    from saham_id.errors import error_boundary

    wl = Watchlist.load(watchlist_name)
    src = get_source()

    with error_boundary("checking alerts"):
        triggered = wl.check_alerts(source=src)

    if not triggered:
        print("No alerts triggered.")
        return

    for result in triggered:
        notif = Notification(
            title=f"Alert: {result.ticker}",
            message="; ".join(str(a) for a in result.triggered_alerts[:3]),
            level="alert",
            ticker=result.ticker,
            extra=result.current_values,
        )
        manager.send_all(notif)
        print(f"  Notified: {result.ticker}")

# Uncomment to run:
# alert_and_notify()

# %% [markdown]
# ## 5. Real-time Price Polling
#
# Monitor harga secara berkala (simple polling pattern).

# %%
import time


def monitor_prices(tickers: list[str], interval_sec: int = 10, max_iterations: int = 3):
    """Poll prices periodically and display changes."""
    src = get_source()
    prev_prices = {}

    for i in range(max_iterations):
        print(f"\n--- Iteration {i + 1}/{max_iterations} ---")
        for ticker in tickers:
            try:
                q = src.get_quote(ticker)
                price = float(q.last)
                prev = prev_prices.get(ticker)

                if prev:
                    change = price - prev
                    arrow = "+" if change >= 0 else ""
                    print(f"  {ticker}: Rp {price:,.0f} ({arrow}{change:,.0f})")
                else:
                    print(f"  {ticker}: Rp {price:,.0f}")

                prev_prices[ticker] = price
            except Exception as e:
                print(f"  {ticker}: ERROR - {e}")

        if i < max_iterations - 1:
            print(f"  [waiting {interval_sec}s...]")
            time.sleep(interval_sec)

    print("\nMonitoring selesai.")


# Run with 3 iterations, 5 second interval
# (uses cached data in test mode, real data with API key)
try:
    monitor_prices(["BBCA", "BBRI", "TLKM"], interval_sec=5, max_iterations=2)
except Exception as e:
    print(f"Skipped monitoring (no data source): {e}")

# %% [markdown]
# ## 6. Backtest Parameter Optimization
#
# Grid search untuk menemukan parameter optimal.

# %%
from saham_id.backtest.optimizer import (
    optimize_rsi_strategy,
    optimize_ma_crossover,
    ParameterGrid,
)

# Generate sample OHLC data for demo
import math

n = 500
close_data = [10000 + 2000 * math.sin(i * 0.05) + i * 5 + (i % 7) * 50 for i in range(n)]
open_data = [c - 50 + (i % 3) * 30 for i, c in enumerate(close_data)]
high_data = [max(o, c) + 100 + (i % 5) * 20 for i, (o, c) in enumerate(zip(open_data, close_data))]
low_data = [min(o, c) - 80 - (i % 4) * 15 for i, (o, c) in enumerate(zip(open_data, close_data))]
volume_data = [5_000_000 + (i % 10) * 500_000 for i in range(n)]

import pandas as pd

df = pd.DataFrame({
    "open": open_data,
    "high": high_data,
    "low": low_data,
    "close": close_data,
    "volume": volume_data,
}, index=list(range(n)))

print(f"Sample data: {len(df)} bars")

# %%
# Optimize RSI strategy
print("\n=== RSI Strategy Optimization ===")
rsi_result = optimize_rsi_strategy(
    df,
    rsi_periods=[7, 14, 21],
    oversold_levels=[25, 30, 35],
    overbought_levels=[65, 70, 75],
    metric="sharpe",
    ticker="DEMO",
)

print(f"Total runs: {rsi_result.total_runs}")
print(f"Successful: {rsi_result.successful_runs}")
if rsi_result.best_run:
    print(f"Best params: {rsi_result.best_params}")
    print(f"Best Sharpe: {rsi_result.best_score:.4f}")
    if rsi_result.best_metrics:
        m = rsi_result.best_metrics
        print(f"  Return: {m.total_return:.2%}, MaxDD: {m.max_drawdown:.2%}, Trades: {m.num_trades}")

# %%
# Optimize MA crossover
print("\n=== MA Crossover Optimization ===")
ma_result = optimize_ma_crossover(
    df,
    fast_periods=[5, 10, 20],
    slow_periods=[30, 50, 100],
    metric="total_return",
    ticker="DEMO",
)

print(f"Total runs: {ma_result.total_runs}")
print(f"Successful: {ma_result.successful_runs}")
if ma_result.best_run:
    print(f"Best params: {ma_result.best_params}")
    print(f"Best return: {ma_result.best_score:.2%}")

# Show top 3
print("\nTop 3:")
for i, run in enumerate(ma_result.top_n(3), 1):
    if run.metrics:
        print(f"  #{i}: {run.params} -> return={run.metrics.total_return:.2%}, sharpe={run.metrics.sharpe:.2f}")

# %% [markdown]
# ## 7. CLI Commands Reference
#
# Semua fitur di atas juga bisa diakses via CLI:
#
# ```bash
# # Alert management
# saham alert setup --token BOT_TOKEN --chat-id CHAT_ID
# saham alert test --message "Hello from CLI"
# saham alert add BBCA --field last --op "<" --value 9000
# saham alert list
# saham alert check --notify
# saham alert remove BBCA
#
# # Backtest optimization
# saham backtest-optimize BBCA --strategy rsi --metric sharpe
# saham backtest-optimize BBRI --strategy ma_crossover --metric total_return --period 3y
#
# # Cache management
# saham cache stats
# saham cache clear --yes
#
# # Charting
# saham chart BBCA --indicators rsi,macd --export chart.html
# ```

# %%
print("\nNotebook 07 selesai.")
print("Untuk real-time streaming via WebSocket, lihat dashboard page 'Real-time'.")
print("Atau gunakan: `streamlit run dashboard/app.py`")
