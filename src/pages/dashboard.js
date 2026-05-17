function getDashboardPage() {
    return `
    <div class="space-y-6">
        <!-- Page Title -->
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Dashboard</h2>
                <p class="text-dark-400 text-sm mt-1">Ringkasan pasar saham Indonesia hari ini</p>
            </div>
            <div class="flex items-center gap-2">
                <span class="text-xs text-dark-400">Terakhir update:</span>
                <span class="text-xs text-primary-400 font-medium">${new Date().toLocaleString('id-ID')}</span>
                <button onclick="navigateTo('dashboard')" class="ml-2 p-2 rounded-lg bg-dark-800 hover:bg-dark-700 text-dark-400 hover:text-white transition">
                    <i class="fas fa-sync-alt text-sm"></i>
                </button>
            </div>
        </div>

        <!-- Market Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            ${marketCard('IHSG', '7,432.15', '+91.23', '+1.24%', true, 'fa-chart-line')}
            ${marketCard('LQ45', '982.30', '+8.47', '+0.87%', true, 'fa-gem')}
            ${marketCard('IDX30', '512.85', '+4.12', '+0.81%', true, 'fa-crown')}
            ${marketCard('JII', '578.40', '-2.35', '-0.41%', false, 'fa-moon')}
        </div>

        <!-- Trading Stats -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="card p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-dark-400">Total Transaksi</span>
                    <i class="fas fa-exchange-alt text-primary-400"></i>
                </div>
                <p class="text-2xl font-bold text-white">Rp 12.8 T</p>
                <p class="text-xs text-success mt-1"><i class="fas fa-arrow-up mr-1"></i>+15.3% vs kemarin</p>
            </div>
            <div class="card p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-dark-400">Volume</span>
                    <i class="fas fa-layer-group text-emerald-400"></i>
                </div>
                <p class="text-2xl font-bold text-white">18.5 B</p>
                <p class="text-xs text-success mt-1"><i class="fas fa-arrow-up mr-1"></i>+8.7% vs kemarin</p>
            </div>
            <div class="card p-5">
                <div class="flex items-center justify-between mb-3">
                    <span class="text-sm text-dark-400">Foreign Flow</span>
                    <i class="fas fa-globe text-cyan-400"></i>
                </div>
                <p class="text-2xl font-bold text-white stat-up">+Rp 485 M</p>
                <p class="text-xs text-dark-400 mt-1">Net Buy (5 hari berturut)</p>
            </div>
        </div>

        <!-- Main Content Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Top Movers -->
            <div class="lg:col-span-2 card p-5">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-white">Top Movers</h3>
                    <div class="flex gap-2">
                        <button class="px-3 py-1 text-xs rounded-md bg-primary-600 text-white">Gainers</button>
                        <button class="px-3 py-1 text-xs rounded-md bg-dark-700 text-dark-300 hover:bg-dark-600">Losers</button>
                        <button class="px-3 py-1 text-xs rounded-md bg-dark-700 text-dark-300 hover:bg-dark-600">Volume</button>
                    </div>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="text-dark-400 border-b border-dark-700">
                                <th class="text-left py-3 font-medium">Saham</th>
                                <th class="text-right py-3 font-medium">Harga</th>
                                <th class="text-right py-3 font-medium">Perubahan</th>
                                <th class="text-right py-3 font-medium">Volume</th>
                                <th class="text-right py-3 font-medium">Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${stockRow('BBCA', 'Bank Central Asia', 9875, 225, 2.33, '12.5M', '123.4B')}
                            ${stockRow('TLKM', 'Telkom Indonesia', 3980, 120, 3.11, '45.2M', '179.8B')}
                            ${stockRow('BMRI', 'Bank Mandiri', 6425, 150, 2.39, '23.1M', '148.3B')}
                            ${stockRow('ASII', 'Astra International', 5225, 100, 1.95, '18.7M', '97.7B')}
                            ${stockRow('UNVR', 'Unilever Indonesia', 4150, -75, -1.78, '8.3M', '34.4B')}
                            ${stockRow('GOTO', 'GoTo Gojek', 82, 6, 7.89, '892.5M', '73.2B')}
                            ${stockRow('BRIS', 'BSI', 2680, 80, 3.08, '34.6M', '92.7B')}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Market Sentiment -->
            <div class="space-y-4">
                <div class="card p-5">
                    <h3 class="text-lg font-semibold text-white mb-4">Sentimen Pasar</h3>
                    <div class="flex items-center justify-center mb-4">
                        <div class="relative w-32 h-32">
                            <svg class="w-full h-full transform -rotate-90">
                                <circle cx="64" cy="64" r="56" stroke="#334155" stroke-width="8" fill="none"/>
                                <circle cx="64" cy="64" r="56" stroke="#10b981" stroke-width="8" fill="none" stroke-dasharray="352" stroke-dashoffset="105" stroke-linecap="round"/>
                            </svg>
                            <div class="absolute inset-0 flex items-center justify-center flex-col">
                                <span class="text-2xl font-bold text-success">70</span>
                                <span class="text-xs text-dark-400">Bullish</span>
                            </div>
                        </div>
                    </div>
                    <div class="grid grid-cols-3 gap-2 text-center">
                        <div class="bg-dark-800 rounded-lg p-2">
                            <p class="text-lg font-bold stat-up">342</p>
                            <p class="text-xs text-dark-400">Naik</p>
                        </div>
                        <div class="bg-dark-800 rounded-lg p-2">
                            <p class="text-lg font-bold text-warning">85</p>
                            <p class="text-xs text-dark-400">Tetap</p>
                        </div>
                        <div class="bg-dark-800 rounded-lg p-2">
                            <p class="text-lg font-bold stat-down">198</p>
                            <p class="text-xs text-dark-400">Turun</p>
                        </div>
                    </div>
                </div>

                <!-- Sector Performance -->
                <div class="card p-5">
                    <h3 class="text-lg font-semibold text-white mb-4">Sektor Hari Ini</h3>
                    <div class="space-y-3">
                        ${sectorItem('Keuangan', 2.15)}
                        ${sectorItem('Teknologi', 1.82)}
                        ${sectorItem('Konsumer', 0.95)}
                        ${sectorItem('Infrastruktur', 0.42)}
                        ${sectorItem('Energi', -0.67)}
                        ${sectorItem('Properti', -1.23)}
                    </div>
                </div>
            </div>
        </div>

        <!-- Bottom Section -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Recent Signals -->
            <div class="card p-5">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-white">Sinyal Terbaru</h3>
                    <a href="#" onclick="navigateTo('signals')" class="text-primary-400 text-sm hover:underline">Lihat semua</a>
                </div>
                <div class="space-y-3">
                    ${signalItem('BBCA', 'Golden Cross MA50/MA200', 'buy', '10 menit lalu')}
                    ${signalItem('TLKM', 'RSI Oversold Bounce', 'buy', '25 menit lalu')}
                    ${signalItem('UNVR', 'MACD Bearish Crossover', 'sell', '1 jam lalu')}
                    ${signalItem('BMRI', 'Breakout Resistance', 'buy', '2 jam lalu')}
                </div>
            </div>

            <!-- News -->
            <div class="card p-5">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-white">Berita Terkini</h3>
                    <a href="#" onclick="navigateTo('news')" class="text-primary-400 text-sm hover:underline">Lihat semua</a>
                </div>
                <div class="space-y-3">
                    ${newsItem('IHSG Menguat, Asing Net Buy Rp 485 Miliar', 'Market', '30 menit lalu')}
                    ${newsItem('Bank Indonesia Pertahankan Suku Bunga di 5.75%', 'Ekonomi', '1 jam lalu')}
                    ${newsItem('BBCA Cetak Laba Bersih Rp 12.1 T di Q1 2026', 'Emiten', '3 jam lalu')}
                    ${newsItem('GoTo Pangkas Rugi 40% YoY, Saham Melesat', 'Emiten', '5 jam lalu')}
                </div>
            </div>
        </div>
    </div>
    `;
}

function marketCard(name, value, change, percent, isUp, icon) {
    const color = isUp ? 'stat-up' : 'stat-down';
    const arrow = isUp ? 'fa-arrow-up' : 'fa-arrow-down';
    const bgGlow = isUp ? 'from-emerald-500/10 to-transparent' : 'from-red-500/10 to-transparent';
    return `
    <div class="card p-5 relative overflow-hidden">
        <div class="absolute top-0 right-0 w-24 h-24 bg-gradient-to-bl ${bgGlow} rounded-bl-full"></div>
        <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-dark-400">${name}</span>
            <i class="fas ${icon} text-dark-500"></i>
        </div>
        <p class="text-xl font-bold text-white">${value}</p>
        <div class="flex items-center gap-2 mt-1">
            <span class="${color} text-sm font-medium"><i class="fas ${arrow} text-xs"></i> ${change}</span>
            <span class="${color} text-xs">(${percent})</span>
        </div>
    </div>`;
}

function stockRow(code, name, price, change, percent, vol, value) {
    const isUp = change >= 0;
    const color = isUp ? 'stat-up' : 'stat-down';
    const sign = isUp ? '+' : '';
    return `
    <tr class="border-b border-dark-800 hover:bg-dark-800/50 cursor-pointer">
        <td class="py-3">
            <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-dark-700 flex items-center justify-center">
                    <span class="text-xs font-bold text-primary-400">${code.substring(0,2)}</span>
                </div>
                <div>
                    <p class="font-semibold text-white">${code}</p>
                    <p class="text-xs text-dark-400">${name}</p>
                </div>
            </div>
        </td>
        <td class="text-right font-medium text-white">${price.toLocaleString('id-ID')}</td>
        <td class="text-right ${color} font-medium">${sign}${change} (${sign}${percent}%)</td>
        <td class="text-right text-dark-300">${vol}</td>
        <td class="text-right text-dark-300">${value}</td>
    </tr>`;
}

function sectorItem(name, change) {
    const isUp = change >= 0;
    const color = isUp ? 'text-success bg-success/10' : 'text-danger bg-danger/10';
    const sign = isUp ? '+' : '';
    const width = Math.min(Math.abs(change) * 30, 100);
    const barColor = isUp ? 'bg-success' : 'bg-danger';
    return `
    <div class="flex items-center justify-between">
        <span class="text-sm text-dark-200">${name}</span>
        <div class="flex items-center gap-3">
            <div class="w-20 h-1.5 bg-dark-700 rounded-full overflow-hidden">
                <div class="${barColor} h-full rounded-full" style="width:${width}%"></div>
            </div>
            <span class="text-sm font-medium ${color} px-2 py-0.5 rounded">${sign}${change}%</span>
        </div>
    </div>`;
}

function signalItem(code, desc, type, time) {
    const isBuy = type === 'buy';
    const badge = isBuy ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger';
    const label = isBuy ? 'BUY' : 'SELL';
    const icon = isBuy ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down';
    return `
    <div class="flex items-center justify-between p-3 rounded-lg bg-dark-800/50 hover:bg-dark-800">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg ${badge} flex items-center justify-center">
                <i class="fas ${icon} text-sm"></i>
            </div>
            <div>
                <p class="text-sm font-medium text-white">${code} - ${desc}</p>
                <p class="text-xs text-dark-400">${time}</p>
            </div>
        </div>
        <span class="text-xs font-bold ${badge} px-2 py-1 rounded">${label}</span>
    </div>`;
}

function newsItem(title, category, time) {
    return `
    <div class="flex items-start gap-3 p-3 rounded-lg hover:bg-dark-800/50 cursor-pointer">
        <div class="w-2 h-2 rounded-full bg-primary-400 mt-2 flex-shrink-0"></div>
        <div class="flex-1">
            <p class="text-sm text-dark-200 leading-relaxed">${title}</p>
            <div class="flex items-center gap-2 mt-1">
                <span class="text-xs text-primary-400">${category}</span>
                <span class="text-xs text-dark-500">${time}</span>
            </div>
        </div>
    </div>`;
}
