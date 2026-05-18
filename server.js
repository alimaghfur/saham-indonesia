/**
 * SahamID Backend Server
 * Pure Node.js server (no external dependencies) that proxies Yahoo Finance API
 * and serves the frontend.
 */

const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = process.env.PORT || 8000;

// MIME types
const MIME = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
    '.svg': 'image/svg+xml',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
    '.ttf': 'font/ttf',
    '.map': 'application/json',
};

// Yahoo Finance API helper with cookie/crumb authentication
let yfCookie = '';
let yfCrumb = '';
let yfAuthTime = 0;
let yfAuthFailed = false;

function httpsRequest(urlStr, options = {}) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(urlStr);
        const reqOpts = {
            hostname: parsed.hostname,
            port: parsed.port || 443,
            path: parsed.pathname + parsed.search,
            method: options.method || 'GET',
            headers: {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                ...(options.headers || {}),
            },
        };
        const req = https.request(reqOpts, (res) => {
            // Follow redirects
            if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                const redirectUrl = res.headers.location.startsWith('http')
                    ? res.headers.location
                    : `https://${parsed.hostname}${res.headers.location}`;
                resolve(httpsRequest(redirectUrl, { ...options, headers: { ...reqOpts.headers, ...options.headers } }));
                return;
            }
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve({ statusCode: res.statusCode, headers: res.headers, body: data }));
        });
        req.on('error', reject);
        req.setTimeout(15000, () => { req.destroy(); reject(new Error('Timeout')); });
        req.end();
    });
}

async function refreshYahooAuth() {
    if (yfCookie && yfCrumb && (Date.now() - yfAuthTime) < 1800000) return true;
    
    console.log('Refreshing Yahoo Finance authentication...');
    
    try {
        // Method 1: Get consent cookie first, then crumb
        // Visit fc.yahoo.com to get initial cookie
        const initRes = await httpsRequest('https://fc.yahoo.com');
        let cookies = '';
        const setCookies = initRes.headers['set-cookie'] || [];
        if (setCookies.length > 0) {
            cookies = setCookies.map(c => c.split(';')[0]).join('; ');
        }
        
        // If no cookies from fc.yahoo.com, try direct approach
        if (!cookies) {
            const directRes = await httpsRequest('https://finance.yahoo.com', {
                headers: { 'Accept': 'text/html' }
            });
            const directCookies = directRes.headers['set-cookie'] || [];
            cookies = directCookies.map(c => c.split(';')[0]).join('; ');
        }
        
        if (!cookies) {
            console.warn('No cookies received from Yahoo');
            yfAuthFailed = true;
            return false;
        }
        
        // Get crumb with cookie
        const crumbRes = await httpsRequest('https://query2.finance.yahoo.com/v1/test/getcrumb', {
            headers: {
                'Cookie': cookies,
                'Accept': 'text/plain',
            }
        });
        
        if (crumbRes.statusCode === 200 && crumbRes.body && !crumbRes.body.includes('<') && crumbRes.body.length < 50) {
            yfCookie = cookies;
            yfCrumb = crumbRes.body.trim();
            yfAuthTime = Date.now();
            yfAuthFailed = false;
            console.log('Yahoo Finance auth OK (crumb obtained)');
            return true;
        }
        
        // Method 2: Try with A3 consent cookie
        const consentCookie = 'A1=d=AQABBKV1YmcCEPKm_xKP&S=AQAAAkMx; A3=d=AQABBKV1YmcCEPKm_xKP&S=AQAAAkMx; GUC=AQEBAgJlda1';
        const crumbRes2 = await httpsRequest('https://query2.finance.yahoo.com/v1/test/getcrumb', {
            headers: {
                'Cookie': consentCookie,
                'Accept': 'text/plain',
            }
        });
        
        if (crumbRes2.statusCode === 200 && crumbRes2.body && !crumbRes2.body.includes('<') && crumbRes2.body.length < 50) {
            yfCookie = consentCookie;
            yfCrumb = crumbRes2.body.trim();
            yfAuthTime = Date.now();
            yfAuthFailed = false;
            console.log('Yahoo Finance auth OK (method 2)');
            return true;
        }
        
        console.warn('Could not obtain crumb. Status:', crumbRes.statusCode, 'Body:', crumbRes.body.substring(0, 100));
        yfAuthFailed = true;
        return false;
    } catch (e) {
        console.warn('Yahoo auth failed:', e.message);
        yfAuthFailed = true;
        return false;
    }
}

async function yahooFetch(endpoint) {
    const authOk = await refreshYahooAuth();
    
    let url;
    const headers = { 'Accept': 'application/json' };
    
    if (authOk && yfCrumb) {
        const separator = endpoint.includes('?') ? '&' : '?';
        url = `https://query1.finance.yahoo.com${endpoint}${separator}crumb=${encodeURIComponent(yfCrumb)}`;
        headers['Cookie'] = yfCookie;
    } else {
        // Try without auth (v8 chart sometimes works without)
        url = `https://query1.finance.yahoo.com${endpoint}`;
    }
    
    const res = await httpsRequest(url, { headers });
    
    if (res.statusCode === 401 || res.statusCode === 403) {
        // Force re-auth and retry
        yfAuthTime = 0;
        yfCookie = '';
        yfCrumb = '';
        const retryAuth = await refreshYahooAuth();
        
        if (retryAuth && yfCrumb) {
            const separator = endpoint.includes('?') ? '&' : '?';
            const retryUrl = `https://query1.finance.yahoo.com${endpoint}${separator}crumb=${encodeURIComponent(yfCrumb)}`;
            const retryRes = await httpsRequest(retryUrl, { headers: { 'Accept': 'application/json', 'Cookie': yfCookie } });
            try {
                return JSON.parse(retryRes.body);
            } catch (e) {
                throw new Error(`Yahoo API error (retry): status ${retryRes.statusCode}`);
            }
        }
        throw new Error(`Yahoo API unauthorized - could not authenticate`);
    }
    
    try {
        return JSON.parse(res.body);
    } catch (e) {
        throw new Error(`Yahoo API parse error (status ${res.statusCode}): ${res.body.substring(0, 150)}`);
    }
}

// Get quote data for multiple symbols
async function getQuotes(symbols) {
    const symbolStr = symbols.join(',');
    const data = await yahooFetch(`/v7/finance/quote?symbols=${symbolStr}&fields=regularMarketPrice,regularMarketChange,regularMarketChangePercent,regularMarketVolume,regularMarketPreviousClose,regularMarketOpen,regularMarketDayHigh,regularMarketDayLow,marketCap,trailingPE,priceToBook,shortName,longName`);
    return data?.quoteResponse?.result || [];
}

// Get historical data
async function getHistory(symbol, period1, period2, interval) {
    const data = await yahooFetch(`/v8/finance/chart/${symbol}?period1=${period1}&period2=${period2}&interval=${interval}`);
    const result = data?.chart?.result?.[0];
    if (!result) return [];
    const timestamps = result.timestamp || [];
    const ohlcv = result.indicators?.quote?.[0] || {};
    return timestamps.map((t, i) => ({
        date: new Date(t * 1000).toISOString().split('T')[0],
        open: Math.round(ohlcv.open?.[i] || 0),
        high: Math.round(ohlcv.high?.[i] || 0),
        low: Math.round(ohlcv.low?.[i] || 0),
        close: Math.round(ohlcv.close?.[i] || 0),
        volume: ohlcv.volume?.[i] || 0,
    })).filter(c => c.close > 0);
}

// Calculate technical indicators
function calcSMA(data, period) {
    if (!data || data.length === 0) return [];
    const result = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) { result.push(null); continue; }
        const slice = data.slice(i - period + 1, i + 1);
        result.push(slice.reduce((s, v) => s + v, 0) / period);
    }
    return result;
}

function calcRSI(closes, period = 14) {
    if (!closes || closes.length === 0) return [];
    const result = new Array(closes.length).fill(null);
    if (closes.length < period + 1) return result;
    let gainSum = 0, lossSum = 0;
    for (let i = 1; i <= period; i++) {
        const diff = closes[i] - closes[i - 1];
        if (diff > 0) gainSum += diff; else lossSum -= diff;
    }
    let avgGain = gainSum / period;
    let avgLoss = lossSum / period;
    result[period] = avgLoss === 0 ? 100 : 100 - (100 / (1 + avgGain / avgLoss));
    for (let i = period + 1; i < closes.length; i++) {
        const diff = closes[i] - closes[i - 1];
        avgGain = (avgGain * (period - 1) + (diff > 0 ? diff : 0)) / period;
        avgLoss = (avgLoss * (period - 1) + (diff < 0 ? -diff : 0)) / period;
        result[i] = avgLoss === 0 ? 100 : 100 - (100 / (1 + avgGain / avgLoss));
    }
    return result;
}

function calcEMA(data, period) {
    if (!data || data.length === 0) return [];
    const result = [];
    const k = 2 / (period + 1);
    let ema = data[0];
    result.push(ema);
    for (let i = 1; i < data.length; i++) {
        ema = data[i] * k + ema * (1 - k);
        result.push(ema);
    }
    return result;
}

function calcMACD(closes) {
    const ema12 = calcEMA(closes, 12);
    const ema26 = calcEMA(closes, 26);
    const macd = ema12.map((v, i) => v - ema26[i]);
    const signal = calcEMA(macd, 9);
    const histogram = macd.map((v, i) => v - signal[i]);
    return { macd, signal, histogram };
}

// Period string to unix timestamps
function periodToTimestamps(period) {
    const now = Math.floor(Date.now() / 1000);
    const periods = { '1d': 86400, '5d': 432000, '1mo': 2592000, '3mo': 7776000, '6mo': 15552000, '1y': 31536000, '2y': 63072000, '5y': 157680000 };
    const seconds = periods[period] || periods['3mo'];
    return { period1: now - seconds, period2: now };
}

// Indonesian stocks
const TOP_STOCKS = ['BBCA.JK','BBRI.JK','BMRI.JK','TLKM.JK','ASII.JK','UNVR.JK','BBNI.JK','GOTO.JK','BRIS.JK','ICBP.JK','KLBF.JK','INDF.JK','ANTM.JK','PGAS.JK','SMGR.JK','PTBA.JK','ADRO.JK','EXCL.JK','ISAT.JK','CPIN.JK','MAPI.JK','ERAA.JK','AMRT.JK','SIDO.JK','UNTR.JK','ITMG.JK','MEDC.JK','BRPT.JK','INKP.JK','MDKA.JK'];

const INDICES = { 'IHSG': '^JKSE', 'LQ45': '^JKLQ45', 'IDX30': '^JKIDX30', 'JII': '^JKII' };

const SECTORS = {
    'Keuangan': ['BBCA.JK','BBRI.JK','BMRI.JK','BBNI.JK','BRIS.JK'],
    'Teknologi': ['GOTO.JK','EMTK.JK'],
    'Konsumer': ['UNVR.JK','ICBP.JK','INDF.JK'],
    'Telekomunikasi': ['TLKM.JK','EXCL.JK','ISAT.JK'],
    'Energi': ['ADRO.JK','PTBA.JK','ANTM.JK','MDKA.JK'],
    'Infrastruktur': ['PGAS.JK','SMGR.JK'],
};

// API Route handlers
const routes = {};

routes['/api/health'] = async () => ({ status: 'ok', source: 'Yahoo Finance', delay: '15 min' });

routes['/api/market/indices'] = async () => {
    const symbols = Object.values(INDICES);
    const quotes = await getQuotes(symbols);
    const indices = Object.entries(INDICES).map(([name, sym]) => {
        const q = quotes.find(r => r.symbol === sym) || {};
        return {
            name,
            symbol: sym,
            price: q.regularMarketPrice || 0,
            change: round(q.regularMarketChange || 0),
            change_pct: round(q.regularMarketChangePercent || 0),
        };
    });
    return { indices };
};

routes['/api/market/top-movers'] = async (params) => {
    const limit = parseInt(params.limit) || 10;
    const quotes = await getQuotes(TOP_STOCKS);
    const stocks = quotes.map(q => ({
        symbol: q.symbol.replace('.JK', ''),
        price: Math.round(q.regularMarketPrice || 0),
        change: round(q.regularMarketChange || 0),
        change_pct: round(q.regularMarketChangePercent || 0),
        volume: q.regularMarketVolume || 0,
        market_cap: q.marketCap || 0,
    })).filter(s => s.price > 0);
    const gainers = [...stocks].sort((a, b) => b.change_pct - a.change_pct).slice(0, limit);
    const losers = [...stocks].sort((a, b) => a.change_pct - b.change_pct).slice(0, limit);
    return { gainers, losers };
};

routes['/api/market/sectors'] = async () => {
    const allSymbols = [...new Set(Object.values(SECTORS).flat())];
    const quotes = await getQuotes(allSymbols);
    const sectors = Object.entries(SECTORS).map(([name, syms]) => {
        const sectorQuotes = syms.map(s => quotes.find(q => q.symbol === s)).filter(Boolean);
        const changes = sectorQuotes.map(q => q.regularMarketChangePercent || 0);
        const avg = changes.length ? changes.reduce((s, v) => s + v, 0) / changes.length : 0;
        return {
            sector: name,
            change_pct: round(avg),
            stocks: sectorQuotes.map(q => ({ symbol: q.symbol.replace('.JK', ''), change_pct: round(q.regularMarketChangePercent || 0) })).sort((a, b) => b.change_pct - a.change_pct),
        };
    }).sort((a, b) => b.change_pct - a.change_pct);
    return { sectors };
};

routes['/api/market/summary'] = async () => {
    const quotes = await getQuotes(TOP_STOCKS);
    let advancing = 0, declining = 0, unchanged = 0, totalVol = 0;
    quotes.forEach(q => {
        const chg = q.regularMarketChange || 0;
        if (chg > 0) advancing++; else if (chg < 0) declining++; else unchanged++;
        totalVol += q.regularMarketVolume || 0;
    });
    return { advancing, declining, unchanged, total_volume: totalVol, sentiment_score: Math.round(advancing / Math.max(advancing + declining, 1) * 100) };
};

routes['/api/screener/scan'] = async (params) => {
    const limit = parseInt(params.limit) || 20;
    const quotes = await getQuotes(TOP_STOCKS);

    // Get RSI for each (simplified - use recent price data)
    const results = [];
    for (const q of quotes) {
        if (!q.regularMarketPrice) continue;
        const pe = q.trailingPE || null;
        const pb = q.priceToBook || null;
        const chgPct = round(q.regularMarketChangePercent || 0);

        // Apply filters
        if (params.max_pe && pe && pe > parseFloat(params.max_pe)) continue;
        if (params.min_roe && (!q.returnOnEquity || q.returnOnEquity * 100 < parseFloat(params.min_roe))) continue;

        results.push({
            symbol: q.symbol.replace('.JK', ''),
            price: Math.round(q.regularMarketPrice),
            change_pct: chgPct,
            pe: pe ? round(pe) : null,
            pb: pb ? round(pb) : null,
            roe: null, // Would need separate info call
            div_yield: null,
            rsi: 50, // Placeholder - real RSI needs historical data
            volume: q.regularMarketVolume || 0,
            volume_ratio: 1.0,
            market_cap: q.marketCap || 0,
            signal: chgPct > 1 ? 'buy' : chgPct < -1 ? 'sell' : 'neutral',
        });
    }

    results.sort((a, b) => b.change_pct - a.change_pct);
    return { count: results.length, stocks: results.slice(0, limit) };
};

// Dynamic routes with path params
async function handleStockRoute(symbol, action, params) {
    const ticker = `${symbol.toUpperCase()}.JK`;

    if (action === 'quote') {
        const quotes = await getQuotes([ticker]);
        const q = quotes[0];
        if (!q) throw new Error('Stock not found');
        return {
            symbol: symbol.toUpperCase(),
            name: q.longName || q.shortName || symbol,
            price: q.regularMarketPrice,
            previous_close: q.regularMarketPreviousClose,
            open: q.regularMarketOpen,
            day_high: q.regularMarketDayHigh,
            day_low: q.regularMarketDayLow,
            volume: q.regularMarketVolume,
            market_cap: q.marketCap,
            change: round(q.regularMarketChange || 0),
            change_pct: round(q.regularMarketChangePercent || 0),
        };
    }

    if (action === 'history') {
        const period = params.period || '3mo';
        const interval = params.interval || '1d';
        const { period1, period2 } = periodToTimestamps(period);
        const data = await getHistory(ticker, period1, period2, interval);
        return { symbol: symbol.toUpperCase(), period, data };
    }

    throw new Error('Unknown action');
}

async function handleTechnicalRoute(symbol, action, params) {
    const ticker = `${symbol.toUpperCase()}.JK`;
    const period = params.period || '6mo';
    const { period1, period2 } = periodToTimestamps(period);
    const candles = await getHistory(ticker, period1, period2, '1d');

    if (candles.length < 30) throw new Error('Insufficient data');

    const closes = candles.map(c => c.close);
    const highs = candles.map(c => c.high);
    const lows = candles.map(c => c.low);
    const volumes = candles.map(c => c.volume);

    const ma20 = calcSMA(closes, 20);
    const ma50 = calcSMA(closes, 50);
    const ma200 = calcSMA(closes, 200);
    const rsi = calcRSI(closes, 14);
    const { macd, signal: macdSignal, histogram } = calcMACD(closes);
    const bb_mid = calcSMA(closes, 20);
    const volAvg = calcSMA(volumes.map(v => v), 20);

    const last = closes.length - 1;
    const currentPrice = closes[last];
    const currentRSI = rsi[last] != null ? round(rsi[last]) : 50;
    const currentMACD = round(macd[last]);
    const currentMACDSignal = round(macdSignal[last]);
    const currentMA20 = ma20[last] ? Math.round(ma20[last]) : null;
    const currentMA50 = ma50[last] ? Math.round(ma50[last]) : null;
    const currentMA200 = ma200[last] ? Math.round(ma200[last]) : null;
    const volRatio = volAvg[last] > 0 ? round(volumes[last] / volAvg[last]) : 1;

    // BB
    let bbStd = 0;
    if (last >= 19) {
        const slice = closes.slice(last - 19, last + 1);
        const mean = slice.reduce((s, v) => s + v, 0) / 20;
        bbStd = Math.sqrt(slice.reduce((s, v) => s + (v - mean) ** 2, 0) / 20);
    }
    const bbUpper = currentMA20 ? Math.round(currentMA20 + 2 * bbStd) : null;
    const bbLower = currentMA20 ? Math.round(currentMA20 - 2 * bbStd) : null;

    // Support & Resistance (simple pivot)
    const recentHighs = highs.slice(-20);
    const recentLows = lows.slice(-20);
    const resistances = [...new Set(recentHighs)].filter(h => h > currentPrice).sort((a, b) => a - b).slice(0, 3);
    const supports = [...new Set(recentLows)].filter(l => l < currentPrice).sort((a, b) => b - a).slice(0, 3);

    // Signals
    const signals = [];
    if (currentRSI < 30) signals.push({ indicator: 'RSI', signal: 'oversold', type: 'buy' });
    else if (currentRSI > 70) signals.push({ indicator: 'RSI', signal: 'overbought', type: 'sell' });
    else signals.push({ indicator: 'RSI', signal: 'netral', type: currentRSI < 50 ? 'buy' : 'sell' });

    if (currentMACD > currentMACDSignal) signals.push({ indicator: 'MACD', signal: 'bullish crossover', type: 'buy' });
    else signals.push({ indicator: 'MACD', signal: 'bearish crossover', type: 'sell' });

    if (currentPrice > currentMA20) signals.push({ indicator: 'MA20', signal: 'harga di atas MA20', type: 'buy' });
    else signals.push({ indicator: 'MA20', signal: 'harga di bawah MA20', type: 'sell' });

    if (currentMA20 && currentMA50 && currentMA20 > currentMA50) signals.push({ indicator: 'Golden Cross', signal: 'MA20 > MA50', type: 'buy' });

    const buyCount = signals.filter(s => s.type === 'buy').length;
    const score = round((buyCount / signals.length) * 10);
    const rec = score >= 8 ? 'Strong Buy' : score >= 6 ? 'Buy' : score >= 4 ? 'Neutral' : score >= 2 ? 'Sell' : 'Strong Sell';

    if (action === 'indicators') {
        return {
            symbol: symbol.toUpperCase(), price: currentPrice,
            indicators: { ma20: currentMA20, ma50: currentMA50, ma200: currentMA200, rsi: currentRSI, macd: currentMACD, macd_signal: currentMACDSignal, macd_histogram: round(histogram[last]), bb_upper: bbUpper, bb_middle: currentMA20, bb_lower: bbLower, stochastic_k: null, stochastic_d: null, volume: volumes[last], volume_avg_20: volAvg[last] ? Math.round(volAvg[last]) : 0, volume_ratio: volRatio },
            support_resistance: { supports, resistances },
            signals, score, recommendation: rec,
        };
    }

    if (action === 'chart-data') {
        const chartCandles = candles.map((c, i) => ({ ...c, ma20: ma20[i] ? Math.round(ma20[i]) : null, ma50: ma50[i] ? Math.round(ma50[i]) : null, rsi: rsi[i] != null ? round(rsi[i]) : null, macd: round(macd[i]), macd_signal: round(macdSignal[i]), macd_hist: round(histogram[i]) }));
        return { symbol: symbol.toUpperCase(), data: chartCandles };
    }

    throw new Error('Unknown action');
}

async function handleFundamentalRoute(symbol) {
    const ticker = `${symbol.toUpperCase()}.JK`;
    const quotes = await getQuotes([ticker]);
    const q = quotes[0];
    if (!q) throw new Error('Stock not found');
    return {
        symbol: symbol.toUpperCase(),
        name: q.longName || q.shortName || symbol,
        sector: q.sector || '',
        industry: q.industry || '',
        market_cap: q.marketCap || 0,
        ratios: {
            pe_ratio: q.trailingPE ? round(q.trailingPE) : null,
            pb_ratio: q.priceToBook ? round(q.priceToBook) : null,
            roe: null, roa: null, debt_to_equity: null, current_ratio: null, dividend_yield: null, payout_ratio: null,
        },
        growth: { revenue_growth: null, earnings_growth: null },
        margins: { profit_margin: null, operating_margin: null, gross_margin: null },
        valuation: { enterprise_value: 0, ev_to_revenue: 0, ev_to_ebitda: 0, peg_ratio: 0 },
    };
}

function round(n) { return n != null ? Math.round(n * 100) / 100 : 0; }

// HTTP Server
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

        // Handle preflight
        if (req.method === 'OPTIONS') {
            res.writeHead(204);
            res.end();
            return;
        }

        try {
            // Static routes
            if (routes[pathname]) {
                const result = await routes[pathname](params);
                res.writeHead(200);
                res.end(JSON.stringify(result));
                return;
            }

            // /api/stock/:symbol/:action
            const stockMatch = pathname.match(/^\/api\/stock\/([^/]+)\/([^/]+)$/);
            if (stockMatch) {
                const result = await handleStockRoute(stockMatch[1], stockMatch[2], params);
                res.writeHead(200);
                res.end(JSON.stringify(result));
                return;
            }

            // /api/technical/:symbol/:action
            const techMatch = pathname.match(/^\/api\/technical\/([^/]+)\/([^/]+)$/);
            if (techMatch) {
                const result = await handleTechnicalRoute(techMatch[1], techMatch[2], params);
                res.writeHead(200);
                res.end(JSON.stringify(result));
                return;
            }

            // /api/fundamental/:symbol
            const fundMatch = pathname.match(/^\/api\/fundamental\/([^/]+)$/);
            if (fundMatch) {
                const result = await handleFundamentalRoute(fundMatch[1]);
                res.writeHead(200);
                res.end(JSON.stringify(result));
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

    // Serve static files
    let filePath = pathname === '/' ? '/index.html' : pathname;
    filePath = path.join(__dirname, filePath);

    // Security: prevent path traversal attacks
    const resolvedPath = path.resolve(filePath);
    if (!resolvedPath.startsWith(__dirname)) {
        res.writeHead(403);
        res.end('Forbidden');
        return;
    }

    try {
        const content = fs.readFileSync(resolvedPath);
        const ext = path.extname(resolvedPath);
        res.setHeader('Content-Type', MIME[ext] || 'application/octet-stream');
        res.writeHead(200);
        res.end(content);
    } catch {
        res.writeHead(404);
        res.end('Not found');
    }
});

server.listen(PORT, () => {
    console.log(`\n  ╔══════════════════════════════════════╗`);
    console.log(`  ║   SahamID - Analisa Saham Indonesia  ║`);
    console.log(`  ╠══════════════════════════════════════╣`);
    console.log(`  ║  Server: http://localhost:${PORT}       ║`);
    console.log(`  ║  Data:   Yahoo Finance (real-time)   ║`);
    console.log(`  ╚══════════════════════════════════════╝\n`);
});
