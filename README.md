# saham-indonesia 📈

> **Analytics & screener toolkit untuk saham Indonesia (IDX / Bursa Efek Indonesia).**
>
> Python library + CLI + Streamlit Dashboard — arsitektur multi-source data yang bisa di-swap.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Fitur Utama

| Kategori | Fitur |
|----------|-------|
| **Data Sources** | yfinance, RTI Business, iTick (realtime + WS), GoAPI, Sectors.app |
| **Market** | Top Gainer/Loser, Most Active, Trending, Unusual Activity, Market Breadth |
| **Screener** | Swing Breakout, Pullback, Reversal, BPJS, BSJP, Scalping |
| **Indikator** | SMA, EMA, MACD, RSI, Stochastic, Williams %R, ATR, Bollinger Bands, OBV, VWAP, RVOL |
| **Analisis** | Fundamental scoring, DCF valuation, Graham Number, Risk metrics (Sharpe, Sortino, VaR, Beta) |
| **Backtest** | Event-driven engine, commission modeling, equity curve, performance metrics |
| **Portfolio** | Transaction recording, P/L tracking, allocation, live quotes |
| **CLI** | 20+ commands via `saham` |
| **Dashboard** | Streamlit multi-page app (Market, Screener, Backtest, Portfolio) |
| **Calendar** | IDX holidays 2025-2026, trading day detection |

---

## Quick Start

```bash
# Clone & install
git clone https://github.com/alimaghfur/saham-indonesia.git
cd saham-indonesia
pip install -e ".[dev]"

# Copy env template
cp .env.example .env
# (optional) Isi API keys untuk iTick/GoAPI/Sectors.app

# Test
python run_tests.py     # 164 tests, no dependencies needed

# CLI
saham --help
saham quote BBCA
saham movers top-gainers --universe LQ45
saham screen bpjs --universe LQ45 --top 10
saham trending --universe LQ45
```

### Streamlit Dashboard

```bash
pip install -e ".[dashboard]"
streamlit run dashboard/app.py
```

---

## CLI Commands

```
saham --help                          # Show all commands
saham sources                         # List data sources
saham universes                       # List stock universes
saham quote BBCA                      # Get quote
saham ohlc BBCA --period 1y           # Historical OHLC
saham trending --universe LQ45        # Trending stocks
saham breadth --universe LQ45         # Market breadth

saham movers top-gainers              # Top gainers
saham movers top-losers               # Top losers
saham movers most-active --by value   # Most active
saham movers native --source goapi    # Native movers from GoAPI

saham screen bpjs                     # Beli Pagi Jual Sore
saham screen bsjp                     # Beli Sore Jual Pagi
saham screen swing-breakout           # Swing breakout
saham screen swing-pullback           # Swing pullback
saham screen swing-reversal           # Swing reversal (oversold bounce)
saham screen scalping                 # Scalping screener
saham screen unusual                  # Unusual activity
```

---

## Python API

```python
from saham_id.data import get_source
from saham_id.analysis.indicators import rsi, macd, bollinger_bands
from saham_id.screener.swing.breakout import screen as breakout_screen
from saham_id.backtest import Backtester, compute_metrics
from saham_id.portfolio import Portfolio, Transaction

# Data
src = get_source("yahoo")
quote = src.get_quote("BBCA")
df = src.get_ohlc("BBCA", period="1y", interval="1d")

# Indicators
df["RSI"] = rsi(df["close"], 14)
bb = bollinger_bands(df["close"], 20, 2.0)

# Screener
result = breakout_screen(universe="LQ45", top_n=10, source=src)
print(result.to_dataframe())

# Backtest
from saham_id.backtest.strategies import bpjs_strategy
bt = Backtester(strategy=bpjs_strategy, initial_capital=100_000_000)
result = bt.run(df)
metrics = compute_metrics(result)
print(f"Return: {metrics.total_return:.2%}, Sharpe: {metrics.sharpe:.2f}")
```

---

## Data Sources

| Source | Tier | Delay | API Key | Features |
|--------|------|-------|---------|----------|
| **yfinance** | Free | ~15m | No | Default. Daily OHLC, intraday 7 hari |
| **RTI Business** | Free | ~15m | No | Rate-limited scraper |
| **iTick** | Freemium | Realtime | Yes | REST + WebSocket streaming, intraday klines |
| **GoAPI** | Freemium | Realtime | Yes | Quotes, OHLC, native movers endpoint |
| **Sectors.app** | Paid | Realtime | Yes | Fundamental data lengkap, sector classification |

Switch source:
```python
src = get_source("itick")    # realtime
src = get_source("goapi")    # Indonesian provider
src = get_source("sectors")  # premium fundamentals
```

Or via environment:
```bash
SAHAM_ID_DATA_SOURCES=itick,yahoo,rti   # fallback chain
```

---

## Project Structure

```
saham-indonesia/
├── src/saham_id/           # Core library
│   ├── data/               # Models, sources, universe
│   │   └── sources/        # yahoo, rti, itick, goapi, sectors
│   ├── analysis/           # Indicators, fundamental, valuation, risk
│   │   └── indicators/     # trend, momentum, volatility, volume
│   ├── market/             # Movers, trending, unusual, breadth
│   ├── screener/           # Strategy screeners
│   │   ├── intraday/       # bpjs, bsjp, scalping
│   │   └── swing/          # breakout, pullback, reversal
│   ├── backtest/           # Engine, metrics, strategies
│   ├── portfolio/          # Position & transaction tracker
│   ├── indices/            # IHSG, LQ45, IDX30 index data
│   ├── utils/              # Formatting, calendar, logging
│   └── cli.py              # Typer CLI
├── tests/                  # 164 unit tests
├── stubs/                  # Offline test stubs (pandas/numpy/yfinance)
├── notebooks/              # 5 example notebooks
├── dashboard/              # Streamlit multi-page app
├── .github/workflows/      # CI pipeline
├── pyproject.toml          # Project config (hatchling)
├── run_tests.py            # Custom test runner (no pytest needed)
├── Dockerfile              # Docker deployment
└── docker-compose.yml      # Dashboard + optional services
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests (works offline, no pandas/numpy needed)
python run_tests.py

# Or with pytest (needs pandas/numpy installed)
pytest tests/ -v

# Lint
ruff check src/ tests/

# Type check
mypy src/saham_id/
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

## IDX Trading Calendar

Library menyertakan kalender hari libur IDX 2025-2026 (berdasarkan SKB 3 Menteri):

```python
from saham_id.utils.calendar import (
    is_trading_day, next_trading_day, trading_days_between,
    detect_holidays_from_ohlc,  # auto-detect dari data
)
from datetime import date

is_trading_day(date(2025, 3, 31))  # False (Idul Fitri)
next_trading_day(date(2025, 3, 31))  # 2025-04-07
```

---

## Docker

```bash
# Build & run dashboard
docker compose up dashboard

# Access: http://localhost:8501
```

---

## Disclaimer

⚠️ **Toolkit ini untuk edukasi & riset.**

- Hasil screener bersifat statistikal — *past performance ≠ future results*
- Bukan nasihat investasi / finansial
- Verifikasi data dari sumber resmi sebelum trading real money
- Author tidak bertanggung jawab atas loss apapun

---

## Status

✅ **Beta** — semua modul terimplementasi dan ter-test.

| Modul | Status |
|-------|--------|
| Data models & universe (IDX30/LQ45/IDX80/Kompas100) | ✅ |
| yfinance source | ✅ |
| RTI Business scraper | ✅ |
| iTick REST + WebSocket | ✅ |
| GoAPI (quotes + OHLC + movers) | ✅ |
| Sectors.app (quotes + OHLC + fundamentals) | ✅ |
| Technical indicators (11 indicators) | ✅ |
| Screener BPJS / BSJP | ✅ |
| Screener Swing (breakout/pullback/reversal) | ✅ |
| Screener Scalping | ✅ |
| Market Movers / Trending / Unusual / Breadth | ✅ |
| Backtest engine + metrics | ✅ |
| Portfolio tracker | ✅ |
| CLI (20+ commands) | ✅ |
| Streamlit Dashboard (4 pages) | ✅ |
| Unit tests (164 tests) | ✅ |
| IDX Calendar (2025-2026 holidays) | ✅ |
| Example Notebooks (5) | ✅ |
| CI/CD (GitHub Actions) | ✅ |
| Docker deployment | ✅ |

---

## License

MIT
