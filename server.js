/**
 * SahamID Backend Server
 * Data Source: Twelve Data API (realtime)
 * Endpoint: https://api.twelvedata.com
 * API Key required - Free tier: 800 credits/day, 8 calls/min
 */
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

// Load .env manually
try {
    const envContent = fs.readFileSync(path.join(__dirname, '.env'), 'utf8');
    envContent.split('\n').forEach(line => {
        const match = line.match(/^([^#=]+)=(.*)$/);
        if (match) process.env[match[1].trim()] = match[2].trim();
    });
} catch (e) {}

const PORT = process.env.PORT || 8000;
const TWELVE_DATA_KEY = process.env.TWELVE_DATA_KEY || '';
const TD_BASE = 'https://api.twelvedata.com';

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

// ============ STOCK INFO ============
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

// ============ TWELVE DATA API HELPERS ============
function tdGet(endpoint, params = {}) {
    return new Promise((resolve, reject) => {
        params.apikey = TWELVE_DATA_KEY;
        const qs = Object.entries(params).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&');
        const url = `${TD_BASE}${endpoint}?${qs}`;
        const parsed = new URL(url);
        const opts = {
            hostname: parsed.hostname, port: 443,
            path: parsed.pathname + parsed.search,
            method: 'GET',
            headers: { 'User-Agent': 'SahamID/1.0' }
        };
        const req = https.request(opts, (res) => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    reject(new Error('Invalid JSON response'));
                }
            });
            res.on('error', (e) => reject(e));
        });
        req.on('error', (e) => reject(e));
        req.setTimeout(15000, () => { req.destroy(new Error('Timeout')); });
        req.end();
    });
}


// Helper: convert symbol to Twelve Data format
function toTDSymbol(symbol) {
    const s = symbol.toUpperCase().replace('.JK', '');
    return `${s}:XIDX`;
}

// Helper: batch quote for multiple symbols (max 8/min on free tier)
async function getQuotes(symbols) {
    const tdSymbols = symbols.map(s => toTDSymbol(s)).join(',');
    const data = await tdGet('/quote', { symbol: tdSymbols });
    
    // Single symbol returns object, multiple returns object keyed by symbol
    if (symbols.length === 1) {
        if (data.status === 'error') {
            console.warn('[TwelveData] Quote error:', data.message);
            return [];
        }
        return [parseQuote(symbols[0], data)];
    }
    
    const results = [];
    for (const sym of symbols) {
        const key = toTDSymbol(sym);
        const item = data[key];
        if (item && item.status !== 'error') {
            results.push(parseQuote(sym, item));
        }
    }
    return results;
}

function parseQuote(symbol, d) {
    const close = parseFloat(d.close) || 0;
    const open = parseFloat(d.open) || 0;
    const high = parseFloat(d.high) || 0;
    const low = parseFloat(d.low) || 0;
    const prevClose = parseFloat(d.previous_close) || 0;
    const volume = parseInt(d.volume) || 0;
    const change = parseFloat(d.change) || 0;
    const changePct = parseFloat(d.percent_change) || 0;
    const info = STOCK_INFO[symbol.toUpperCase()] || {};
    return {
        symbol: symbol.toUpperCase(),
        name: d.name || info.name || symbol,
        description: d.name || info.name || symbol,
        sector: info.sector || '',
        close, open, high, low,
        prev_close: prevClose,
        volume,
        change_abs: change,
        change_pct: changePct,
        market_cap: 0,
        pe: null,
        pb: null
    };
}


// Get time series data
async function getTimeSeries(symbol, interval = '1day', outputsize = 90) {
    const data = await tdGet('/time_series', {
        symbol: toTDSymbol(symbol),
        interval,
        outputsize: String(outputsize),
        order: 'ASC'
    });
    if (data.status === 'error') {
        console.warn('[TwelveData] TimeSeries error:', data.message);
        return [];
    }
    if (!data.values) return [];
    return data.values.map(v => ({
        date: v.datetime.split(' ')[0],
        open: Math.round(parseFloat(v.open)),
        high: Math.round(parseFloat(v.high)),
        low: Math.round(parseFloat(v.low)),
        close: Math.round(parseFloat(v.close)),
        volume: parseInt(v.volume) || 0
    }));
}

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


// ============ API ROUTES ============
const routes = {};

routes['/api/health'] = async () => ({
    status: 'ok',
    source: 'Twelve Data API',
    apikey: TWELVE_DATA_KEY ? 'configured' : 'MISSING'
});

routes['/api/market/indices'] = async () => {
    // Twelve Data doesn't have IHSG directly, use composite approach
    const indexSymbols = ['COMPOSITE:XIDX'];
    try {
        const data = await tdGet('/quote', { symbol: indexSymbols.join(',') });
        const compositeData = data.status !== 'error' ? data : null;
        
        const indices = [];
        if (compositeData && compositeData.close) {
            indices.push({
                name: 'IHSG',
                symbol: 'COMPOSITE',
                price: parseFloat(compositeData.close) || 0,
                change: parseFloat(compositeData.change) || 0,
                change_pct: parseFloat(compositeData.percent_change) || 0
            });
        }
        
        // Get LQ45 proxy from top stocks performance
        const topQuotes = await getQuotes(['BBCA', 'BBRI', 'BMRI', 'TLKM', 'ASII']);
        if (topQuotes.length > 0) {
            const avgChange = topQuotes.reduce((s, q) => s + q.change_pct, 0) / topQuotes.length;
            indices.push({
                name: 'LQ45',
                symbol: 'LQ45',
                price: Math.round(topQuotes.reduce((s, q) => s + q.close, 0) / topQuotes.length),
                change: round(avgChange * 10),
                change_pct: round(avgChange)
            });
        }
        
        return { indices };
    } catch (e) {
        console.warn('[TwelveData] Indices error:', e.message);
        return { indices: [] };
    }
};


routes['/api/market/top-movers'] = async (params) => {
    const limit = parseInt(params.limit) || 10;
    const allSymbols = Object.keys(STOCK_INFO);
    const quotes = await getQuotes(allSymbols);
    
    const formatStock = (q) => ({
        symbol: q.symbol,
        price: Math.round(q.close || 0),
        change: round(q.change_abs || 0),
        change_pct: round(q.change_pct || 0),
        volume: q.volume || 0,
        market_cap: q.market_cap || 0
    });

    const validQuotes = quotes.filter(q => q.close > 0);
    const gainers = [...validQuotes].filter(q => q.change_pct > 0)
        .sort((a, b) => b.change_pct - a.change_pct)
        .slice(0, limit).map(formatStock);
    const losers = [...validQuotes].filter(q => q.change_pct < 0)
        .sort((a, b) => a.change_pct - b.change_pct)
        .slice(0, limit).map(formatStock);

    return { gainers, losers };
};

routes['/api/market/sectors'] = async () => {
    const allSyms = [...new Set(Object.values(SECTORS).flat())];
    const quotes = await getQuotes(allSyms);

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
    const allSymbols = Object.keys(STOCK_INFO);
    const quotes = await getQuotes(allSymbols);
    let adv = 0, dec = 0, unc = 0, vol = 0;
    quotes.forEach(q => {
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

    const allSymbols = Object.keys(STOCK_INFO);
    const quotes = await getQuotes(allSymbols);
    
    let stocks = quotes.filter(q => q.close > 0);

    // Apply filters
    if (params.min_price) stocks = stocks.filter(s => s.close >= parseFloat(params.min_price));
    if (params.max_price) stocks = stocks.filter(s => s.close <= parseFloat(params.max_price));
    if (params.min_volume) stocks = stocks.filter(s => s.volume >= parseFloat(params.min_volume));

    // Sort
    const sortField = sortBy === 'change_pct' ? 'change_pct' : sortBy === 'price' ? 'close' : 'volume';
    stocks.sort((a, b) => {
        const av = a[sortField] || 0, bv = b[sortField] || 0;
        return sortOrder === 'asc' ? av - bv : bv - av;
    });

    const results = stocks.slice(0, limit).map(q => ({
        symbol: q.symbol,
        price: Math.round(q.close || 0),
        change_pct: round(q.change_pct || 0),
        pe: q.pe ? round(q.pe) : null,
        pb: q.pb ? round(q.pb) : null,
        roe: null,
        div_yield: null,
        rsi: null,
        volume: q.volume || 0,
        volume_ratio: 1.0,
        market_cap: q.market_cap || 0,
        signal: q.change_pct > 1 ? 'buy' : q.change_pct < -1 ? 'sell' : 'neutral'
    }));

    return { count: results.length, stocks: results };
};


// ============ DYNAMIC ROUTES ============
async function handleStockRoute(symbol, action, params) {
    const ticker = symbol.toUpperCase();

    if (action === 'quote') {
        const quotes = await getQuotes([ticker]);
        const q = quotes[0];
        if (!q || !q.close) throw new Error('Stock not found');
        return {
            symbol: ticker,
            name: q.description || q.name || ticker,
            price: q.close,
            previous_close: q.prev_close,
            open: q.open,
            day_high: q.high,
            day_low: q.low,
            volume: q.volume,
            market_cap: q.market_cap || 0,
            change: round(q.change_abs || 0),
            change_pct: round(q.change_pct || 0)
        };
    }

    if (action === 'history') {
        const periodMap = { '5y': 1300, '2y': 520, '1y': 250, '6mo': 130, '3mo': 65, '1mo': 22 };
        const size = periodMap[params.period] || 65;
        const candles = await getTimeSeries(ticker, '1day', size);
        return {
            symbol: ticker,
            period: params.period || '3mo',
            data: candles
        };
    }

    throw new Error('Unknown action');
}


async function handleTechnicalRoute(symbol, action, params) {
    const ticker = symbol.toUpperCase();
    const periodMap = { '5y': 1300, '2y': 520, '1y': 250, '6mo': 130, '3mo': 90 };
    const size = periodMap[params.period] || 90;
    const candles = await getTimeSeries(ticker, '1day', size);
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
    const quotes = await getQuotes([ticker]);
    const q = quotes[0];
    if (!q || !q.close) throw new Error('Stock not found');
    const info = STOCK_INFO[ticker] || {};

    // Try to get additional stats from Twelve Data
    let stats = {};
    try {
        stats = await tdGet('/statistics', { symbol: toTDSymbol(ticker) });
        if (stats.status === 'error') stats = {};
    } catch (e) {
        stats = {};
    }

    const pe = stats.valuations_metrics?.pe_ratio || q.pe;
    const pb = stats.valuations_metrics?.pb_ratio || q.pb;
    const roe = stats.financials?.return_on_equity;
    const roa = stats.financials?.return_on_assets;
    const divYield = stats.dividends_and_splits?.dividend_yield;

    return {
        symbol: ticker,
        name: q.description || q.name || info.name || ticker,
        sector: q.sector || info.sector || '',
        industry: q.sector || info.sector || '',
        market_cap: q.market_cap || 0,
        ratios: {
            pe_ratio: pe ? round(parseFloat(pe)) : null,
            pb_ratio: pb ? round(parseFloat(pb)) : null,
            roe: roe ? round(parseFloat(roe)) : null,
            roa: roa ? round(parseFloat(roa)) : null,
            debt_to_equity: stats.financials?.debt_to_equity ? round(parseFloat(stats.financials.debt_to_equity)) : null,
            current_ratio: stats.financials?.current_ratio ? round(parseFloat(stats.financials.current_ratio)) : null,
            dividend_yield: divYield ? round(parseFloat(divYield)) : null,
            payout_ratio: stats.dividends_and_splits?.payout_ratio ? round(parseFloat(stats.dividends_and_splits.payout_ratio)) : null
        },
        growth: {
            revenue_growth: stats.financials?.revenue_growth ? round(parseFloat(stats.financials.revenue_growth)) : null,
            earnings_growth: stats.financials?.earnings_growth ? round(parseFloat(stats.financials.earnings_growth)) : null
        },
        margins: {
            profit_margin: stats.financials?.profit_margin ? round(parseFloat(stats.financials.profit_margin)) : null,
            operating_margin: stats.financials?.operating_margin ? round(parseFloat(stats.financials.operating_margin)) : null,
            gross_margin: stats.financials?.gross_margin ? round(parseFloat(stats.financials.gross_margin)) : null
        },
        valuation: {
            enterprise_value: stats.valuations_metrics?.enterprise_value ? parseInt(stats.valuations_metrics.enterprise_value) : null,
            ev_to_revenue: stats.valuations_metrics?.ev_to_revenue ? round(parseFloat(stats.valuations_metrics.ev_to_revenue)) : null,
            ev_to_ebitda: stats.valuations_metrics?.ev_to_ebitda ? round(parseFloat(stats.valuations_metrics.ev_to_ebitda)) : null,
            peg_ratio: stats.valuations_metrics?.peg_ratio ? round(parseFloat(stats.valuations_metrics.peg_ratio)) : null
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


    // Static file serving
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
    console.log(`  ║  Data    : Twelve Data API (REALTIME)             ║`);
    console.log(`  ║  API Key : ${TWELVE_DATA_KEY ? 'Configured ✓' : 'MISSING ✗'}                          ║`);
    console.log(`  ╠══════════════════════════════════════════════════╣`);
    console.log(`  ║  Endpoints:                                       ║`);
    console.log(`  ║    GET /api/health                                 ║`);
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
