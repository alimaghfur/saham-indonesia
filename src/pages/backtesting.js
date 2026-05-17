function getBacktestingPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Backtesting</h2>
                <p class="text-dark-400 text-sm mt-1">Simulasi strategi trading pada data historis real</p>
            </div>
        </div>

        <div class="card p-5">
            <h3 class="text-sm font-semibold text-dark-300 uppercase tracking-wider mb-4">Konfigurasi Strategi</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Strategi</label>
                    <select id="bt-strategy" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                        <option value="golden_cross">Golden Cross MA</option>
                        <option value="rsi">RSI Reversal</option>
                        <option value="macd">MACD Crossover</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Saham</label>
                    <input id="bt-symbol" type="text" value="BBCA" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white uppercase">
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Periode</label>
                    <select id="bt-period" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                        <option value="1y">1 Tahun</option>
                        <option value="2y">2 Tahun</option>
                        <option value="5y">5 Tahun</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Modal Awal (Rp)</label>
                    <input id="bt-capital" type="number" value="100000000" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
            </div>
            <button onclick="runBacktest()" class="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
                <i class="fas fa-play mr-2"></i>Jalankan Backtest
            </button>
        </div>

        <div id="bt-results"></div>
    </div>`;
}

async function runBacktest() {
    const symbol = document.getElementById('bt-symbol').value.trim().toUpperCase();
    const period = document.getElementById('bt-period').value;
    const capital = parseInt(document.getElementById('bt-capital').value) || 100000000;
    const strategy = document.getElementById('bt-strategy').value;

    const container = document.getElementById('bt-results');
    container.innerHTML = '<div class="card p-8 text-center"><div class="animate-spin w-8 h-8 border-4 border-primary-400 border-t-transparent rounded-full mx-auto mb-3"></div><p class="text-dark-400">Mengambil data historis & menjalankan backtest...</p></div>';

    const chartData = await fetchAPI(`/technical/${symbol}/chart-data?period=${period}`);
    if (!chartData || !chartData.data || chartData.data.length < 50) {
        container.innerHTML = '<div class="card p-5 text-center text-danger">Data tidak cukup untuk backtest</div>';
        return;
    }

    const candles = chartData.data;
    // Simple Golden Cross backtest
    let trades = [];
    let position = null;
    let wins = 0, losses = 0;
    let totalPL = 0;

    for (let i = 50; i < candles.length; i++) {
        const ma20 = candles.slice(i-20, i).reduce((s, c) => s + c.close, 0) / 20;
        const ma50 = candles.slice(i-50, i).reduce((s, c) => s + c.close, 0) / 50;
        const prevMa20 = candles.slice(i-21, i-1).reduce((s, c) => s + c.close, 0) / 20;
        const prevMa50 = candles.slice(i-51, i-1).reduce((s, c) => s + c.close, 0) / 50;

        if (!position && prevMa20 <= prevMa50 && ma20 > ma50) {
            position = { entry: candles[i].close, date: candles[i].date };
        } else if (position && prevMa20 >= prevMa50 && ma20 < ma50) {
            const pl = ((candles[i].close - position.entry) / position.entry) * 100;
            trades.push({ ...position, exit: candles[i].close, exitDate: candles[i].date, pl: pl.toFixed(2) });
            totalPL += pl;
            if (pl > 0) wins++; else losses++;
            position = null;
        }
    }

    const winRate = trades.length > 0 ? ((wins / trades.length) * 100).toFixed(1) : 0;
    const finalCapital = capital * (1 + totalPL / 100);

    container.innerHTML = `
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <div class="card p-4 text-center"><p class="text-xs text-dark-400">Total Return</p><p class="text-lg font-bold ${totalPL >= 0 ? 'stat-up' : 'stat-down'}">${totalPL >= 0 ? '+' : ''}${totalPL.toFixed(2)}%</p></div>
        <div class="card p-4 text-center"><p class="text-xs text-dark-400">Win Rate</p><p class="text-lg font-bold text-white">${winRate}%</p></div>
        <div class="card p-4 text-center"><p class="text-xs text-dark-400">Total Trades</p><p class="text-lg font-bold text-white">${trades.length}</p></div>
        <div class="card p-4 text-center"><p class="text-xs text-dark-400">Final Capital</p><p class="text-lg font-bold ${finalCapital > capital ? 'stat-up' : 'stat-down'}">Rp ${formatRupiah(Math.round(finalCapital))}</p></div>
    </div>
    <div class="card p-5">
        <h3 class="text-sm font-semibold text-white mb-3">Trade History (Data Real ${symbol})</h3>
        <div class="overflow-x-auto"><table class="w-full text-sm">
            <thead><tr class="text-dark-400 border-b border-dark-700">
                <th class="text-left py-2">#</th><th class="text-left py-2">Entry</th><th class="text-left py-2">Exit</th><th class="text-right py-2">Buy</th><th class="text-right py-2">Sell</th><th class="text-right py-2">P/L</th>
            </tr></thead>
            <tbody>${trades.slice(-10).map((t, i) => `
                <tr class="border-b border-dark-800">
                    <td class="py-2 text-dark-400">${i+1}</td>
                    <td class="py-2 text-dark-300">${t.date}</td>
                    <td class="py-2 text-dark-300">${t.exitDate}</td>
                    <td class="text-right text-dark-300">${t.entry.toLocaleString('id-ID')}</td>
                    <td class="text-right text-white">${t.exit.toLocaleString('id-ID')}</td>
                    <td class="text-right font-medium ${parseFloat(t.pl) >= 0 ? 'stat-up' : 'stat-down'}">${parseFloat(t.pl) >= 0 ? '+' : ''}${t.pl}%</td>
                </tr>`).join('')}
            </tbody>
        </table></div>
    </div>`;
}
