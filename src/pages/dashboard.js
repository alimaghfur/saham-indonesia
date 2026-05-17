async function getDashboardPage() {
    const [indicesData, moversData, summaryData, sectorsData] = await Promise.all([
        fetchAPI('/market/indices'),
        fetchAPI('/market/top-movers?limit=7'),
        fetchAPI('/market/summary'),
        fetchAPI('/market/sectors'),
    ]);

    const indices = indicesData?.indices || [];
    const gainers = moversData?.gainers || [];
    const summary = summaryData || {};
    const sectors = sectorsData?.sectors || [];

    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Dashboard</h2>
                <p class="text-dark-400 text-sm mt-1">Ringkasan pasar saham Indonesia hari ini (data real-time)</p>
            </div>
            <div class="flex items-center gap-2">
                <span class="w-2 h-2 bg-success rounded-full pulse-dot"></span>
                <span class="text-xs text-dark-400">Live dari Yahoo Finance</span>
                <button onclick="navigateTo('dashboard')" class="ml-2 p-2 rounded-lg bg-dark-800 hover:bg-dark-700 text-dark-400 hover:text-white">
                    <i class="fas fa-sync-alt text-sm"></i>
                </button>
            </div>
        </div>

        <!-- Market Indices -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            ${indices.map(idx => marketCard(idx)).join('')}
        </div>

        <!-- Trading Stats -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="card p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-dark-400">Total Volume</span>
                    <i class="fas fa-layer-group text-emerald-400"></i>
                </div>
                <p class="text-2xl font-bold text-white">${formatVolume(summary.total_volume)}</p>
            </div>
            <div class="card p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-dark-400">Sentimen</span>
                    <i class="fas fa-chart-pie text-primary-400"></i>
                </div>
                <p class="text-2xl font-bold ${(summary.sentiment_score || 50) >= 50 ? 'stat-up' : 'stat-down'}">${summary.sentiment_score || 50}% ${(summary.sentiment_score || 50) >= 50 ? 'Bullish' : 'Bearish'}</p>
            </div>
            <div class="card p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-dark-400">Naik / Turun / Tetap</span>
                    <i class="fas fa-exchange-alt text-cyan-400"></i>
                </div>
                <p class="text-lg font-bold"><span class="stat-up">${summary.advancing || 0}</span> / <span class="stat-down">${summary.declining || 0}</span> / <span class="text-dark-400">${summary.unchanged || 0}</span></p>
            </div>
        </div>

        <!-- Main Content -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Top Movers -->
            <div class="lg:col-span-2 card p-5">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-white">Top Gainers</h3>
                    <span class="text-xs text-dark-400">Data real-time</span>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="text-dark-400 border-b border-dark-700">
                                <th class="text-left py-3 font-medium">Saham</th>
                                <th class="text-right py-3 font-medium">Harga</th>
                                <th class="text-right py-3 font-medium">Perubahan</th>
                                <th class="text-right py-3 font-medium">Volume</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${gainers.map(s => stockRow(s)).join('')}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Sector Performance -->
            <div class="card p-5">
                <h3 class="text-lg font-semibold text-white mb-4">Sektor Hari Ini</h3>
                <div class="space-y-3">
                    ${sectors.map(s => sectorItem(s)).join('')}
                </div>
            </div>
        </div>
    </div>`;
}

function marketCard(idx) {
    const isUp = idx.change >= 0;
    const color = isUp ? 'stat-up' : 'stat-down';
    const arrow = isUp ? 'fa-arrow-up' : 'fa-arrow-down';
    const bgGlow = isUp ? 'from-emerald-500/10 to-transparent' : 'from-red-500/10 to-transparent';
    return `
    <div class="card p-5 relative overflow-hidden">
        <div class="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl ${bgGlow} rounded-bl-full"></div>
        <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-dark-400">${idx.name}</span>
            <i class="fas fa-chart-line text-dark-500"></i>
        </div>
        <p class="text-xl font-bold text-white">${idx.price ? idx.price.toLocaleString('id-ID', {maximumFractionDigits: 2}) : '-'}</p>
        <div class="flex items-center gap-2 mt-1">
            <span class="${color} text-sm font-medium"><i class="fas ${arrow} text-xs"></i> ${isUp ? '+' : ''}${idx.change}</span>
            <span class="${color} text-xs">(${isUp ? '+' : ''}${idx.change_pct}%)</span>
        </div>
    </div>`;
}

function stockRow(s) {
    const isUp = s.change_pct >= 0;
    const color = isUp ? 'stat-up' : 'stat-down';
    const sign = isUp ? '+' : '';
    return `
    <tr class="border-b border-dark-800 hover:bg-dark-800/50 cursor-pointer" onclick="navigateTo('technical')">
        <td class="py-3">
            <p class="font-semibold text-white">${s.symbol}</p>
        </td>
        <td class="text-right font-medium text-white">${s.price ? s.price.toLocaleString('id-ID') : '-'}</td>
        <td class="text-right ${color} font-medium">${sign}${s.change_pct}%</td>
        <td class="text-right text-dark-300">${formatVolume(s.volume)}</td>
    </tr>`;
}

function sectorItem(s) {
    const isUp = s.change_pct >= 0;
    const color = isUp ? 'text-success bg-success/10' : 'text-danger bg-danger/10';
    const sign = isUp ? '+' : '';
    const barColor = isUp ? 'bg-success' : 'bg-danger';
    const width = Math.min(Math.abs(s.change_pct) * 25, 100);
    return `
    <div class="flex items-center justify-between">
        <span class="text-sm text-dark-200">${s.sector}</span>
        <div class="flex items-center gap-3">
            <div class="w-20 h-1.5 bg-dark-700 rounded-full overflow-hidden">
                <div class="${barColor} h-full rounded-full" style="width:${width}%"></div>
            </div>
            <span class="text-sm font-medium ${color} px-2 py-0.5 rounded">${sign}${s.change_pct}%</span>
        </div>
    </div>`;
}
