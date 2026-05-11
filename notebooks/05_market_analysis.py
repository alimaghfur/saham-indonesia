"""
# 05 — Market Analysis
#
# Contoh analisis pasar: movers, trending, unusual activity, breadth, risk.
"""

# %% [markdown]
# ## Market Movers

# %%
from saham_id.market.movers import top_gainers, top_losers, most_active
from saham_id.data.sources import get_source

src = get_source("yahoo")

print("=" * 50)
print("TOP GAINERS (1D) — LQ45")
print("=" * 50)
gainers = top_gainers(universe="LQ45", period="1D", top_n=5, source=src)
for m in gainers:
    print(f"  {m.rank}. {m.ticker:<6} Rp {float(m.last):>8,.0f}  {m.change_pct:>+.2%}")

print("\n" + "=" * 50)
print("TOP LOSERS (1D) — LQ45")
print("=" * 50)
losers = top_losers(universe="LQ45", period="1D", top_n=5, source=src)
for m in losers:
    print(f"  {m.rank}. {m.ticker:<6} Rp {float(m.last):>8,.0f}  {m.change_pct:>+.2%}")

# %% [markdown]
# ## Trending Detection

# %%
from saham_id.market.trending import detect

print("\n" + "=" * 50)
print("TRENDING STOCKS — LQ45")
print("=" * 50)
trending = detect(universe="LQ45", timeframe="1D", min_rvol=1.5, top_n=10, source=src)
df = trending.to_dataframe()
if not df.empty:
    print(df[["ticker", "score", "rvol", "momentum_z"]].to_string(index=False))
else:
    print("  No trending stocks detected.")

# %% [markdown]
# ## Unusual Activity

# %%
from saham_id.market.unusual_activity import detect as detect_unusual

print("\n" + "=" * 50)
print("UNUSUAL ACTIVITY — LQ45")
print("=" * 50)
unusual = detect_unusual(universe="LQ45", volume_sigma=2.0, top_n=10, source=src)
df = unusual.to_dataframe()
if not df.empty:
    print(df[["ticker", "score", "volume_sigma", "price_sigma"]].to_string(index=False))
else:
    print("  No unusual activity detected.")

# %% [markdown]
# ## Market Breadth

# %%
from saham_id.market.breadth import snapshot

print("\n" + "=" * 50)
print("MARKET BREADTH — LQ45")
print("=" * 50)
snap = snapshot(universe="LQ45", source=src)
print(f"  Advancers:  {snap.advancers}")
print(f"  Decliners:  {snap.decliners}")
print(f"  Unchanged:  {snap.unchanged}")
print(f"  A/D Ratio:  {snap.ad_ratio:.2f}")
print(f"  New 52w Hi: {snap.new_highs_52w}")
print(f"  New 52w Lo: {snap.new_lows_52w}")

# %% [markdown]
# ## Risk Analysis

# %%
from saham_id.analysis.risk import volatility, sharpe, sortino, max_drawdown, beta

# Ambil data BBCA dan IHSG untuk perbandingan
bbca_df = src.get_ohlc("BBCA", period="1y", interval="1d")
ihsg_df = src.get_ohlc("^JKSE", period="1y", interval="1d")

bbca_returns = bbca_df["close"].pct_change().dropna()
ihsg_returns = ihsg_df["close"].pct_change().dropna()

print("\n" + "=" * 50)
print("RISK METRICS — BBCA (1Y)")
print("=" * 50)
print(f"  Ann. Volatility: {volatility(bbca_returns):.2%}")
print(f"  Sharpe Ratio:    {sharpe(bbca_returns):.2f}")
print(f"  Sortino Ratio:   {sortino(bbca_returns):.2f}")
print(f"  Max Drawdown:    {max_drawdown(bbca_df['close']):.2%}")
print(f"  Beta vs IHSG:    {beta(bbca_returns, ihsg_returns):.2f}")

# %% [markdown]
# ## Valuation

# %%
from saham_id.analysis.valuation import dcf_fair_value, DCFInputs, graham_number

# DCF example: BBCA-like stock
inputs = DCFInputs(
    fcf_last=40_000_000_000_000,  # 40T FCF
    growth_high=0.12,              # 12% growth 5 years
    growth_terminal=0.04,          # 4% perpetuity
    discount_rate=0.10,            # 10% WACC
    years_high=5,
    shares_outstanding=123_000_000_000,  # ~123B shares
)

fv = dcf_fair_value(inputs)
print(f"\nDCF Fair Value: Rp {fv:,.0f} per share")

# Graham Number
gn = graham_number(eps=550, bvps=2_500)
print(f"Graham Number: Rp {gn:,.0f}")
