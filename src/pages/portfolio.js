function getPortfolioPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Portfolio</h2>
                <p class="text-dark-400 text-sm mt-1">Tracking performa investasi Anda (data disimpan lokal)</p>
            </div>
            <button class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">
                <i class="fas fa-plus mr-2"></i>Tambah Transaksi
            </button>
        </div>
        <div class="card p-8 text-center">
            <i class="fas fa-briefcase text-4xl text-dark-600 mb-4"></i>
            <h3 class="text-lg font-semibold text-white mb-2">Portfolio Kosong</h3>
            <p class="text-dark-400 text-sm mb-4">Tambahkan transaksi beli/jual untuk mulai tracking portfolio Anda.</p>
            <p class="text-xs text-dark-500">Fitur ini akan menyimpan data di browser (localStorage).<br>Harga saham akan di-update real-time dari TradingView.</p>
        </div>
    </div>`;
}
