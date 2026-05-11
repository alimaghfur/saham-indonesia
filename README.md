# saham-indonesia

> Analytics & screener toolkit untuk saham Indonesia (IDX / Bursa Efek Indonesia).
> Python library + CLI dengan arsitektur multi-source data yang bisa di-swap.

## Fitur

- **Multi-source data layer** — yfinance, RTI scraper, iTick, GoAPI, Sectors.app (swappable)
- **Market Movers** — Top Gainer, Top Loser, Trending, Unusual Activity
- **Screener strategi trading:**
  - **Scalping** — intraday momentum (butuh data tick/1-min)
  - **BPJS** — Beli Pagi Jual Sore (intraday)
  - **BSJP** — Beli Sore Jual Pagi (overnight gap)
  - **Swing** — breakout, pullback, reversal (3-30 hari)
- **Analisa Fundamental** — PER, PBV, ROE, DER, dividend yield
- **Indikator Teknikal** — MA, EMA, RSI, MACD, Bollinger Bands, ATR, VWAP
- **Valuasi** — DCF, Graham Number, fair value
- **Backtesting** — uji strategi di data historis
- **Portfolio Tracker** — tracking posisi & P/L
- **CLI** — `saham movers`, `saham screen bpjs`, dll.

## Quick Start

```bash
# Clone & install (editable)
git clone https://github.com/alimaghfur/saham-indonesia.git
cd saham-indonesia
pip install -e ".[dev]"

# Copy env template
cp .env.example .env

# Jalankan CLI
saham --help
saham movers top-gainers --universe LQ45
saham screen bpjs --universe LQ45 --top 10
```

## Struktur Proyek

```
saham-indonesia/
├── src/saham_id/
│   ├── data/            # Data layer (sources, models, universe)
│   ├── analysis/        # Indicators, fundamental, valuation, risk
│   ├── market/          # Market movers & breadth
│   ├── screener/        # Strategy screeners
│   │   ├── intraday/    # Scalping, BPJS, BSJP
│   │   └── swing/       # Breakout, pullback, reversal
│   ├── backtest/        # Backtesting engine
│   ├── portfolio/       # Portfolio tracker
│   ├── indices/         # IHSG, LQ45, IDX30, Kompas100
│   ├── utils/           # Formatting, calendar, logging
│   └── cli.py           # CLI entry point
├── tests/
├── notebooks/
├── dashboard/           # (Optional) Streamlit dashboard
└── scripts/
```

## Data Sources

| Source | Tier | Delay | API Key | Notes |
|---|---|---|---|---|
| **yfinance** | Free | ~15 min | No | Default. Daily OHLC lengkap, intraday 7 hari |
| **RTI scraper** | Free | ~15 min | No | Hati-hati ToS. Rate-limited. |
| **iTick** | Freemium | Realtime | Yes | WebSocket streaming, free tier terbatas |
| **GoAPI** | Freemium | Realtime | Yes | Provider lokal Indonesia |
| **Sectors.app** | Paid | Realtime | Yes | Mulai $49/mo, fundamental lengkap |

Ganti source cukup via config:

```python
from saham_id.data import get_source

src = get_source("yahoo")          # default
src = get_source("itick")          # realtime (butuh API key)

quote = src.get_quote("BBCA")
ohlc = src.get_ohlc("BBCA", period="1y")
```

## Disclaimer

⚠️ **Toolkit ini untuk edukasi & riset.**
- Hasil screener bersifat statistikal — *past performance ≠ future results*
- Bukan nasihat investasi / finansial
- Verifikasi data dari sumber resmi sebelum trading real money
- Author tidak bertanggung jawab atas loss apapun

## Status

🚧 **Alpha.** Struktur lengkap, implementasi bertahap per modul.

| Modul | Status |
|---|---|
| Foundation & data models | ✅ |
| yfinance source | ✅ |
| RTI / iTick / GoAPI / Sectors | 🟡 skeleton |
| Indicators | 🟡 skeleton |
| Screener BPJS / BSJP / Swing | 🟡 skeleton |
| Screener Scalping | 🟡 skeleton (butuh realtime) |
| Market Movers | 🟡 skeleton |
| Backtest engine | 🟡 skeleton |
| Portfolio tracker | 🟡 skeleton |
| CLI | 🟡 skeleton |
| Dashboard Streamlit | ⏳ planned |

## Lisensi

MIT
