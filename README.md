# saham-indonesia 📈

> **Analytics & screener toolkit untuk saham Indonesia (IDX / Bursa Efek Indonesia).**
>
> Python library + CLI + Streamlit Dashboard — arsitektur multi-source data yang bisa di-swap.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-467%20passing-brightgreen.svg)]()

---

## Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Instalasi](#instalasi)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [Python API](#python-api)
- [Dashboard Streamlit](#dashboard-streamlit)
- [Modul Lengkap](#modul-lengkap)
- [Data Sources](#data-sources)
- [Struktur Project](#struktur-project)
- [Development](#development)
- [Docker](#docker)
- [Disclaimer](#disclaimer)

---

## Fitur Utama

### 📊 Data & Sources
| Fitur | Deskripsi |
|-------|-----------|
| Multi-source | yfinance, RTI Business, iTick (realtime+WS), GoAPI, Sectors.app |
| Auto-fallback | Jika satu source gagal, otomatis coba source berikutnya |
| IDX Universes | IDX30, LQ45, IDX80, Kompas100 (hardcoded + auto-detect) |

### 📈 Indikator Teknikal (12 indicators)
| Indikator | Fungsi |
|-----------|--------|
| SMA, EMA | Moving averages (simple & exponential) |
| MACD | Moving Average Convergence Divergence + histogram |
| RSI | Relative Strength Index (Wilder's smoothing) |
| Stochastic | %K, %D oscillator |
| Williams %R | Williams Percent Range |
| ATR | Average True Range (volatility) |
| Bollinger Bands | Middle/Upper/Lower/Bandwidth/%B |
| OBV | On-Balance Volume |
| VWAP | Volume-Weighted Average Price |
| RVOL | Relative Volume (vs 20-day avg) |
| **Ichimoku Cloud** | Tenkan/Kijun/Senkou A&B/Chikou + cloud analysis |

### 🔍 Screener (11+ strategies)
| Screener | Deskripsi |
|----------|-----------|
| BPJS | Beli Pagi Jual Sore (intraday return) |
| BSJP | Beli Sore Jual Pagi (overnight gap) |
| Swing Breakout | Tembus resistance N-day high |
| Swing Pullback | Retrace ke MA dalam uptrend |
| Swing Reversal | Oversold bounce (RSI + BB) |
| Scalping | High ATR% + high RVOL + momentum |
| Unusual Activity | Volume/price anomaly detector |
| Gap Screener | Saham yang gap hari ini |
| Combo Screener | Multi-factor composite scoring |
| Custom (Scoring Builder) | Buat screener tanpa coding via JSON config |

### 🕵️ Bandarmology & Foreign Flow
| Fitur | Deskripsi |
|-------|-----------|
| Bandar Phase Detection | ACCUMULATION, MARKUP, DISTRIBUTION, MARKDOWN |
| Money Flow | Net buying/selling estimation |
| Smart Money Index | Deteksi stealth accumulation/distribution |
| ADL (Accumulation/Distribution Line) | Chaikin indicator |
| Foreign Flow Analysis | Track asing masuk/keluar per saham |
| Foreign Net Buy/Sell Top | Ranking saham diakumulasi/didistribusi asing |

### 🎯 Signal Engine
| Fitur | Deskripsi |
|-------|-----------|
| Composite Signals | BUY/SELL/HOLD dari multiple indicators |
| Pre-built Engines | swing_buy, swing_sell, scalping |
| Signal History | Track & evaluate akurasi sinyal |
| Multi-Timeframe | Weekly/Daily/4H/1H alignment analysis |

### 📊 Analysis
| Fitur | Deskripsi |
|-------|-----------|
| Support/Resistance | Pivot Points (3 metode) + Fibonacci Retracement |
| Candlestick Patterns | 8 patterns (Doji, Hammer, Engulfing, dll) |
| Volume Profile | POC, Value Area, HVN/LVN |
| Correlation Matrix | Pearson + find uncorrelated/correlated |
| Sector Rotation | 11 sektor IDX + leading/lagging detection |
| Seasonality | Monthly + day-of-week effect + Sell in May |
| Gap Analysis | Gap detection, classification, fill rate |
| Price Action | Bar analysis + compression/breakout detection |
| Stock Comparison | Head-to-head return/risk/Sharpe |
| Fundamental Scoring | Value score + Quality score |
| DCF Valuation | Two-stage DCF + Graham Number |
| Risk Metrics | Volatility, Sharpe, Sortino, Max DD, Beta, VaR |

### 💰 Portfolio & Trading
| Fitur | Deskripsi |
|-------|-----------|
| Portfolio Tracker | Transaction recording, P/L, allocation |
| Paper Trading | Simulasi live trading tanpa uang asli |
| Position Sizing | Kelly criterion, fixed-fractional, ATR-based |
| Portfolio Optimizer | Equal weight, risk parity, min-correlation |
| Auto-Rebalancer | Hitung lot beli/jual untuk target allocation |
| Lot Calculator | Budget → berapa lot + fee + sisa cash |
| Dividend Tracker | Yield, DRIP calculator, IDX dividend data |
| Risk Manager | Stop-loss, trailing stop, circuit breaker |

### 🔔 Notifications & Automation
| Fitur | Deskripsi |
|-------|-----------|
| Watchlist | Alert conditions, target buy/sell/stop |
| Telegram Bot | Real-time alerts via Telegram |
| Discord Webhook | Alerts ke Discord channel |
| Generic Webhook | Slack-compatible webhook |
| Scheduler | Automated periodic scanning |
| Earnings Calendar | Track jadwal laporan keuangan |

### 📋 Lainnya
| Fitur | Deskripsi |
|-------|-----------|
| Stock Score Card | Complete single-stock summary + recommendation |
| Market Regime | Trending/Sideways/High Vol detection |
| Market Heatmap | Per-stock + per-sector performance data |
| News Sentiment | Keyword-based sentiment (70+ keywords ID/EN) |
| Export | CSV, JSON, Excel, HTML report |
| IDX Calendar | Hari libur 2025-2026 + auto-detection |
| Scoring Model Builder | Custom screener tanpa coding |

---

## Instalasi

### Requirements
- Python 3.10+
- pip

### Install

```bash
# Clone repository
git clone https://github.com/alimaghfur/saham-indonesia.git
cd saham-indonesia

# Checkout branch terbaru
git checkout feat/scaffold-foundation

# Install (editable mode)
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env
```

### Install dengan Dashboard (optional)

```bash
pip install -e ".[dashboard]"
```

### Install untuk realtime streaming (optional)

```bash
pip install -e ".[realtime]"
```

---

## Quick Start

### 1. Cek Data Source

```bash
saham sources
```

### 2. Ambil Quote

```bash
saham quote BBCA
```

### 3. Jalankan Screener

```bash
saham screen bpjs --universe LQ45 --top 10
```

### 4. Generate Sinyal

```bash
saham signals --universe IDX30 --engine swing_buy
```

### 5. Multi-Timeframe Analysis

```bash
saham mtf BBCA
```

### 6. Position Sizing

```bash
saham position-size --entry 9500 --stop 9000 --risk 0.02 --capital 100000000
```

---

## CLI Commands

```bash
# === DATA ===
saham sources                          # List data sources
saham universes                        # List stock universes (IDX30/LQ45/etc)
saham quote BBCA                       # Get latest quote
saham ohlc BBCA --period 1y            # Historical OHLC

# === MARKET ===
saham trending --universe LQ45         # Trending stocks
saham breadth --universe LQ45          # Market breadth (A/D ratio)
saham movers top-gainers               # Top gainers
saham movers top-losers                # Top losers
saham movers most-active --by value    # Most active
saham movers native --source goapi     # Native movers from GoAPI

# === SCREENER ===
saham screen bpjs                      # Beli Pagi Jual Sore
saham screen bsjp                      # Beli Sore Jual Pagi
saham screen swing-breakout            # Swing breakout
saham screen swing-pullback            # Swing pullback
saham screen swing-reversal            # Swing reversal (oversold bounce)
saham screen scalping                  # Scalping screener
saham screen unusual                   # Unusual activity

# === SIGNALS & ANALYSIS ===
saham signals --universe IDX30         # Generate BUY/SELL signals
saham mtf BBCA                         # Multi-timeframe analysis
saham position-size --entry 9500 --stop 9000  # Position sizing
```

---

## Python API

### Data

```python
from saham_id.data import get_source

src = get_source("yahoo")       # or "itick", "goapi", "sectors", "rti"
quote = src.get_quote("BBCA")
df = src.get_ohlc("BBCA", period="1y", interval="1d")
```

### Indikator Teknikal

```python
from saham_id.analysis.indicators import rsi, macd, bollinger_bands, sma
from saham_id.analysis.indicators.ichimoku import ichimoku

df["RSI"] = rsi(df["close"], 14)
bb = bollinger_bands(df["close"], 20, 2.0)
ichi = ichimoku(df["high"], df["low"], df["close"])
print(f"Cloud: {ichi.cloud_color}, Price: {ichi.price_vs_cloud}")
```

### Bandarmology

```python
from saham_id.analysis.bandarmology import bandar_score, bandar_scan

# Analisis satu saham
result = bandar_score("BBCA")
print(f"Phase: {result.phase}")       # "ACCUMULATION"
print(f"Score: {result.score}/100")
print(result.interpretation)          # "Indikasi KUAT akumulasi bandar"

# Scan universe
top_picks = bandar_scan(universe="LQ45", min_score=60)
```

### Foreign Flow (Asing Masuk/Keluar)

```python
from saham_id.analysis.foreign_flow import foreign_net_buy_top, foreign_net_sell_top

# Top saham diakumulasi asing
top_buys = foreign_net_buy_top(universe="LQ45", days=20, top_n=10)
for item in top_buys:
    print(f"{item.ticker}: Rp {item.total_net_20d/1e9:.1f}B ({item.activity.value})")

# Top saham didistribusi asing
top_sells = foreign_net_sell_top(universe="LQ45", days=20, top_n=10)
```

### Screener

```python
from saham_id.screener.swing.breakout import screen as breakout_screen
from saham_id.screener.combo import combo_screen

result = breakout_screen(universe="LQ45", top_n=10)
print(result.to_dataframe())

# Multi-factor combo
result = combo_screen(universe="LQ45", min_score=60)
```

### Signal Engine

```python
from saham_id.signals import generate_signals, swing_buy_engine
from saham_id.data.universe import get_universe

tickers = get_universe("IDX30")
signals = generate_signals(tickers, engine=swing_buy_engine())
for s in signals:
    if s.action.value != "HOLD":
        print(f"{s.ticker}: {s.action.value} ({s.confidence:.0%})")
```

### Stock Score Card

```python
from saham_id.scorecard import generate_scorecard

card = generate_scorecard("BBCA")
print(f"Score: {card.overall_score}/100 — {card.recommendation}")
print(f"Trend: {card.trend}, RSI: {card.rsi:.1f}")
print(f"Bandar: {card.bandar_phase}, Asing: {card.foreign_activity}")
print(f"Support: {card.support}")
print(f"Resistance: {card.resistance}")
```

### Lot Calculator

```python
from saham_id.lot_calculator import calculate_lots

result = calculate_lots(budget=10_000_000, price=9500)
print(f"{result.lots} lot ({result.shares} lembar)")
print(f"Total: Rp {result.total_with_fee:,.0f}")
print(f"Sisa: Rp {result.remaining_cash:,.0f}")
```

### Backtest

```python
from saham_id.backtest import Backtester, compute_metrics
from saham_id.backtest.strategies import bpjs_strategy
from saham_id.backtest.report import generate_report

bt = Backtester(strategy=bpjs_strategy, initial_capital=100_000_000)
result = bt.run(df)
metrics = compute_metrics(result)
print(f"Return: {metrics.total_return:.2%}, Sharpe: {metrics.sharpe:.2f}")

# Export ke HTML
path = generate_report(result, metrics, ticker="BBCA", strategy_name="BPJS")
```

### Portfolio & Risk

```python
from saham_id.portfolio import Portfolio, Transaction
from saham_id.risk_manager import RiskManager, StopRule
from saham_id.portfolio.rebalancer import rebalance

# Risk manager
rm = RiskManager(max_portfolio_drawdown=0.10)
rm.add_stop(StopRule(ticker="BBCA", entry_price=9500, stop_price=9000, trailing_pct=0.05))

# Auto-rebalance
result = rebalance(
    current_positions={"BBCA": 1000, "BBRI": 500},
    target_weights={"BBCA": 0.6, "BBRI": 0.4},
    total_capital=50_000_000,
)
```

### Notifications

```python
from saham_id.notifications import NotificationManager, TelegramBackend

manager = NotificationManager()
manager.add_backend(TelegramBackend(bot_token="...", chat_id="..."))
manager.notify("BBCA hit target buy Rp 9000!", level="alert", ticker="BBCA")
```

### Watchlist

```python
from saham_id.watchlist import Watchlist, AlertCondition

wl = Watchlist("portfolio_saya")
wl.add("BBCA", target_buy=9000, stop_loss=8500, alerts=[
    AlertCondition(field="rsi", op="<", value=30, message="RSI oversold!")
])
wl.save()

# Check alerts
triggered = wl.check_alerts()
```

---

## Dashboard Streamlit

```bash
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
# Buka http://localhost:8501
```

### Halaman Dashboard:
1. **Market Overview** — Breadth, top movers, trending, unusual activity
2. **Sinyal** — Generate BUY/SELL signals + detail per saham
3. **Screener** — 6 strategies interaktif
4. **Backtest** — Run strategies + equity curve + trade log
5. **Portfolio** — Transaction recording, P/L, allocation

---

## Modul Lengkap

| Kategori | Modul | File |
|----------|-------|------|
| Data | Sources registry | `data/sources/__init__.py` |
| Data | Yahoo Finance | `data/sources/yahoo_finance.py` |
| Data | RTI Business | `data/sources/rti_scraper.py` |
| Data | iTick (realtime) | `data/sources/itick.py` |
| Data | GoAPI | `data/sources/goapi.py` |
| Data | Sectors.app | `data/sources/sectors_app.py` |
| Data | Universe | `data/universe.py` |
| Data | Models | `data/models.py` |
| Indicators | Trend (SMA/EMA/MACD) | `analysis/indicators/trend.py` |
| Indicators | Momentum (RSI/Stoch/WR) | `analysis/indicators/momentum.py` |
| Indicators | Volatility (ATR/BB) | `analysis/indicators/volatility.py` |
| Indicators | Volume (OBV/VWAP/RVOL) | `analysis/indicators/volume.py` |
| Indicators | Ichimoku Cloud | `analysis/indicators/ichimoku.py` |
| Analysis | Bandarmology | `analysis/bandarmology.py` |
| Analysis | Foreign Flow | `analysis/foreign_flow.py` |
| Analysis | Fundamental | `analysis/fundamental.py` |
| Analysis | Valuation (DCF) | `analysis/valuation.py` |
| Analysis | Risk Metrics | `analysis/risk.py` |
| Analysis | Correlation | `analysis/correlation.py` |
| Analysis | Sector Rotation | `analysis/sector.py` |
| Analysis | Patterns (Candlestick) | `analysis/patterns.py` |
| Analysis | Support/Resistance | `analysis/support_resistance.py` |
| Analysis | Volume Profile | `analysis/volume_profile.py` |
| Analysis | Seasonality | `analysis/seasonality.py` |
| Analysis | Comparison | `analysis/comparison.py` |
| Analysis | Gap Analysis | `analysis/gap_analysis.py` |
| Analysis | Price Action | `analysis/price_action.py` |
| Analysis | Multi-Timeframe | `analysis/mtf.py` |
| Analysis | Intraday Stats | `analysis/intraday_stats.py` |
| Screener | BPJS | `screener/intraday/bpjs.py` |
| Screener | BSJP | `screener/intraday/bsjp.py` |
| Screener | Scalping | `screener/intraday/scalping.py` |
| Screener | Swing Breakout | `screener/swing/breakout.py` |
| Screener | Swing Pullback | `screener/swing/pullback.py` |
| Screener | Swing Reversal | `screener/swing/reversal.py` |
| Screener | Combo | `screener/combo.py` |
| Screener | Gap | `screener/gap_screener.py` |
| Market | Movers | `market/movers.py` |
| Market | Trending | `market/trending.py` |
| Market | Unusual Activity | `market/unusual_activity.py` |
| Market | Breadth | `market/breadth.py` |
| Market | Heatmap | `market/heatmap.py` |
| Market | Regime Detection | `market/regime.py` |
| Backtest | Engine | `backtest/engine.py` |
| Backtest | Metrics | `backtest/metrics.py` |
| Backtest | Optimizer | `backtest/optimizer.py` |
| Backtest | Report (HTML) | `backtest/report.py` |
| Backtest | Strategies | `backtest/strategies/` |
| Portfolio | Tracker | `portfolio/tracker.py` |
| Portfolio | Optimizer | `portfolio/optimizer.py` |
| Portfolio | Sizing | `portfolio/sizing.py` |
| Portfolio | Rebalancer | `portfolio/rebalancer.py` |
| Signals | Signal Engine | `signals.py` |
| Signals | Signal History | `signal_history.py` |
| Tools | Scorecard | `scorecard.py` |
| Tools | Lot Calculator | `lot_calculator.py` |
| Tools | Watchlist | `watchlist.py` |
| Tools | Export | `export.py` |
| Tools | Paper Trading | `paper_trading.py` |
| Tools | Dividend Tracker | `dividend.py` |
| Tools | Earnings Calendar | `earnings_calendar.py` |
| Tools | Scoring Builder | `scoring_builder.py` |
| Notifications | Manager | `notifications.py` |
| Notifications | Scheduler | `scheduler.py` |
| Tools | News Sentiment | `news_sentiment.py` |
| Tools | Risk Manager | `risk_manager.py` |
| Utils | Formatting | `utils/formatting.py` |
| Utils | Calendar (holidays) | `utils/calendar.py` |
| Utils | Logging | `utils/logging.py` |
| CLI | Commands | `cli.py` |

---

## Data Sources

| Source | Tier | Delay | API Key | Features |
|--------|------|-------|---------|----------|
| **yfinance** | Free | ~15m | No | Default. Daily OHLC, limited intraday |
| **RTI Business** | Free | ~15m | No | Rate-limited scraper, daily data |
| **iTick** | Freemium | Realtime | Yes | REST + WebSocket streaming, intraday klines |
| **GoAPI** | Freemium | Realtime | Yes | Quotes, OHLC, native movers |
| **Sectors.app** | Paid | Realtime | Yes | Full fundamentals, sector data |

### Switch source:
```python
src = get_source("itick")    # realtime
src = get_source("goapi")    # Indonesian provider
```

### Atau via environment:
```bash
SAHAM_ID_DATA_SOURCES=itick,yahoo,rti   # fallback chain
```

---

## Struktur Project

```
saham-indonesia/
├── src/saham_id/           # Core library (~29,000 lines)
│   ├── data/               # Models, sources, universe
│   ├── analysis/           # 15+ analysis modules
│   │   └── indicators/     # 12 technical indicators
│   ├── market/             # Movers, trending, breadth, regime, heatmap
│   ├── screener/           # 11+ strategy screeners
│   ├── backtest/           # Engine, metrics, optimizer, report, strategies
│   ├── portfolio/          # Tracker, optimizer, sizing, rebalancer
│   ├── indices/            # IHSG, LQ45, IDX30 data
│   ├── utils/              # Formatting, calendar, logging
│   ├── signals.py          # Composite signal engine
│   ├── scorecard.py        # Stock score card
│   ├── bandarmology → analysis/bandarmology.py
│   ├── notifications.py    # Telegram/Discord/Webhook
│   ├── scheduler.py        # Automated scanning
│   ├── watchlist.py        # Alert system
│   └── cli.py              # 28+ CLI commands
├── tests/                  # 467 unit tests
├── stubs/                  # Offline test stubs
├── notebooks/              # 5 example notebooks
├── dashboard/              # Streamlit 5-page app
├── .github/workflows/      # CI pipeline
├── pyproject.toml          # Project config
├── Dockerfile              # Docker deployment
└── docker-compose.yml      # Dashboard service
```

---

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (works offline, 467 tests)
python run_tests.py

# Or with real pandas
pytest tests/ -v

# Lint
ruff check src/ tests/
```

---

## Docker

```bash
docker compose up dashboard
# Access: http://localhost:8501
```

---

## Notebooks

| Notebook | Topik |
|----------|-------|
| `01_quickstart.py` | Data sources, quotes, OHLC, indicators |
| `02_screeners.py` | Semua screener strategies |
| `03_backtest.py` | BPJS, swing pullback, custom strategy |
| `04_portfolio.py` | Transaction tracking, P/L |
| `05_market_analysis.py` | Movers, trending, risk, valuation |

---

## Environment Variables

```bash
# .env
SAHAM_ID_DATA_SOURCES=yahoo,rti
ITICK_API_KEY=your_key_here
GOAPI_API_KEY=your_key_here
SECTORS_API_KEY=your_key_here
SAHAM_ID_TELEGRAM_TOKEN=your_bot_token
SAHAM_ID_TELEGRAM_CHAT_ID=your_chat_id
SAHAM_ID_DISCORD_WEBHOOK=your_webhook_url
SAHAM_ID_CACHE_DIR=./data/cache
SAHAM_ID_LOG_LEVEL=INFO
```

---

## Disclaimer

⚠️ **Toolkit ini untuk edukasi & riset.**

- Hasil screener/signal bersifat statistikal — *past performance ≠ future results*
- Bukan nasihat investasi / finansial
- Verifikasi data dari sumber resmi sebelum trading real money
- Author tidak bertanggung jawab atas loss apapun

---

## Status

✅ **Production-Ready** — 467 tests passing, semua modul terimplementasi.

---

## License

MIT
