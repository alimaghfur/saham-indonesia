function getFundamentalPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Analisa Fundamental</h2>
                <p class="text-dark-400 text-sm mt-1">Laporan keuangan, rasio, dan valuasi emiten</p>
            </div>
            <div class="flex items-center gap-2 bg-dark-800 rounded-lg px-3 py-2">
                <i class="fas fa-search text-dark-500 text-sm"></i>
                <input type="text" value="BBCA" class="bg-transparent text-white text-sm focus:outline-none w-20">
            </div>
        </div>

        <!-- Company Header -->
        <div class="card p-5">
            <div class="flex items-center gap-4">
                <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
                    <span class="text-xl font-bold text-white">BCA</span>
                </div>
                <div class="flex-1">
                    <h3 class="text-xl font-bold text-white">Bank Central Asia Tbk (BBCA)</h3>
                    <p class="text-sm text-dark-400">Sektor: Keuangan | Sub: Perbankan | Papan: Utama</p>
                </div>
                <div class="text-right">
                    <p class="text-2xl font-bold text-white">Rp 9,875</p>
                    <p class="text-sm stat-up">+225 (+2.33%)</p>
                </div>
            </div>
        </div>

        <!-- Key Metrics -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            ${metricCard('Market Cap', 'Rp 1,215 T', '')}
            ${metricCard('PER', '22.5x', 'vs Sektor: 15.2x')}
            ${metricCard('PBV', '4.8x', 'vs Sektor: 2.1x')}
            ${metricCard('ROE', '21.3%', 'vs Sektor: 14.5%')}
            ${metricCard('DER', '5.2x', '')}
            ${metricCard('Div Yield', '2.8%', 'Annual')}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Income Statement -->
            <div class="card p-5">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-white">Laba Rugi</h3>
                    <select class="bg-dark-800 border border-dark-600 rounded px-2 py-1 text-xs text-dark-300">
                        <option>Tahunan</option>
                        <option>Kuartalan</option>
                    </select>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="text-dark-400 border-b border-dark-700">
                                <th class="text-left py-2 font-medium">Item</th>
                                <th class="text-right py-2 font-medium">2024</th>
                                <th class="text-right py-2 font-medium">2025</th>
                                <th class="text-right py-2 font-medium">YoY</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${finRow('Pendapatan', '98.2 T', '112.5 T', 14.6)}
                            ${finRow('Laba Operasi', '52.1 T', '59.8 T', 14.8)}
                            ${finRow('Laba Bersih', '42.3 T', '48.7 T', 15.1)}
                            ${finRow('EPS', '350', '403', 15.1)}
                            ${finRow('NPM', '43.1%', '43.3%', 0.5)}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Balance Sheet -->
            <div class="card p-5">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold text-white">Neraca</h3>
                    <select class="bg-dark-800 border border-dark-600 rounded px-2 py-1 text-xs text-dark-300">
                        <option>2025</option>
                        <option>2024</option>
                    </select>
                </div>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm">
                        <thead>
                            <tr class="text-dark-400 border-b border-dark-700">
                                <th class="text-left py-2 font-medium">Item</th>
                                <th class="text-right py-2 font-medium">Nilai</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${simpleFinRow('Total Aset', 'Rp 1,350 T')}
                            ${simpleFinRow('Total Liabilitas', 'Rp 1,125 T')}
                            ${simpleFinRow('Total Ekuitas', 'Rp 225 T')}
                            ${simpleFinRow('DPK', 'Rp 980 T')}
                            ${simpleFinRow('Total Kredit', 'Rp 785 T')}
                            ${simpleFinRow('CAR', '25.8%')}
                            ${simpleFinRow('NPL', '1.2%')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Valuation -->
        <div class="card p-5">
            <h3 class="text-lg font-semibold text-white mb-4">Valuasi</h3>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="text-center p-4 bg-dark-800 rounded-xl">
                    <p class="text-xs text-dark-400 mb-2">DCF Valuation</p>
                    <p class="text-2xl font-bold text-success">Rp 11,200</p>
                    <p class="text-xs text-success mt-1">Upside +13.4%</p>
                </div>
                <div class="text-center p-4 bg-dark-800 rounded-xl">
                    <p class="text-xs text-dark-400 mb-2">Graham Number</p>
                    <p class="text-2xl font-bold text-success">Rp 10,450</p>
                    <p class="text-xs text-success mt-1">Upside +5.8%</p>
                </div>
                <div class="text-center p-4 bg-dark-800 rounded-xl">
                    <p class="text-xs text-dark-400 mb-2">PEG Ratio</p>
                    <p class="text-2xl font-bold text-warning">1.49</p>
                    <p class="text-xs text-warning mt-1">Fairly Valued</p>
                </div>
            </div>
        </div>

        <!-- Comparison -->
        <div class="card p-5">
            <h3 class="text-lg font-semibold text-white mb-4">Perbandingan Sektor Perbankan</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="text-dark-400 border-b border-dark-700">
                            <th class="text-left py-3 font-medium">Emiten</th>
                            <th class="text-right py-3 font-medium">Harga</th>
                            <th class="text-right py-3 font-medium">MCap</th>
                            <th class="text-right py-3 font-medium">PER</th>
                            <th class="text-right py-3 font-medium">PBV</th>
                            <th class="text-right py-3 font-medium">ROE</th>
                            <th class="text-right py-3 font-medium">NPM</th>
                            <th class="text-right py-3 font-medium">DY</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${compRow('BBCA', '9,875', '1,215 T', '22.5x', '4.8x', '21.3%', '43.3%', '2.8%')}
                        ${compRow('BBRI', '5,150', '762 T', '13.2x', '2.5x', '20.1%', '28.5%', '4.2%')}
                        ${compRow('BMRI', '6,425', '600 T', '12.1x', '2.3x', '19.8%', '32.1%', '5.1%')}
                        ${compRow('BBNI', '5,800', '216 T', '10.5x', '1.6x', '16.2%', '26.8%', '5.8%')}
                        ${compRow('BRIS', '2,680', '130 T', '18.3x', '3.2x', '16.7%', '22.4%', '1.5%')}
                    </tbody>
                </table>
            </div>
        </div>
    </div>`;
}

function metricCard(label, value, sub) {
    return `
    <div class="card p-4 text-center">
        <p class="text-xs text-dark-400">${label}</p>
        <p class="text-lg font-bold text-white mt-1">${value}</p>
        ${sub ? `<p class="text-xs text-dark-500 mt-0.5">${sub}</p>` : ''}
    </div>`;
}

function finRow(item, val2024, val2025, yoy) {
    const color = yoy >= 0 ? 'stat-up' : 'stat-down';
    const sign = yoy >= 0 ? '+' : '';
    return `
    <tr class="border-b border-dark-800">
        <td class="py-2 text-dark-300">${item}</td>
        <td class="text-right text-dark-400">${val2024}</td>
        <td class="text-right text-white font-medium">${val2025}</td>
        <td class="text-right ${color} font-medium">${sign}${yoy}%</td>
    </tr>`;
}

function simpleFinRow(item, value) {
    return `
    <tr class="border-b border-dark-800">
        <td class="py-2 text-dark-300">${item}</td>
        <td class="text-right text-white font-medium">${value}</td>
    </tr>`;
}

function compRow(code, price, mcap, per, pbv, roe, npm, dy) {
    return `
    <tr class="border-b border-dark-800 hover:bg-dark-800/50">
        <td class="py-2 font-semibold text-white">${code}</td>
        <td class="text-right text-dark-300">${price}</td>
        <td class="text-right text-dark-300">${mcap}</td>
        <td class="text-right text-dark-300">${per}</td>
        <td class="text-right text-dark-300">${pbv}</td>
        <td class="text-right text-dark-300">${roe}</td>
        <td class="text-right text-dark-300">${npm}</td>
        <td class="text-right text-dark-300">${dy}</td>
    </tr>`;
}
