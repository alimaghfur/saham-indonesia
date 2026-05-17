let techSymbol = 'BBCA';

async function getTechnicalPage() {
    const [indicators, chartData] = await Promise.all([
        fetchAPI(`/technical/${techSymbol}/indicators`),
        fetchAPI(`/technical/${techSymbol}/chart-data?period=3mo`),
    ]);

    const ind = indicators?.indicators || {};
    const signals = indicators?.signals || [];
    const sr = indicators?.support_resistance || {};
    const score = indicators?.score || 5;
    const rec = indicators?.recommendation || 'Neutral';
    const candles = chartData?.data || [];

    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <h2 class="text-2xl font-bold text-white">Analisa Teknikal</h2>
        </div>

        <!-- Stock Selector -->
        <div class="card p-4">
            <div class="flex flex-wrap items-center gap-4">
                <div class="flex items-center gap-2">
                    <input id="tech-symbol-input" type="text" value="${techSymbol}" class="w-20 bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-white font-bold uppercase" onkeydown="if(event.key==='Enter')changeTechSymbol()">
                    <button onclick="changeTechSymbol()" class="px-3 py-2 bg-primary-600 text-white rounded-lg text-sm"><i class="fas fa-search"></i></button>
                </div>
                <div class="flex items-center gap-2 ml-4">
                    <span class="text-2xl font-bold text-white">${indicators?.price ? indicators.price.toLocaleString('id-ID') : '-'}</span>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <!-- Chart -->
            <div class="lg:col-span-3 space-y-4">
                <div class="card p-5">
                    <h4 class="text-sm font-medium text-dark-300 mb-3">Candlestick Chart (3 Bulan) - Data Real</h4>
                    <div class="h-72 bg-dark-800 rounded-lg overflow-hidden relative" id="chart-container">
                        ${renderSVGChart(candles)}
                    </div>
                </div>

                <!-- Indicators Panels -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="card p-4">
                        <h4 class="text-sm font-medium text-dark-300 mb-2">RSI (14)</h4>
                        <div class="flex items-center justify-between">
                            <div class="flex-1 h-3 bg-dark-700 rounded-full overflow-hidden mr-3">
                                <div class="${ind.rsi > 70 ? 'bg-danger' : ind.rsi < 30 ? 'bg-success' : 'bg-primary-500'} h-full rounded-full" style="width:${ind.rsi || 50}%"></div>
                            </div>
                            <span class="text-lg font-bold ${ind.rsi > 70 ? 'text-danger' : ind.rsi < 30 ? 'text-success' : 'text-white'}">${ind.rsi || '-'}</span>
                        </div>
                        <p class="text-xs text-dark-400 mt-1">${ind.rsi > 70 ? 'Overbought - potensi turun' : ind.rsi < 30 ? 'Oversold - potensi naik' : 'Netral'}</p>
                    </div>
                    <div class="card p-4">
                        <h4 class="text-sm font-medium text-dark-300 mb-2">MACD</h4>
                        <div class="flex items-center gap-4">
                            <div><span class="text-xs text-dark-400">MACD:</span> <span class="text-sm font-bold text-primary-400">${ind.macd || '-'}</span></div>
                            <div><span class="text-xs text-dark-400">Signal:</span> <span class="text-sm font-bold text-danger">${ind.macd_signal || '-'}</span></div>
                            <div><span class="text-xs text-dark-400">Hist:</span> <span class="text-sm font-bold ${(ind.macd_histogram || 0) >= 0 ? 'stat-up' : 'stat-down'}">${ind.macd_histogram || '-'}</span></div>
                        </div>
                        <p class="text-xs text-dark-400 mt-1">${(ind.macd || 0) > (ind.macd_signal || 0) ? 'Bullish - MACD di atas signal' : 'Bearish - MACD di bawah signal'}</p>
                    </div>
                </div>
            </div>

            <!-- Right Panel -->
            <div class="space-y-4">
                <div class="card p-4">
                    <h4 class="text-sm font-semibold text-white mb-3">Indikator</h4>
                    <div class="space-y-2">
                        ${indicatorRow('MA20', ind.ma20, indicators?.price > ind.ma20)}
                        ${indicatorRow('MA50', ind.ma50, indicators?.price > ind.ma50)}
                        ${indicatorRow('MA200', ind.ma200, indicators?.price > ind.ma200)}
                        ${indicatorRow('RSI', ind.rsi, ind.rsi < 70)}
                        ${indicatorRow('Stochastic K', ind.stochastic_k, ind.stochastic_k < 80)}
                        ${indicatorRow('BB Upper', ind.bb_upper, null)}
                        ${indicatorRow('BB Lower', ind.bb_lower, null)}
                        ${indicatorRow('Vol Ratio', ind.volume_ratio ? ind.volume_ratio + 'x' : '-', ind.volume_ratio > 1)}
                    </div>
                </div>

                <div class="card p-4">
                    <h4 class="text-sm font-semibold text-white mb-3">Support & Resistance</h4>
                    <div class="space-y-2">
                        ${(sr.resistances || []).map((r, i) => `<div class="flex justify-between text-xs"><span class="text-dark-400">R${i+1}</span><span class="text-danger font-medium">${r?.toLocaleString('id-ID')}</span></div>`).join('')}
                        <div class="flex justify-between text-xs bg-primary-600/20 p-1.5 rounded"><span class="text-primary-400 font-medium">Harga</span><span class="text-white font-bold">${indicators?.price?.toLocaleString('id-ID') || '-'}</span></div>
                        ${(sr.supports || []).map((s, i) => `<div class="flex justify-between text-xs"><span class="text-dark-400">S${i+1}</span><span class="text-success font-medium">${s?.toLocaleString('id-ID')}</span></div>`).join('')}
                    </div>
                </div>

                <div class="card p-4 text-center">
                    <h4 class="text-sm font-semibold text-white mb-2">Skor Teknikal</h4>
                    <div class="text-4xl font-bold ${score >= 7 ? 'text-success' : score >= 4 ? 'text-warning' : 'text-danger'}">${score}</div>
                    <div class="text-xs text-dark-400 mt-1">dari 10 - ${rec}</div>
                    <div class="w-full bg-dark-700 rounded-full h-2 mt-3">
                        <div class="bg-gradient-to-r ${score >= 7 ? 'from-success to-emerald-400' : score >= 4 ? 'from-warning to-amber-400' : 'from-danger to-red-400'} h-2 rounded-full" style="width:${score * 10}%"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>`;
}

function changeTechSymbol() {
    const input = document.getElementById('tech-symbol-input');
    if (input && input.value.trim()) {
        techSymbol = input.value.trim().toUpperCase();
        navigateTo('technical');
    }
}

function indicatorRow(name, value, isBullish) {
    const display = value != null ? (typeof value === 'number' ? value.toLocaleString('id-ID') : value) : '-';
    const color = isBullish === true ? 'text-success' : isBullish === false ? 'text-danger' : 'text-dark-300';
    const icon = isBullish === true ? 'fa-check-circle text-success' : isBullish === false ? 'fa-times-circle text-danger' : 'fa-minus-circle text-dark-500';
    return `
    <div class="flex items-center justify-between py-1.5 border-b border-dark-800">
        <span class="text-xs text-dark-400">${name}</span>
        <div class="flex items-center gap-2">
            <span class="text-xs ${color} font-medium">${display}</span>
            <i class="fas ${icon} text-xs"></i>
        </div>
    </div>`;
}

function renderSVGChart(candles) {
    if (!candles || candles.length < 2) return '<p class="text-center text-dark-400 py-12">No data</p>';
    
    const width = 800, height = 280, padding = 40;
    const prices = candles.map(c => [c.high, c.low]).flat();
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = maxPrice - minPrice || 1;
    
    const barWidth = Math.max(2, (width - padding * 2) / candles.length - 1);
    
    let svg = `<svg class="w-full h-full" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">`;
    
    // Grid lines
    for (let i = 0; i <= 4; i++) {
        const y = padding + (i / 4) * (height - padding * 2);
        svg += `<line x1="${padding}" y1="${y}" x2="${width-padding}" y2="${y}" stroke="#334155" stroke-width="0.5" stroke-dasharray="4"/>`;
    }
    
    // MA20 line
    const ma20Points = candles.filter(c => c.ma20).map((c, i) => {
        const x = padding + ((candles.indexOf(c)) / (candles.length - 1)) * (width - padding * 2);
        const y = padding + ((maxPrice - c.ma20) / priceRange) * (height - padding * 2);
        return `${x},${y}`;
    }).join(' ');
    if (ma20Points) svg += `<polyline points="${ma20Points}" fill="none" stroke="#f59e0b" stroke-width="1.5" opacity="0.7"/>`;

    // Candlesticks
    candles.forEach((c, i) => {
        const x = padding + (i / (candles.length - 1)) * (width - padding * 2);
        const yOpen = padding + ((maxPrice - c.open) / priceRange) * (height - padding * 2);
        const yClose = padding + ((maxPrice - c.close) / priceRange) * (height - padding * 2);
        const yHigh = padding + ((maxPrice - c.high) / priceRange) * (height - padding * 2);
        const yLow = padding + ((maxPrice - c.low) / priceRange) * (height - padding * 2);
        const isGreen = c.close >= c.open;
        const color = isGreen ? '#10b981' : '#ef4444';
        
        // Wick
        svg += `<line x1="${x}" y1="${yHigh}" x2="${x}" y2="${yLow}" stroke="${color}" stroke-width="1"/>`;
        // Body
        const bodyTop = Math.min(yOpen, yClose);
        const bodyHeight = Math.max(Math.abs(yClose - yOpen), 1);
        svg += `<rect x="${x - barWidth/2}" y="${bodyTop}" width="${barWidth}" height="${bodyHeight}" fill="${color}" rx="0.5"/>`;
    });
    
    svg += '</svg>';
    return svg;
}
