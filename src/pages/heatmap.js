function getHeatmapPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Heatmap & Sektoral</h2>
                <p class="text-dark-400 text-sm mt-1">Visualisasi pergerakan seluruh pasar</p>
            </div>
            <div class="flex gap-2">
                <select class="bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                    <option>Market Cap</option>
                    <option>Volume</option>
                    <option>Performance</option>
                </select>
                <select class="bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                    <option>Hari ini</option>
                    <option>1 Minggu</option>
                    <option>1 Bulan</option>
                </select>
            </div>
        </div>

        <!-- Heatmap Grid -->
        <div class="card p-5">
            <h3 class="text-sm font-semibold text-white mb-4">Market Heatmap</h3>
            <div class="grid grid-cols-6 md:grid-cols-8 lg:grid-cols-12 gap-1">
                ${heatmapCell('BBCA', 2.33, 5)}
                ${heatmapCell('BBRI', 1.57, 4)}
                ${heatmapCell('BMRI', 2.39, 3)}
                ${heatmapCell('TLKM', 3.11, 3)}
                ${heatmapCell('ASII', 1.95, 2)}
                ${heatmapCell('UNVR', -1.78, 2)}
                ${heatmapCell('HMSP', -0.95, 2)}
                ${heatmapCell('GOTO', 7.89, 2)}
                ${heatmapCell('BRIS', 3.08, 2)}
                ${heatmapCell('BBNI', 1.82, 2)}
                ${heatmapCell('ICBP', 0.89, 1)}
                ${heatmapCell('INDF', 0.45, 1)}
                ${heatmapCell('KLBF', -0.67, 1)}
                ${heatmapCell('ACES', 1.35, 1)}
                ${heatmapCell('ANTM', -2.11, 1)}
                ${heatmapCell('PGAS', 1.25, 1)}
                ${heatmapCell('SMGR', -0.55, 1)}
                ${heatmapCell('PTBA', 0.78, 1)}
                ${heatmapCell('MDKA', 2.45, 1)}
                ${heatmapCell('EMTK', -1.35, 1)}
                ${heatmapCell('BUKA', 4.55, 1)}
                ${heatmapCell('ARTO', -3.21, 1)}
                ${heatmapCell('CPIN', 0.92, 1)}
                ${heatmapCell('EXCL', 1.68, 1)}
            </div>
            <div class="flex items-center justify-center mt-4 gap-2 text-xs text-dark-400">
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-red-700 rounded"></div><span>-5%</span></div>
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-red-500 rounded"></div><span>-3%</span></div>
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-red-400/60 rounded"></div><span>-1%</span></div>
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-dark-600 rounded"></div><span>0%</span></div>
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-green-400/60 rounded"></div><span>+1%</span></div>
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-green-500 rounded"></div><span>+3%</span></div>
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-green-700 rounded"></div><span>+5%</span></div>
            </div>
        </div>

        <!-- Sector Performance -->
        <div class="card p-5">
            <h3 class="text-sm font-semibold text-white mb-4">Performa Sektoral</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                ${sectorCard('Keuangan', 2.15, ['BBCA +2.33%', 'BMRI +2.39%', 'BBRI +1.57%'])}
                ${sectorCard('Teknologi', 1.82, ['GOTO +7.89%', 'BUKA +4.55%', 'EMTK -1.35%'])}
                ${sectorCard('Konsumer', 0.95, ['ICBP +0.89%', 'INDF +0.45%', 'UNVR -1.78%'])}
                ${sectorCard('Telekomunikasi', 1.45, ['TLKM +3.11%', 'EXCL +1.68%', 'ISAT +0.55%'])}
                ${sectorCard('Energi & Tambang', -0.67, ['PTBA +0.78%', 'MDKA +2.45%', 'ANTM -2.11%'])}
                ${sectorCard('Infrastruktur', 0.42, ['PGAS +1.25%', 'JSMR +0.32%', 'SMGR -0.55%'])}
            </div>
        </div>

        <!-- Sector Rotation -->
        <div class="card p-5">
            <h3 class="text-sm font-semibold text-white mb-4">Rotasi Sektoral (30 Hari)</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="text-dark-400 border-b border-dark-700">
                            <th class="text-left py-3 font-medium">Sektor</th>
                            <th class="text-right py-3 font-medium">1D</th>
                            <th class="text-right py-3 font-medium">1W</th>
                            <th class="text-right py-3 font-medium">1M</th>
                            <th class="text-right py-3 font-medium">3M</th>
                            <th class="text-left py-3 font-medium">Trend</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rotationRow('Keuangan', 2.15, 4.32, 8.75, 12.3, 'up')}
                        ${rotationRow('Teknologi', 1.82, 3.45, 6.21, 15.8, 'up')}
                        ${rotationRow('Konsumer', 0.95, 1.23, 3.45, 5.2, 'up')}
                        ${rotationRow('Telekomunikasi', 1.45, 2.87, 5.12, 8.9, 'up')}
                        ${rotationRow('Energi & Tambang', -0.67, -1.23, -3.45, -5.8, 'down')}
                        ${rotationRow('Infrastruktur', 0.42, 0.85, 2.13, 4.1, 'up')}
                        ${rotationRow('Properti', -1.23, -2.45, -4.67, -8.2, 'down')}
                        ${rotationRow('Kesehatan', 0.78, 1.56, 4.23, 7.5, 'up')}
                    </tbody>
                </table>
            </div>
        </div>
    </div>`;
}

function heatmapCell(code, change, size) {
    const intensity = Math.min(Math.abs(change) / 5, 1);
    let bg;
    if (change > 0) {
        const g = Math.round(100 + intensity * 155);
        bg = `rgba(16, ${g}, 80, ${0.3 + intensity * 0.5})`;
    } else if (change < 0) {
        const r = Math.round(100 + intensity * 155);
        bg = `rgba(${r}, 40, 40, ${0.3 + intensity * 0.5})`;
    } else {
        bg = 'rgba(51, 65, 85, 0.5)';
    }
    const span = size > 2 ? `col-span-${size > 4 ? 3 : 2} row-span-2` : size > 1 ? 'col-span-2 row-span-2' : '';
    const textSize = size > 2 ? 'text-sm' : 'text-xs';
    const sign = change >= 0 ? '+' : '';
    return `
    <div class="${span} rounded-lg p-2 flex flex-col items-center justify-center cursor-pointer hover:opacity-80 transition" style="background:${bg}; min-height:${size > 1 ? '80px' : '50px'}">
        <span class="${textSize} font-bold text-white">${code}</span>
        <span class="text-xs text-white/80">${sign}${change}%</span>
    </div>`;
}

function sectorCard(name, change, stocks) {
    const isUp = change >= 0;
    const color = isUp ? 'text-success border-success/30' : 'text-danger border-danger/30';
    const sign = isUp ? '+' : '';
    const bg = isUp ? 'bg-success/5' : 'bg-danger/5';
    return `
    <div class="p-4 rounded-xl border border-dark-700 ${bg} hover:border-dark-500 transition">
        <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-medium text-white">${name}</span>
            <span class="text-sm font-bold ${color}">${sign}${change}%</span>
        </div>
        <div class="space-y-1">
            ${stocks.map(s => `<p class="text-xs text-dark-400">${s}</p>`).join('')}
        </div>
    </div>`;
}

function rotationRow(sector, d1, w1, m1, m3, trend) {
    const trendIcon = trend === 'up' ? 'fa-arrow-trend-up text-success' : 'fa-arrow-trend-down text-danger';
    return `
    <tr class="border-b border-dark-800">
        <td class="py-2 text-white font-medium">${sector}</td>
        <td class="text-right ${d1 >= 0 ? 'stat-up' : 'stat-down'}">${d1 >= 0 ? '+' : ''}${d1}%</td>
        <td class="text-right ${w1 >= 0 ? 'stat-up' : 'stat-down'}">${w1 >= 0 ? '+' : ''}${w1}%</td>
        <td class="text-right ${m1 >= 0 ? 'stat-up' : 'stat-down'}">${m1 >= 0 ? '+' : ''}${m1}%</td>
        <td class="text-right ${m3 >= 0 ? 'stat-up' : 'stat-down'}">${m3 >= 0 ? '+' : ''}${m3}%</td>
        <td><i class="fas ${trendIcon}"></i></td>
    </tr>`;
}
