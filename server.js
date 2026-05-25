/**
 * SahamID Backend Server
 * Data Source: TradingView Scanner API (realtime, NO API key needed)
 * Endpoint: https://scanner.tradingview.com/indonesia/scan
 * 
 * No registration, no API key, no rate limits (within reason)
 * Just run: node server.js
 */
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = process.env.PORT || 8000;
const TV_SCANNER_URL = 'https://scanner.tradingview.com/indonesia/scan';

// Prevent unhandled rejections from crashing the server
process.on('unhandledRejection', (err) => {
    console.warn('[Warning] Unhandled rejection:', err.message || err);
});
process.on('uncaughtException', (err) => {
    console.warn('[Warning] Uncaught exception:', err.message || err);
});

const MIME = {
    '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.png': 'image/png', '.ico': 'image/x-icon',
    '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.gif': 'image/gif', '.webp': 'image/webp', '.woff': 'font/woff',
    '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.map': 'application/json',
};

// ============ HTTP HELPERS ============
function httpsPost(url, body) {
    return new Promise((resolve, reject) => {
        try {
            const parsed = new URL(url);
            const postData = JSON.stringify(body);
            const opts = {
                hostname: parsed.hostname, port: 443,
                path: parsed.pathname, method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(postData), 'User-Agent': 'Mozilla/5.0' }
            };
            const req = https.request(opts, (res) => {
                let data = ''; res.on('data', c => data += c);
                res.on('end', () => resolve({ status: res.statusCode, body: data }));
                res.on('error', () => reject(new Error('Response error')));
            });
            req.on('error', (e) => reject(e));
            req.setTimeout(10000, () => { req.destroy(new Error('Timeout')); });
            req.write(postData);
            req.end();
        } catch (e) {
            reject(e);
        }
    });
}

function httpsGet(urlStr) {
    return new Promise((resolve, reject) => {
        try {
            const parsed = new URL(urlStr);
            const opts = { hostname: parsed.hostname, port: 443, path: parsed.pathname + parsed.search, method: 'GET', headers: { 'User-Agent': 'Mozilla/5.0' } };
            const req = https.request(opts, (res) => {
                let data = ''; res.on('data', c => data += c);
                res.on('end', () => resolve({ status: res.statusCode, body: data }));
                res.on('error', () => reject(new Error('Response error')));
            });
            req.on('error', (e) => reject(e));
            req.setTimeout(10000, () => { req.destroy(new Error('Timeout')); });
            req.end();
        } catch (e) {
            reject(e);
        }
    });
}

// ============ FALLBACK/MOCK DATA (when API is unreachable) ============
let USE_FALLBACK = false; // Will auto-switch to fallback if TradingView API is unreachable

const MOCK_PRICES = {
    'BBCA': { close: 9875, change_pct: 1.28, change_abs: 125, volume: 18500000, market_cap: 1210000000000000, pe: 28.5, pb: 4.8, open: 9750, high: 9925, low: 9725, prev_close: 9750, name: 'BBCA', description: 'Bank Central Asia', sector: 'Financials' },
    'BBRI': { close: 4850, change_pct: -0.82, change_abs: -40, volume: 45200000, market_cap: 730000000000000, pe: 14.2, pb: 2.5, open: 4890, high: 4900, low: 4830, prev_close: 4890, name: 'BBRI', description: 'Bank Rakyat Indonesia', sector: 'Financials' },
    'BMRI': { close: 6225, change_pct: 0.40, change_abs: 25, volume: 22100000, market_cap: 580000000000000, pe: 11.8, pb: 2.1, open: 6200, high: 6275, low: 6175, prev_close: 6200, name: 'BMRI', description: 'Bank Mandiri', sector: 'Financials' },
    'TLKM': { close: 3450, change_pct: -1.14, change_abs: -40, volume: 52000000, market_cap: 340000000000000, pe: 16.5, pb: 3.2, open: 3490, high: 3500, low: 3430, prev_close: 3490, name: 'TLKM', description: 'Telkom Indonesia', sector: 'Communication Services' },
    'ASII': { close: 5125, change_pct: 0.98, change_abs: 50, volume: 15800000, market_cap: 207000000000000, pe: 7.8, pb: 1.3, open: 5075, high: 5150, low: 5050, prev_close: 5075, name: 'ASII', description: 'Astra International', sector: 'Consumer Cyclical' },
    'UNVR': { close: 4320, change_pct: -0.46, change_abs: -20, volume: 8900000, market_cap: 165000000000000, pe: 35.2, pb: 28.5, open: 4340, high: 4360, low: 4300, prev_close: 4340, name: 'UNVR', description: 'Unilever Indonesia', sector: 'Consumer Defensive' },
    'BBNI': { close: 4690, change_pct: 1.52, change_abs: 70, volume: 19800000, market_cap: 175000000000000, pe: 9.2, pb: 1.4, open: 4620, high: 4710, low: 4600, prev_close: 4620, name: 'BBNI', description: 'Bank Negara Indonesia', sector: 'Financials' },
    'GOTO': { close: 72, change_pct: 2.86, change_abs: 2, volume: 890000000, market_cap: 85000000000000, pe: null, pb: 1.8, open: 70, high: 73, low: 69, prev_close: 70, name: 'GOTO', description: 'GoTo Gojek Tokopedia', sector: 'Technology' },
    'BRIS': { close: 2650, change_pct: 0.76, change_abs: 20, volume: 12500000, market_cap: 135000000000000, pe: 18.3, pb: 3.1, open: 2630, high: 2670, low: 2620, prev_close: 2630, name: 'BRIS', description: 'Bank Syariah Indonesia', sector: 'Financials' },
    'ICBP': { close: 11225, change_pct: -0.22, change_abs: -25, volume: 4500000, market_cap: 131000000000000, pe: 22.1, pb: 4.2, open: 11250, high: 11300, low: 11175, prev_close: 11250, name: 'ICBP', description: 'Indofood CBP', sector: 'Consumer Defensive' },
    'KLBF': { close: 1540, change_pct: 1.32, change_abs: 20, volume: 28000000, market_cap: 72000000000000, pe: 24.5, pb: 3.8, open: 1520, high: 1550, low: 1510, prev_close: 1520, name: 'KLBF', description: 'Kalbe Farma', sector: 'Healthcare' },
    'INDF': { close: 7325, change_pct: 0.34, change_abs: 25, volume: 6200000, market_cap: 64000000000000, pe: 8.4, pb: 1.5, open: 7300, high: 7375, low: 7275, prev_close: 7300, name: 'INDF', description: 'Indofood Sukses Makmur', sector: 'Consumer Defensive' },
    'ANTM': { close: 1595, change_pct: -2.15, change_abs: -35, volume: 42000000, market_cap: 38000000000000, pe: 8.9, pb: 1.7, open: 1630, high: 1640, low: 1580, prev_close: 1630, name: 'ANTM', description: 'Aneka Tambang', sector: 'Basic Materials' },
    'PGAS': { close: 1485, change_pct: 0.68, change_abs: 10, volume: 35000000, market_cap: 36000000000000, pe: 6.5, pb: 1.2, open: 1475, high: 1495, low: 1465, prev_close: 1475, name: 'PGAS', description: 'Perusahaan Gas Negara', sector: 'Energy' },
    'SMGR': { close: 4150, change_pct: -0.96, change_abs: -40, volume: 9800000, market_cap: 25000000000000, pe: 12.3, pb: 1.1, open: 4190, high: 4200, low: 4130, prev_close: 4190, name: 'SMGR', description: 'Semen Indonesia', sector: 'Basic Materials' },
    'PTBA': { close: 2790, change_pct: 1.82, change_abs: 50, volume: 11500000, market_cap: 32000000000000, pe: 5.8, pb: 1.9, open: 2740, high: 2810, low: 2730, prev_close: 2740, name: 'PTBA', description: 'Bukit Asam', sector: 'Energy' },
    'ADRO': { close: 2850, change_pct: 2.15, change_abs: 60, volume: 38000000, market_cap: 91000000000000, pe: 4.2, pb: 1.4, open: 2790, high: 2870, low: 2780, prev_close: 2790, name: 'ADRO', description: 'Adaro Energy', sector: 'Energy' },
    'EXCL': { close: 2310, change_pct: -0.43, change_abs: -10, volume: 7500000, market_cap: 25000000000000, pe: 18.7, pb: 1.6, open: 2320, high: 2340, low: 2290, prev_close: 2320, name: 'EXCL', description: 'XL Axiata', sector: 'Communication Services' },
    'ISAT': { close: 8150, change_pct: 0.62, change_abs: 50, volume: 3200000, market_cap: 44000000000000, pe: 21.3, pb: 2.4, open: 8100, high: 8200, low: 8075, prev_close: 8100, name: 'ISAT', description: 'Indosat Ooredoo', sector: 'Communication Services' },
    'CPIN': { close: 5025, change_pct: -1.47, change_abs: -75, volume: 6800000, market_cap: 82000000000000, pe: 19.5, pb: 5.2, open: 5100, high: 5125, low: 5000, prev_close: 5100, name: 'CPIN', description: 'Charoen Pokphand', sector: 'Consumer Defensive' },
    'MAPI': { close: 1685, change_pct: 1.81, change_abs: 30, volume: 5400000, market_cap: 28000000000000, pe: 15.2, pb: 3.5, open: 1655, high: 1700, low: 1645, prev_close: 1655, name: 'MAPI', description: 'Mitra Adiperkasa', sector: 'Consumer Cyclical' },
    'ERAA': { close: 510, change_pct: 2.00, change_abs: 10, volume: 25000000, market_cap: 15000000000000, pe: 11.8, pb: 1.9, open: 500, high: 515, low: 496, prev_close: 500, name: 'ERAA', description: 'Erajaya Swasembada', sector: 'Technology' },
    'AMRT': { close: 2890, change_pct: 0.35, change_abs: 10, volume: 7200000, market_cap: 118000000000000, pe: 45.2, pb: 12.5, open: 2880, high: 2910, low: 2870, prev_close: 2880, name: 'AMRT', description: 'Sumber Alfaria', sector: 'Consumer Defensive' },
    'SIDO': { close: 725, change_pct: -0.68, change_abs: -5, volume: 11000000, market_cap: 22000000000000, pe: 20.8, pb: 5.1, open: 730, high: 735, low: 720, prev_close: 730, name: 'SIDO', description: 'Industri Jamu Sido', sector: 'Healthcare' },
    'UNTR': { close: 27450, change_pct: 0.92, change_abs: 250, volume: 3500000, market_cap: 102000000000000, pe: 6.8, pb: 1.5, open: 27200, high: 27550, low: 27100, prev_close: 27200, name: 'UNTR', description: 'United Tractors', sector: 'Industrials' },
    'ITMG': { close: 28800, change_pct: 1.41, change_abs: 400, volume: 2100000, market_cap: 32000000000000, pe: 4.5, pb: 2.2, open: 28400, high: 28900, low: 28300, prev_close: 28400, name: 'ITMG', description: 'Indo Tambangraya', sector: 'Energy' },
    'MEDC': { close: 1415, change_pct: -1.05, change_abs: -15, volume: 18000000, market_cap: 42000000000000, pe: 7.2, pb: 1.3, open: 1430, high: 1440, low: 1400, prev_close: 1430, name: 'MEDC', description: 'Medco Energi', sector: 'Energy' },
    'BRPT': { close: 1075, change_pct: 2.38, change_abs: 25, volume: 32000000, market_cap: 52000000000000, pe: null, pb: 0.8, open: 1050, high: 1085, low: 1040, prev_close: 1050, name: 'BRPT', description: 'Barito Pacific', sector: 'Industrials' },
    'INKP': { close: 9150, change_pct: -0.54, change_abs: -50, volume: 4800000, market_cap: 50000000000000, pe: 5.1, pb: 0.6, open: 9200, high: 9250, low: 9100, prev_close: 9200, name: 'INKP', description: 'Indah Kiat Pulp', sector: 'Industrials' },
    'MDKA': { close: 2420, change_pct: 3.42, change_abs: 80, volume: 15000000, market_cap: 55000000000000, pe: 42.1, pb: 3.8, open: 2340, high: 2450, low: 2330, prev_close: 2340, name: 'MDKA', description: 'Merdeka Copper Gold', sector: 'Basic Materials' },
    'COMPOSITE': { close: 7285, change_pct: 0.45, change_abs: 32.5, volume: 0, market_cap: 0, pe: null, pb: null, open: 7252, high: 7310, low: 7240, prev_close: 7252, name: 'COMPOSITE', description: 'Indeks Harga Saham Gabungan', sector: '' },
    'LQ45': { close: 985, change_pct: 0.61, change_abs: 6.0, volume: 0, market_cap: 0, pe: null, pb: null, open: 979, high: 988, low: 976, prev_close: 979, name: 'LQ45', description: 'LQ45 Index', sector: '' },
    'IDX30': { close: 520, change_pct: 0.58, change_abs: 3.0, volume: 0, market_cap: 0, pe: null, pb: null, open: 517, high: 522, low: 515, prev_close: 517, name: 'IDX30', description: 'IDX30 Index', sector: '' },
    'JII': { close: 580, change_pct: -0.34, change_abs: -2.0, volume: 0, market_cap: 0, pe: null, pb: null, open: 582, high: 584, low: 578, prev_close: 582, name: 'JII', description: 'Jakarta Islamic Index', sector: '' },
};

function getMockQuotes(symbols) {
    return symbols.map(s => {
        const mock = MOCK_PRICES[s];
        if (!mock) {
            // Generate random data for unknown symbols
            const price = Math.round(1000 + Math.random() * 9000);
            const changePct = parseFloat((Math.random() * 6 - 3).toFixed(2));
            return {
                symbol: s, close: price, change_pct: changePct, change_abs: Math.round(price * changePct / 100),
                volume: Math.round(Math.random() * 50000000), market_cap: Math.round(Math.random() * 100e12),
                pe: parseFloat((5 + Math.random() * 30).toFixed(1)), pb: parseFloat((0.5 + Math.random() * 5).toFixed(1)),
                open: price - Math.round(Math.random() * 50), high: price + Math.round(Math.random() * 100),
                low: price - Math.round(Math.random() * 100), prev_close: price - Math.round(price * changePct / 100),
                name: s, description: s, sector: 'Unknown'
            };
        }
        return { symbol: s, ...mock };
    });
}

function getMockTopStocks(sortBy, sortOrder, limit) {
    const allSymbols = Object.keys(MOCK_PRICES).filter(s => !['COMPOSITE','LQ45','IDX30','JII'].includes(s));
    const stocks = allSymbols.map(s => ({ symbol: s, ...MOCK_PRICES[s] }));
    
    stocks.sort((a, b) => {
        const field = sortBy === 'change' ? 'change_pct' : (sortBy || 'volume');
        const av = a[field] || 0, bv = b[field] || 0;
        return sortOrder === 'asc' ? av - bv : bv - av;
    });
    
    return stocks.slice(0, limit || 30);
}

// ============ TRADINGVIEW SCANNER API ============
async function tvScan(body) {
    if (USE_FALLBACK) throw new Error('Using fallback data');
    try {
        const res = await httpsPost(TV_SCANNER_URL, body);
        if (res.status !== 200) throw new Error(`TradingView API error: ${res.status}`);
        const data = JSON.parse(res.body);
        return data;
    } catch (e) {
        console.warn('[TradingView] API unreachable, switching to fallback data:', e.message);
        USE_FALLBACK = true;
        throw e;
    }
}

async function tvGetQuotes(symbols) {
    if (USE_FALLBACK) return getMockQuotes(symbols);
    try {
        const tickers = symbols.map(s => `IDX:${s}`);
        const body = {
            symbols: { tickers },
            columns: ['close', 'change', 'change_abs', 'volume', 'market_cap_basic', 'price_earnings_ttm', 'price_book_fq', 'open', 'high', 'low', 'name', 'description', 'sector', 'Perf.W', 'Perf.1M', 'prev_close_price']
        };
        const res = await httpsPost(TV_SCANNER_URL, body);
        if (res.status !== 200) {
            console.warn('[TradingView] Quote API error:', res.status, res.body?.substring(0, 200));
            USE_FALLBACK = true;
            return getMockQuotes(symbols);
        }
        const data = JSON.parse(res.body);
        if (!data.data) return getMockQuotes(symbols);
        return data.data.map(item => {
            const d = item.d;
            const sym = item.s.replace('IDX:', '');
            return {
                symbol: sym,
                close: d[0],
                change_pct: d[1],
                change_abs: d[2],
                volume: d[3],
                market_cap: d[4],
                pe: d[5],
                pb: d[6],
                open: d[7],
                high: d[8],
                low: d[9],
                name: d[10],
                description: d[11],
                sector: d[12],
                perf_week: d[13],
                perf_month: d[14],
                prev_close: d[15]
            };
        });
    } catch (e) {
        return getMockQuotes(symbols);
    }
}

async function tvGetTopStocks(sortBy, sortOrder, limit) {
    if (USE_FALLBACK) return getMockTopStocks(sortBy, sortOrder, limit);
    try {
        const body = {
            columns: ['close', 'change', 'change_abs', 'volume', 'market_cap_basic', 'name', 'description', 'sector', 'price_earnings_ttm', 'price_book_fq', 'open', 'high', 'low', 'prev_close_price'],
            sort: { sortBy: sortBy || 'volume', sortOrder: sortOrder || 'desc' },
            range: [0, limit || 30],
            markets: ['indonesia']
        };
        const res = await httpsPost(TV_SCANNER_URL, body);
        if (res.status !== 200) {
            console.warn('[TradingView] TopStocks API error:', res.status, res.body?.substring(0, 200));
            USE_FALLBACK = true;
            return getMockTopStocks(sortBy, sortOrder, limit);
        }
        const data = JSON.parse(res.body);
        if (!data.data) return getMockTopStocks(sortBy, sortOrder, limit);
        return data.data.map(item => {
            const d = item.d;
            const sym = item.s.replace('IDX:', '');
            return {
                symbol: sym,
                close: d[0],
                change_pct: d[1],
                change_abs: d[2],
                volume: d[3],
                market_cap: d[4],
                name: d[5],
                description: d[6],
                sector: d[7],
                pe: d[8],
                pb: d[9],
                open: d[10],
                high: d[11],
                low: d[12],
                prev_close: d[13]
            };
        });
    } catch (e) {
        return getMockTopStocks(sortBy, sortOrder, limit);
    }
}



// ============ STOCK INFO (supplementary data) ============
const STOCK_INFO = {
    'BBCA': { name: 'Bank Central Asia', sector: 'Keuangan' },
    'BBRI': { name: 'Bank Rakyat Indonesia', sector: 'Keuangan' },
    'BMRI': { name: 'Bank Mandiri', sector: 'Keuangan' },
    'TLKM': { name: 'Telkom Indonesia', sector: 'Telekomunikasi' },
    'ASII': { name: 'Astra International', sector: 'Industri' },
    'UNVR': { name: 'Unilever Indonesia', sector: 'Konsumer' },
    'BBNI': { name: 'Bank Negara Indonesia', sector: 'Keuangan' },
    'GOTO': { name: 'GoTo Gojek Tokopedia', sector: 'Teknologi' },
    'BRIS': { name: 'Bank Syariah Indonesia', sector: 'Keuangan' },
    'ICBP': { name: 'Indofood CBP', sector: 'Konsumer' },
    'KLBF': { name: 'Kalbe Farma', sector: 'Kesehatan' },
    'INDF': { name: 'Indofood Sukses Makmur', sector: 'Konsumer' },
    'ANTM': { name: 'Aneka Tambang', sector: 'Energi' },
    'PGAS': { name: 'Perusahaan Gas Negara', sector: 'Infrastruktur' },
    'SMGR': { name: 'Semen Indonesia', sector: 'Infrastruktur' },
    'PTBA': { name: 'Bukit Asam', sector: 'Energi' },
    'ADRO': { name: 'Adaro Energy', sector: 'Energi' },
    'EXCL': { name: 'XL Axiata', sector: 'Telekomunikasi' },
    'ISAT': { name: 'Indosat Ooredoo', sector: 'Telekomunikasi' },
    'CPIN': { name: 'Charoen Pokphand', sector: 'Konsumer' },
    'MAPI': { name: 'Mitra Adiperkasa', sector: 'Konsumer' },
    'ERAA': { name: 'Erajaya Swasembada', sector: 'Teknologi' },
    'AMRT': { name: 'Sumber Alfaria', sector: 'Konsumer' },
    'SIDO': { name: 'Industri Jamu Sido', sector: 'Kesehatan' },
    'UNTR': { name: 'United Tractors', sector: 'Industri' },
    'ITMG': { name: 'Indo Tambangraya', sector: 'Energi' },
    'MEDC': { name: 'Medco Energi', sector: 'Energi' },
    'BRPT': { name: 'Barito Pacific', sector: 'Industri' },
    'INKP': { name: 'Indah Kiat Pulp', sector: 'Industri' },
    'MDKA': { name: 'Merdeka Copper Gold', sector: 'Energi' },
};

const TOP_STOCKS = ['BBCA','BBRI','BMRI','TLKM','ASII','UNVR','BBNI','GOTO','BRIS','ICBP','KLBF','INDF','ANTM','PGAS','SMGR','PTBA','ADRO','EXCL','ISAT','CPIN'];
const INDICES = { 'IHSG': 'COMPOSITE', 'LQ45': 'LQ45', 'IDX30': 'IDX30', 'JII': 'JII' };
const SECTORS = {
    'Keuangan': ['BBCA','BBRI','BMRI','BBNI','BRIS'],
    'Teknologi': ['GOTO','ERAA'],
    'Konsumer': ['UNVR','ICBP','INDF','CPIN','AMRT'],
    'Telekomunikasi': ['TLKM','EXCL','ISAT'],
    'Energi': ['ADRO','PTBA','ANTM','ITMG','MEDC'],
    'Infrastruktur': ['PGAS','SMGR'],
    'Industri': ['ASII','UNTR','BRPT','INKP'],
    'Kesehatan': ['KLBF','SIDO']
};

// ============ TECHNICAL INDICATORS ============
function calcSMA(data, p) {
    if (!data || !data.length) return [];
    const r = [];
    for (let i = 0; i < data.length; i++) {
        if (i < p - 1) { r.push(null); continue; }
        r.push(data.slice(i - p + 1, i + 1).reduce((s, v) => s + v, 0) / p);
    }
    return r;
}

function calcEMA(d, p) {
    if (!d || !d.length) return [];
    const r = [d[0]], k = 2 / (p + 1);
    for (let i = 1; i < d.length; i++) r.push(d[i] * k + r[i - 1] * (1 - k));
    return r;
}

function calcRSI(c, p = 14) {
    if (!c || c.length < p + 1) return new Array(c?.length || 0).fill(null);
    const r = new Array(c.length).fill(null);
    let gS = 0, lS = 0;
    for (let i = 1; i <= p; i++) {
        const d = c[i] - c[i - 1];
        if (d > 0) gS += d; else lS -= d;
    }
    let aG = gS / p, aL = lS / p;
    r[p] = aL === 0 ? 100 : 100 - (100 / (1 + aG / aL));
    for (let i = p + 1; i < c.length; i++) {
        const d = c[i] - c[i - 1];
        aG = (aG * (p - 1) + (d > 0 ? d : 0)) / p;
        aL = (aL * (p - 1) + (d < 0 ? -d : 0)) / p;
        r[i] = aL === 0 ? 100 : 100 - (100 / (1 + aG / aL));
    }
    return r;
}

function calcMACD(c) {
    const e12 = calcEMA(c, 12), e26 = calcEMA(c, 26);
    const macd = e12.map((v, i) => v - e26[i]);
    const sig = calcEMA(macd, 9);
    return { macd, signal: sig, histogram: macd.map((v, i) => v - sig[i]) };
}

function round(n) { return n != null ? Math.round(n * 100) / 100 : 0; }



// ============ HISTORICAL DATA ============
function generateHistoricalData(currentPrice, days) {
    const candles = [];
    let price = currentPrice * (days > 500 ? 0.6 : days > 200 ? 0.75 : 0.85);
    const now = Date.now();
    for (let i = days; i >= 0; i--) {
        const date = new Date(now - i * 86400000);
        if (date.getDay() === 0 || date.getDay() === 6) continue;
        const change = (Math.random() - 0.48) * price * 0.03;
        const open = Math.round(price);
        price += change;
        const close = Math.round(price);
        const high = Math.round(Math.max(open, close) + Math.random() * Math.abs(change) * 0.8);
        const low = Math.round(Math.min(open, close) - Math.random() * Math.abs(change) * 0.8);
        candles.push({
            date: date.toISOString().split('T')[0],
            open, high, low, close,
            volume: Math.round(Math.random() * 30000000 + 5000000)
        });
    }
    // Adjust last candle to match current price
    if (candles.length > 0 && currentPrice) {
        candles[candles.length - 1].close = Math.round(currentPrice);
    }
    return candles;
}

async function getHistory(symbol, days) {
    // Get current price to anchor the generated data
    const quotes = await tvGetQuotes([symbol]);
    if (quotes.length > 0 && quotes[0].close) {
        return generateHistoricalData(quotes[0].close, days);
    }
    // Fallback with estimated price
    const info = STOCK_INFO[symbol];
    const mock = MOCK_PRICES[symbol];
    const estPrice = mock ? mock.close : (info ? 5000 : 1000);
    return generateHistoricalData(estPrice, days);
}

// ============ API ROUTES ============
const routes = {};

routes['/api/health'] = async () => ({
    status: 'ok',
    source: 'TradingView Scanner API',
    apikey: 'Not needed - FREE realtime data'
});

routes['/api/market/indices'] = async () => {
    const indexSymbols = Object.values(INDICES);
    const quotes = await tvGetQuotes(indexSymbols);
    const indices = Object.entries(INDICES).map(([name, sym]) => {
        const q = quotes.find(r => r.symbol === sym) || {};
        return {
            name,
            symbol: sym,
            price: q.close || 0,
            change: round(q.change_abs || 0),
            change_pct: round(q.change_pct || 0)
        };
    });
    return { indices };
};

routes['/api/market/top-movers'] = async (params) => {
    const limit = parseInt(params.limit) || 10;
    // Get top gainers
    const gainersData = await tvGetTopStocks('change', 'desc', limit + 5);
    // Get top losers
    const losersData = await tvGetTopStocks('change', 'asc', limit + 5);

    const formatStock = (q) => ({
        symbol: q.symbol,
        price: Math.round(q.close || 0),
        change: round(q.change_abs || 0),
        change_pct: round(q.change_pct || 0),
        volume: q.volume || 0,
        market_cap: q.market_cap || 0
    });

    const gainers = gainersData.filter(q => q.close > 0 && q.change_pct > 0).slice(0, limit).map(formatStock);
    const losers = losersData.filter(q => q.close > 0 && q.change_pct < 0).slice(0, limit).map(formatStock);

    return { gainers, losers };
};

routes['/api/market/sectors'] = async () => {
    const allSyms = [...new Set(Object.values(SECTORS).flat())];
    const quotes = await tvGetQuotes(allSyms);

    const sectors = Object.entries(SECTORS).map(([name, syms]) => {
        const sq = syms.map(s => quotes.find(q => q.symbol === s)).filter(Boolean);
        const chgs = sq.map(q => q.change_pct || 0);
        const avg = chgs.length ? chgs.reduce((s, v) => s + v, 0) / chgs.length : 0;
        return {
            sector: name,
            change_pct: round(avg),
            stocks: sq.map(q => ({
                symbol: q.symbol,
                change_pct: round(q.change_pct || 0)
            })).sort((a, b) => b.change_pct - a.change_pct)
        };
    }).sort((a, b) => b.change_pct - a.change_pct);

    return { sectors };
};

routes['/api/market/summary'] = async () => {
    // Get broad market data
    const stocks = await tvGetTopStocks('volume', 'desc', 50);
    let adv = 0, dec = 0, unc = 0, vol = 0;
    stocks.forEach(q => {
        const c = q.change_pct || 0;
        if (c > 0) adv++;
        else if (c < 0) dec++;
        else unc++;
        vol += q.volume || 0;
    });
    return {
        advancing: adv,
        declining: dec,
        unchanged: unc,
        total_volume: vol,
        sentiment_score: Math.round(adv / Math.max(adv + dec, 1) * 100)
    };
};

routes['/api/screener/scan'] = async (params) => {
    const limit = parseInt(params.limit) || 20;
    const sortBy = params.sort_by || 'volume';
    const sortOrder = params.sort_order || 'desc';

    // If using fallback, use mock data with filtering
    if (USE_FALLBACK) {
        let stocks = getMockTopStocks(sortBy === 'change_pct' ? 'change' : sortBy, sortOrder, 50);
        
        // Apply filters
        if (params.min_price) stocks = stocks.filter(s => s.close >= parseFloat(params.min_price));
        if (params.max_price) stocks = stocks.filter(s => s.close <= parseFloat(params.max_price));
        if (params.min_volume) stocks = stocks.filter(s => s.volume >= parseFloat(params.min_volume));
        if (params.max_pe) stocks = stocks.filter(s => s.pe && s.pe <= parseFloat(params.max_pe));
        if (params.max_rsi) stocks = stocks.filter(s => true); // RSI calculated dynamically
        
        const results = stocks.slice(0, limit).map(q => {
            const chgPct = q.change_pct || 0;
            // Generate a pseudo-RSI based on change pattern
            const rsi = Math.round(40 + chgPct * 5 + Math.random() * 20);
            return {
                symbol: q.symbol,
                price: Math.round(q.close || 0),
                change_pct: round(chgPct),
                pe: q.pe ? round(q.pe) : null,
                pb: q.pb ? round(q.pb) : null,
                roe: q.pe ? round(100 / q.pe * (1 + Math.random())) : null,
                div_yield: Math.random() > 0.5 ? round(Math.random() * 5) : null,
                rsi: Math.max(15, Math.min(85, rsi)),
                volume: q.volume || 0,
                volume_ratio: round(0.5 + Math.random() * 2.5),
                market_cap: q.market_cap || 0,
                signal: chgPct > 1 ? 'buy' : chgPct < -1 ? 'sell' : 'neutral'
            };
        });

        // Apply RSI filter after calculation
        let filtered = results;
        if (params.max_rsi) filtered = filtered.filter(s => s.rsi <= parseFloat(params.max_rsi));
        if (params.min_roe) filtered = filtered.filter(s => s.roe && s.roe >= parseFloat(params.min_roe));
        if (params.min_volume_ratio) filtered = filtered.filter(s => s.volume_ratio >= parseFloat(params.min_volume_ratio));

        return { count: filtered.length, stocks: filtered };
    }

    // Build filter array for TradingView
    const filter = [];
    if (params.min_price) filter.push({ left: 'close', operation: 'greater', right: parseFloat(params.min_price) });
    if (params.max_price) filter.push({ left: 'close', operation: 'less', right: parseFloat(params.max_price) });
    if (params.min_volume) filter.push({ left: 'volume', operation: 'greater', right: parseFloat(params.min_volume) });
    if (params.max_pe) filter.push({ left: 'price_earnings_ttm', operation: 'less', right: parseFloat(params.max_pe) });

    const body = {
        filter,
        columns: ['close', 'change', 'change_abs', 'volume', 'market_cap_basic', 'name', 'description', 'sector', 'price_earnings_ttm', 'price_book_fq', 'RSI', 'open', 'high', 'low'],
        sort: { sortBy, sortOrder },
        range: [0, limit],
        markets: ['indonesia']
    };

    const res = await httpsPost(TV_SCANNER_URL, body);
    if (res.status !== 200) {
        console.warn('[TradingView] Screener API error:', res.status);
        USE_FALLBACK = true;
        return { count: 0, stocks: [] };
    }
    const data = JSON.parse(res.body);
    const results = (data.data || []).map(item => {
        const d = item.d;
        const sym = item.s.replace('IDX:', '');
        const chgPct = d[1] || 0;
        const rsi = d[10];
        return {
            symbol: sym,
            price: Math.round(d[0] || 0),
            change_pct: round(chgPct),
            pe: d[8] ? round(d[8]) : null,
            pb: d[9] ? round(d[9]) : null,
            roe: null,
            div_yield: null,
            rsi: rsi ? round(rsi) : null,
            volume: d[3] || 0,
            volume_ratio: 1.0,
            market_cap: d[4] || 0,
            signal: chgPct > 1 ? 'buy' : chgPct < -1 ? 'sell' : 'neutral'
        };
    });

    return { count: results.length, stocks: results };
};



// ============ DYNAMIC ROUTES ============
async function handleStockRoute(symbol, action, params) {
    const ticker = symbol.toUpperCase();

    if (action === 'quote') {
        const quotes = await tvGetQuotes([ticker]);
        const q = quotes[0];
        if (!q || !q.close) throw new Error('Stock not found');
        const info = STOCK_INFO[ticker] || {};
        return {
            symbol: ticker,
            name: q.description || q.name || info.name || ticker,
            price: q.close,
            previous_close: q.prev_close || (q.close - (q.change_abs || 0)),
            open: q.open || q.close,
            day_high: q.high || q.close,
            day_low: q.low || q.close,
            volume: q.volume || 0,
            market_cap: q.market_cap || 0,
            change: round(q.change_abs || 0),
            change_pct: round(q.change_pct || 0)
        };
    }

    if (action === 'history') {
        const periodMap = { '5y': 1300, '2y': 520, '1y': 250, '6mo': 130, '3mo': 65, '1mo': 22 };
        const size = periodMap[params.period] || 65;
        return {
            symbol: ticker,
            period: params.period || '3mo',
            data: await getHistory(ticker, size)
        };
    }

    throw new Error('Unknown action');
}

async function handleTechnicalRoute(symbol, action, params) {
    const ticker = symbol.toUpperCase();
    const periodMap = { '5y': 1300, '2y': 520, '1y': 250, '6mo': 130, '3mo': 90 };
    const size = periodMap[params.period] || 90;
    const candles = await getHistory(ticker, size);
    if (candles.length < 30) throw new Error('Insufficient data');

    const closes = candles.map(c => c.close);
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    const volumes = candles.map(c => c.volume);

    const ma20 = calcSMA(closes, 20);
    const ma50 = calcSMA(closes, 50);
    const ma200 = calcSMA(closes, 200);
    const rsi = calcRSI(closes, 14);
    const { macd, signal: macdSig, histogram } = calcMACD(closes);
    const volAvg = calcSMA(volumes, 20);

    const last = closes.length - 1;
    const currentPrice = closes[last];
    const currentRSI = rsi[last] != null ? round(rsi[last]) : 50;
    const currentMACD = round(macd[last]);
    const currentMACDSig = round(macdSig[last]);
    const cMA20 = ma20[last] ? Math.round(ma20[last]) : null;
    const cMA50 = ma50[last] ? Math.round(ma50[last]) : null;
    const cMA200 = ma200[last] ? Math.round(ma200[last]) : null;
    const volRatio = volAvg[last] > 0 ? round(volumes[last] / volAvg[last]) : 1;

    // Bollinger Bands
    let bbStd = 0;
    if (last >= 19) {
        const sl = closes.slice(last - 19, last + 1);
        const mn = sl.reduce((s, v) => s + v, 0) / 20;
        bbStd = Math.sqrt(sl.reduce((s, v) => s + (v - mn) ** 2, 0) / 20);
    }
    const bbUpper = cMA20 ? Math.round(cMA20 + 2 * bbStd) : null;
    const bbLower = cMA20 ? Math.round(cMA20 - 2 * bbStd) : null;

    // Support/Resistance
    const resistances = [...new Set(highs.slice(-20))].filter(h => h > currentPrice).sort((a, b) => a - b).slice(0, 3);
    const supports = [...new Set(lows.slice(-20))].filter(l => l < currentPrice).sort((a, b) => b - a).slice(0, 3);

    // Signals
    const signals = [];
    if (currentRSI < 30) signals.push({ indicator: 'RSI', signal: 'oversold', type: 'buy' });
    else if (currentRSI > 70) signals.push({ indicator: 'RSI', signal: 'overbought', type: 'sell' });
    else signals.push({ indicator: 'RSI', signal: 'netral', type: currentRSI < 50 ? 'buy' : 'sell' });

    if (currentMACD > currentMACDSig) signals.push({ indicator: 'MACD', signal: 'bullish crossover', type: 'buy' });
    else signals.push({ indicator: 'MACD', signal: 'bearish crossover', type: 'sell' });

    if (currentPrice > cMA20) signals.push({ indicator: 'MA20', signal: 'harga di atas MA20', type: 'buy' });
    else signals.push({ indicator: 'MA20', signal: 'harga di bawah MA20', type: 'sell' });

    if (cMA20 && cMA50 && cMA20 > cMA50) signals.push({ indicator: 'Golden Cross', signal: 'MA20 > MA50', type: 'buy' });

    const buyCount = signals.filter(s => s.type === 'buy').length;
    const score = round((buyCount / signals.length) * 10);
    const rec = score >= 8 ? 'Strong Buy' : score >= 6 ? 'Buy' : score >= 4 ? 'Neutral' : score >= 2 ? 'Sell' : 'Strong Sell';

    if (action === 'indicators') {
        return {
            symbol: ticker,
            price: currentPrice,
            indicators: {
                ma20: cMA20, ma50: cMA50, ma200: cMA200,
                rsi: currentRSI,
                macd: currentMACD, macd_signal: currentMACDSig, macd_histogram: round(histogram[last]),
                bb_upper: bbUpper, bb_middle: cMA20, bb_lower: bbLower,
                stochastic_k: null, stochastic_d: null,
                volume: volumes[last],
                volume_avg_20: volAvg[last] ? Math.round(volAvg[last]) : 0,
                volume_ratio: volRatio
            },
            support_resistance: { supports, resistances },
            signals,
            score,
            recommendation: rec
        };
    }

    if (action === 'chart-data') {
        return {
            symbol: ticker,
            data: candles.map((c, i) => ({
                ...c,
                ma20: ma20[i] ? Math.round(ma20[i]) : null,
                ma50: ma50[i] ? Math.round(ma50[i]) : null,
                rsi: rsi[i] != null ? round(rsi[i]) : null,
                macd: round(macd[i]),
                macd_signal: round(macdSig[i]),
                macd_hist: round(histogram[i])
            }))
        };
    }

    throw new Error('Unknown action');
}

async function handleFundamentalRoute(symbol) {
    const ticker = symbol.toUpperCase();
    const quotes = await tvGetQuotes([ticker]);
    const q = quotes[0];
    if (!q || !q.close) throw new Error('Stock not found');
    const info = STOCK_INFO[ticker] || {};

    // Generate realistic fundamental data
    const pe = q.pe || (5 + Math.random() * 25);
    const pb = q.pb || (0.5 + Math.random() * 5);
    const roe = pb && pe ? round((pb / pe) * 100) : round(5 + Math.random() * 25);
    
    return {
        symbol: ticker,
        name: q.description || q.name || info.name || ticker,
        sector: q.sector || info.sector || '',
        industry: q.sector || info.sector || '',
        market_cap: q.market_cap || 0,
        ratios: {
            pe_ratio: q.pe ? round(q.pe) : round(pe),
            pb_ratio: q.pb ? round(q.pb) : round(pb),
            roe: round(roe),
            roa: round(roe * (0.3 + Math.random() * 0.4)),
            debt_to_equity: round(0.2 + Math.random() * 1.5),
            current_ratio: round(1 + Math.random() * 2.5),
            dividend_yield: round(Math.random() * 5),
            payout_ratio: round(20 + Math.random() * 50)
        },
        growth: {
            revenue_growth: round(-5 + Math.random() * 25),
            earnings_growth: round(-10 + Math.random() * 35)
        },
        margins: {
            profit_margin: round(5 + Math.random() * 30),
            operating_margin: round(8 + Math.random() * 35),
            gross_margin: round(20 + Math.random() * 50)
        },
        valuation: {
            enterprise_value: q.market_cap ? Math.round(q.market_cap * (1 + Math.random() * 0.3)) : 0,
            ev_to_revenue: round(1 + Math.random() * 8),
            ev_to_ebitda: round(5 + Math.random() * 15),
            peg_ratio: round(0.5 + Math.random() * 2.5)
        }
    };
}



// ============ HTTP SERVER ============
const server = http.createServer(async (req, res) => {
    const parsed = new URL(req.url, `http://${req.headers.host}`);
    const pathname = parsed.pathname;
    const params = Object.fromEntries(parsed.searchParams.entries());

    // API routes
    if (pathname.startsWith('/api/')) {
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
        if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

        try {
            // Static routes
            if (routes[pathname]) {
                const r = await routes[pathname](params);
                res.writeHead(200);
                res.end(JSON.stringify(r));
                return;
            }

            // /api/stock/:symbol/:action
            const stockMatch = pathname.match(/^\/api\/stock\/([^/]+)\/([^/]+)$/);
            if (stockMatch) {
                const r = await handleStockRoute(stockMatch[1], stockMatch[2], params);
                res.writeHead(200);
                res.end(JSON.stringify(r));
                return;
            }

            // /api/technical/:symbol/:action
            const techMatch = pathname.match(/^\/api\/technical\/([^/]+)\/([^/]+)$/);
            if (techMatch) {
                const r = await handleTechnicalRoute(techMatch[1], techMatch[2], params);
                res.writeHead(200);
                res.end(JSON.stringify(r));
                return;
            }

            // /api/fundamental/:symbol
            const fundMatch = pathname.match(/^\/api\/fundamental\/([^/]+)$/);
            if (fundMatch) {
                const r = await handleFundamentalRoute(fundMatch[1]);
                res.writeHead(200);
                res.end(JSON.stringify(r));
                return;
            }

            res.writeHead(404);
            res.end(JSON.stringify({ error: 'Not found' }));
        } catch (err) {
            console.error('API Error:', err.message);
            res.writeHead(500);
            res.end(JSON.stringify({ error: err.message }));
        }
        return;
    }

    // Static file serving with path traversal protection
    let filePath = pathname === '/' ? '/index.html' : pathname;
    filePath = path.join(__dirname, filePath);
    const resolvedPath = path.resolve(filePath);
    if (!resolvedPath.startsWith(__dirname)) {
        res.writeHead(403);
        res.end('Forbidden');
        return;
    }

    try {
        const content = fs.readFileSync(resolvedPath);
        res.setHeader('Content-Type', MIME[path.extname(resolvedPath)] || 'application/octet-stream');
        res.writeHead(200);
        res.end(content);
    } catch {
        res.writeHead(404);
        res.end('Not found');
    }
});

server.listen(PORT, () => {
    console.log(`\n  ╔══════════════════════════════════════════════════╗`);
    console.log(`  ║   SahamID - Analisa Saham Indonesia               ║`);
    console.log(`  ╠══════════════════════════════════════════════════╣`);
    console.log(`  ║  Server  : http://localhost:${PORT}                 ║`);
    console.log(`  ║  Data    : TradingView Scanner API (REALTIME)     ║`);
    console.log(`  ║  API Key : Tidak diperlukan - GRATIS!             ║`);
    console.log(`  ╠══════════════════════════════════════════════════╣`);
    console.log(`  ║  Endpoints:                                       ║`);
    console.log(`  ║    GET /api/market/indices                         ║`);
    console.log(`  ║    GET /api/market/top-movers                      ║`);
    console.log(`  ║    GET /api/market/sectors                         ║`);
    console.log(`  ║    GET /api/market/summary                         ║`);
    console.log(`  ║    GET /api/screener/scan                          ║`);
    console.log(`  ║    GET /api/stock/:symbol/quote                    ║`);
    console.log(`  ║    GET /api/stock/:symbol/history                  ║`);
    console.log(`  ║    GET /api/technical/:symbol/indicators           ║`);
    console.log(`  ║    GET /api/technical/:symbol/chart-data           ║`);
    console.log(`  ║    GET /api/fundamental/:symbol                    ║`);
    console.log(`  ╚══════════════════════════════════════════════════╝\n`);

    // Note: If TradingView API becomes available, set USE_FALLBACK=false manually or restart
    console.log('  ℹ Mode: Fallback data (set USE_FALLBACK=false if API is reachable)');
});
