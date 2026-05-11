"""
# 04 — Portfolio Tracking
#
# Contoh penggunaan portfolio tracker untuk mencatat transaksi dan menghitung P/L.
"""

# %% [markdown]
# ## Buat Portfolio

# %%
from datetime import datetime
from decimal import Decimal
from saham_id.portfolio.tracker import Portfolio, Transaction

# Mulai dengan Rp 500 juta cash
portfolio = Portfolio(cash=Decimal("500_000_000"))
print(f"Cash awal: Rp {portfolio.cash:,}")

# %% [markdown]
# ## Catat Transaksi

# %%
# Beli 10 lot BBCA @ 9.500
tx1 = Transaction(
    ticker="BBCA",
    side="buy",
    quantity=1000,    # 10 lot = 1000 lembar
    price=Decimal("9500"),
    timestamp=datetime(2025, 1, 6, 9, 30),
    fee=Decimal("14250"),  # 15 bps
    note="Akumulasi awal",
)
portfolio.record(tx1)

# Beli 5 lot BBRI @ 5.200
tx2 = Transaction(
    ticker="BBRI",
    side="buy",
    quantity=500,
    price=Decimal("5200"),
    timestamp=datetime(2025, 1, 7, 10, 0),
    fee=Decimal("3900"),
    note="Diversifikasi bank",
)
portfolio.record(tx2)

# Beli 5 lot TLKM @ 3.600
tx3 = Transaction(
    ticker="TLKM",
    side="buy",
    quantity=500,
    price=Decimal("3600"),
    timestamp=datetime(2025, 1, 8, 9, 45),
    fee=Decimal("2700"),
)
portfolio.record(tx3)

print(f"Cash setelah beli: Rp {portfolio.cash:,}")
print(f"Posisi: {list(portfolio.positions.keys())}")

# %% [markdown]
# ## Jual Sebagian

# %%
# Jual 5 lot BBCA @ 10.100 (profit taking)
tx4 = Transaction(
    ticker="BBCA",
    side="sell",
    quantity=500,
    price=Decimal("10100"),
    timestamp=datetime(2025, 2, 3, 14, 0),
    fee=Decimal("7575"),
    note="Profit taking 50%",
)
portfolio.record(tx4)

bbca_pos = portfolio.positions["BBCA"]
print(f"BBCA remaining: {bbca_pos.quantity} shares @ avg Rp {bbca_pos.avg_cost:,.0f}")
print(f"BBCA realized P/L: Rp {bbca_pos.realized_pnl:,}")

# %% [markdown]
# ## Lihat Snapshot

# %%
# Snapshot menggunakan live quotes (butuh internet + yfinance)
try:
    from saham_id.data.sources import get_source
    src = get_source("yahoo")
    snap = portfolio.snapshot(source=src)
    print("\nPortfolio Snapshot:")
    print(snap)
    print(f"\nTotal portfolio value: Rp {portfolio.total_value(source=src):,}")
except Exception as e:
    print(f"(Live quote unavailable: {e})")
    # Fallback: show positions manually
    for ticker, pos in portfolio.positions.items():
        if pos.quantity > 0:
            print(f"  {ticker}: {pos.quantity} shares @ Rp {pos.avg_cost:,.0f}")

# %% [markdown]
# ## Riwayat Transaksi

# %%
print("\nTransaction History:")
print(f"{'Time':<20} {'Ticker':<6} {'Side':<5} {'Qty':>6} {'Price':>8} {'Note'}")
print("-" * 70)
for tx in portfolio.transactions:
    print(
        f"{tx.timestamp.strftime('%Y-%m-%d %H:%M'):<20} "
        f"{tx.ticker:<6} "
        f"{tx.side:<5} "
        f"{tx.quantity:>6} "
        f"{float(tx.price):>8,.0f} "
        f"{tx.note}"
    )
