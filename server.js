/**
 * SahamID Backend Server
 * Pure Node.js - proxies Yahoo Finance API with fallback to realistic data
 */
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = process.env.PORT || 8000;

const MIME = {
    '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.png': 'image/png', '.ico': 'image/x-icon',
    '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.gif': 'image/gif', '.webp': 'image/webp', '.woff': 'font/woff',
    '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.map': 'application/json',
};

// ============ HTTP HELPER ============
function httpsRequest(urlStr, headers = {}) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(urlStr);
        const opts = {
            hostname: parsed.hostname, port: 443,
            path: parsed.pathname + parsed.search, method: 'GET',
            headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', ...headers },
        };
        const req = https.request(opts, (res) => {
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                const loc = res.headers.location.startsWith('http') ? res.headers.location : `https://${parsed.hostname}${res.headers.location}`;
                resolve(httpsRequest(loc, headers)); return;
            }
            let data = ''; res.on('data', c => data += c);
            res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
        });
        req.on('error', reject);
        req.setTimeout(12000, () => { req.destroy(); reject(new Error('Timeout')); });
        req.end();
    });
}

// ============ YAHOO FINANCE PROXY (andihermanto.id) ============
// This is a free proxy hosted in Indonesia - accessible without auth
async function proxyFetch(symbol, range = '3mo', interval = '1d') {
    const url = `https://data-api-saham.andihermanto.id/api/stock?symbol=${symbol}&range=${range}&interval=${interval}`;
    const res = await httpsRequest(url, { 'Accept': 'application/json' });
    if (res.status === 200) return JSON.parse(res.body);
    throw new Error(`Proxy API error: ${res.status}`);
}

// ============ YAHOO FINANCE DIRECT WITH AUTH ============
let yfCookie = '', yfCrumb = '', yfAuthTime = 0;

async function refreshAuth() {
    if (yfCookie && yfCrumb && (Date.now() - yfAuthTime) < 1800000) return true;
    try {
        const r1 = await httpsRequest('https://fc.yahoo.com');
        let cookies = (r1.headers['set-cookie'] || []).map(c => c.split(';')[0]).join('; ');
        if (!cookies) {
            const r2 = await httpsRequest('https://finance.yahoo.com');
            cookies = (r2.headers['set-cookie'] || []).map(c => c.split(';')[0]).join('; ');
        }
        if (!cookies) return false;
        const r3 = await httpsRequest('https://query2.finance.yahoo.com/v1/test/getcrumb', { 'Cookie': cookies });
        if (r3.status === 200 && r3.body && !r3.body.includes('<') && r3.body.length < 50) {
            yfCookie = cookies; yfCrumb = r3.body.trim(); yfAuthTime = Date.now();
            console.log('[Yahoo] Auth OK'); return true;
        }
        return false;
    } catch (e) { return false; }
}

async function yahooFetch(endpoint) {
    const ok = await refreshAuth();
    const sep = endpoint.includes('?') ? '&' : '?';
    const url = ok ? `https://query1.finance.yahoo.com${endpoint}${sep}crumb=${encodeURIComponent(yfCrumb)}` : `https://query1.finance.yahoo.com${endpoint}`;
    const hdrs = { 'Accept': 'application/json' }; if (ok) hdrs['Cookie'] = yfCookie;
    const res = await httpsRequest(url, hdrs);
    if ((res.status === 401 || res.status === 403) && ok) {
        yfAuthTime = 0; yfCookie = ''; yfCrumb = '';
        if (await refreshAuth()) {
            const r2 = await httpsRequest(`https://query1.finance.yahoo.com${endpoint}${sep}crumb=${encodeURIComponent(yfCrumb)}`, { 'Accept': 'application/json', 'Cookie': yfCookie });
            return JSON.parse(r2.body);
        }
        throw new Error('Auth failed');
    }
    return JSON.parse(res.body);
}

// ============ REALISTIC FALLBACK DATA ============
const STOCK_DATA = {
    'BBCA': { name: 'Bank Central Asia', sector: 'Keuangan', price: 9875, pe: 24.5, pb: 4.8, mcap: 1215e12 },
    'BBRI': { name: 'Bank Rakyat Indonesia', sector: 'Keuangan', price: 4650, pe: 13.2, pb: 2.4, mcap: 700e12 },
    'BMRI': { name: 'Bank Mandiri', sector: 'Keuangan', price: 6225, pe: 11.8, pb: 2.1, mcap: 580e12 },
    'TLKM': { name: 'Telkom Indonesia', sector: 'Telekomunikasi', price: 2780, pe: 12.5, pb: 2.9, mcap: 275e12 },
    'ASII': { name: 'Astra International', sector: 'Industri', price: 4850, pe: 7.8, pb: 1.3, mcap: 196e12 },
    'UNVR': { name: 'Unilever Indonesia', sector: 'Konsumer', price: 2450, pe: 18.9, pb: 25.1, mcap: 93e12 },
    'BBNI': { name: 'Bank Negara Indonesia', sector: 'Keuangan', price: 4520, pe: 9.5, pb: 1.4, mcap: 168e12 },
    'GOTO': { name: 'GoTo Gojek Tokopedia', sector: 'Teknologi', price: 72, pe: null, pb: 1.2, mcap: 85e12 },
    'BRIS': { name: 'Bank Syariah Indonesia', sector: 'Keuangan', price: 2650, pe: 18.3, pb: 3.1, mcap: 135e12 },
    'ICBP': { name: 'Indofood CBP', sector: 'Konsumer', price: 11025, pe: 20.1, pb: 3.8, mcap: 128e12 },
    'KLBF': { name: 'Kalbe Farma', sector: 'Kesehatan', price: 1560, pe: 22.4, pb: 3.5, mcap: 73e12 },
    'INDF': { name: 'Indofood Sukses Makmur', sector: 'Konsumer', price: 6550, pe: 7.2, pb: 1.1, mcap: 57e12 },
    'ANTM': { name: 'Aneka Tambang', sector: 'Energi', price: 1385, pe: 8.9, pb: 1.3, mcap: 33e12 },
    'PGAS': { name: 'Perusahaan Gas Negara', sector: 'Infrastruktur', price: 1520, pe: 6.5, pb: 1.8, mcap: 37e12 },
    'SMGR': { name: 'Semen Indonesia', sector: 'Infrastruktur', price: 3920, pe: 15.7, pb: 1.2, mcap: 46e12 },
    'PTBA': { name: 'Bukit Asam', sector: 'Energi', price: 2680, pe: 5.4, pb: 1.5, mcap: 31e12 },
    'ADRO': { name: 'Adaro Energy', sector: 'Energi', price: 2950, pe: 4.8, pb: 1.1, mcap: 94e12 },
    'EXCL': { name: 'XL Axiata', sector: 'Telekomunikasi', price: 2240, pe: 28.3, pb: 1.4, mcap: 30e12 },
    'ISAT': { name: 'Indosat Ooredoo', sector: 'Telekomunikasi', price: 7450, pe: 15.1, pb: 2.2, mcap: 40e12 },
    'CPIN': { name: 'Charoen Pokphand', sector: 'Konsumer', price: 4950, pe: 18.6, pb: 4.2, mcap: 81e12 },
    'MAPI': { name: 'Mitra Adiperkasa', sector: 'Konsumer', price: 1725, pe: 14.2, pb: 3.0, mcap: 29e12 },
    'ERAA': { name: 'Erajaya Swasembada', sector: 'Teknologi', price: 378, pe: 7.1, pb: 1.0, mcap: 10e12 },
    'AMRT': { name: 'Sumber Alfaria', sector: 'Konsumer', price: 2870, pe: 38.5, pb: 12.3, mcap: 117e12 },
    'SIDO': { name: 'Industri Jamu Sido', sector: 'Kesehatan', price: 710, pe: 20.8, pb: 7.2, mcap: 21e12 },
    'UNTR': { name: 'United Tractors', sector: 'Industri', price: 26350, pe: 5.9, pb: 1.4, mcap: 98e12 },
    'ITMG': { name: 'Indo Tambangraya', sector: 'Energi', price: 26800, pe: 4.2, pb: 2.1, mcap: 30e12 },
    'MEDC': { name: 'Medco Energi', sector: 'Energi', price: 1215, pe: 6.8, pb: 0.9, mcap: 30e12 },
    'BRPT': { name: 'Barito Pacific', sector: 'Industri', price: 875, pe: null, pb: 0.7, mcap: 46e12 },
    'INKP': { name: 'Indah Kiat Pulp', sector: 'Industri', price: 8375, pe: 5.5, pb: 0.6, mcap: 46e12 },
    'MDKA': { name: 'Merdeka Copper Gold', sector: 'Energi', price: 2380, pe: null, pb: 2.8, mcap: 56e12 },
};

function generateChange() { return (Math.random() * 6 - 3); }
function generateVolume() { return Math.round(Math.random() * 50000000 + 5000000); }

function getFallbackQuotes(symbols) {
    return symbols.map(sym => {
        const ticker = sym.replace('.JK', '').replace('^JKSE', 'IHSG').replace('^JKLQ45', 'LQ45').replace('^JKIDX30', 'IDX30').replace('^JKII', 'JII');
        const base = STOCK_DATA[ticker];
        if (!base) {
            // Index data
            const indexData = { 'IHSG': 7250, 'LQ45': 945, 'IDX30': 480, 'JII': 510 };
            const price = indexData[ticker] || 1000;
            const chg = generateChange();
            return { symbol: sym, shortName: ticker, longName: ticker, regularMarketPrice: price, regularMarketChange: round(price * chg / 100), regularMarketChangePercent: round(chg), regularMarketVolume: generateVolume(), marketCap: 0, trailingPE: null, priceToBook: null };
        }
        const chg = generateChange();
        const chgAbs = round(base.price * chg / 100);
        return {
            symbol: sym, shortName: base.name, longName: base.name,
            regularMarketPrice: base.price + Math.round(chgAbs),
            regularMarketChange: chgAbs,
            regularMarketChangePercent: round(chg),
            regularMarketVolume: generateVolume(),
            regularMarketPreviousClose: base.price,
            regularMarketOpen: base.price + Math.round(chgAbs * 0.5),
            regularMarketDayHigh: base.price + Math.round(Math.abs(chgAbs) * 1.5),
            regularMarketDayLow: base.price - Math.round(Math.abs(chgAbs) * 0.5),
            marketCap: base.mcap, trailingPE: base.pe, priceToBook: base.pb,
            sector: base.sector, industry: base.sector,
        };
    });
}

function generateHistoricalData(symbol, days) {
    const ticker = symbol.replace('.JK', '');
    const base = STOCK_DATA[ticker];
    const startPrice = base ? base.price * 0.85 : 5000;
    const candles = [];
    let price = startPrice;
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
        const volume = Math.round(Math.random() * 30000000 + 5000000);
        candles.push({ date: date.toISOString().split('T')[0], open, high, low, close, volume });
    }
    return candles;
}

// ============ DATA FETCHER WITH MULTI-SOURCE ============
// Priority: 1) Indonesian Proxy  2) Yahoo Direct  3) Fallback
let dataSource = 'proxy'; // 'proxy' | 'yahoo' | 'fallback'

async function getQuotes(symbols) {
    // Try Indonesian proxy first (most reliable from Indonesia)
    if (dataSource === 'proxy') {
        try {
            const results = [];
            // Proxy only supports single symbol, batch in parallel (max 6 concurrent)
            const batches = [];
            for (let i = 0; i < symbols.length; i += 6) batches.push(symbols.slice(i, i + 6));
            for (const batch of batches) {
                const batchResults = await Promise.all(batch.map(async (sym) => {
                    try {
                        const data = await proxyFetch(sym.replace('^JKSE', '%5EJKSE').replace('^JKLQ45', '%5EJKLQ45').replace('^JKIDX30', '%5EJKIDX30').replace('^JKII', '%5EJKII'), '1d', '1d');
                        const meta = data?.chart?.result?.[0]?.meta;
                        if (meta && meta.regularMarketPrice) {
                            const prev = meta.previousClose || meta.chartPreviousClose || meta.regularMarketPrice;
                            const change = meta.regularMarketPrice - prev;
                            const changePct = prev ? (change / prev) * 100 : 0;
                            const ticker = sym.replace('.JK', '').replace('^JKSE', 'IHSG').replace('^JKLQ45', 'LQ45').replace('^JKIDX30', 'IDX30').replace('^JKII', 'JII');
                            const stockInfo = STOCK_DATA[ticker] || {};
                            return {
                                symbol: sym, shortName: stockInfo.name || meta.shortName || ticker, longName: stockInfo.name || meta.longName || ticker,
                                regularMarketPrice: meta.regularMarketPrice,
                                regularMarketChange: round(change), regularMarketChangePercent: round(changePct),
                                regularMarketVolume: meta.regularMarketVolume || generateVolume(),
                                regularMarketPreviousClose: prev,
                                marketCap: stockInfo.mcap || 0, trailingPE: stockInfo.pe || null, priceToBook: stockInfo.pb || null,
                                sector: stockInfo.sector || '', industry: stockInfo.sector || '',
                            };
                        }
                    } catch (e) { /* skip failed symbol */ }
                    return null;
                }));
                results.push(...batchResults.filter(Boolean));
            }
            if (results.length > 0) {
                console.log(`[Proxy] Got ${results.length}/${symbols.length} quotes`);
                return results;
            }
            throw new Error('No data from proxy');
        } catch (e) {
            console.warn('[Proxy] Failed:', e.message, '- trying Yahoo...');
            dataSource = 'yahoo';
        }
    }

    // Try Yahoo Finance direct
    if (dataSource === 'yahoo') {
        try {
            const symbolStr = symbols.join(',');
            const data = await yahooFetch(`/v7/finance/quote?symbols=${symbolStr}`);
            if (data?.quoteResponse?.result?.length > 0) {
                console.log('[Yahoo] Got quotes OK');
                return data.quoteResponse.result;
            }
        } catch (e) {
            console.warn('[Yahoo] Failed:', e.message, '- using fallback');
            dataSource = 'fallback';
            setTimeout(() => { dataSource = 'proxy'; console.log('[Data] Will retry proxy on next request'); }, 300000);
        }
    }

    // Fallback
    return getFallbackQuotes(symbols);
}

async function getHistory(symbol, period1, period2, interval) {
    const days = Math.round((period2 - period1) / 86400);
    const range = days <= 5 ? '5d' : days <= 30 ? '1mo' : days <= 90 ? '3mo' : days <= 180 ? '6mo' : days <= 365 ? '1y' : '2y';

    // Try proxy first
    if (dataSource === 'proxy' || dataSource === 'yahoo') {
        try {
            const data = await proxyFetch(symbol, range, interval || '1d');
            const result = data?.chart?.result?.[0];
            if (result && result.timestamp && result.timestamp.length > 0) {
                const ts = result.timestamp; const ohlcv = result.indicators?.quote?.[0] || {};
                const candles = ts.map((t, i) => ({
                    date: new Date(t * 1000).toISOString().split('T')[0],
                    open: Math.round(ohlcv.open?.[i] || 0), high: Math.round(ohlcv.high?.[i] || 0),
                    low: Math.round(ohlcv.low?.[i] || 0), close: Math.round(ohlcv.close?.[i] || 0),
                    volume: ohlcv.volume?.[i] || 0,
                })).filter(c => c.close > 0);
                if (candles.length > 0) return candles;
            }
        } catch (e) { console.warn('[History] Proxy/Yahoo failed:', e.message); }

        // Try Yahoo direct for history
        try {
            const data = await yahooFetch(`/v8/finance/chart/${symbol}?period1=${period1}&period2=${period2}&interval=${interval || '1d'}`);
            const result = data?.chart?.result?.[0];
            if (result && result.timestamp) {
                const ts = result.timestamp; const ohlcv = result.indicators?.quote?.[0] || {};
                return ts.map((t, i) => ({
                    date: new Date(t * 1000).toISOString().split('T')[0],
                    open: Math.round(ohlcv.open?.[i] || 0), high: Math.round(ohlcv.high?.[i] || 0),
                    low: Math.round(ohlcv.low?.[i] || 0), close: Math.round(ohlcv.close?.[i] || 0),
                    volume: ohlcv.volume?.[i] || 0,
                })).filter(c => c.close > 0);
            }
        } catch (e) { /* fall through to fallback */ }
    }

    return generateHistoricalData(symbol, days);
}


// ============ TECHNICAL INDICATORS ============
function calcSMA(data, period) {
    if (!data || data.length === 0) return [];
    const r = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) { r.push(null); continue; }
        r.push(data.slice(i - period + 1, i + 1).reduce((s, v) => s + v, 0) / period);
    }
    return r;
}
function calcRSI(closes, period = 14) {
    if (!closes || closes.length < period + 1) return new Array(closes?.length || 0).fill(null);
    const r = new Array(closes.length).fill(null);
    let gainSum = 0, lossSum = 0;
    for (let i = 1; i <= period; i++) { const d = closes[i] - closes[i-1]; if (d > 0) gainSum += d; else lossSum -= d; }
    let avgG = gainSum / period, avgL = lossSum / period;
    r[period] = avgL === 0 ? 100 : 100 - (100 / (1 + avgG / avgL));
    for (let i = period + 1; i < closes.length; i++) {
        const d = closes[i] - closes[i-1];
        avgG = (avgG * (period-1) + (d > 0 ? d : 0)) / period;
        avgL = (avgL * (period-1) + (d < 0 ? -d : 0)) / period;
        r[i] = avgL === 0 ? 100 : 100 - (100 / (1 + avgG / avgL));
    }
    return r;
}
function calcEMA(data, period) {
    if (!data || data.length === 0) return [];
    const r = [data[0]], k = 2 / (period + 1);
    for (let i = 1; i < data.length; i++) r.push(data[i] * k + r[i-1] * (1-k));
    return r;
}
function calcMACD(closes) {
    const e12 = calcEMA(closes, 12), e26 = calcEMA(closes, 26);
    const macd = e12.map((v, i) => v - e26[i]);
    const signal = calcEMA(macd, 9);
    return { macd, signal, histogram: macd.map((v, i) => v - signal[i]) };
}
function periodToTimestamps(period) {
    const now = Math.floor(Date.now() / 1000);
    const p = { '1d':86400,'5d':432000,'1mo':2592000,'3mo':7776000,'6mo':15552000,'1y':31536000,'2y':63072000,'5y':157680000 };
    return { period1: now - (p[period] || p['3mo']), period2: now };
}
function round(n) { return n != null ? Math.round(n * 100) / 100 : 0; }

// ============ STOCKS CONFIG ============
const TOP_STOCKS = ['BBCA.JK','BBRI.JK','BMRI.JK','TLKM.JK','ASII.JK','UNVR.JK','BBNI.JK','GOTO.JK','BRIS.JK','ICBP.JK','KLBF.JK','INDF.JK','ANTM.JK','PGAS.JK','SMGR.JK','PTBA.JK','ADRO.JK','EXCL.JK','ISAT.JK','CPIN.JK','MAPI.JK','ERAA.JK','AMRT.JK','SIDO.JK','UNTR.JK','ITMG.JK','MEDC.JK','BRPT.JK','INKP.JK','MDKA.JK'];
const INDICES = { 'IHSG': '^JKSE', 'LQ45': '^JKLQ45', 'IDX30': '^JKIDX30', 'JII': '^JKII' };
const SECTORS = {
    'Keuangan': ['BBCA.JK','BBRI.JK','BMRI.JK','BBNI.JK','BRIS.JK'],
    'Teknologi': ['GOTO.JK'],
    'Konsumer': ['UNVR.JK','ICBP.JK','INDF.JK','CPIN.JK','AMRT.JK'],
    'Telekomunikasi': ['TLKM.JK','EXCL.JK','ISAT.JK'],
    'Energi': ['ADRO.JK','PTBA.JK','ANTM.JK','MDKA.JK','MEDC.JK','ITMG.JK'],
    'Infrastruktur': ['PGAS.JK','SMGR.JK'],
};

// ============ API ROUTES ============
const routes = {};
routes['/api/health'] = async () => ({ status: 'ok', source: dataSource, note: dataSource === 'proxy' ? 'Real-time via Indonesian proxy' : dataSource === 'yahoo' ? 'Real-time via Yahoo Finance' : 'Simulated fallback data' });

routes['/api/market/indices'] = async () => {
    const quotes = await getQuotes(Object.values(INDICES));
    const indices = Object.entries(INDICES).map(([name, sym]) => {
        const q = quotes.find(r => r.symbol === sym) || {};
        return { name, symbol: sym, price: q.regularMarketPrice || 0, change: round(q.regularMarketChange || 0), change_pct: round(q.regularMarketChangePercent || 0) };
    });
    return { indices };
};

routes['/api/market/top-movers'] = async (params) => {
    const limit = parseInt(params.limit) || 10;
    const quotes = await getQuotes(TOP_STOCKS);
    const stocks = quotes.map(q => ({ symbol: q.symbol.replace('.JK',''), price: Math.round(q.regularMarketPrice||0), change: round(q.regularMarketChange||0), change_pct: round(q.regularMarketChangePercent||0), volume: q.regularMarketVolume||0, market_cap: q.marketCap||0 })).filter(s => s.price > 0);
    return { gainers: [...stocks].sort((a,b)=>b.change_pct-a.change_pct).slice(0,limit), losers: [...stocks].sort((a,b)=>a.change_pct-b.change_pct).slice(0,limit) };
};

routes['/api/market/sectors'] = async () => {
    const allSyms = [...new Set(Object.values(SECTORS).flat())];
    const quotes = await getQuotes(allSyms);
    const sectors = Object.entries(SECTORS).map(([name, syms]) => {
        const sq = syms.map(s => quotes.find(q => q.symbol === s)).filter(Boolean);
        const chgs = sq.map(q => q.regularMarketChangePercent || 0);
        const avg = chgs.length ? chgs.reduce((s,v)=>s+v,0)/chgs.length : 0;
        return { sector: name, change_pct: round(avg), stocks: sq.map(q => ({ symbol: q.symbol.replace('.JK',''), change_pct: round(q.regularMarketChangePercent||0) })).sort((a,b)=>b.change_pct-a.change_pct) };
    }).sort((a,b)=>b.change_pct-a.change_pct);
    return { sectors };
};

routes['/api/market/summary'] = async () => {
    const quotes = await getQuotes(TOP_STOCKS);
    let adv=0, dec=0, unc=0, vol=0;
    quotes.forEach(q => { const c=q.regularMarketChange||0; if(c>0)adv++;else if(c<0)dec++;else unc++; vol+=q.regularMarketVolume||0; });
    return { advancing:adv, declining:dec, unchanged:unc, total_volume:vol, sentiment_score: Math.round(adv/Math.max(adv+dec,1)*100) };
};

routes['/api/screener/scan'] = async (params) => {
    const limit = parseInt(params.limit)||20;
    const quotes = await getQuotes(TOP_STOCKS);
    const results = [];
    for (const q of quotes) {
        if (!q.regularMarketPrice) continue;
        const pe=q.trailingPE||null, pb=q.priceToBook||null, chg=round(q.regularMarketChangePercent||0);
        if (params.max_pe && pe && pe > parseFloat(params.max_pe)) continue;
        results.push({ symbol:q.symbol.replace('.JK',''), price:Math.round(q.regularMarketPrice), change_pct:chg, pe:pe?round(pe):null, pb:pb?round(pb):null, roe:null, div_yield:null, rsi:50, volume:q.regularMarketVolume||0, volume_ratio:1.0, market_cap:q.marketCap||0, signal:chg>1?'buy':chg<-1?'sell':'neutral' });
    }
    results.sort((a,b)=>b.change_pct-a.change_pct);
    return { count: results.length, stocks: results.slice(0,limit) };
};


// ============ DYNAMIC ROUTES ============
async function handleStockRoute(symbol, action, params) {
    const ticker = `${symbol.toUpperCase()}.JK`;
    if (action === 'quote') {
        const quotes = await getQuotes([ticker]);
        const q = quotes[0]; if (!q) throw new Error('Stock not found');
        return { symbol: symbol.toUpperCase(), name: q.longName||q.shortName||symbol, price: q.regularMarketPrice, previous_close: q.regularMarketPreviousClose, open: q.regularMarketOpen, day_high: q.regularMarketDayHigh, day_low: q.regularMarketDayLow, volume: q.regularMarketVolume, market_cap: q.marketCap, change: round(q.regularMarketChange||0), change_pct: round(q.regularMarketChangePercent||0) };
    }
    if (action === 'history') {
        const { period1, period2 } = periodToTimestamps(params.period || '3mo');
        return { symbol: symbol.toUpperCase(), period: params.period||'3mo', data: await getHistory(ticker, period1, period2, params.interval||'1d') };
    }
    throw new Error('Unknown action');
}

async function handleTechnicalRoute(symbol, action, params) {
    const ticker = `${symbol.toUpperCase()}.JK`;
    const { period1, period2 } = periodToTimestamps(params.period || '6mo');
    const candles = await getHistory(ticker, period1, period2, '1d');
    if (candles.length < 30) throw new Error('Insufficient data');

    const closes = candles.map(c=>c.close), highs = candles.map(c=>c.high), lows = candles.map(c=>c.low), volumes = candles.map(c=>c.volume);
    const ma20 = calcSMA(closes,20), ma50 = calcSMA(closes,50), ma200 = calcSMA(closes,200);
    const rsi = calcRSI(closes,14);
    const { macd, signal: macdSig, histogram } = calcMACD(closes);
    const volAvg = calcSMA(volumes, 20);
    const last = closes.length - 1;
    const currentPrice = closes[last];
    const currentRSI = rsi[last] != null ? round(rsi[last]) : 50;
    const currentMACD = round(macd[last]), currentMACDSig = round(macdSig[last]);
    const cMA20 = ma20[last]?Math.round(ma20[last]):null, cMA50 = ma50[last]?Math.round(ma50[last]):null, cMA200 = ma200[last]?Math.round(ma200[last]):null;
    const volRatio = volAvg[last] > 0 ? round(volumes[last] / volAvg[last]) : 1;

    let bbStd = 0;
    if (last >= 19) { const sl = closes.slice(last-19,last+1); const mn = sl.reduce((s,v)=>s+v,0)/20; bbStd = Math.sqrt(sl.reduce((s,v)=>s+(v-mn)**2,0)/20); }
    const bbUpper = cMA20 ? Math.round(cMA20 + 2*bbStd) : null;
    const bbLower = cMA20 ? Math.round(cMA20 - 2*bbStd) : null;

    const resistances = [...new Set(highs.slice(-20))].filter(h=>h>currentPrice).sort((a,b)=>a-b).slice(0,3);
    const supports = [...new Set(lows.slice(-20))].filter(l=>l<currentPrice).sort((a,b)=>b-a).slice(0,3);

    const signals = [];
    if (currentRSI < 30) signals.push({indicator:'RSI',signal:'oversold',type:'buy'}); else if (currentRSI > 70) signals.push({indicator:'RSI',signal:'overbought',type:'sell'}); else signals.push({indicator:'RSI',signal:'netral',type:currentRSI<50?'buy':'sell'});
    if (currentMACD > currentMACDSig) signals.push({indicator:'MACD',signal:'bullish crossover',type:'buy'}); else signals.push({indicator:'MACD',signal:'bearish crossover',type:'sell'});
    if (currentPrice > cMA20) signals.push({indicator:'MA20',signal:'harga di atas MA20',type:'buy'}); else signals.push({indicator:'MA20',signal:'harga di bawah MA20',type:'sell'});
    if (cMA20 && cMA50 && cMA20 > cMA50) signals.push({indicator:'Golden Cross',signal:'MA20 > MA50',type:'buy'});

    const buyCount = signals.filter(s=>s.type==='buy').length;
    const score = round((buyCount/signals.length)*10);
    const rec = score>=8?'Strong Buy':score>=6?'Buy':score>=4?'Neutral':score>=2?'Sell':'Strong Sell';

    if (action === 'indicators') {
        return { symbol: symbol.toUpperCase(), price: currentPrice, indicators: { ma20:cMA20, ma50:cMA50, ma200:cMA200, rsi:currentRSI, macd:currentMACD, macd_signal:currentMACDSig, macd_histogram:round(histogram[last]), bb_upper:bbUpper, bb_middle:cMA20, bb_lower:bbLower, stochastic_k:null, stochastic_d:null, volume:volumes[last], volume_avg_20:volAvg[last]?Math.round(volAvg[last]):0, volume_ratio:volRatio }, support_resistance:{supports,resistances}, signals, score, recommendation:rec };
    }
    if (action === 'chart-data') {
        return { symbol: symbol.toUpperCase(), data: candles.map((c,i) => ({...c, ma20:ma20[i]?Math.round(ma20[i]):null, ma50:ma50[i]?Math.round(ma50[i]):null, rsi:rsi[i]!=null?round(rsi[i]):null, macd:round(macd[i]), macd_signal:round(macdSig[i]), macd_hist:round(histogram[i])})) };
    }
    throw new Error('Unknown action');
}

async function handleFundamentalRoute(symbol) {
    const ticker = `${symbol.toUpperCase()}.JK`;
    const quotes = await getQuotes([ticker]);
    const q = quotes[0]; if (!q) throw new Error('Stock not found');
    return { symbol: symbol.toUpperCase(), name: q.longName||q.shortName||symbol, sector: q.sector||'', industry: q.industry||'', market_cap: q.marketCap||0, ratios: { pe_ratio:q.trailingPE?round(q.trailingPE):null, pb_ratio:q.priceToBook?round(q.priceToBook):null, roe:null,roa:null,debt_to_equity:null,current_ratio:null,dividend_yield:null,payout_ratio:null }, growth:{revenue_growth:null,earnings_growth:null}, margins:{profit_margin:null,operating_margin:null,gross_margin:null}, valuation:{enterprise_value:0,ev_to_revenue:0,ev_to_ebitda:0,peg_ratio:0} };
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

    // Static files with path traversal protection
    let filePath = pathname === '/' ? '/index.html' : pathname;
    filePath = path.join(__dirname, filePath);
    const resolvedPath = path.resolve(filePath);
    if (!resolvedPath.startsWith(__dirname)) { res.writeHead(403); res.end('Forbidden'); return; }
    try {
        const content = fs.readFileSync(resolvedPath);
        res.setHeader('Content-Type', MIME[path.extname(resolvedPath)] || 'application/octet-stream');
        res.writeHead(200); res.end(content);
    } catch { res.writeHead(404); res.end('Not found'); }
});

server.listen(PORT, () => {
    console.log(`\n  ╔══════════════════════════════════════════╗`);
    console.log(`  ║   SahamID - Analisa Saham Indonesia      ║`);
    console.log(`  ╠══════════════════════════════════════════╣`);
    console.log(`  ║  Server: http://localhost:${PORT}           ║`);
    console.log(`  ║  Mode:   Yahoo Finance + Auto Fallback   ║`);
    console.log(`  ║  Info:   Jika Yahoo gagal, data simulasi  ║`);
    console.log(`  ║          realistis akan ditampilkan       ║`);
    console.log(`  ╚══════════════════════════════════════════╝\n`);
});
