function getPortfolioPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Portfolio</h2>
                <p class="text-dark-400 text-sm mt-1">Tracking performa investasi Anda</p>
            </div>
            <button class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
                <i class="fas fa-plus mr-2"></i>Tambah Transaksi
            </button>
        </div>

        <!-- Portfolio Summary -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="card p-5">
                <p class="text-xs text-dark-400">Total Nilai</p>
                <p class="text-2xl font-bold text-white mt-1">Rp 125.8 Jt</p>
                <p class="text-xs text-dark-500 mt-1">Modal: Rp 100 Jt</p>
            </div>
            <div class="card p-5">
                <p class="text-xs text-dark-400">Total Profit/Loss</p>
                <p class="text-2xl font-bold stat-up mt-1">+Rp 25.8 Jt</p>
                <p class="text-xs text-success mt-1">+25.8% keuntungan</p>
            </div>
            <div class="card p-5">
                <p class="text-xs text-dark-400">Hari Ini</p>
                <p class="text-2xl font-bold stat-up mt-1">+Rp 1.2 Jt</p>
                <p class="text-xs text-success mt-1">+0.96%</p>
            </div>
            <div class="card p-5">
                <p class="text-xs text-dark-400">Dividen Diterima</p>
                <p class="text-2xl font-bold text-primary-400 mt-1">Rp 3.5 Jt</p>
                <p class="text-xs text-dark-500 mt-1">YTD 2026</p>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Holdings -->
            <div class="lg:col-span-2 card p-5">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-white">Holdings</h3>
                    <div class="flex gap-2">
                        <button class="px-3 py-1 text-xs rounded bg-primary-600 text-white">Aktif</button>
                        <button class="px-3 py-1 text-xs rounded bg-dark-700 text-dark-300">Riwayat</button>
                    </div>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="text-dark-400 border-b border-dark-700">
                                <th class="text-left py-3 font-medium">Saham</th>
                                <th class="text-right py-3 font-medium">Lot</th>
                                <th class="text-right py-3 font-medium">Avg Price</th>
                                <th class="text-right py-3 font-medium">Harga Now</th>
                                <th class="text-right py-3 font-medium">P/L</th>
                                <th class="text-right py-3 font-medium">%P/L</th>
                                <th class="text-right py-3 font-medium">Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${holdingRow('BBCA', 50, 8500, 9875, 'Keuangan')}
                            ${holdingRow('BMRI', 80, 5200, 6425, 'Keuangan')}
                            ${holdingRow('TLKM', 100, 3500, 3980, 'Telko')}
                            ${holdingRow('ASII', 40, 4800, 5225, 'Otomotif')}
                            ${holdingRow('BRIS', 60, 2200, 2680, 'Keuangan')}
                            ${holdingRow('UNVR', 30, 4500, 4150, 'Konsumer')}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Allocation -->
            <div class="space-y-4">
                <div class="card p-5">
                    <h3 class="text-sm font-semibold text-white mb-4">Alokasi Sektor</h3>
                    <div class="space-y-3">
                        ${allocationItem('Keuangan', 62, '#3b82f6')}
                        ${allocationItem('Telekomunikasi', 18, '#10b981')}
                        ${allocationItem('Otomotif', 10, '#f59e0b')}
                        ${allocationItem('Konsumer', 10, '#8b5cf6')}
                    </div>
                </div>

                <div class="card p-5">
                    <h3 class="text-sm font-semibold text-white mb-4">Performa Bulanan</h3>
                    <div class="space-y-2">
                        ${monthPerf('Mei 2026', '+3.2%', true)}
                        ${monthPerf('Apr 2026', '+5.1%', true)}
                        ${monthPerf('Mar 2026', '-1.8%', false)}
                        ${monthPerf('Feb 2026', '+7.4%', true)}
                        ${monthPerf('Jan 2026', '+2.9%', true)}
                    </div>
                </div>
            </div>
        </div>
    </div>`;
}

function holdingRow(code, lot, avg, now, sector) {
    const shares = lot * 100;
    const pl = (now - avg) * shares;
    const plPct = ((now - avg) / avg * 100).toFixed(2);
    const value = now * shares;
    const isUp = pl >= 0;
    const color = isUp ? 'stat-up' : 'stat-down';
    const sign = isUp ? '+' : '';
    return `
    <tr class="border-b border-dark-800 hover:bg-dark-800/50">
        <td class="py-3">
            <p class="font-semibold text-white">${code}</p>
            <p class="text-xs text-dark-400">${sector}</p>
        </td>
        <td class="text-right text-dark-300">${lot}</td>
        <td class="text-right text-dark-300">${avg.toLocaleString('id-ID')}</td>
        <td class="text-right text-white font-medium">${now.toLocaleString('id-ID')}</td>
        <td class="text-right ${color} font-medium">${sign}${(pl/1000000).toFixed(1)} Jt</td>
        <td class="text-right ${color} font-medium">${sign}${plPct}%</td>
        <td class="text-right text-white">${(value/1000000).toFixed(1)} Jt</td>
    </tr>`;
}

function allocationItem(name, pct, color) {
    return `
    <div>
        <div class="flex justify-between text-sm mb-1">
            <span class="text-dark-300">${name}</span>
            <span class="text-white font-medium">${pct}%</span>
        </div>
        <div class="w-full h-2 bg-dark-700 rounded-full">
            <div class="h-2 rounded-full" style="width:${pct}%; background:${color}"></div>
        </div>
    </div>`;
}

function monthPerf(month, perf, isUp) {
    const color = isUp ? 'stat-up' : 'stat-down';
    const icon = isUp ? 'fa-arrow-up' : 'fa-arrow-down';
    return `
    <div class="flex items-center justify-between py-1.5">
        <span class="text-sm text-dark-300">${month}</span>
        <span class="text-sm font-medium ${color}"><i class="fas ${icon} text-xs mr-1"></i>${perf}</span>
    </div>`;
}
