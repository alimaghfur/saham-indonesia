# SahamID - Analisa Saham Indonesia

Aplikasi analisa saham Indonesia profesional dengan data **100% real-time** dari Yahoo Finance.

## Fitur

- **Dashboard** - IHSG, LQ45, IDX30, JII real-time + top movers + sentimen pasar
- **Screener** - Filter saham berdasarkan kriteria (PE, ROE, volume, dll)
- **Analisa Teknikal** - Chart candlestick real + RSI, MACD, MA20/50/200, Bollinger Bands, Support/Resistance
- **Analisa Fundamental** - PER, PBV, Market Cap, Growth dari Yahoo Finance
- **Signal & Alert** - Sinyal otomatis dari indikator teknikal
- **Backtesting** - Simulasi Golden Cross pada data historis real
- **Heatmap** - Visualisasi pergerakan semua saham
- **Portfolio & Watchlist** - Tracking investasi

## Sumber Data

**Yahoo Finance** (delay 15 menit, standar industri)
- Harga saham: `BBCA.JK`, `TLKM.JK`, dll
- Indeks: `^JKSE` (IHSG), `^JKLQ45`, `^JKIDX30`
- Historis: OHLCV lengkap
- Fundamental: PE, PBV, Market Cap

## Cara Menjalankan

```bash
# Hanya butuh Node.js (tanpa npm install!)
node server.js

# Atau
./start.sh
```

Buka http://localhost:8000

## Arsitektur

```
┌──────────────┐     ┌─────────────────┐     ┌───────────────┐
│   Browser    │ ←→  │  Node.js Server │ ←→  │ Yahoo Finance │
│  (Frontend)  │     │  (Port 8000)    │     │     API       │
└──────────────┘     └─────────────────┘     └───────────────┘
                            ↓
                    ┌───────────────┐
                    │  Kalkulasi    │
                    │  RSI, MACD,   │
                    │  MA, BB, dll  │
                    └───────────────┘
```

## Tech Stack

- **Backend**: Pure Node.js (zero dependencies!)
- **Frontend**: HTML + Tailwind CSS (CDN) + Vanilla JS
- **Data**: Yahoo Finance API
- **Indikator**: Dihitung server-side (RSI, MACD, MA, Bollinger Bands)

## API Endpoints

| Endpoint | Deskripsi |
|----------|-----------|
| GET /api/market/indices | IHSG, LQ45, IDX30, JII |
| GET /api/market/top-movers | Top gainers & losers |
| GET /api/market/sectors | Performa per sektor |
| GET /api/market/summary | Ringkasan pasar |
| GET /api/stock/:symbol/quote | Harga real-time |
| GET /api/stock/:symbol/history | Data historis OHLCV |
| GET /api/technical/:symbol/indicators | Semua indikator teknikal |
| GET /api/technical/:symbol/chart-data | Data chart + overlay |
| GET /api/fundamental/:symbol | Data fundamental |
| GET /api/screener/scan | Screener saham |

## Kelebihan

- **Zero dependencies** - tidak perlu npm install
- **Data akurat** - langsung dari Yahoo Finance
- **Indikator dihitung sendiri** - RSI, MACD, MA, Bollinger Bands
- **Cepat** - batched API calls
- **Profesional** - UI dark mode modern
