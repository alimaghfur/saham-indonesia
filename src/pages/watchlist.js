function getWatchlistPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Watchlist</h2>
                <p class="text-dark-400 text-sm mt-1">Daftar saham yang Anda pantau</p>
            </div>
            <button class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
                <i class="fas fa-plus mr-2"></i>Tambah Saham
            </button>
        </div>

        <!-- Watchlist Groups -->
        <div class="flex gap-2 flex-wrap">
            <button class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm">Semua (15)</button>
            <button class="px-4 py-2 bg-dark-800 text-dark-300 rounded-lg text-sm hover:bg-dark-700">Blue Chip (6)</button>
            <button class="px-4 py-2 bg-dark-800 text-dark-300 rounded-lg text-sm hover:bg-dark-700">Growth (5)</button>
            <button class="px-4 py-2 bg-dark-800 text-dark-300 rounded-lg text-sm hover:bg-dark-700">Dividend (4)</button>
            <button class="px-4 py-2 bg-dark-800 text-dark-300 rounded-lg text-sm hover:bg-dark-700"><i class="fas fa-plus text-xs"></i></button>
        </div>

        <!-- Watchlist Table -->
        <div class="card p-5">
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="text-dark-400 border-b border-dark-700">
                            <th class="text-left py-3 font-medium">Saham</th>
                            <th class="text-right py-3 font-medium">Harga</th>
                            <th class="text-right py-3 font-medium">Chg %</th>
                            <th class="text-right py-3 font-medium">Volume</th>
                            <th class="text-right py-3 font-medium">RSI</th>
                            <th class="text-left py-3 font-medium">Catatan</th>
                            <th class="text-center py-3 font-medium">Signal</th>
                            <th class="text-center py-3 font-medium">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${watchRow('BBCA', 'Bank Central Asia', 9875, 2.33, '12.5M', 58, 'Target entry di 9,500', 'buy')}
                        ${watchRow('TLKM', 'Telkom Indonesia', 3980, 3.11, '45.2M', 45, 'Tunggu RSI < 30', 'buy')}
                        ${watchRow('BMRI', 'Bank Mandiri', 6425, 2.39, '23.1M', 62, 'Breakout 6,400 confirmed', 'buy')}
                        ${watchRow('ASII', 'Astra International', 5225, 1.95, '18.7M', 52, 'Sideways, wait breakout', 'neutral')}
                        ${watchRow('UNVR', 'Unilever Indonesia', 4150, -1.78, '8.3M', 35, 'Downtrend, avoid', 'sell')}
                        ${watchRow('GOTO', 'GoTo Gojek', 82, 7.89, '892.5M', 72, 'Speculative play', 'neutral')}
                        ${watchRow('BRIS', 'BSI', 2680, 3.08, '34.6M', 68, 'Islamic banking growth', 'buy')}
                        ${watchRow('ACES', 'Ace Hardware', 750, 1.35, '15.2M', 48, 'Consumer recovery play', 'neutral')}
                        ${watchRow('ICBP', 'Indofood CBP', 11250, 0.89, '5.6M', 55, 'Defensive stock', 'buy')}
                        ${watchRow('ANTM', 'Aneka Tambang', 1850, -2.11, '42.3M', 38, 'Gold price correlation', 'neutral')}
                    </tbody>
                </table>
            </div>
        </div>
    </div>`;
}

function watchRow(code, name, price, change, volume, rsi, note, signal) {
    const isUp = change >= 0;
    const chgColor = isUp ? 'stat-up' : 'stat-down';
    const sign = isUp ? '+' : '';
    const signalBadge = signal === 'buy' ? 'bg-success/20 text-success' : signal === 'sell' ? 'bg-danger/20 text-danger' : 'bg-dark-600 text-dark-300';
    const signalIcon = signal === 'buy' ? 'fa-arrow-up' : signal === 'sell' ? 'fa-arrow-down' : 'fa-minus';
    return `
    <tr class="border-b border-dark-800 hover:bg-dark-800/50">
        <td class="py-3">
            <p class="font-semibold text-white">${code}</p>
            <p class="text-xs text-dark-400">${name}</p>
        </td>
        <td class="text-right text-white font-medium">${price.toLocaleString('id-ID')}</td>
        <td class="text-right ${chgColor} font-medium">${sign}${change}%</td>
        <td class="text-right text-dark-300">${volume}</td>
        <td class="text-right text-white">${rsi}</td>
        <td class="text-left text-xs text-dark-400 max-w-[150px] truncate">${note}</td>
        <td class="text-center"><span class="text-xs ${signalBadge} px-2 py-1 rounded"><i class="fas ${signalIcon}"></i></span></td>
        <td class="text-center">
            <button class="text-dark-500 hover:text-danger text-xs"><i class="fas fa-trash"></i></button>
        </td>
    </tr>`;
}
