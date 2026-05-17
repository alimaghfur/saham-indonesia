function getScreenerPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Screener</h2>
                <p class="text-dark-400 text-sm mt-1">Filter dan temukan saham sesuai kriteria Anda</p>
            </div>
            <div class="flex gap-2">
                <button class="px-4 py-2 bg-dark-800 text-dark-300 rounded-lg text-sm hover:bg-dark-700"><i class="fas fa-bookmark mr-2"></i>Preset</button>
                <button class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700"><i class="fas fa-play mr-2"></i>Jalankan</button>
            </div>
        </div>

        <!-- Filter Section -->
        <div class="card p-5">
            <h3 class="text-sm font-semibold text-dark-300 uppercase tracking-wider mb-4">Filter Kriteria</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Market Cap</label>
                    <select class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                        <option>Semua</option>
                        <option>Large Cap (>50T)</option>
                        <option>Mid Cap (10T-50T)</option>
                        <option>Small Cap (<10T)</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Sektor</label>
                    <select class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                        <option>Semua Sektor</option>
                        <option>Keuangan</option>
                        <option>Teknologi</option>
                        <option>Konsumer</option>
                        <option>Energi</option>
                        <option>Infrastruktur</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">PER</label>
                    <div class="flex gap-2">
                        <input type="number" placeholder="Min" class="w-1/2 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                        <input type="number" placeholder="Max" class="w-1/2 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                    </div>
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">RSI (14)</label>
                    <div class="flex gap-2">
                        <input type="number" placeholder="Min" class="w-1/2 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                        <input type="number" placeholder="Max" class="w-1/2 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                    </div>
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Volume (vs Avg 20)</label>
                    <select class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                        <option>Semua</option>
                        <option>>2x Average</option>
                        <option>>3x Average</option>
                        <option>>5x Average</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">MA Signal</label>
                    <select class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                        <option>Semua</option>
                        <option>Harga di atas MA20</option>
                        <option>Golden Cross</option>
                        <option>Death Cross</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Dividend Yield</label>
                    <div class="flex gap-2">
                        <input type="number" placeholder="Min %" class="w-1/2 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                        <input type="number" placeholder="Max %" class="w-1/2 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                    </div>
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">ROE</label>
                    <div class="flex gap-2">
                        <input type="number" placeholder="Min %" class="w-1/2 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                        <input type="number" placeholder="Max %" class="w-1/2 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white focus:border-primary-500 focus:outline-none">
                    </div>
                </div>
            </div>
        </div>

        <!-- Preset Filters -->
        <div class="flex flex-wrap gap-2">
            <button class="px-3 py-1.5 bg-primary-600/20 text-primary-400 rounded-lg text-xs font-medium hover:bg-primary-600/30 border border-primary-600/30">
                <i class="fas fa-fire mr-1"></i>High Momentum
            </button>
            <button class="px-3 py-1.5 bg-emerald-600/20 text-emerald-400 rounded-lg text-xs font-medium hover:bg-emerald-600/30 border border-emerald-600/30">
                <i class="fas fa-gem mr-1"></i>Undervalued
            </button>
            <button class="px-3 py-1.5 bg-amber-600/20 text-amber-400 rounded-lg text-xs font-medium hover:bg-amber-600/30 border border-amber-600/30">
                <i class="fas fa-coins mr-1"></i>High Dividend
            </button>
            <button class="px-3 py-1.5 bg-purple-600/20 text-purple-400 rounded-lg text-xs font-medium hover:bg-purple-600/30 border border-purple-600/30">
                <i class="fas fa-chart-bar mr-1"></i>Volume Spike
            </button>
            <button class="px-3 py-1.5 bg-cyan-600/20 text-cyan-400 rounded-lg text-xs font-medium hover:bg-cyan-600/30 border border-cyan-600/30">
                <i class="fas fa-shield-alt mr-1"></i>Blue Chip
            </button>
        </div>

        <!-- Results -->
        <div class="card p-5">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-sm font-semibold text-dark-300">Hasil: <span class="text-white">24 saham ditemukan</span></h3>
                <div class="flex items-center gap-2">
                    <button class="p-2 bg-dark-700 rounded text-dark-400 text-xs"><i class="fas fa-download"></i></button>
                    <select class="bg-dark-800 border border-dark-600 rounded px-2 py-1 text-xs text-dark-300">
                        <option>Sort: Performance</option>
                        <option>Sort: Volume</option>
                        <option>Sort: Market Cap</option>
                    </select>
                </div>
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
                        ${screenerRow('BBCA', 9875, 2.33, 22.5, 4.8, 21.3, 58, 1.8, 'buy')}
                        ${screenerRow('BMRI', 6425, 2.39, 12.1, 2.3, 19.8, 62, 2.1, 'buy')}
                        ${screenerRow('TLKM', 3980, 3.11, 14.8, 3.1, 18.5, 45, 3.2, 'buy')}
                        ${screenerRow('BBRI', 5150, 1.57, 13.2, 2.5, 20.1, 55, 1.5, 'buy')}
                        ${screenerRow('ASII', 5225, 1.95, 8.9, 1.4, 15.2, 52, 1.3, 'neutral')}
                        ${screenerRow('BRIS', 2680, 3.08, 18.3, 3.2, 16.7, 68, 2.8, 'buy')}
                        ${screenerRow('UNVR', 4150, -1.78, 32.5, 28.1, 85.6, 35, 0.8, 'sell')}
                        ${screenerRow('GOTO', 82, 7.89, -45.2, 5.1, -8.3, 72, 4.5, 'neutral')}
                    </tbody>
                </table>
            </div>
        </div>
    </div>`;
}

function screenerRow(code, price, change, per, pbv, roe, rsi, volRatio, signal) {
    const isUp = change >= 0;
    const chgColor = isUp ? 'stat-up' : 'stat-down';
    const sign = isUp ? '+' : '';
    const rsiColor = rsi > 70 ? 'text-danger' : rsi < 30 ? 'text-success' : 'text-white';
    const signalBadge = signal === 'buy' ? 'bg-success/20 text-success' : signal === 'sell' ? 'bg-danger/20 text-danger' : 'bg-dark-600 text-dark-300';
    const signalLabel = signal === 'buy' ? 'BUY' : signal === 'sell' ? 'SELL' : 'HOLD';
    return `
    <tr class="border-b border-dark-800 hover:bg-dark-800/50 cursor-pointer">
        <td class="py-3 font-semibold text-white">${code}</td>
        <td class="text-right text-white">${price.toLocaleString('id-ID')}</td>
        <td class="text-right ${chgColor} font-medium">${sign}${change}%</td>
        <td class="text-right text-dark-300">${per}x</td>
        <td class="text-right text-dark-300">${pbv}x</td>
        <td class="text-right text-dark-300">${roe}%</td>
        <td class="text-right ${rsiColor} font-medium">${rsi}</td>
        <td class="text-right text-dark-300">${volRatio}x</td>
        <td class="text-center"><span class="text-xs font-bold ${signalBadge} px-2 py-1 rounded">${signalLabel}</span></td>
    </tr>`;
}
