function getNewsPage() {
    return `
    <div class="space-y-6">
        <div>
            <h2 class="text-2xl font-bold text-white">Berita & Sentimen</h2>
            <p class="text-dark-400 text-sm mt-1">Berita pasar terkini</p>
        </div>
        <div class="card p-8 text-center">
            <i class="fas fa-newspaper text-4xl text-dark-600 mb-4"></i>
            <h3 class="text-lg font-semibold text-white mb-2">Berita Market</h3>
            <p class="text-dark-400 text-sm">Fitur berita membutuhkan integrasi dengan news provider.<br>Sumber data yang tersedia: IDNFinancials, Bisnis.com, CNBC Indonesia.</p>
            <a href="https://www.idnfinancials.com" target="_blank" class="inline-block mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">Buka IDN Financials <i class="fas fa-external-link-alt ml-1"></i></a>
        </div>
    </div>`;
}
