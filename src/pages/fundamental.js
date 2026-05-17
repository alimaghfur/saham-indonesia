let fundSymbol = 'BBCA';

async function getFundamentalPage() {
    const data = await fetchAPI(`/fundamental/${fundSymbol}`);
    if (!data) return '<div class="text-center text-dark-400 py-12">Gagal memuat data</div>';

    const r = data.ratios || {};
    const g = data.growth || {};
    const m = data.margins || {};
    const v = data.valuation || {};

    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Analisa Fundamental</h2>
                <p class="text-dark-400 text-sm mt-1">Data real dari Yahoo Finance</p>
            </div>
            <div class="flex items-center gap-2 bg-dark-800 rounded-lg px-3 py-2">
                <i class="fas fa-search text-dark-500 text-sm"></i>
                <input id="fund-input" type="text" value="${fundSymbol}" class="bg-transparent text-white text-sm focus:outline-none w-20 uppercase" onkeydown="if(event.key==='Enter')changeFundSymbol()">
                <button onclick="changeFundSymbol()" class="text-primary-400 text-sm"><i class="fas fa-arrow-right"></i></button>
            </div>
        </div>

        <!-- Company Header -->
        <div class="card p-5">
            <div class="flex items-center gap-4">
                <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center">
                    <span class="text-lg font-bold text-white">${fundSymbol.substring(0,3)}</span>
                </div>
                <div class="flex-1">
                    <h3 class="text-xl font-bold text-white">${data.name || fundSymbol} (${data.symbol})</h3>
                    <p class="text-sm text-dark-400">Sektor: ${data.sector || '-'} | Industri: ${data.industry || '-'}</p>
                </div>
                <div class="text-right">
                    <p class="text-lg font-bold text-dark-300">MCap: ${formatRupiah(data.market_cap)}</p>
                </div>
            </div>
        </div>

        <!-- Ratios -->
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
            ${metricCard('PER', r.pe_ratio ? r.pe_ratio + 'x' : '-')}
            ${metricCard('PBV', r.pb_ratio ? r.pb_ratio + 'x' : '-')}
            ${metricCard('ROE', r.roe ? r.roe + '%' : '-')}
            ${metricCard('ROA', r.roa ? r.roa + '%' : '-')}
            ${metricCard('DER', r.debt_to_equity ? r.debt_to_equity + 'x' : '-')}
            ${metricCard('Div Yield', r.dividend_yield ? r.dividend_yield + '%' : '-')}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- Growth -->
            <div class="card p-5">
                <h3 class="text-lg font-semibold text-white mb-4">Pertumbuhan</h3>
                <div class="space-y-3">
                    ${growthRow('Revenue Growth', g.revenue_growth)}
                    ${growthRow('Earnings Growth', g.earnings_growth)}
                </div>
            </div>

            <!-- Margins -->
            <div class="card p-5">
                <h3 class="text-lg font-semibold text-white mb-4">Margin</h3>
                <div class="space-y-3">
                    ${marginRow('Gross Margin', m.gross_margin)}
                    ${marginRow('Operating Margin', m.operating_margin)}
                    ${marginRow('Net Profit Margin', m.profit_margin)}
                </div>
            </div>
        </div>

        <!-- Valuation -->
        <div class="card p-5">
            <h3 class="text-lg font-semibold text-white mb-4">Valuasi</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                ${metricCard('EV/Revenue', v.ev_to_revenue ? v.ev_to_revenue.toFixed(2) + 'x' : '-')}
                ${metricCard('EV/EBITDA', v.ev_to_ebitda ? v.ev_to_ebitda.toFixed(2) + 'x' : '-')}
                ${metricCard('PEG Ratio', v.peg_ratio ? v.peg_ratio.toFixed(2) : '-')}
                ${metricCard('Payout Ratio', r.payout_ratio ? r.payout_ratio + '%' : '-')}
            </div>
        </div>
    </div>`;
}

function changeFundSymbol() {
    const input = document.getElementById('fund-input');
    if (input && input.value.trim()) {
        fundSymbol = input.value.trim().toUpperCase();
        navigateTo('fundamental');
    }
}

function metricCard(label, value) {
    return `
    <div class="card p-4 text-center">
        <p class="text-xs text-dark-400">${label}</p>
        <p class="text-lg font-bold text-white mt-1">${value}</p>
    </div>`;
}

function growthRow(label, value) {
    const isUp = value && value > 0;
    const color = value == null ? 'text-dark-400' : isUp ? 'stat-up' : 'stat-down';
    const display = value != null ? (value > 0 ? '+' : '') + value + '%' : '-';
    return `
    <div class="flex items-center justify-between py-2 border-b border-dark-800">
        <span class="text-sm text-dark-300">${label}</span>
        <span class="text-sm font-bold ${color}">${display}</span>
    </div>`;
}

function marginRow(label, value) {
    const display = value != null ? value + '%' : '-';
    const width = value ? Math.min(value, 100) : 0;
    return `
    <div>
        <div class="flex items-center justify-between mb-1">
            <span class="text-sm text-dark-300">${label}</span>
            <span class="text-sm font-bold text-white">${display}</span>
        </div>
        <div class="w-full h-2 bg-dark-700 rounded-full">
            <div class="h-2 bg-primary-500 rounded-full" style="width:${width}%"></div>
        </div>
    </div>`;
}
