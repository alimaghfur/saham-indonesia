// SahamID - Main Application Script

let currentPage = 'dashboard';

function navigateTo(page) {
    currentPage = page;
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) item.classList.add('active');
    });
    const content = document.getElementById('page-content');
    content.classList.remove('fade-in');
    void content.offsetWidth;
    content.classList.add('fade-in');
    content.innerHTML = getPageContent(page);
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('-translate-x-full');
}

function getPageContent(page) {
    switch(page) {
        case 'dashboard': return getDashboardPage();
        case 'screener': return getScreenerPage();
        case 'technical': return getTechnicalPage();
        case 'fundamental': return getFundamentalPage();
        case 'signals': return getSignalsPage();
        case 'portfolio': return getPortfolioPage();
        case 'watchlist': return getWatchlistPage();
        case 'backtesting': return getBacktestingPage();
        case 'news': return getNewsPage();
        case 'heatmap': return getHeatmapPage();
        case 'settings': return getSettingsPage();
        default: return getDashboardPage();
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    navigateTo('dashboard');
});
