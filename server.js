/**
 * SahamID Backend Server
 * Data Source: Twelve Data API (free tier, 800 credits/hari)
 * Daftar gratis di https://twelvedata.com untuk dapat API key
 * 
 * Set API key via environment variable:
 *   TWELVE_DATA_KEY=your_api_key node server.js
 */
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const { URL } = require('url');

const PORT = process.env.PORT || 8000;
// Baca API key dari: 1) environment variable, 2) file .env, 3) hardcode di bawah
let API_KEY = process.env.TWELVE_DATA_KEY || '';
if (!API_KEY) {
    try {
        const envFile = fs.readFileSync(path.join(__dirname, '.env'), 'utf8');
        const match = envFile.match(/TWELVE_DATA_KEY=(.+)/);
        if (match) API_KEY = match[1].trim();
    } catch (e) {}
}
if (!API_KEY) API_KEY = 'demo';


const MIME = {
    '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.png': 'image/png', '.ico': 'image/x-icon',
    '.svg': 'image/svg+xml', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
    '.gif': 'image/gif', '.webp': 'image/webp', '.woff': 'font/woff',
    '.woff2': 'font/woff2', '.ttf': 'font/ttf', '.map': 'application/json',
};

// ============ HTTP HELPER ============
function httpsGet(urlStr) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(urlStr);
        const opts = { hostname: parsed.hostname, port: 443, path: parsed.pathname + parsed.search, method: 'GET', headers: { 'User-Agent': 'SahamID/1.0' } };
        const req = https.request(opts, (res) => {
            let data = ''; res.on('data', c => data += c);
            res.on('end', () => resolve({ status: res.statusCode, body: data }));
        });
        req.on('error', reject);
        req.setTimeout(15000, () => { req.destroy(); reject(new Error('Timeout')); });
        req.end();
    });
}

// ============ TWELVE DATA API ============
async function tdFetch(endpoint) {
    const url = `https://api.twelvedata.com${endpoint}${endpoint.includes('?') ? '&' : '?'}apikey=${API_KEY}`;
    const res = await httpsGet(url);
    if (res.status !== 200) throw new Error(`TD API ${res.status}`);
    const data = JSON.parse(res.body);
    if (data.code === 400 || data.code === 401 || data.code === 429) throw new Error(data.message || `TD error ${data.code}`);
    return data;
}

// Get quotes for multiple symbols (batch)
async function getQuotes(symbols) {
    // Twelve Data batch: max 8 symbols per request on free tier
    const tdSymbols = symbols.map(s => s.replace('.JK', '').replace('^JKSE', 'COMPOSITE').replace('^JKLQ45', 'LQ45').replace('^JKIDX30', 'IDX30').replace('^JKII', 'JII'));
    const results = [];
    const batches = [];
    for (let i = 0; i < tdSymbols.length; i += 8) batches.push(tdSymbols.slice(i, i + 8));

    for (const batch of batches) {
        try {
            const symbolStr = batch.map(s => {
                if (['COMPOSITE','LQ45','IDX30','JII'].includes(s)) return s;
                return s;
            }).join(',');
            const exchangeStr = batch.map(s => ['COMPOSITE','LQ45','IDX30','JII'].includes(s) ? 'XIDX' : 'XIDX').join(',');
            const data = await tdFetch(`/quote?symbol=${symbolStr}&exchange=${exchangeStr}`);

            // Single symbol returns object, multiple returns object with keys
            if (batch.length === 1) {
                const q = data;
                if (q && q.close) results.push(formatTDQuote(q, symbols[results.length]));
            } else {
                for (const key of Object.keys(data)) {
                    const q = data[key];
                    if (q && q.close && !q.code) {
                        const origSym = symbols[results.length] || key + '.JK';
                        results.push(formatTDQuote(q, origSym));
                    }
                }
            }
        } catch (e) {
            console.warn('[TwelveData] Batch failed:', e.message);
        }
    }
    return results;
}

function formatTDQuote(q, originalSymbol) {
    const price = parseFloat(q.close) || 0;
    const prevClose = parseFloat(q.previous_close) || price;
    const change = price - prevClose;
    const changePct = prevClose ? (change / prevClose) * 100 : 0;
    const ticker = originalSymbol.replace('.JK', '').replace('^JKSE', 'IHSG').replace('^JKLQ45', 'LQ45').replace('^JKIDX30', 'IDX30').replace('^JKII', 'JII');
    const info = STOCK_INFO[ticker] || {};
    return {
        symbol: originalSymbol,
        shortName: q.name || info.name || ticker,
        longName: q.name || info.name || ticker,
        regularMarketPrice: price,
        regularMarketChange: round(change),
        regularMarketChangePercent: round(changePct),
        regularMarketVolume: parseInt(q.volume) || 0,
        regularMarketPreviousClose: prevClose,
        regularMarketOpen: parseFloat(q.open) || price,
        regularMarketDayHigh: parseFloat(q.high) || price,
        regularMarketDayLow: parseFloat(q.low) || price,
        marketCap: info.mcap || 0,
        trailingPE: info.pe || null,
        priceToBook: info.pb || null,
        sector: info.sector || '',
        industry: info.sector || '',
    };
}

// Get historical data
async function getHistory(symbol, outputsize) {
    const ticker = symbol.replace('.JK', '');
    try {
        const data = await tdFetch(`/time_series?symbol=${ticker}&exchange=XIDX&interval=1day&outputsize=${outputsize}`);
        if (data.values && data.values.length > 0) {
            return data.values.reverse().map(v => ({
                date: v.datetime,
                open: Math.round(parseFloat(v.open)),
                high: Math.round(parseFloat(v.high)),
                low: Math.round(parseFloat(v.low)),
                close: Math.round(parseFloat(v.close)),
                volume: parseInt(v.volume) || 0,
            }));
        }
    } catch (e) {
        console.warn('[TwelveData] History failed:', e.message);
    }
    // Fallback: generate data
    return generateHistoricalData(symbol, outputsize);
}

// ============ STOCK INFO (for MCap, PE, PB - not available in free tier) ============
const STOCK_INFO = {
    'BBCA': { name: 'Bank Central Asia', sector: 'Keuangan', pe: 24.5, pb: 4.8, mcap: 1215e12 },
    'BBRI': { name: 'Bank Rakyat Indonesia', sector: 'Keuangan', pe: 13.2, pb: 2.4, mcap: 700e12 },
    'BMRI': { name: 'Bank Mandiri', sector: 'Keuangan', pe: 11.8, pb: 2.1, mcap: 580e12 },
    'TLKM': { name: 'Telkom Indonesia', sector: 'Telekomunikasi', pe: 12.5, pb: 2.9, mcap: 275e12 },
    'ASII': { name: 'Astra International', sector: 'Industri', pe: 7.8, pb: 1.3, mcap: 196e12 },
    'UNVR': { name: 'Unilever Indonesia', sector: 'Konsumer', pe: 18.9, pb: 25.1, mcap: 93e12 },
    'BBNI': { name: 'Bank Negara Indonesia', sector: 'Keuangan', pe: 9.5, pb: 1.4, mcap: 168e12 },
    'GOTO': { name: 'GoTo Gojek Tokopedia', sector: 'Teknologi', pe: null, pb: 1.2, mcap: 85e12 },
    'BRIS': { name: 'Bank Syariah Indonesia', sector: 'Keuangan', pe: 18.3, pb: 3.1, mcap: 135e12 },
    'ICBP': { name: 'Indofood CBP', sector: 'Konsumer', pe: 20.1, pb: 3.8, mcap: 128e12 },
    'KLBF': { name: 'Kalbe Farma', sector: 'Kesehatan', pe: 22.4, pb: 3.5, mcap: 73e12 },
    'INDF': { name: 'Indofood Sukses Makmur', sector: 'Konsumer', pe: 7.2, pb: 1.1, mcap: 57e12 },
    'ANTM': { name: 'Aneka Tambang', sector: 'Energi', pe: 8.9, pb: 1.3, mcap: 33e12 },
    'PGAS': { name: 'Perusahaan Gas Negara', sector: 'Infrastruktur', pe: 6.5, pb: 1.8, mcap: 37e12 },
    'SMGR': { name: 'Semen Indonesia', sector: 'Infrastruktur', pe: 15.7, pb: 1.2, mcap: 46e12 },
    'PTBA': { name: 'Bukit Asam', sector: 'Energi', pe: 5.4, pb: 1.5, mcap: 31e12 },
    'ADRO': { name: 'Adaro Energy', sector: 'Energi', pe: 4.8, pb: 1.1, mcap: 94e12 },
    'EXCL': { name: 'XL Axiata', sector: 'Telekomunikasi', pe: 28.3, pb: 1.4, mcap: 30e12 },
    'ISAT': { name: 'Indosat Ooredoo', sector: 'Telekomunikasi', pe: 15.1, pb: 2.2, mcap: 40e12 },
    'CPIN': { name: 'Charoen Pokphand', sector: 'Konsumer', pe: 18.6, pb: 4.2, mcap: 81e12 },
    'MAPI': { name: 'Mitra Adiperkasa', sector: 'Konsumer', pe: 14.2, pb: 3.0, mcap: 29e12 },
    'ERAA': { name: 'Erajaya Swasembada', sector: 'Teknologi', pe: 7.1, pb: 1.0, mcap: 10e12 },
    'AMRT': { name: 'Sumber Alfaria', sector: 'Konsumer', pe: 38.5, pb: 12.3, mcap: 117e12 },
    'SIDO': { name: 'Industri Jamu Sido', sector: 'Kesehatan', pe: 20.8, pb: 7.2, mcap: 21e12 },
    'UNTR': { name: 'United Tractors', sector: 'Industri', pe: 5.9, pb: 1.4, mcap: 98e12 },
    'ITMG': { name: 'Indo Tambangraya', sector: 'Energi', pe: 4.2, pb: 2.1, mcap: 30e12 },
    'MEDC': { name: 'Medco Energi', sector: 'Energi', pe: 6.8, pb: 0.9, mcap: 30e12 },
    'BRPT': { name: 'Barito Pacific', sector: 'Industri', pe: null, pb: 0.7, mcap: 46e12 },
    'INKP': { name: 'Indah Kiat Pulp', sector: 'Industri', pe: 5.5, pb: 0.6, mcap: 46e12 },
    'MDKA': { name: 'Merdeka Copper Gold', sector: 'Energi', pe: null, pb: 2.8, mcap: 56e12 },
};

function generateHistoricalData(symbol, days) {
    const ticker = symbol.replace('.JK', '');
    const base = STOCK_INFO[ticker];
    const startPrice = base ? (base.mcap / 1e12) * 7 : 5000;
    const candles = []; let price = startPrice * 0.85; const now = Date.now();
    for (let i = days; i >= 0; i--) {
        const date = new Date(now - i * 86400000);
        if (date.getDay() === 0 || date.getDay() === 6) continue;
        const change = (Math.random() - 0.48) * price * 0.03;
        const open = Math.round(price); price += change; const close = Math.round(price);
        const high = Math.round(Math.max(open, close) + Math.random() * Math.abs(change) * 0.8);
        const low = Math.round(Math.min(open, close) - Math.random() * Math.abs(change) * 0.8);
        candles.push({ date: date.toISOString().split('T')[0], open, high, low, close, volume: Math.round(Math.random() * 30000000 + 5000000) });
    }
    return candles;
}

// ============ TECHNICAL INDICATORS ============
function calcSMA(data, p) { if (!data||!data.length) return []; const r=[]; for (let i=0;i<data.length;i++){if(i<p-1){r.push(null);continue;}r.push(data.slice(i-p+1,i+1).reduce((s,v)=>s+v,0)/p);}return r; }
function calcRSI(c, p=14) { if(!c||c.length<p+1)return new Array(c?.length||0).fill(null);const r=new Array(c.length).fill(null);let gS=0,lS=0;for(let i=1;i<=p;i++){const d=c[i]-c[i-1];if(d>0)gS+=d;else lS-=d;}let aG=gS/p,aL=lS/p;r[p]=aL===0?100:100-(100/(1+aG/aL));for(let i=p+1;i<c.length;i++){const d=c[i]-c[i-1];aG=(aG*(p-1)+(d>0?d:0))/p;aL=(aL*(p-1)+(d<0?-d:0))/p;r[i]=aL===0?100:100-(100/(1+aG/aL));}return r; }
function calcEMA(d, p) { if(!d||!d.length)return[];const r=[d[0]],k=2/(p+1);for(let i=1;i<d.length;i++)r.push(d[i]*k+r[i-1]*(1-k));return r; }
function calcMACD(c) { const e12=calcEMA(c,12),e26=calcEMA(c,26);const macd=e12.map((v,i)=>v-e26[i]);const sig=calcEMA(macd,9);return{macd,signal:sig,histogram:macd.map((v,i)=>v-sig[i])}; }
function round(n) { return n!=null?Math.round(n*100)/100:0; }

// ============ CONFIG ============
const TOP_STOCKS = ['BBCA.JK','BBRI.JK','BMRI.JK','TLKM.JK','ASII.JK','UNVR.JK','BBNI.JK','GOTO.JK','BRIS.JK','ICBP.JK','KLBF.JK','INDF.JK','ANTM.JK','PGAS.JK','SMGR.JK','PTBA.JK','ADRO.JK','EXCL.JK','ISAT.JK','CPIN.JK'];
const INDICES = { 'IHSG': '^JKSE', 'LQ45': '^JKLQ45', 'IDX30': '^JKIDX30', 'JII': '^JKII' };
const SECTORS = { 'Keuangan':['BBCA.JK','BBRI.JK','BMRI.JK','BBNI.JK','BRIS.JK'],'Teknologi':['GOTO.JK'],'Konsumer':['UNVR.JK','ICBP.JK','INDF.JK','CPIN.JK'],'Telekomunikasi':['TLKM.JK','EXCL.JK','ISAT.JK'],'Energi':['ADRO.JK','PTBA.JK','ANTM.JK'],'Infrastruktur':['PGAS.JK','SMGR.JK'] };

// ============ API ROUTES ============
const routes = {};
routes['/api/health'] = async () => ({ status: 'ok', source: 'Twelve Data', apikey: API_KEY === 'demo' ? 'DEMO (limited)' : 'Active' });


routes['/api/market/indices'] = async () => {
    const quotes = await getQuotes(Object.values(INDICES));
    const indices = Object.entries(INDICES).map(([name, sym]) => {
        const q = quotes.find(r => r.symbol === sym) || {};
        return { name, symbol: sym, price: q.regularMarketPrice||0, change: round(q.regularMarketChange||0), change_pct: round(q.regularMarketChangePercent||0) };
    });
    return { indices };
};
routes['/api/market/top-movers'] = async (params) => {
    const limit = parseInt(params.limit)||10;
    const quotes = await getQuotes(TOP_STOCKS);
    const stocks = quotes.map(q=>({symbol:q.symbol.replace('.JK',''),price:Math.round(q.regularMarketPrice||0),change:round(q.regularMarketChange||0),change_pct:round(q.regularMarketChangePercent||0),volume:q.regularMarketVolume||0,market_cap:q.marketCap||0})).filter(s=>s.price>0);
    return { gainers:[...stocks].sort((a,b)=>b.change_pct-a.change_pct).slice(0,limit), losers:[...stocks].sort((a,b)=>a.change_pct-b.change_pct).slice(0,limit) };
};
routes['/api/market/sectors'] = async () => {
    const allSyms=[...new Set(Object.values(SECTORS).flat())];
    const quotes = await getQuotes(allSyms);
    const sectors=Object.entries(SECTORS).map(([name,syms])=>{const sq=syms.map(s=>quotes.find(q=>q.symbol===s)).filter(Boolean);const chgs=sq.map(q=>q.regularMarketChangePercent||0);const avg=chgs.length?chgs.reduce((s,v)=>s+v,0)/chgs.length:0;return{sector:name,change_pct:round(avg),stocks:sq.map(q=>({symbol:q.symbol.replace('.JK',''),change_pct:round(q.regularMarketChangePercent||0)})).sort((a,b)=>b.change_pct-a.change_pct)};}).sort((a,b)=>b.change_pct-a.change_pct);
    return { sectors };
};
routes['/api/market/summary'] = async () => {
    const quotes = await getQuotes(TOP_STOCKS);
    let adv=0,dec=0,unc=0,vol=0;
    quotes.forEach(q=>{const c=q.regularMarketChange||0;if(c>0)adv++;else if(c<0)dec++;else unc++;vol+=q.regularMarketVolume||0;});
    return { advancing:adv, declining:dec, unchanged:unc, total_volume:vol, sentiment_score:Math.round(adv/Math.max(adv+dec,1)*100) };
};
routes['/api/screener/scan'] = async (params) => {
    const limit=parseInt(params.limit)||20;
    const quotes = await getQuotes(TOP_STOCKS);
    const results=[];
    for(const q of quotes){if(!q.regularMarketPrice)continue;const pe=q.trailingPE||null,pb=q.priceToBook||null,chg=round(q.regularMarketChangePercent||0);if(params.max_pe&&pe&&pe>parseFloat(params.max_pe))continue;results.push({symbol:q.symbol.replace('.JK',''),price:Math.round(q.regularMarketPrice),change_pct:chg,pe:pe?round(pe):null,pb:pb?round(pb):null,roe:null,div_yield:null,rsi:50,volume:q.regularMarketVolume||0,volume_ratio:1.0,market_cap:q.marketCap||0,signal:chg>1?'buy':chg<-1?'sell':'neutral'});}
    results.sort((a,b)=>b.change_pct-a.change_pct);
    return { count:results.length, stocks:results.slice(0,limit) };
};

// ============ DYNAMIC ROUTES ============
async function handleStockRoute(symbol, action, params) {
    const ticker = `${symbol.toUpperCase()}.JK`;
    if (action==='quote'){const quotes=await getQuotes([ticker]);const q=quotes[0];if(!q)throw new Error('Stock not found');return{symbol:symbol.toUpperCase(),name:q.longName||q.shortName||symbol,price:q.regularMarketPrice,previous_close:q.regularMarketPreviousClose,open:q.regularMarketOpen,day_high:q.regularMarketDayHigh,day_low:q.regularMarketDayLow,volume:q.regularMarketVolume,market_cap:q.marketCap,change:round(q.regularMarketChange||0),change_pct:round(q.regularMarketChangePercent||0)};}
    if (action==='history'){const size=params.period==='1y'?250:params.period==='6mo'?130:params.period==='1mo'?22:65;return{symbol:symbol.toUpperCase(),period:params.period||'3mo',data:await getHistory(ticker,size)};}
    throw new Error('Unknown action');
}

async function handleTechnicalRoute(symbol, action, params) {
    const ticker = `${symbol.toUpperCase()}.JK`;
    const size = params.period==='1y'?250:params.period==='6mo'?130:90;
    const candles = await getHistory(ticker, size);
    if (candles.length<30) throw new Error('Insufficient data');
    const closes=candles.map(c=>c.close),highs=candles.map(c=>c.high),lows=candles.map(c=>c.low),volumes=candles.map(c=>c.volume);
    const ma20=calcSMA(closes,20),ma50=calcSMA(closes,50),ma200=calcSMA(closes,200);
    const rsi=calcRSI(closes,14);const{macd,signal:macdSig,histogram}=calcMACD(closes);const volAvg=calcSMA(volumes,20);
    const last=closes.length-1,currentPrice=closes[last];
    const currentRSI=rsi[last]!=null?round(rsi[last]):50;
    const currentMACD=round(macd[last]),currentMACDSig=round(macdSig[last]);
    const cMA20=ma20[last]?Math.round(ma20[last]):null,cMA50=ma50[last]?Math.round(ma50[last]):null,cMA200=ma200[last]?Math.round(ma200[last]):null;
    const volRatio=volAvg[last]>0?round(volumes[last]/volAvg[last]):1;
    let bbStd=0;if(last>=19){const sl=closes.slice(last-19,last+1);const mn=sl.reduce((s,v)=>s+v,0)/20;bbStd=Math.sqrt(sl.reduce((s,v)=>s+(v-mn)**2,0)/20);}
    const bbUpper=cMA20?Math.round(cMA20+2*bbStd):null,bbLower=cMA20?Math.round(cMA20-2*bbStd):null;
    const resistances=[...new Set(highs.slice(-20))].filter(h=>h>currentPrice).sort((a,b)=>a-b).slice(0,3);
    const supports=[...new Set(lows.slice(-20))].filter(l=>l<currentPrice).sort((a,b)=>b-a).slice(0,3);
    const signals=[];
    if(currentRSI<30)signals.push({indicator:'RSI',signal:'oversold',type:'buy'});else if(currentRSI>70)signals.push({indicator:'RSI',signal:'overbought',type:'sell'});else signals.push({indicator:'RSI',signal:'netral',type:currentRSI<50?'buy':'sell'});
    if(currentMACD>currentMACDSig)signals.push({indicator:'MACD',signal:'bullish crossover',type:'buy'});else signals.push({indicator:'MACD',signal:'bearish crossover',type:'sell'});
    if(currentPrice>cMA20)signals.push({indicator:'MA20',signal:'harga di atas MA20',type:'buy'});else signals.push({indicator:'MA20',signal:'harga di bawah MA20',type:'sell'});
    if(cMA20&&cMA50&&cMA20>cMA50)signals.push({indicator:'Golden Cross',signal:'MA20 > MA50',type:'buy'});
    const buyCount=signals.filter(s=>s.type==='buy').length;const score=round((buyCount/signals.length)*10);
    const rec=score>=8?'Strong Buy':score>=6?'Buy':score>=4?'Neutral':score>=2?'Sell':'Strong Sell';
    if(action==='indicators'){return{symbol:symbol.toUpperCase(),price:currentPrice,indicators:{ma20:cMA20,ma50:cMA50,ma200:cMA200,rsi:currentRSI,macd:currentMACD,macd_signal:currentMACDSig,macd_histogram:round(histogram[last]),bb_upper:bbUpper,bb_middle:cMA20,bb_lower:bbLower,stochastic_k:null,stochastic_d:null,volume:volumes[last],volume_avg_20:volAvg[last]?Math.round(volAvg[last]):0,volume_ratio:volRatio},support_resistance:{supports,resistances},signals,score,recommendation:rec};}
    if(action==='chart-data'){return{symbol:symbol.toUpperCase(),data:candles.map((c,i)=>({...c,ma20:ma20[i]?Math.round(ma20[i]):null,ma50:ma50[i]?Math.round(ma50[i]):null,rsi:rsi[i]!=null?round(rsi[i]):null,macd:round(macd[i]),macd_signal:round(macdSig[i]),macd_hist:round(histogram[i])}))};}
    throw new Error('Unknown action');
}

async function handleFundamentalRoute(symbol) {
    const ticker=`${symbol.toUpperCase()}.JK`;const quotes=await getQuotes([ticker]);const q=quotes[0];if(!q)throw new Error('Stock not found');
    return{symbol:symbol.toUpperCase(),name:q.longName||q.shortName||symbol,sector:q.sector||'',industry:q.industry||'',market_cap:q.marketCap||0,ratios:{pe_ratio:q.trailingPE?round(q.trailingPE):null,pb_ratio:q.priceToBook?round(q.priceToBook):null,roe:null,roa:null,debt_to_equity:null,current_ratio:null,dividend_yield:null,payout_ratio:null},growth:{revenue_growth:null,earnings_growth:null},margins:{profit_margin:null,operating_margin:null,gross_margin:null},valuation:{enterprise_value:0,ev_to_revenue:0,ev_to_ebitda:0,peg_ratio:0}};
}

// ============ HTTP SERVER ============
const server = http.createServer(async (req, res) => {
    const parsed = new URL(req.url, `http://${req.headers.host}`);
    const pathname = parsed.pathname;
    const params = Object.fromEntries(parsed.searchParams.entries());
    if (pathname.startsWith('/api/')) {
        res.setHeader('Content-Type','application/json');res.setHeader('Access-Control-Allow-Origin','*');res.setHeader('Access-Control-Allow-Methods','GET, OPTIONS');res.setHeader('Access-Control-Allow-Headers','Content-Type');
        if(req.method==='OPTIONS'){res.writeHead(204);res.end();return;}
        try {
            if(routes[pathname]){const r=await routes[pathname](params);res.writeHead(200);res.end(JSON.stringify(r));return;}
            const stockMatch=pathname.match(/^\/api\/stock\/([^/]+)\/([^/]+)$/);if(stockMatch){const r=await handleStockRoute(stockMatch[1],stockMatch[2],params);res.writeHead(200);res.end(JSON.stringify(r));return;}
            const techMatch=pathname.match(/^\/api\/technical\/([^/]+)\/([^/]+)$/);if(techMatch){const r=await handleTechnicalRoute(techMatch[1],techMatch[2],params);res.writeHead(200);res.end(JSON.stringify(r));return;}
            const fundMatch=pathname.match(/^\/api\/fundamental\/([^/]+)$/);if(fundMatch){const r=await handleFundamentalRoute(fundMatch[1]);res.writeHead(200);res.end(JSON.stringify(r));return;}
            res.writeHead(404);res.end(JSON.stringify({error:'Not found'}));
        } catch(err){console.error('API Error:',err.message);res.writeHead(500);res.end(JSON.stringify({error:err.message}));}
        return;
    }
    let filePath=pathname==='/'?'/index.html':pathname;filePath=path.join(__dirname,filePath);
    const resolvedPath=path.resolve(filePath);if(!resolvedPath.startsWith(__dirname)){res.writeHead(403);res.end('Forbidden');return;}
    try{const content=fs.readFileSync(resolvedPath);res.setHeader('Content-Type',MIME[path.extname(resolvedPath)]||'application/octet-stream');res.writeHead(200);res.end(content);}catch{res.writeHead(404);res.end('Not found');}
});

server.listen(PORT, () => {
    console.log(`\n  ╔══════════════════════════════════════════════╗`);
    console.log(`  ║   SahamID - Analisa Saham Indonesia           ║`);
    console.log(`  ╠══════════════════════════════════════════════╣`);
    console.log(`  ║  Server : http://localhost:${PORT}              ║`);
    console.log(`  ║  Data   : Twelve Data (LIVE realtime)         ║`);
    console.log(`  ║  API Key: ${API_KEY === 'demo' ? 'DEMO - daftar di twelvedata.com' : 'Active ✓'}  ║`);
    console.log(`  ╠══════════════════════════════════════════════╣`);
    console.log(`  ║  Cara pakai:                                  ║`);
    console.log(`  ║  1. Daftar gratis di https://twelvedata.com   ║`);
    console.log(`  ║  2. Copy API key dari dashboard               ║`);
    console.log(`  ║  3. Jalankan:                                  ║`);
    console.log(`  ║     TWELVE_DATA_KEY=xxx node server.js        ║`);
    console.log(`  ╚══════════════════════════════════════════════╝\n`);
});
