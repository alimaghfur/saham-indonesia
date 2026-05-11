"""Backtest report generator — export results to HTML.

Generates a standalone HTML report with performance summary,
equity curve info, and trade log.

Usage:
    from saham_id.backtest.report import generate_report
    path = generate_report(result, metrics, ticker="BBCA", strategy_name="BPJS")
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from saham_id.backtest.engine import BacktestResult
from saham_id.backtest.metrics import PerformanceMetrics


def generate_report(
    result: BacktestResult,
    metrics: PerformanceMetrics,
    ticker: str = "",
    strategy_name: str = "",
    output_dir: str | Path = "output/reports",
) -> Path:
    """Generate standalone HTML backtest report."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"backtest_{ticker}_{strategy_name}_{timestamp}.html".replace(" ", "_")
    filepath = out_dir / filename

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    title = f"Backtest Report - {ticker} ({strategy_name})"

    perf_rows = [
        ("Total Return", f"{metrics.total_return*100:.2f}%"),
        ("CAGR", f"{metrics.cagr*100:.2f}%"),
        ("Sharpe Ratio", f"{metrics.sharpe:.2f}"),
        ("Sortino Ratio", f"{metrics.sortino:.2f}"),
        ("Max Drawdown", f"{metrics.max_drawdown*100:.2f}%"),
        ("Win Rate", f"{metrics.win_rate*100:.1f}%"),
        ("Total Trades", f"{metrics.num_trades}"),
        ("Profit Factor", f"{metrics.profit_factor:.2f}"),
        ("Initial Capital", f"Rp {result.initial_capital:,.0f}"),
        ("Final Capital", f"Rp {result.final_capital:,.0f}"),
    ]
    perf_html = "\n".join(f"<tr><td>{k}</td><td><b>{v}</b></td></tr>" for k, v in perf_rows)

    trade_rows = ""
    for i, t in enumerate(result.trades[:50], 1):
        color = "green" if t.pnl >= 0 else "red"
        exit_price_str = f"{t.exit_price:,.0f}" if t.exit_price else "-"
        trade_rows += (
            f"<tr><td>{i}</td><td>{t.entry_time}</td><td>{t.exit_time or '-'}</td>"
            f"<td>{t.entry_price:,.0f}</td><td>{exit_price_str}</td>"
            f"<td>{t.quantity}</td><td style='color:{color}'>Rp {t.pnl:,.0f}</td>"
            f"<td style='color:{color}'>{t.pnl_pct*100:.2f}%</td></tr>\n"
        )

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
body{{font-family:sans-serif;max-width:900px;margin:40px auto;padding:0 20px}}
h1{{color:#1a5276;border-bottom:2px solid #1a5276;padding-bottom:10px}}
table{{border-collapse:collapse;width:100%;margin:15px 0}}
th,td{{border:1px solid #ddd;padding:8px 12px;text-align:left}}
th{{background:#f8f9fa}}
tr:nth-child(even){{background:#f9f9f9}}
.footer{{margin-top:40px;color:#888;font-size:0.85em;border-top:1px solid #ddd;padding-top:15px}}
</style></head><body>
<h1>{title}</h1>
<p>Generated: {now}</p>
<h2>Performance</h2>
<table><tr><th>Metric</th><th>Value</th></tr>{perf_html}</table>
<h2>Trade Log ({len(result.trades)} trades)</h2>
<table><tr><th>#</th><th>Entry</th><th>Exit</th><th>Entry Price</th><th>Exit Price</th><th>Qty</th><th>P/L</th><th>P/L %</th></tr>
{trade_rows}</table>
<div class="footer"><p>saham-indonesia | Disclaimer: Past performance does not guarantee future results.</p></div>
</body></html>"""

    filepath.write_text(html, encoding="utf-8")
    return filepath
