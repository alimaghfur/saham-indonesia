async function getSignalsPage() {
    // Generate signals from multiple stocks technical data
    const stocks = ['BBCA', 'BBRI', 'BMRI', 'TLKM', 'ASII', 'BRIS', 'GOTO', 'UNVR'];
    const signalResults = [];

    for (const sym of stocks) {
        const data = await fetchAPI(`/technical/${sym}/indicators`);
        if (data && data.signals) {
            data.signals.forEach(sig => {
                signalResults.push({
                    symbol: sym,
                    price: data.price,
                    indicator: sig.indicator,
                    signal: sig.signal,
                    type: sig.type,
                    score: data.score,
                });
            });
        }
    }

    const buySignals = signalResults.filter(s => s.type === 'buy');
    const sellSignals = signalResults.filter(s => s.type === 'sell');

    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Signal & Alert</h2>
                <p class="text-dark-400 text-sm mt-1">Sinyal real-time dari indikator teknikal</p>
            </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="card p-4 border-l-4 border-l-success">
                <p class="text-xs text-dark-400">Buy Signals</p>
                <p class="text-2xl font-bold text-success">${buySignals.length}</p>
            </div>
            <div class="card p-4 border-l-4 border-l-danger">
                <p class="text-xs text-dark-400">Sell Signals</p>
                <p class="text-2xl font-bold text-danger">${sellSignals.length}</p>
            </div>
            <div class="card p-4 border-l-4 border-l-primary-400">
                <p class="text-xs text-dark-400">Total Scanned</p>
                <p class="text-2xl font-bold text-primary-400">${stocks.length} saham</p>
            </div>
        </div>

        <div class="card p-5">
            <h3 class="text-lg font-semibold text-white mb-4">Sinyal Aktif</h3>
            <div class="space-y-2">
                ${signalResults.map(s => signalCard(s)).join('')}
            </div>
        </div>
    </div>`;
}

function signalCard(s) {
    const isBuy = s.type === 'buy';
    const badge = isBuy ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger';
    const label = isBuy ? 'BUY' : 'SELL';
    const icon = isBuy ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down';
    return `
    <div class="p-4 bg-dark-800/50 rounded-lg border border-dark-700 flex items-center justify-between">
        <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg ${badge} flex items-center justify-center">
                <i class="fas ${icon}"></i>
            </div>
            <div>
                <div class="flex items-center gap-2">
                    <span class="font-bold text-white">${s.symbol}</span>
                    <span class="text-xs ${badge} px-2 py-0.5 rounded font-bold">${label}</span>
                </div>
                <p class="text-sm text-dark-300">${s.indicator}: ${s.signal}</p>
            </div>
        </div>
        <div class="text-right">
            <p class="text-sm font-medium text-white">Rp ${s.price?.toLocaleString('id-ID') || '-'}</p>
            <p class="text-xs text-dark-400">Score: ${s.score}/10</p>
        </div>
    </div>`;
}
