function getNewsPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Berita & Sentimen</h2>
                <p class="text-dark-400 text-sm mt-1">Berita pasar terkini dan analisa sentimen</p>
            </div>
        </div>

        <!-- Sentiment Overview -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="card p-5 text-center">
                <p class="text-xs text-dark-400 mb-2">Sentimen Hari Ini</p>
                <div class="text-3xl font-bold text-success">Bullish</div>
                <div class="flex justify-center gap-4 mt-3 text-xs">
                    <span class="text-success"><i class="fas fa-smile mr-1"></i>62%</span>
                    <span class="text-dark-400"><i class="fas fa-meh mr-1"></i>23%</span>
                    <span class="text-danger"><i class="fas fa-frown mr-1"></i>15%</span>
                </div>
            </div>
            <div class="card p-5 text-center">
                <p class="text-xs text-dark-400 mb-2">Fear & Greed Index</p>
                <div class="text-3xl font-bold text-success">68</div>
                <div class="w-full bg-dark-700 rounded-full h-2 mt-3">
                    <div class="bg-gradient-to-r from-danger via-warning to-success h-2 rounded-full" style="width:68%"></div>
                </div>
                <p class="text-xs text-dark-400 mt-2">Greed</p>
            </div>
            <div class="card p-5 text-center">
                <p class="text-xs text-dark-400 mb-2">Foreign Flow (5D)</p>
                <div class="text-3xl font-bold text-success">+2.1 T</div>
                <p class="text-xs text-success mt-2">5 hari Net Buy berturut</p>
            </div>
        </div>

        <!-- News Categories -->
        <div class="flex gap-2 flex-wrap">
            <button class="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-xs">Semua</button>
            <button class="px-3 py-1.5 bg-dark-800 text-dark-300 rounded-lg text-xs hover:bg-dark-700">Market</button>
            <button class="px-3 py-1.5 bg-dark-800 text-dark-300 rounded-lg text-xs hover:bg-dark-700">Emiten</button>
            <button class="px-3 py-1.5 bg-dark-800 text-dark-300 rounded-lg text-xs hover:bg-dark-700">Ekonomi</button>
            <button class="px-3 py-1.5 bg-dark-800 text-dark-300 rounded-lg text-xs hover:bg-dark-700">Regulasi</button>
            <button class="px-3 py-1.5 bg-dark-800 text-dark-300 rounded-lg text-xs hover:bg-dark-700">Global</button>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Main News -->
            <div class="lg:col-span-2 space-y-4">
                ${newsCard('IHSG Menguat 1.24%, Asing Net Buy Rp 485 Miliar di Sesi I', 'Market', '30 menit lalu', 'IHSG ditutup menguat di level 7,432 pada perdagangan Jumat (16/5). Penguatan ditopang oleh aksi beli investor asing yang mencatatkan net buy sebesar Rp 485 miliar.', 'bullish')}
                ${newsCard('Bank Indonesia Pertahankan Suku Bunga Acuan di 5.75%', 'Ekonomi', '1 jam lalu', 'Rapat Dewan Gubernur (RDG) Bank Indonesia memutuskan untuk mempertahankan BI Rate di level 5.75%. Keputusan ini sejalan dengan upaya menjaga stabilitas rupiah.', 'neutral')}
                ${newsCard('BBCA Cetak Laba Bersih Rp 12.1 Triliun di Kuartal I-2026', 'Emiten', '3 jam lalu', 'PT Bank Central Asia Tbk (BBCA) membukukan laba bersih Rp 12.1 triliun pada kuartal pertama 2026, tumbuh 15.3% year-on-year dibandingkan periode sama tahun lalu.', 'bullish')}
                ${newsCard('GoTo Pangkas Rugi Bersih 40% YoY, Pendapatan Naik 22%', 'Emiten', '5 jam lalu', 'PT GoTo Gojek Tokopedia Tbk (GOTO) berhasil memangkas rugi bersih hingga 40% secara tahunan. Pendapatan bersih perseroan naik 22% menjadi Rp 4.8 triliun.', 'bullish')}
                ${newsCard('Rupiah Menguat ke Rp 15,850/USD Ditopang Arus Modal Masuk', 'Ekonomi', '6 jam lalu', 'Nilai tukar rupiah ditutup menguat 0.3% ke level Rp 15,850 per dolar AS. Penguatan ini didorong oleh masuknya arus modal asing ke pasar keuangan domestik.', 'bullish')}
            </div>

            <!-- Sidebar -->
            <div class="space-y-4">
                <!-- Calendar -->
                <div class="card p-5">
                    <h3 class="text-sm font-semibold text-white mb-3">Kalender Mendatang</h3>
                    <div class="space-y-3">
                        ${calendarItem('19 Mei', 'BBRI', 'Dividen - Cum Date', 'event')}
                        ${calendarItem('20 Mei', 'TLKM', 'Earning Report Q1', 'earning')}
                        ${calendarItem('22 Mei', 'ASII', 'RUPST', 'event')}
                        ${calendarItem('25 Mei', 'BMRI', 'Dividen - Payment', 'dividend')}
                        ${calendarItem('28 Mei', 'BRIS', 'Earning Report Q1', 'earning')}
                    </div>
                </div>

                <!-- Trending Topics -->
                <div class="card p-5">
                    <h3 class="text-sm font-semibold text-white mb-3">Trending</h3>
                    <div class="space-y-2">
                        <div class="flex items-center gap-2 text-sm">
                            <span class="text-dark-500 font-medium">1</span>
                            <span class="text-dark-200">#BBCA</span>
                            <span class="text-xs text-dark-500 ml-auto">2.4k mentions</span>
                        </div>
                        <div class="flex items-center gap-2 text-sm">
                            <span class="text-dark-500 font-medium">2</span>
                            <span class="text-dark-200">#GOTO</span>
                            <span class="text-xs text-dark-500 ml-auto">1.8k mentions</span>
                        </div>
                        <div class="flex items-center gap-2 text-sm">
                            <span class="text-dark-500 font-medium">3</span>
                            <span class="text-dark-200">#SukuBunga</span>
                            <span class="text-xs text-dark-500 ml-auto">1.2k mentions</span>
                        </div>
                        <div class="flex items-center gap-2 text-sm">
                            <span class="text-dark-500 font-medium">4</span>
                            <span class="text-dark-200">#IHSG</span>
                            <span class="text-xs text-dark-500 ml-auto">980 mentions</span>
                        </div>
                        <div class="flex items-center gap-2 text-sm">
                            <span class="text-dark-500 font-medium">5</span>
                            <span class="text-dark-200">#Rupiah</span>
                            <span class="text-xs text-dark-500 ml-auto">756 mentions</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>`;
}

function newsCard(title, category, time, desc, sentiment) {
    const sentColor = sentiment === 'bullish' ? 'text-success' : sentiment === 'bearish' ? 'text-danger' : 'text-dark-400';
    const sentIcon = sentiment === 'bullish' ? 'fa-arrow-trend-up' : sentiment === 'bearish' ? 'fa-arrow-trend-down' : 'fa-minus';
    return `
    <div class="card p-5 hover:border-dark-500 cursor-pointer">
        <div class="flex items-start justify-between mb-2">
            <span class="text-xs text-primary-400 font-medium">${category}</span>
            <div class="flex items-center gap-2">
                <span class="${sentColor} text-xs"><i class="fas ${sentIcon}"></i></span>
                <span class="text-xs text-dark-500">${time}</span>
            </div>
        </div>
        <h4 class="text-base font-semibold text-white mb-2">${title}</h4>
        <p class="text-sm text-dark-400 leading-relaxed">${desc}</p>
    </div>`;
}

function calendarItem(date, code, event, type) {
    const colors = { event: 'text-primary-400 bg-primary-400/10', earning: 'text-amber-400 bg-amber-400/10', dividend: 'text-success bg-success/10' };
    const c = colors[type] || colors.event;
    return `
    <div class="flex items-center gap-3">
        <div class="text-center w-12">
            <p class="text-xs text-dark-400">${date}</p>
        </div>
        <div class="flex-1">
            <p class="text-sm text-white font-medium">${code}</p>
            <p class="text-xs text-dark-400">${event}</p>
        </div>
        <span class="text-xs ${c} px-2 py-0.5 rounded">${type}</span>
    </div>`;
}
