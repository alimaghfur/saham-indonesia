/**
 * SahamID Backend Server
 * Data Source: iTick API (realtime)
 * Endpoint: https://api.itick.org
 * Region: ID (Indonesia)
 * Free tier: 5 calls/min
 */
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

// Load .env manually
try {
    const envPath = path.join(__dirname, '.env');
    const envContent = fs.readFileSync(envPath, 'utf8');
    envContent.split('\n').forEach(line => {
        line = line.trim();
        if (!line || line.startsWith('#')) return;
        const idx = line.indexOf('=');
        if (idx > 0) {
            const key = line.substring(0, idx).trim();
            const val = line.substring(idx + 1).trim();
            process.env[key] = val;
        }
    });
} catch (e) {
    console.warn('[ENV] Failed to load .env:', e.message);
}

const PORT = process.env.PORT || 8000;
const ITICK_KEY = process.env.ITICK_API_KEY || '';
const ITICK_BASE = 'https://api.itick.org';

console.log('[Config] iTick API Key:', ITICK_KEY ? ITICK_KEY.substring(0, 10) + '...' : 'NOT SET');

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

const TOP_STOCKS = Object.keys(STOCK_INFO);
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


// ============ iTick API HELPERS ============
function itickGet(endpoint, params = {}) {
    return new Promise((resolve, reject) => {
        const qs = Object.entries(params).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&');
        const url = `${ITICK_BASE}${endpoint}?${qs}`;
        const parsed = new URL(url);
        const opts = {
            hostname: parsed.hostname, port: 443,
            path: parsed.pathname + parsed.search,
            method: 'GET',
            headers: { 'token': ITICK_KEY, 'User-Agent': 'SahamID/1.0' }
        };
        const req = https.request(opts, (res) => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => {
                try { resolve(JSON.parse(data)); }
                catch (e) { reject(new Error('Invalid JSON: ' + data.substring(0, 200))); }
            });
            res.on('error', (e) => reject(e));
        });
        req.on('error', (e) => reject(e));
        req.setTimeout(15000, () => { req.destroy(new Error('Timeout')); });
        req.end();
    });
}

// Get quotes for multiple symbols (batch)
async function getQuotes(symbols) {
    const codes = symbols.join(',');
    try {
        const data = await itickGet('/stock/quotes', { region: 'ID', codes });
        if (data.code !== 0 || !data.data) {
            console.warn('[iTick] Quotes error:', data.msg || data.message || JSON.stringify(data));
            return [];
        }
        return data.data.map(d => parseQuote(d));
    } catch (e) {
        console.warn('[iTick] Quotes exception:', e.message);
        return [];
    }
}

// Get single quote
async function getQuote(symbol) {
    try {
        const data = await itickGet('/stock/quote', { region: 'ID', code: symbol });
        if (data.code !== 0 || !data.data) {
            console.warn('[iTick] Quote error:', data.msg || data.message);
            return null;
        }
        return parseQuote(data.data);
    } catch (e) {
        console.warn('[iTick] Quote exception:', e.message);
        return null;
    }
}

function parseQuote(d) {
    const symbol = (d.symbol || d.code || '').toUpperCase();
    const info = STOCK_INFO[symbol] || {};
    const last = parseFloat(d.last || d.close || d.price || 0);
    const prevClose = parseFloat(d.prevClose || d.prev_close || d.preClose || 0);
    const open = parseFloat(d.open || 0);
    const high = parseFloat(d.high || 0);
    const low = parseFloat(d.low || 0);
    const volume = parseInt(d.volume || d.vol || 0);
    const change = prevClose ? last - prevClose : parseFloat(d.change || 0);
    const changePct = prevClose ? ((change / prevClose) * 100) : parseFloat(d.changeRate || d.changePct || d.percent_change || 0);
    return {
        symbol,
        name: d.name || info.name || symbol,
        description: d.name || info.name || symbol,
        sector: info.sector || '',
        close: last, open, high, low,
        prev_close: prevClose,
        volume,
        change_abs: round(change),
        change_pct: round(changePct),
        market_cap: parseInt(d.marketCap || d.market_cap || 0),
        pe: d.pe ? parseFloat(d.pe) : null,
        pb: d.pb ? parseFloat(d.pb) : null
    };
}


// Get kline/historical data
async function getTimeSeries(symbol, period = 'day', size = 90) {
    try {
        const data = await itickGet('/stock/kline', {
            region: 'ID', code: symbol, kType: period, limit: String(size)
        });
        if (data.code !== 0 || !data.data) {
            console.warn('[iTick] Kline error:', data.msg || data.message);
            return [];
        }
        return data.data.map(v => ({
            date: v.time ? new Date(parseInt(v.time) * 1000).toISOString().split('T')[0] : (v.date || v.timestamp || ''),
            open: Math.round(parseFloat(v.open || 0)),
            high: Math.round(parseFloat(v.high || 0)),
            low: Math.round(parseFloat(v.low || 0)),
            close: Math.round(parseFloat(v.close || 0)),
            volume: parseInt(v.volume || v.vol || 0)
        }));
    } catch (e) {
        console.warn('[iTick] Kline exception:', e.message);
        return [];
    }
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
    for (let i = 1; i <= p; i++) { const d = c[i] - c[i-1]; if (d > 0) gS += d; else lS -= d; }
    let aG = gS / p, aL = lS / p;
    r[p] = aL === 0 ? 100 : 100 - (100 / (1 + aG / aL));
    for (let i = p + 1; i < c.length; i++) {
        const d = c[i] - c[i-1];
        aG = (aG * (p-1) + (d > 0 ? d : 0)) / p;
        aL = (aL * (p-1) + (d < 0 ? -d : 0)) / p;
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
    status: 'ok', source: 'iTick API', region: 'ID (Indonesia)',
    apikey: ITICK_KEY ? 'configured' : 'MISSING'
});

routes['/api/market/indices'] = async () => {
    const topQuotes = await getQuotes(['BBCA','BBRI','BMRI','TLKM','ASII']);
    const indices = [];
    if (topQuotes.length > 0) {
        const avgChange = topQuotes.reduce((s, q) => s + q.change_pct, 0) / topQuotes.length;
        const avgPrice = topQuotes.reduce((s, q) => s + q.close, 0) / topQuotes.length;
        indices.push({ name: 'IHSG', symbol: 'COMPOSITE', price: Math.round(avgPrice * 1.4), change: round(avgChange * 50), change_pct: round(avgChange) });
        indices.push({ name: 'LQ45', symbol: 'LQ45', price: Math.round(avgPrice), change: round(avgChange * 10), change_pct: round(avgChange) });
    }
    return { indices };
};

routes['/api/market/top-movers'] = async (params) => {
    const limit = parseInt(params.limit) || 10;
    const quotes = await getQuotes(TOP_STOCKS);
    const fmt = (q) => ({ symbol: q.symbol, price: Math.round(q.close || 0), change: round(q.change_abs || 0), change_pct: round(q.change_pct || 0), volume: q.volume || 0, market_cap: q.market_cap || 0 });
    const valid = quotes.filter(q => q.close > 0);
    const gainers = [...valid].filter(q => q.change_pct > 0).sort((a,b) => b.change_pct - a.change_pct).slice(0, limit).map(fmt);
    const losers = [...valid].filter(q => q.change_pct < 0).sort((a,b) => a.change_pct - b.change_pct).slice(0, limit).map(fmt);
    return { gainers, losers };
};

routes['/api/market/sectors'] = async () => {
    const allSyms = [...new Set(Object.values(SECTORS).flat())];
    const quotes = await getQuotes(allSyms);
    const sectors = Object.entries(SECTORS).map(([name, syms]) => {
        const sq = syms.map(s => quotes.find(q => q.symbol === s)).filter(Boolean);
        const chgs = sq.map(q => q.change_pct || 0);
        const avg = chgs.length ? chgs.reduce((s, v) => s + v, 0) / chgs.length : 0;
        return { sector: name, change_pct: round(avg), stocks: sq.map(q => ({ symbol: q.symbol, change_pct: round(q.change_pct || 0) })).sort((a,b) => b.change_pct - a.change_pct) };
    }).sort((a,b) => b.change_pct - a.change_pct);
    return { sectors };
};

routes['/api/market/summary'] = async () => {
    const quotes = await getQuotes(TOP_STOCKS);
    let adv = 0, dec = 0, unc = 0, vol = 0;
    quotes.forEach(q => { const c = q.change_pct || 0; if (c > 0) adv++; else if (c < 0) dec++; else unc++; vol += q.volume || 0; });
    return { advancing: adv, declining: dec, unchanged: unc, total_volume: vol, sentiment_score: Math.round(adv / Math.max(adv + dec, 1) * 100) };
};

routes['/api/screener/scan'] = async (params) => {
    const limit = parseInt(params.limit) || 20;
    const sortBy = params.sort_by || 'volume';
    const sortOrder = params.sort_order || 'desc';
    const quotes = await getQuotes(TOP_STOCKS);
    let stocks = quotes.filter(q => q.close > 0);
    if (params.min_price) stocks = stocks.filter(s => s.close >= parseFloat(params.min_price));
    if (params.max_price) stocks = stocks.filter(s => s.close <= parseFloat(params.max_price));
    if (params.min_volume) stocks = stocks.filter(s => s.volume >= parseFloat(params.min_volume));
    const sortField = sortBy === 'change_pct' ? 'change_pct' : sortBy === 'price' ? 'close' : 'volume';
    stocks.sort((a,b) => { const av = a[sortField]||0, bv = b[sortField]||0; return sortOrder === 'asc' ? av - bv : bv - av; });
    const results = stocks.slice(0, limit).map(q => ({ symbol: q.symbol, price: Math.round(q.close||0), change_pct: round(q.change_pct||0), pe: q.pe ? round(q.pe) : null, pb: q.pb ? round(q.pb) : null, roe: null, div_yield: null, rsi: null, volume: q.volume||0, volume_ratio: 1.0, market_cap: q.market_cap||0, signal: q.change_pct > 1 ? 'buy' : q.change_pct < -1 ? 'sell' : 'neutral' }));
    return { count: results.length, stocks: results };
};


// ============ DYNAMIC ROUTES ============
async function handleStockRoute(symbol, action, params) {
    const ticker = symbol.toUpperCase();
    if (action === 'quote') {
        const q = await getQuote(ticker);
        if (!q || !q.close) throw new Error('Stock not found');
        return { symbol: ticker, name: q.description || q.name || ticker, price: q.close, previous_close: q.prev_close, open: q.open, day_high: q.high, day_low: q.low, volume: q.volume, market_cap: q.market_cap || 0, change: round(q.change_abs || 0), change_pct: round(q.change_pct || 0) };
    }
    if (action === 'history') {
        const periodMap = { '5y': 1300, '2y': 520, '1y': 250, '6mo': 130, '3mo': 65, '1mo': 22 };
        const size = periodMap[params.period] || 65;
        const candles = await getTimeSeries(ticker, 'day', size);
        return { symbol: ticker, period: params.period || '3mo', data: candles };
    }
    throw new Error('Unknown action');
}

async function handleTechnicalRoute(symbol, action, params) {
    const ticker = symbol.toUpperCase();
    const periodMap = { '5y': 1300, '2y': 520, '1y': 250, '6mo': 130, '3mo': 90 };
    const size = periodMap[params.period] || 90;
    const candles = await getTimeSeries(ticker, 'day', size);
    if (candles.length < 30) throw new Error('Insufficient data');
    const closes = candles.map(c => c.close);
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    const volumes = candles.map(c => c.volume);
    const ma20 = calcSMA(closes, 20), ma50 = calcSMA(closes, 50), ma200 = calcSMA(closes, 200);
    const rsi = calcRSI(closes, 14);
    const { macd, signal: macdSig, histogram } = calcMACD(closes);
    const volAvg = calcSMA(volumes, 20);
    const last = closes.length - 1;
    const currentPrice = closes[last];
    const currentRSI = rsi[last] != null ? round(rsi[last]) : 50;
    const currentMACD = round(macd[last]), currentMACDSig = round(macdSig[last]);
    const cMA20 = ma20[last] ? Math.round(ma20[last]) : null;
    const cMA50 = ma50[last] ? Math.round(ma50[last]) : null;
    const cMA200 = ma200[last] ? Math.round(ma200[last]) : null;
    const volRatio = volAvg[last] > 0 ? round(volumes[last] / volAvg[last]) : 1;
    let bbStd = 0;
    if (last >= 19) { const sl = closes.slice(last-19, last+1); const mn = sl.reduce((s,v)=>s+v,0)/20; bbStd = Math.sqrt(sl.reduce((s,v)=>s+(v-mn)**2,0)/20); }
    const bbUpper = cMA20 ? Math.round(cMA20 + 2*bbStd) : null;
    const bbLower = cMA20 ? Math.round(cMA20 - 2*bbStd) : null;
    const resistances = [...new Set(highs.slice(-20))].filter(h => h > currentPrice).sort((a,b) => a-b).slice(0,3);
    const supports = [...new Set(lows.slice(-20))].filter(l => l < currentPrice).sort((a,b) => b-a).slice(0,3);
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
        return { symbol: ticker, price: currentPrice, indicators: { ma20: cMA20, ma50: cMA50, ma200: cMA200, rsi: currentRSI, macd: currentMACD, macd_signal: currentMACDSig, macd_histogram: round(histogram[last]), bb_upper: bbUpper, bb_middle: cMA20, bb_lower: bbLower, stochastic_k: null, stochastic_d: null, volume: volumes[last], volume_avg_20: volAvg[last] ? Math.round(volAvg[last]) : 0, volume_ratio: volRatio }, support_resistance: { supports, resistances }, signals, score, recommendation: rec };
    }
    if (action === 'chart-data') {
        return { symbol: ticker, data: candles.map((c, i) => ({ ...c, ma20: ma20[i] ? Math.round(ma20[i]) : null, ma50: ma50[i] ? Math.round(ma50[i]) : null, rsi: rsi[i] != null ? round(rsi[i]) : null, macd: round(macd[i]), macd_signal: round(macdSig[i]), macd_hist: round(histogram[i]) })) };
    }
    throw new Error('Unknown action');
}


async function handleFundamentalRoute(symbol) {
    const ticker = symbol.toUpperCase();
    const q = await getQuote(ticker);
    if (!q || !q.close) throw new Error('Stock not found');
    const info = STOCK_INFO[ticker] || {};
    return { symbol: ticker, name: q.description || q.name || info.name || ticker, sector: q.sector || info.sector || '', industry: q.sector || info.sector || '', market_cap: q.market_cap || 0, ratios: { pe_ratio: q.pe ? round(q.pe) : null, pb_ratio: q.pb ? round(q.pb) : null, roe: null, roa: null, debt_to_equity: null, current_ratio: null, dividend_yield: null, payout_ratio: null }, growth: { revenue_growth: null, earnings_growth: null }, margins: { profit_margin: null, operating_margin: null, gross_margin: null }, valuation: { enterprise_value: null, ev_to_revenue: null, ev_to_ebitda: null, peg_ratio: null } };
}

// ============ HTTP SERVER ============
const server = http.createServer(async (req, res) => {
    const parsed = new URL(req.url, `http://${req.headers.host}`);
    const pathname = parsed.pathname;
    const params = Object.fromEntries(parsed.searchParams.entries());
    if (pathname.startsWith('/api/')) {
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
        if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }
        try {
            if (routes[pathname]) { const r = await routes[pathname](params); res.writeHead(200); res.end(JSON.stringify(r)); return; }
            const stockMatch = pathname.match(/^\/api\/stock\/([^/]+)\/([^/]+)$/);
            if (stockMatch) { const r = await handleStockRoute(stockMatch[1], stockMatch[2], params); res.writeHead(200); res.end(JSON.stringify(r)); return; }
            const techMatch = pathname.match(/^\/api\/technical\/([^/]+)\/([^/]+)$/);
            if (techMatch) { const r = await handleTechnicalRoute(techMatch[1], techMatch[2], params); res.writeHead(200); res.end(JSON.stringify(r)); return; }
            const fundMatch = pathname.match(/^\/api\/fundamental\/([^/]+)$/);
            if (fundMatch) { const r = await handleFundamentalRoute(fundMatch[1]); res.writeHead(200); res.end(JSON.stringify(r)); return; }
            res.writeHead(404); res.end(JSON.stringify({ error: 'Not found' }));
        } catch (err) { console.error('API Error:', err.message); res.writeHead(500); res.end(JSON.stringify({ error: err.message })); }
        return;
    }
    let filePath = pathname === '/' ? '/index.html' : pathname;
    filePath = path.join(__dirname, filePath);
    const resolvedPath = path.resolve(filePath);
    if (!resolvedPath.startsWith(__dirname)) { res.writeHead(403); res.end('Forbidden'); return; }
    try { const content = fs.readFileSync(resolvedPath); res.setHeader('Content-Type', MIME[path.extname(resolvedPath)] || 'application/octet-stream'); res.writeHead(200); res.end(content); }
    catch { res.writeHead(404); res.end('Not found'); }
});

server.listen(PORT, () => {
    console.log(`\n  ╔══════════════════════════════════════════════════╗`);
    console.log(`  ║   SahamID - Analisa Saham Indonesia               ║`);
    console.log(`  ╠══════════════════════════════════════════════════╣`);
    console.log(`  ║  Server  : http://localhost:${PORT}                 ║`);
    console.log(`  ║  Data    : iTick API (REALTIME)                   ║`);
    console.log(`  ║  Region  : ID (Indonesia)                         ║`);
    console.log(`  ║  API Key : ${ITICK_KEY ? 'Configured ✓' : 'MISSING ✗'}                          ║`);
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
