async function getHeatmapPage() {
    const data = await fetchAPI('/market/top-movers?limit=30');
    const allStocks = [...(data?.gainers || []), ...(data?.losers || [])];
    const sectorsData = await fetchAPI('/market/sectors');
    const sectors = sectorsData?.sectors || [];

    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Heatmap & Sektoral</h2>
                <p class="text-dark-400 text-sm mt-1">Data real-time pergerakan pasar</p>
            </div>
        </div>

        <div class="card p-5">
            <h3 class="text-sm font-semibold text-white mb-4">Market Heatmap</h3>
            <div class="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-1">
                ${allStocks.map(s => heatCell(s)).join('')}
            </div>
            <div class="flex items-center justify-center mt-4 gap-2 text-xs text-dark-400">
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-red-600 rounded"></div><span>&lt;-3%</span></div>
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-red-400/60 rounded"></div><span>-1%</span></div>
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-dark-600 rounded"></div><span>0%</span></div>
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-green-400/60 rounded"></div><span>+1%</span></div>
                <div class="flex items-center gap-1"><div class="w-4 h-3 bg-green-600 rounded"></div><span>&gt;+3%</span></div>
            </div>
        </div>

        <div class="card p-5">
            <h3 class="text-sm font-semibold text-white mb-4">Performa Sektoral</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                ${sectors.map(s => sectorCardHeat(s)).join('')}
            </div>
        </div>
    </div>`;
}

function heatCell(s) {
    const change = s.change_pct || 0;
    const intensity = Math.min(Math.abs(change) / 5, 1);
    let bg;
    if (change > 0) bg = `rgba(16, ${Math.round(100 + intensity * 155)}, 80, ${0.3 + intensity * 0.5})`;
    else if (change < 0) bg = `rgba(${Math.round(100 + intensity * 155)}, 40, 40, ${0.3 + intensity * 0.5})`;
    else bg = 'rgba(51,65,85,0.5)';
    const sign = change >= 0 ? '+' : '';
    return `
    <div class="rounded-lg p-2 flex flex-col items-center justify-center cursor-pointer hover:opacity-80" style="background:${bg};min-height:60px">
        <span class="text-xs font-bold text-white">${s.symbol}</span>
        <span class="text-xs text-white/80">${sign}${change}%</span>
    </div>`;
}

function sectorCardHeat(s) {
    const isUp = s.change_pct >= 0;
    const color = isUp ? 'text-success' : 'text-danger';
    const bg = isUp ? 'bg-success/5' : 'bg-danger/5';
    const sign = isUp ? '+' : '';
    return `
    <div class="p-4 rounded-xl border border-dark-700 ${bg}">
        <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-white">${s.sector}</span>
            <span class="text-sm font-bold ${color}">${sign}${s.change_pct}%</span>
        </div>
        <div class="space-y-1">
            ${(s.stocks || []).slice(0, 3).map(st => `<p class="text-xs text-dark-400">${st.symbol} ${st.change_pct >= 0 ? '+' : ''}${st.change_pct}%</p>`).join('')}
        </div>
    </div>`;
}
