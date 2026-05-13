"""Shared professional CSS styling for the Saham Indonesia dashboard."""


def inject_global_css() -> str:
    """Return global CSS to inject via st.markdown for a professional look."""
    return """
<style>
/* ══════════════════════════════════════════════════════════════
   SAHAM INDONESIA — Professional Dashboard Theme
   ══════════════════════════════════════════════════════════════ */

/* --- Page & Container --- */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 1400px;
}

/* --- Sidebar --- */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1321 0%, #1a1f2e 100%);
    border-right: 1px solid #2a3040;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.9em;
}

/* --- Metric Cards --- */
[data-testid="stMetric"] {
    background: #1a1f2e;
    border: 1px solid #2a3040;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}
[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 0.8em !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.5em !important;
    font-weight: 700 !important;
    color: #f1f5f9 !important;
}
[data-testid="stMetricDelta"] svg { display: none; }

/* --- Tabs --- */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #1a1f2e;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #2a3040;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 20px;
    color: #94a3b8;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: #2563EB !important;
    color: white !important;
    border-radius: 8px;
}

/* --- DataFrames --- */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #2a3040;
}

/* --- Buttons --- */
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.2s ease;
    border: 1px solid #2a3040;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563EB, #1d4ed8);
    border: none;
}

/* --- Expander --- */
[data-testid="stExpander"] {
    background: #1a1f2e;
    border: 1px solid #2a3040;
    border-radius: 10px;
}

/* --- Text Input / Select --- */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: #1a1f2e;
    border: 1px solid #2a3040;
    border-radius: 8px;
    color: #e2e8f0;
}
.stTextInput > div > div > input:focus {
    border-color: #2563EB;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
}

/* --- Divider --- */
hr {
    border-color: #2a3040 !important;
    margin: 1.5rem 0 !important;
}

/* --- Progress bar --- */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #2563EB, #7c3aed);
    border-radius: 10px;
}

/* --- Plotly Charts transparent bg --- */
.js-plotly-plot .plotly .main-svg {
    background: transparent !important;
}

/* --- Success / Warning / Error boxes --- */
.stSuccess, .stWarning, .stError, .stInfo {
    border-radius: 10px !important;
    border-left-width: 4px !important;
}

/* --- Scrollbar --- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0f1117; }
::-webkit-scrollbar-thumb { background: #2a3040; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3b4560; }

/* --- Hide Streamlit branding --- */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

/* --- Custom helper classes --- */
.pro-card {
    background: #1a1f2e;
    border: 1px solid #2a3040;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 12px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.pro-card-title {
    font-weight: 600;
    font-size: 1em;
    color: #f1f5f9;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.pro-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7em;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.pro-badge-green { background: rgba(34,197,94,0.15); color: #22c55e; }
.pro-badge-red { background: rgba(239,68,68,0.15); color: #ef4444; }
.pro-badge-blue { background: rgba(37,99,235,0.15); color: #60a5fa; }
.pro-badge-orange { background: rgba(245,158,11,0.15); color: #f59e0b; }
.pro-badge-purple { background: rgba(139,92,246,0.15); color: #a78bfa; }

.pro-stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid #2a3040;
}
.pro-stat-row:last-child { border-bottom: none; }
.pro-stat-label { color: #94a3b8; font-size: 0.85em; }
.pro-stat-value { color: #f1f5f9; font-weight: 600; font-size: 0.9em; }
</style>
"""
