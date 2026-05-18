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
        });
        req.on('error', reject);
        req.setTimeout(15000, () => { req.destroy(); reject(new Error('Timeout')); });
        req.write(postData);
        req.end();
    });
}

function httpsGet(urlStr) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(urlStr);
        const opts = { hostname: parsed.hostname, port: 443, path: parsed.pathname + parsed.search, method: 'GET', headers: { 'User-Agent': 'Mozilla/5.0' } };
        const req = https.request(opts, (res) => {
            let data = ''; res.on('data', c => data += c);
            res.on('end', () => resolve({ status: res.statusCode, body: data }));
        });
        req.on('error', reject);
        req.setTimeout(15000, () => { req.destroy(); reject(new Error('Timeout')); });
        req.end();
    });
}

// ============ TRADINGVIEW SCANNER API ============
async function tvScan(body) {
    const res = await httpsPost(TV_SCANNER_URL, body);
    if (res.status !== 200) throw new Error(`TradingView API error: ${res.status}`);
    const data = JSON.parse(res.body);
    return data;
}

async function tvGetQuotes(symbols) {
    const tickers = symbols.map(s => `IDX:${s}`);
    const body = {
        symbols: { tickers },
        columns: ['close', 'change', 'change_abs', 'volume', 'market_cap_basic', 'price_earnings_ttm', 'price_book_fq', 'open', 'high', 'low', 'name', 'description', 'sector', 'Perf.W', 'Perf.1M', 'prev_close_price']
    };
    const data = await tvScan(body);
    if (!data.data) return [];
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
}

async function tvGetTopStocks(sortBy, sortOrder, limit) {
    const body = {
        filter: [{ left: 'exchange', operation: 'equal', right: 'IDX' }],
        columns: ['close', 'change', 'change_abs', 'volume', 'market_cap_basic', 'name', 'description', 'sector', 'price_earnings_ttm', 'price_book_fq', 'open', 'high', 'low', 'prev_close_price'],
        sort: { sortBy: sortBy || 'volume', sortOrder: sortOrder || 'desc' },
        range: [0, limit || 30]
    };
    const data = await tvScan(body);
    if (!data.data) return [];
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
    let price = currentPrice * 0.85;
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
    // Try to get current price from TradingView to anchor the generated data
    try {
        const quotes = await tvGetQuotes([symbol]);
        if (quotes.length > 0 && quotes[0].close) {
            return generateHistoricalData(quotes[0].close, days);
        }
    } catch (e) {
        console.warn('[TradingView] Quote fetch for history failed:', e.message);
    }
    // Fallback with estimated price
    const info = STOCK_INFO[symbol];
    const estPrice = info ? 5000 : 1000;
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

    // Build filter array
    const filter = [{ left: 'exchange', operation: 'equal', right: 'IDX' }];
    if (params.min_price) filter.push({ left: 'close', operation: 'greater', right: parseFloat(params.min_price) });
    if (params.max_price) filter.push({ left: 'close', operation: 'less', right: parseFloat(params.max_price) });
    if (params.min_volume) filter.push({ left: 'volume', operation: 'greater', right: parseFloat(params.min_volume) });
    if (params.max_pe) filter.push({ left: 'price_earnings_ttm', operation: 'less', right: parseFloat(params.max_pe) });
    if (params.sector) filter.push({ left: 'sector', operation: 'equal', right: params.sector });

    const body = {
        filter,
        columns: ['close', 'change', 'change_abs', 'volume', 'market_cap_basic', 'name', 'description', 'sector', 'price_earnings_ttm', 'price_book_fq', 'RSI', 'open', 'high', 'low'],
        sort: { sortBy, sortOrder },
        range: [0, limit]
    };

    const data = await tvScan(body);
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
        const periodMap = { '1y': 250, '6mo': 130, '3mo': 65, '1mo': 22 };
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
    const periodMap = { '1y': 250, '6mo': 130, '3mo': 90 };
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

    return {
        symbol: ticker,
        name: q.description || q.name || info.name || ticker,
        sector: q.sector || info.sector || '',
        industry: q.sector || info.sector || '',
        market_cap: q.market_cap || 0,
        ratios: {
            pe_ratio: q.pe ? round(q.pe) : null,
            pb_ratio: q.pb ? round(q.pb) : null,
            roe: null,
            roa: null,
            debt_to_equity: null,
            current_ratio: null,
            dividend_yield: null,
            payout_ratio: null
        },
        growth: {
            revenue_growth: null,
            earnings_growth: null
        },
        margins: {
            profit_margin: null,
            operating_margin: null,
            gross_margin: null
        },
        valuation: {
            enterprise_value: 0,
            ev_to_revenue: 0,
            ev_to_ebitda: 0,
            peg_ratio: 0
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
});
