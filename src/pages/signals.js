function getSignalsPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Signal & Alert</h2>
                <p class="text-dark-400 text-sm mt-1">Sinyal trading otomatis berdasarkan indikator teknikal</p>
            </div>
            <button class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
                <i class="fas fa-plus mr-2"></i>Buat Alert
            </button>
        </div>

        <!-- Signal Summary -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div class="card p-4 border-l-4 border-l-success">
                <p class="text-xs text-dark-400">Strong Buy</p>
                <p class="text-2xl font-bold text-success">12</p>
                <p class="text-xs text-dark-500 mt-1">saham hari ini</p>
            </div>
            <div class="card p-4 border-l-4 border-l-emerald-400">
                <p class="text-xs text-dark-400">Buy</p>
                <p class="text-2xl font-bold text-emerald-400">28</p>
                <p class="text-xs text-dark-500 mt-1">saham hari ini</p>
            </div>
            <div class="card p-4 border-l-4 border-l-warning">
                <p class="text-xs text-dark-400">Neutral</p>
                <p class="text-2xl font-bold text-warning">45</p>
                <p class="text-xs text-dark-500 mt-1">saham hari ini</p>
            </div>
            <div class="card p-4 border-l-4 border-l-danger">
                <p class="text-xs text-dark-400">Sell</p>
                <p class="text-2xl font-bold text-danger">18</p>
                <p class="text-xs text-dark-500 mt-1">saham hari ini</p>
            </div>
        </div>

        <!-- Active Alerts -->
        <div class="card p-5">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-white">Alert Aktif</h3>
                <span class="text-xs text-dark-400">5 alert aktif</span>
            </div>
            <div class="space-y-3">
                ${alertItem('BBCA', 'Harga > 10,000', 'Breakout target', true)}
                ${alertItem('TLKM', 'RSI < 30', 'Oversold entry', true)}
                ${alertItem('BMRI', 'Volume > 3x avg', 'Volume spike', true)}
                ${alertItem('ASII', 'MACD Cross Up', 'Bullish signal', true)}
                ${alertItem('GOTO', 'Harga < 75', 'Stop loss', true)}
            </div>
        </div>

        <!-- Recent Signals -->
        <div class="card p-5">
            <div class="flex items-center justify-between mb-4">
                <h3 class="text-lg font-semibold text-white">Sinyal Terbaru</h3>
                <div class="flex gap-2">
                    <button class="px-3 py-1 text-xs rounded bg-primary-600 text-white">Semua</button>
                    <button class="px-3 py-1 text-xs rounded bg-dark-700 text-dark-300">Buy</button>
                    <button class="px-3 py-1 text-xs rounded bg-dark-700 text-dark-300">Sell</button>
                </div>
            </div>
            <div class="space-y-2">
                ${signalDetailItem('BBCA', 'Golden Cross MA50/MA200', 'buy', 'strong', '10 menit lalu', '9,875', 'MA50 memotong MA200 ke atas, konfirmasi trend bullish jangka menengah')}
                ${signalDetailItem('TLKM', 'RSI Oversold Bounce', 'buy', 'moderate', '25 menit lalu', '3,980', 'RSI naik dari zona oversold (28) ke 35, potensi rebound')}
                ${signalDetailItem('BMRI', 'Breakout Resistance 6,400', 'buy', 'strong', '45 menit lalu', '6,425', 'Harga breakout resistance dengan volume tinggi 2.1x average')}
                ${signalDetailItem('UNVR', 'MACD Bearish Crossover', 'sell', 'moderate', '1 jam lalu', '4,150', 'MACD line memotong signal line ke bawah')}
                ${signalDetailItem('GOTO', 'Volume Anomaly', 'buy', 'weak', '1.5 jam lalu', '82', 'Volume 4.5x diatas rata-rata 20 hari')}
                ${signalDetailItem('BRIS', 'Stochastic Overbought', 'sell', 'weak', '2 jam lalu', '2,680', 'Stochastic di zona 85, potensi koreksi jangka pendek')}
                ${signalDetailItem('ASII', 'Bullish Engulfing', 'buy', 'moderate', '3 jam lalu', '5,225', 'Candlestick pattern bullish engulfing pada support')}
            </div>
        </div>
    </div>`;
}

function alertItem(code, condition, note, active) {
    return `
    <div class="flex items-center justify-between p-3 bg-dark-800 rounded-lg">
        <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded bg-primary-600/20 flex items-center justify-center">
                <i class="fas fa-bell text-primary-400 text-sm"></i>
            </div>
            <div>
                <p class="text-sm font-medium text-white">${code} - ${condition}</p>
                <p class="text-xs text-dark-400">${note}</p>
            </div>
        </div>
        <div class="flex items-center gap-3">
            <div class="w-10 h-5 ${active ? 'bg-primary-600' : 'bg-dark-600'} rounded-full relative cursor-pointer">
                <div class="w-4 h-4 bg-white rounded-full absolute top-0.5 ${active ? 'right-0.5' : 'left-0.5'} transition"></div>
            </div>
            <button class="text-dark-500 hover:text-danger"><i class="fas fa-trash text-xs"></i></button>
        </div>
    </div>`;
}

function signalDetailItem(code, title, type, strength, time, price, description) {
    const isBuy = type === 'buy';
    const badge = isBuy ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger';
    const label = isBuy ? 'BUY' : 'SELL';
    const icon = isBuy ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down';
    const strengthColor = strength === 'strong' ? 'text-success' : strength === 'moderate' ? 'text-warning' : 'text-dark-400';
    const strengthLabel = strength === 'strong' ? 'Kuat' : strength === 'moderate' ? 'Sedang' : 'Lemah';
    return `
    <div class="p-4 bg-dark-800/50 rounded-lg hover:bg-dark-800 border border-dark-700 hover:border-dark-600 transition">
        <div class="flex items-start justify-between">
            <div class="flex items-start gap-3">
                <div class="w-10 h-10 rounded-lg ${badge} flex items-center justify-center mt-0.5">
                    <i class="fas ${icon}"></i>
                </div>
                <div>
                    <div class="flex items-center gap-2">
                        <span class="font-bold text-white">${code}</span>
                        <span class="text-xs ${badge} px-2 py-0.5 rounded font-bold">${label}</span>
                        <span class="text-xs ${strengthColor}"><i class="fas fa-signal mr-1"></i>${strengthLabel}</span>
                    </div>
                    <p class="text-sm text-dark-200 mt-1">${title}</p>
                    <p class="text-xs text-dark-400 mt-1">${description}</p>
                </div>
            </div>
            <div class="text-right">
                <p class="text-sm font-medium text-white">Rp ${price}</p>
                <p class="text-xs text-dark-500">${time}</p>
            </div>
        </div>
    </div>`;
}
