function getBacktestingPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Backtesting</h2>
                <p class="text-dark-400 text-sm mt-1">Simulasi strategi trading pada data historis</p>
            </div>
            <button class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
                <i class="fas fa-play mr-2"></i>Jalankan Backtest
            </button>
        </div>

        <!-- Strategy Config -->
        <div class="card p-5">
            <h3 class="text-sm font-semibold text-dark-300 uppercase tracking-wider mb-4">Konfigurasi Strategi</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Strategi</label>
                    <select class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                        <option>Golden Cross MA</option>
                        <option>RSI Reversal</option>
                        <option>Breakout Volume</option>
                        <option>MACD Crossover</option>
                        <option>Bollinger Bounce</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Saham</label>
                    <input type="text" value="BBCA" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Periode</label>
                    <select class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                        <option>1 Tahun</option>
                        <option>2 Tahun</option>
                        <option>3 Tahun</option>
                        <option>5 Tahun</option>
                    </select>
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Modal Awal</label>
                    <input type="text" value="100,000,000" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">MA Pendek</label>
                    <input type="number" value="20" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">MA Panjang</label>
                    <input type="number" value="50" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Stop Loss (%)</label>
                    <input type="number" value="5" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
                <div>
                    <label class="text-xs text-dark-400 mb-1 block">Take Profit (%)</label>
                    <input type="number" value="15" class="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white">
                </div>
            </div>
        </div>

        <!-- Results -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            ${btMetric('Total Return', '+32.5%', true)}
            ${btMetric('Win Rate', '68.4%', true)}
            ${btMetric('Max Drawdown', '-12.3%', false)}
            ${btMetric('Sharpe Ratio', '1.85', true)}
            ${btMetric('Total Trades', '24', null)}
            ${btMetric('Avg Hold Days', '18', null)}
        </div>

        <!-- Equity Curve -->
        <div class="card p-5">
            <h3 class="text-sm font-semibold text-white mb-4">Equity Curve</h3>
            <div class="h-48 bg-dark-800 rounded-lg relative overflow-hidden">
                <svg class="w-full h-full" viewBox="0 0 800 180" preserveAspectRatio="none">
                    <line x1="0" y1="45" x2="800" y2="45" stroke="#334155" stroke-width="0.5" stroke-dasharray="4"/>
                    <line x1="0" y1="90" x2="800" y2="90" stroke="#334155" stroke-width="0.5" stroke-dasharray="4"/>
                    <line x1="0" y1="135" x2="800" y2="135" stroke="#334155" stroke-width="0.5" stroke-dasharray="4"/>
                    <path d="M0,150 L50,148 L100,145 L150,140 L200,130 L250,125 L300,120 L350,110 L400,115 L450,105 L500,95 L550,85 L600,80 L650,70 L700,55 L750,45 L800,40" fill="none" stroke="#10b981" stroke-width="2.5"/>
                    <path d="M0,150 L50,148 L100,145 L150,140 L200,130 L250,125 L300,120 L350,110 L400,115 L450,105 L500,95 L550,85 L600,80 L650,70 L700,55 L750,45 L800,40 L800,180 L0,180 Z" fill="url(#greenGrad)" opacity="0.2"/>
                    <!-- Buy/Hold comparison -->
                    <path d="M0,150 L50,149 L100,147 L150,144 L200,138 L250,135 L300,130 L350,125 L400,128 L450,122 L500,118 L550,112 L600,108 L650,100 L700,92 L750,85 L800,80" fill="none" stroke="#64748b" stroke-width="1.5" stroke-dasharray="4"/>
                    <defs>
                        <linearGradient id="greenGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="#10b981" stop-opacity="0.4"/>
                            <stop offset="100%" stop-color="#10b981" stop-opacity="0"/>
                        </linearGradient>
                    </defs>
                </svg>
                <div class="absolute top-3 right-3 text-xs space-y-1">
                    <div class="flex items-center gap-2"><div class="w-3 h-0.5 bg-success"></div><span class="text-dark-300">Strategi (+32.5%)</span></div>
                    <div class="flex items-center gap-2"><div class="w-3 h-0.5 bg-dark-500 border-dashed"></div><span class="text-dark-300">Buy & Hold (+18.2%)</span></div>
                </div>
            </div>
        </div>

        <!-- Trade History -->
        <div class="card p-5">
            <h3 class="text-sm font-semibold text-white mb-4">Riwayat Trade</h3>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead>
                        <tr class="text-dark-400 border-b border-dark-700">
                            <th class="text-left py-2 font-medium">#</th>
                            <th class="text-left py-2 font-medium">Entry Date</th>
                            <th class="text-left py-2 font-medium">Exit Date</th>
                            <th class="text-right py-2 font-medium">Entry</th>
                            <th class="text-right py-2 font-medium">Exit</th>
                            <th class="text-right py-2 font-medium">P/L %</th>
                            <th class="text-left py-2 font-medium">Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tradeRow(1, '12 Jan 2026', '28 Jan 2026', 8750, 9200, 'TP Hit')}
                        ${tradeRow(2, '05 Feb 2026', '12 Feb 2026', 9100, 8650, 'SL Hit')}
                        ${tradeRow(3, '20 Feb 2026', '15 Mar 2026', 8800, 9450, 'TP Hit')}
                        ${tradeRow(4, '22 Mar 2026', '05 Apr 2026', 9300, 9800, 'Signal Exit')}
                        ${tradeRow(5, '12 Apr 2026', '—', 9650, 9875, 'Open')}
                    </tbody>
                </table>
            </div>
        </div>
    </div>`;
}

function btMetric(label, value, isPositive) {
    const color = isPositive === true ? 'text-success' : isPositive === false ? 'text-danger' : 'text-white';
    return `
    <div class="card p-4 text-center">
        <p class="text-xs text-dark-400">${label}</p>
        <p class="text-lg font-bold ${color} mt-1">${value}</p>
    </div>`;
}

function tradeRow(num, entry, exit, entryPrice, exitPrice, reason) {
    const pl = ((exitPrice - entryPrice) / entryPrice * 100).toFixed(2);
    const isUp = pl >= 0;
    const color = isUp ? 'stat-up' : 'stat-down';
    const sign = isUp ? '+' : '';
    return `
    <tr class="border-b border-dark-800">
        <td class="py-2 text-dark-400">${num}</td>
        <td class="py-2 text-dark-300">${entry}</td>
        <td class="py-2 text-dark-300">${exit}</td>
        <td class="text-right text-dark-300">${entryPrice.toLocaleString('id-ID')}</td>
        <td class="text-right text-white">${exitPrice.toLocaleString('id-ID')}</td>
        <td class="text-right ${color} font-medium">${sign}${pl}%</td>
        <td class="text-left text-xs text-dark-400">${reason}</td>
    </tr>`;
}
