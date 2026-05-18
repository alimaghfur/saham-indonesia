// SahamID - Main Application Script
const API_BASE = window.location.origin + '/api';
let currentPage = 'dashboard';

async function fetchAPI(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return await res.json();
    } catch (e) {
        console.error(`API Error [${endpoint}]:`, e);
        return null;
    }
}

function navigateTo(page) {
    currentPage = page;
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) item.classList.add('active');
    });
    const content = document.getElementById('page-content');
    content.innerHTML = '<div class="flex items-center justify-center h-64"><div class="text-center"><div class="animate-spin w-8 h-8 border-4 border-primary-400 border-t-transparent rounded-full mx-auto mb-3"></div><p class="text-dark-400 text-sm">Memuat data real-time...</p></div></div>';
    loadPage(page);
}

async function loadPage(page) {
    const content = document.getElementById('page-content');
    switch(page) {
        case 'dashboard': content.innerHTML = await getDashboardPage(); break;
        case 'screener': content.innerHTML = await getScreenerPage(); break;
        case 'technical': content.innerHTML = await getTechnicalPage(); break;
        case 'fundamental': content.innerHTML = await getFundamentalPage(); break;
        case 'signals': content.innerHTML = await getSignalsPage(); break;
        case 'portfolio': content.innerHTML = getPortfolioPage(); break;
        case 'watchlist': content.innerHTML = getWatchlistPage(); break;
        case 'backtesting': content.innerHTML = getBacktestingPage(); break;
        case 'news': content.innerHTML = getNewsPage(); break;
        case 'heatmap': content.innerHTML = await getHeatmapPage(); break;
        case 'settings': content.innerHTML = getSettingsPage(); break;
        default: content.innerHTML = await getDashboardPage();
    }
    content.classList.remove('fade-in');
    void content.offsetWidth;
    content.classList.add('fade-in');
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('-translate-x-full');
    sidebar.classList.toggle('translate-x-0');
}

function formatRupiah(num) {
    if (!num) return '0';
    if (num >= 1e12) return (num / 1e12).toFixed(1) + ' T';
    if (num >= 1e9) return (num / 1e9).toFixed(1) + ' M';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + ' Jt';
    return num.toLocaleString('id-ID');
}

function formatVolume(num) {
    if (!num) return '0';
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toString();
}

// Load header indices
async function loadHeaderIndices() {
    const data = await fetchAPI('/market/indices');
    if (data && data.indices) {
        const ihsg = data.indices.find(i => i.name === 'IHSG');
        const lq45 = data.indices.find(i => i.name === 'LQ45');
        const headerEl = document.getElementById('header-indices');
        if (headerEl && ihsg && lq45) {
            headerEl.innerHTML = `
                <span class="text-dark-300">IHSG</span>
                <span class="font-semibold text-white">${(ihsg.price || 0).toLocaleString('id-ID')}</span>
                <span class="${ihsg.change >= 0 ? 'stat-up' : 'stat-down'} text-xs">${ihsg.change >= 0 ? '+' : ''}${ihsg.change_pct || 0}%</span>
                <span class="text-dark-600">|</span>
                <span class="text-dark-300">LQ45</span>
                <span class="font-semibold text-white">${(lq45.price || 0).toLocaleString('id-ID')}</span>
                <span class="${lq45.change >= 0 ? 'stat-up' : 'stat-down'} text-xs">${lq45.change >= 0 ? '+' : ''}${lq45.change_pct || 0}%</span>
            `;
        }
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    navigateTo('dashboard');
    loadHeaderIndices();
});
