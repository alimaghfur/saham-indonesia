function getTechnicalPage() {
    return `
    <div class="space-y-6">
        <div class="flex items-center justify-between">
            <div>
                <h2 class="text-2xl font-bold text-white">Analisa Teknikal</h2>
                <p class="text-dark-400 text-sm mt-1">Chart interaktif dengan indikator teknikal lengkap</p>
            </div>
        </div>

        <!-- Stock Selector & Timeframe -->
        <div class="card p-4">
            <div class="flex flex-wrap items-center gap-4">
                <div class="flex items-center gap-2">
                    <div class="w-10 h-10 rounded-lg bg-primary-600/20 flex items-center justify-center">
                        <span class="text-sm font-bold text-primary-400">BB</span>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-white">BBCA</h3>
                        <p class="text-xs text-dark-400">Bank Central Asia Tbk</p>
                    </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                    <span class="text-2xl font-bold text-white">9,875</span>
                    <span class="stat-up text-sm font-medium">+225 (+2.33%)</span>
                </div>
                <div class="flex-1"></div>
                <div class="flex gap-1">
                    <button class="px-3 py-1.5 text-xs rounded bg-dark-700 text-dark-300 hover:bg-dark-600">1D</button>
                    <button class="px-3 py-1.5 text-xs rounded bg-dark-700 text-dark-300 hover:bg-dark-600">1W</button>
                    <button class="px-3 py-1.5 text-xs rounded bg-primary-600 text-white">1M</button>
                    <button class="px-3 py-1.5 text-xs rounded bg-dark-700 text-dark-300 hover:bg-dark-600">3M</button>
                    <button class="px-3 py-1.5 text-xs rounded bg-dark-700 text-dark-300 hover:bg-dark-600">6M</button>
                    <button class="px-3 py-1.5 text-xs rounded bg-dark-700 text-dark-300 hover:bg-dark-600">1Y</button>
                    <button class="px-3 py-1.5 text-xs rounded bg-dark-700 text-dark-300 hover:bg-dark-600">5Y</button>
                </div>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <!-- Chart Area -->
            <div class="lg:col-span-3 space-y-4">
                <!-- Candlestick Chart Placeholder -->
                <div class="card p-5">
                    <div class="flex items-center justify-between mb-4">
                        <div class="flex gap-2">
                            <button class="px-3 py-1 text-xs bg-primary-600 text-white rounded">Candlestick</button>
                            <button class="px-3 py-1 text-xs bg-dark-700 text-dark-300 rounded hover:bg-dark-600">Line</button>
                            <button class="px-3 py-1 text-xs bg-dark-700 text-dark-300 rounded hover:bg-dark-600">Area</button>
                        </div>
                        <div class="flex gap-2">
                            <button class="px-3 py-1 text-xs bg-dark-700 text-dark-300 rounded hover:bg-dark-600"><i class="fas fa-crosshairs mr-1"></i>Crosshair</button>
                            <button class="px-3 py-1 text-xs bg-dark-700 text-dark-300 rounded hover:bg-dark-600"><i class="fas fa-ruler mr-1"></i>Measure</button>
                        </div>
                    </div>
                    <!-- Chart Simulation -->
                    <div class="relative h-80 bg-dark-800 rounded-lg overflow-hidden">
                        <svg class="w-full h-full" viewBox="0 0 800 300" preserveAspectRatio="none">
                            <!-- Grid lines -->
                            <line x1="0" y1="75" x2="800" y2="75" stroke="#334155" stroke-width="0.5" stroke-dasharray="4"/>
                            <line x1="0" y1="150" x2="800" y2="150" stroke="#334155" stroke-width="0.5" stroke-dasharray="4"/>
                            <line x1="0" y1="225" x2="800" y2="225" stroke="#334155" stroke-width="0.5" stroke-dasharray="4"/>
                            <!-- Price area -->
                            <path d="M0,200 L50,190 L100,180 L150,195 L200,170 L250,160 L300,165 L350,140 L400,130 L450,145 L500,120 L550,110 L600,100 L650,90 L700,95 L750,80 L800,70" fill="none" stroke="#3b82f6" stroke-width="2"/>
                            <path d="M0,200 L50,190 L100,180 L150,195 L200,170 L250,160 L300,165 L350,140 L400,130 L450,145 L500,120 L550,110 L600,100 L650,90 L700,95 L750,80 L800,70 L800,300 L0,300 Z" fill="url(#blueGradient)" opacity="0.15"/>
                            <!-- MA20 -->
                            <path d="M0,210 L50,205 L100,198 L150,193 L200,185 L250,178 L300,172 L350,160 L400,150 L450,142 L500,135 L550,125 L600,118 L650,110 L700,105 L750,98 L800,92" fill="none" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="4"/>
                            <!-- MA50 -->
                            <path d="M0,220 L50,218 L100,215 L150,210 L200,205 L250,198 L300,190 L350,182 L400,175 L450,168 L500,160 L550,152 L600,145 L650,138 L700,132 L750,125 L800,120" fill="none" stroke="#8b5cf6" stroke-width="1.5" stroke-dasharray="4"/>
                            <!-- Candlesticks -->
                            ${generateCandlesticks()}
                            <!-- Support/Resistance -->
                            <line x1="0" y1="95" x2="800" y2="95" stroke="#ef4444" stroke-width="1" stroke-dasharray="6,3" opacity="0.7"/>
                            <line x1="0" y1="200" x2="800" y2="200" stroke="#10b981" stroke-width="1" stroke-dasharray="6,3" opacity="0.7"/>
                            <text x="10" y="90" fill="#ef4444" font-size="10">Resistance: 10,200</text>
                            <text x="10" y="215" fill="#10b981" font-size="10">Support: 9,450</text>
                            <defs>
                                <linearGradient id="blueGradient" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stop-color="#3b82f6" stop-opacity="0.4"/>
                                    <stop offset="100%" stop-color="#3b82f6" stop-opacity="0"/>
                                </linearGradient>
                            </defs>
                        </svg>
                        <!-- Price labels -->
                        <div class="absolute right-2 top-2 text-xs text-dark-400 space-y-12">
                            <div>10,200</div>
                            <div>9,900</div>
                            <div>9,600</div>
                            <div>9,300</div>
                        </div>
                    </div>
                    <!-- Volume bars -->
                    <div class="h-16 bg-dark-800 rounded-lg mt-2 flex items-end px-2 gap-0.5">
                        ${generateVolumeBars()}
                    </div>
                    <div class="flex items-center justify-between mt-2 text-xs text-dark-500">
                        <span>Apr 17</span><span>Apr 24</span><span>Mei 01</span><span>Mei 08</span><span>Mei 15</span>
                    </div>
                </div>

                <!-- Indicators -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="card p-4">
                        <h4 class="text-sm font-medium text-dark-300 mb-3">RSI (14)</h4>
                        <div class="h-20 bg-dark-800 rounded relative overflow-hidden">
                            <div class="absolute top-1/4 left-0 right-0 border-t border-dashed border-danger/30"></div>
                            <div class="absolute top-3/4 left-0 right-0 border-t border-dashed border-success/30"></div>
                            <svg class="w-full h-full" viewBox="0 0 400 80" preserveAspectRatio="none">
                                <path d="M0,50 L30,48 L60,45 L90,42 L120,38 L150,35 L180,40 L210,38 L240,32 L270,28 L300,30 L330,25 L360,22 L400,28" fill="none" stroke="#a855f7" stroke-width="2"/>
                            </svg>
                            <div class="absolute right-2 top-1 text-xs text-dark-400">70</div>
                            <div class="absolute right-2 bottom-1 text-xs text-dark-400">30</div>
                            <div class="absolute right-10 top-2 text-sm font-bold text-white">58.4</div>
                        </div>
                    </div>
                    <div class="card p-4">
                        <h4 class="text-sm font-medium text-dark-300 mb-3">MACD</h4>
                        <div class="h-20 bg-dark-800 rounded relative overflow-hidden">
                            <div class="absolute top-1/2 left-0 right-0 border-t border-dark-600"></div>
                            <svg class="w-full h-full" viewBox="0 0 400 80" preserveAspectRatio="none">
                                <path d="M0,45 L30,43 L60,40 L90,38 L120,35 L150,32 L180,30 L210,28 L240,25 L270,28 L300,30 L330,28 L360,25 L400,22" fill="none" stroke="#3b82f6" stroke-width="2"/>
                                <path d="M0,48 L30,46 L60,44 L90,42 L120,40 L150,38 L180,36 L210,34 L240,32 L270,30 L300,32 L330,33 L360,30 L400,28" fill="none" stroke="#ef4444" stroke-width="2" stroke-dasharray="3"/>
                            </svg>
                            <div class="absolute right-2 top-2 text-xs">
                                <span class="text-primary-400 font-medium">MACD: 45.2</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Panel -->
            <div class="space-y-4">
                <!-- Indicators Summary -->
                <div class="card p-4">
                    <h4 class="text-sm font-semibold text-white mb-3">Ringkasan Indikator</h4>
                    <div class="space-y-2">
                        ${indicatorRow('MA20', '9,650', 'Di atas', true)}
                        ${indicatorRow('MA50', '9,420', 'Di atas', true)}
                        ${indicatorRow('MA200', '9,100', 'Di atas', true)}
                        ${indicatorRow('RSI (14)', '58.4', 'Netral', null)}
                        ${indicatorRow('MACD', '45.2', 'Bullish', true)}
                        ${indicatorRow('Stochastic', '72.5', 'Overbought', false)}
                        ${indicatorRow('BB Upper', '10,050', '-', null)}
                        ${indicatorRow('BB Lower', '9,500', '-', null)}
                    </div>
                </div>

                <!-- Support & Resistance -->
                <div class="card p-4">
                    <h4 class="text-sm font-semibold text-white mb-3">Support & Resistance</h4>
                    <div class="space-y-2">
                        <div class="flex justify-between text-xs">
                            <span class="text-dark-400">R3</span><span class="text-danger font-medium">10,500</span>
                        </div>
                        <div class="flex justify-between text-xs">
                            <span class="text-dark-400">R2</span><span class="text-danger font-medium">10,200</span>
                        </div>
                        <div class="flex justify-between text-xs">
                            <span class="text-dark-400">R1</span><span class="text-danger font-medium">10,050</span>
                        </div>
                        <div class="flex justify-between text-xs bg-primary-600/20 p-1.5 rounded">
                            <span class="text-primary-400 font-medium">Harga</span><span class="text-white font-bold">9,875</span>
                        </div>
                        <div class="flex justify-between text-xs">
                            <span class="text-dark-400">S1</span><span class="text-success font-medium">9,650</span>
                        </div>
                        <div class="flex justify-between text-xs">
                            <span class="text-dark-400">S2</span><span class="text-success font-medium">9,450</span>
                        </div>
                        <div class="flex justify-between text-xs">
                            <span class="text-dark-400">S3</span><span class="text-success font-medium">9,200</span>
                        </div>
                    </div>
                </div>

                <!-- Pattern Detection -->
                <div class="card p-4">
                    <h4 class="text-sm font-semibold text-white mb-3">Pattern Detected</h4>
                    <div class="space-y-2">
                        <div class="flex items-center gap-2 p-2 bg-success/10 rounded-lg">
                            <i class="fas fa-arrow-trend-up text-success text-xs"></i>
                            <span class="text-xs text-success">Bullish Engulfing</span>
                        </div>
                        <div class="flex items-center gap-2 p-2 bg-success/10 rounded-lg">
                            <i class="fas fa-arrow-trend-up text-success text-xs"></i>
                            <span class="text-xs text-success">Cup & Handle</span>
                        </div>
                        <div class="flex items-center gap-2 p-2 bg-primary-600/10 rounded-lg">
                            <i class="fas fa-info-circle text-primary-400 text-xs"></i>
                            <span class="text-xs text-primary-400">Higher Low Formation</span>
                        </div>
                    </div>
                </div>

                <!-- Overall Score -->
                <div class="card p-4 text-center">
                    <h4 class="text-sm font-semibold text-white mb-2">Skor Teknikal</h4>
                    <div class="text-4xl font-bold text-success">8.2</div>
                    <div class="text-xs text-dark-400 mt-1">dari 10 - Strong Buy</div>
                    <div class="w-full bg-dark-700 rounded-full h-2 mt-3">
                        <div class="bg-gradient-to-r from-success to-emerald-400 h-2 rounded-full" style="width: 82%"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>`;
}

function generateCandlesticks() {
    const candles = [];
    const startX = 60;
    const gap = 48;
    const prices = [195, 185, 180, 190, 170, 155, 160, 135, 125, 140, 115, 105, 95, 85, 90, 75];
    for(let i = 0; i < 15; i++) {
        const x = startX + i * gap;
        const open = prices[i];
        const close = prices[i+1] || prices[i] - 5;
        const high = Math.min(open, close) - 8;
        const low = Math.max(open, close) + 8;
        const isGreen = close < open;
        const color = isGreen ? '#10b981' : '#ef4444';
        const top = Math.min(open, close);
        const bottom = Math.max(open, close);
        candles.push(`<line x1="${x}" y1="${high}" x2="${x}" y2="${low}" stroke="${color}" stroke-width="1"/>`);
        candles.push(`<rect x="${x-4}" y="${top}" width="8" height="${Math.abs(close-open)||3}" fill="${color}" rx="1"/>`);
    }
    return candles.join('');
}

function generateVolumeBars() {
    const volumes = [40, 55, 35, 70, 45, 60, 80, 50, 65, 90, 45, 75, 55, 85, 60, 70, 50, 95, 40, 65, 80, 55, 70, 45, 60, 85, 50, 75, 90, 55];
    return volumes.map((v, i) => {
        const color = i % 3 === 0 ? 'bg-danger/60' : 'bg-success/60';
        return `<div class="${color} rounded-t flex-1" style="height:${v}%"></div>`;
    }).join('');
}

function indicatorRow(name, value, status, isBullish) {
    const color = isBullish === true ? 'text-success' : isBullish === false ? 'text-danger' : 'text-dark-300';
    const icon = isBullish === true ? 'fa-check-circle text-success' : isBullish === false ? 'fa-times-circle text-danger' : 'fa-minus-circle text-dark-500';
    return `
    <div class="flex items-center justify-between py-1.5 border-b border-dark-800">
        <span class="text-xs text-dark-400">${name}</span>
        <div class="flex items-center gap-2">
            <span class="text-xs ${color} font-medium">${value}</span>
            <i class="fas ${icon} text-xs"></i>
        </div>
    </div>`;
}
