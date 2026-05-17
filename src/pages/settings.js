function getSettingsPage() {
    return `
    <div class="space-y-6">
        <div>
            <h2 class="text-2xl font-bold text-white">Pengaturan</h2>
            <p class="text-dark-400 text-sm mt-1">Konfigurasi aplikasi</p>
        </div>
        <div class="card p-5">
            <h3 class="text-lg font-semibold text-white mb-4">Informasi Aplikasi</h3>
            <div class="space-y-3">
                <div class="flex items-center justify-between py-2 border-b border-dark-800">
                    <span class="text-sm text-dark-300">Versi</span>
                    <span class="text-sm text-white">1.0.0</span>
                </div>
                <div class="flex items-center justify-between py-2 border-b border-dark-800">
                    <span class="text-sm text-dark-300">Sumber Data</span>
                    <span class="text-sm text-success"><i class="fas fa-check-circle mr-1"></i>Yahoo Finance (Real-time)</span>
                </div>
                <div class="flex items-center justify-between py-2 border-b border-dark-800">
                    <span class="text-sm text-dark-300">Delay Data</span>
                    <span class="text-sm text-white">15 menit (standard Yahoo Finance)</span>
                </div>
                <div class="flex items-center justify-between py-2 border-b border-dark-800">
                    <span class="text-sm text-dark-300">Backend</span>
                    <span class="text-sm text-white">Node.js (Pure, tanpa dependencies)</span>
                </div>
                <div class="flex items-center justify-between py-2 border-b border-dark-800">
                    <span class="text-sm text-dark-300">Indikator Teknikal</span>
                    <span class="text-sm text-white">MA, EMA, RSI, MACD, BB, Stochastic</span>
                </div>
            </div>
        </div>
        <div class="card p-5">
            <h3 class="text-lg font-semibold text-white mb-4">API Endpoints</h3>
            <div class="bg-dark-800 rounded-lg p-4 text-xs font-mono text-dark-300 space-y-1">
                <p>GET /api/market/indices - Indeks (IHSG, LQ45, IDX30, JII)</p>
                <p>GET /api/market/top-movers - Top gainers & losers</p>
                <p>GET /api/market/sectors - Performa sektoral</p>
                <p>GET /api/market/summary - Ringkasan pasar</p>
                <p>GET /api/stock/{symbol}/quote - Harga real-time</p>
                <p>GET /api/stock/{symbol}/history - Data historis OHLCV</p>
                <p>GET /api/technical/{symbol}/indicators - Indikator teknikal</p>
                <p>GET /api/technical/{symbol}/chart-data - Data chart</p>
                <p>GET /api/fundamental/{symbol} - Data fundamental</p>
                <p>GET /api/screener/scan - Screener saham</p>
            </div>
        </div>
    </div>`;
}
