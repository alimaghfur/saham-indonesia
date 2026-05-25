async function getScreenerPage() {
    const data = await fetchAPI('/screener/scan?limit=20&sort_by=change_pct');
    const stocks = data?.stocks || [];

    const errorState = !data ? `
        <div class="card p-8 text-center">
            <i class="fas fa-exclamation-triangle text-4xl text-warning mb-4"></i>
            <h3 class="text-lg font-semibold text-white mb-2">Gagal Memuat Data</h3>
            <p class="text-dark-400 text-sm mb-4">Tidak dapat terhubung ke server.</p>
            <button onclick="navigateTo('screener')" class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
                <i class="fas fa-sync-alt mr-2"></i>Coba Lagi
            </button>
        </div>` : '';

    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Screener</h2>
                <p class="text-dark-400 text-sm mt-1">Filter dan temukan saham - data real dari TradingView</p>
            </div>
            <button onclick="runScreener()" class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700"><i class="fas fa-play mr-2"></i>Jalankan</button>
        </div>

        <!-- Filter Section -->
        <div class="card p-5">
            <h3 class="text-sm font-semibold text-dark-300 uppercase tracking-wider mb-4">Filter Kriteria</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">PER Maks</label>
                    <input id="f-max-pe" type="number" placeholder="cth: 20" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">ROE Min (%)</label>
                    <input id="f-min-roe" type="number" placeholder="cth: 15" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">RSI Maks</label>
                    <input id="f-max-rsi" type="number" placeholder="cth: 70" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Vol Ratio Min (x avg)</label>
                    <input id="f-min-vol" type="number" step="0.1" placeholder="cth: 2" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
            </div>
        </div>

        <!-- Results -->
        ${errorState}
        <div class="card p-5" id="screener-results">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-sm font-semibold text-dark-300">Hasil: <span class="text-white">${stocks.length} saham</span></h3>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="text-dark-400 border-b border-dark-700">
                            <th class="text-left py-3 font-medium">Saham</th>
                            <th class="text-right py-3 font-medium">Harga</th>
                            <th class="text-right py-3 font-medium">%Chg</th>
                            <th class="text-right py-3 font-medium">PER</th>
                            <th class="text-right py-3 font-medium">PBV</th>
                            <th class="text-right py-3 font-medium">ROE</th>
                            <th class="text-right py-3 font-medium">RSI</th>
                            <th class="text-right py-3 font-medium">Vol Ratio</th>
                            <th class="text-center py-3 font-medium">Signal</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${stocks.map(s => screenerRow(s)).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    </div>`;
}

function screenerRow(s) {
    const isUp = s.change_pct >= 0;
    const chgColor = isUp ? 'stat-up' : 'stat-down';
    const sign = isUp ? '+' : '';
    const rsiColor = s.rsi > 70 ? 'text-danger' : s.rsi < 30 ? 'text-success' : 'text-white';
    const signalBadge = s.signal === 'buy' ? 'bg-success/20 text-success' : s.signal === 'sell' ? 'bg-danger/20 text-danger' : 'bg-dark-600 text-dark-300';
    const signalLabel = s.signal === 'buy' ? 'BUY' : s.signal === 'sell' ? 'SELL' : 'HOLD';
    return `
    <tr class="border-b border-dark-800 hover:bg-dark-800/50 cursor-pointer">
        <td class="py-3 font-semibold text-white">${s.symbol}</td>
        <td class="text-right text-white">${s.price ? s.price.toLocaleString('id-ID') : '-'}</td>
        <td class="text-right ${chgColor} font-medium">${sign}${s.change_pct}%</td>
        <td class="text-right text-dark-300">${s.pe ? s.pe + 'x' : '-'}</td>
        <td class="text-right text-dark-300">${s.pb ? s.pb + 'x' : '-'}</td>
        <td class="text-right text-dark-300">${s.roe ? s.roe + '%' : '-'}</td>
        <td class="text-right ${rsiColor} font-medium">${s.rsi}</td>
        <td class="text-right text-dark-300">${s.volume_ratio}x</td>
        <td class="text-center"><span class="text-xs font-bold ${signalBadge} px-2 py-1 rounded">${signalLabel}</span></td>
    </tr>`;
}

async function runScreener() {
    let params = [];
    const maxPe = document.getElementById('f-max-pe')?.value;
    const minRoe = document.getElementById('f-min-roe')?.value;
    const maxRsi = document.getElementById('f-max-rsi')?.value;
    const minVol = document.getElementById('f-min-vol')?.value;
    if (maxPe) params.push(`max_pe=${maxPe}`);
    if (minRoe) params.push(`min_roe=${minRoe}`);
    if (maxRsi) params.push(`max_rsi=${maxRsi}`);
    if (minVol) params.push(`min_volume_ratio=${minVol}`);
    params.push('limit=20');

    const container = document.getElementById('screener-results');
    container.innerHTML = '<div class="py-8 text-center text-dark-400"><div class="animate-spin w-6 h-6 border-4 border-primary-400 border-t-transparent rounded-full mx-auto mb-2"></div>Scanning...</div>';

    const data = await fetchAPI('/screener/scan?' + params.join('&'));
    const stocks = data?.stocks || [];
    container.innerHTML = `
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-dark-300">Hasil: <span class="text-white">${stocks.length} saham</span></h3>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead><tr class="text-dark-400 border-b border-dark-700">
                    <th class="text-left py-3">Saham</th><th class="text-right py-3">Harga</th><th class="text-right py-3">%Chg</th>
                    <th class="text-right py-3">PER</th><th class="text-right py-3">PBV</th><th class="text-right py-3">ROE</th>
                    <th class="text-right py-3">RSI</th><th class="text-right py-3">Vol Ratio</th><th class="text-center py-3">Signal</th>
                </tr></thead>
                <tbody>${stocks.map(s => screenerRow(s)).join('')}</tbody>
            </table>
        </div>`;
}
