"""CLI entrypoint for `saham-indonesia`.

Entry point is registered as `saham` in `pyproject.toml` so users can run:

    saham --help
    saham quote BBCA
    saham movers top-gainers --universe LQ45 --period 1D
    saham screen bpjs --universe LQ45 --top 10
    saham trending --universe LQ45
    saham breadth --universe LQ45
    saham sources
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from saham_id.data.sources import get_source, list_sources
from saham_id.data.universe import list_universes
from saham_id.utils.formatting import format_pct, format_rupiah
from saham_id.utils.logging import configure_logging

app = typer.Typer(
    name="saham",
    help="saham-indonesia — IDX analytics & screener toolkit.",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()


# Sub-apps
movers_app = typer.Typer(help="Top gainers / losers / most active.", no_args_is_help=True)
screen_app = typer.Typer(help="Strategy screeners.", no_args_is_help=True)
cache_app = typer.Typer(help="Cache management commands.", no_args_is_help=True)
app.add_typer(movers_app, name="movers")
app.add_typer(screen_app, name="screen")
app.add_typer(cache_app, name="cache")


# ---------------------------------------------------------------------------
# Root-level commands
# ---------------------------------------------------------------------------
@app.callback()
def _root(
    log_level: str = typer.Option("INFO", "--log-level", help="DEBUG/INFO/WARNING/ERROR"),
) -> None:
    configure_logging(log_level)


@app.command()
def sources() -> None:
    """List available data sources."""
    table = Table(title="Available Data Sources")
    table.add_column("Name", style="cyan")
    table.add_column("Class")
    for name in list_sources():
        try:
            inst = get_source(name)
            info = f"{inst.__class__.__name__} (delay={inst.typical_delay_minutes}m)"
        except Exception as exc:  # pragma: no cover
            info = f"<error: {exc}>"
        table.add_row(name, info)
    console.print(table)


@app.command()
def universes() -> None:
    """List built-in stock universes."""
    from saham_id.data.universe import UNIVERSES

    table = Table(title="Stock Universes")
    table.add_column("Name", style="cyan")
    table.add_column("# tickers", justify="right")
    table.add_column("Sample")
    for name in list_universes():
        tickers = UNIVERSES[name]
        table.add_row(name, str(len(tickers)), ", ".join(tickers[:5]) + "…")
    console.print(table)


@app.command()
def quote(
    ticker: str = typer.Argument(..., help="IDX ticker, e.g. BBCA"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Get the latest quote for a single ticker."""
    src = get_source(source)
    q = src.get_quote(ticker)
    change_str = format_pct(q.change_pct) if q.change_pct is not None else "n/a"
    console.print(
        f"[bold cyan]{q.ticker}[/] "
        f"{format_rupiah(q.last)} [dim]({change_str})[/] "
        f"[dim]vol={q.volume:,}  src={q.source}  delay={q.delayed_minutes}m[/]"
    )


@app.command()
def ohlc(
    ticker: str = typer.Argument(...),
    period: str = typer.Option("1y", "--period", "-p"),
    interval: str = typer.Option("1d", "--interval", "-i"),
    tail: int = typer.Option(10, "--tail", help="Show last N rows"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Print historical OHLC for a ticker."""
    src = get_source(source)
    df = src.get_ohlc(ticker, period=period, interval=interval)  # type: ignore[arg-type]
    console.print(df.tail(tail))


@app.command()
def trending(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    timeframe: str = typer.Option("1D", "--timeframe", "-t"),
    top: int = typer.Option(20, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Detect trending stocks (composite rvol + momentum + breakout)."""
    from saham_id.market import trending as trending_mod

    src = get_source(source)
    result = trending_mod.detect(
        universe=universe,
        timeframe=timeframe,  # type: ignore[arg-type]
        top_n=top,
        source=src,
    )
    _print_screen_result(result, title=f"Trending ({timeframe}) — {universe}")


@app.command()
def breadth(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Snapshot market breadth (advancers vs decliners)."""
    from saham_id.market import breadth as breadth_mod

    src = get_source(source)
    snap = breadth_mod.snapshot(universe=universe, source=src)
    table = Table(title=f"Market Breadth — {snap.universe}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Advancers", f"{snap.advancers}")
    table.add_row("Decliners", f"{snap.decliners}")
    table.add_row("Unchanged", f"{snap.unchanged}")
    table.add_row("A/D Ratio", f"{snap.ad_ratio:.2f}")
    table.add_row("Advancing %", f"{snap.advancing_pct:.1%}")
    table.add_row("New Highs (52w)", f"{snap.new_highs_52w}")
    table.add_row("New Lows (52w)", f"{snap.new_lows_52w}")
    console.print(table)


# ---------------------------------------------------------------------------
# Movers sub-app
# ---------------------------------------------------------------------------
@movers_app.command("top-gainers")
def cmd_top_gainers(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    period: str = typer.Option("1D", "--period", "-p"),
    top: int = typer.Option(10, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Show top gainers in a universe."""
    from saham_id.market import movers

    src = get_source(source)
    result = movers.top_gainers(
        universe=universe, period=period, top_n=top, source=src  # type: ignore[arg-type]
    )
    _print_movers(result, title=f"Top Gainers ({period}) — {universe}")


@movers_app.command("top-losers")
def cmd_top_losers(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    period: str = typer.Option("1D", "--period", "-p"),
    top: int = typer.Option(10, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Show top losers in a universe."""
    from saham_id.market import movers

    src = get_source(source)
    result = movers.top_losers(
        universe=universe, period=period, top_n=top, source=src  # type: ignore[arg-type]
    )
    _print_movers(result, title=f"Top Losers ({period}) — {universe}")


@movers_app.command("most-active")
def cmd_most_active(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    by: str = typer.Option("value", "--by", help="volume | value"),
    top: int = typer.Option(10, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Show most actively traded stocks."""
    from saham_id.market import movers

    src = get_source(source)
    result = movers.most_active(
        universe=universe, by=by, top_n=top, source=src  # type: ignore[arg-type]
    )
    _print_movers(result, title=f"Most Active (by {by}) — {universe}")


@movers_app.command("native")
def cmd_native_movers(
    kind: str = typer.Option("gainer", "--kind", "-k", help="gainer|loser|most_active|trending"),
    top: int = typer.Option(20, "--top", "-n"),
    source: str = typer.Option("goapi", "--source", "-s", help="Source with native movers (goapi)"),
) -> None:
    """Fetch movers directly from source API (e.g. GoAPI native endpoint)."""
    from saham_id.data.sources.base import NotImplementedForSource

    src = get_source(source)
    try:
        result = src.get_movers(kind=kind, top_n=top)  # type: ignore[arg-type]
    except NotImplementedForSource:
        console.print(
            f"[red]Source '{source}' does not support native get_movers(kind={kind})[/]"
        )
        raise typer.Exit(1)
    _print_movers(result, title=f"Native Movers ({kind}) — {source}")


# ---------------------------------------------------------------------------
# Screen sub-app
# ---------------------------------------------------------------------------
@screen_app.command("bpjs")
def cmd_bpjs(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    lookback: int = typer.Option(60, "--lookback"),
    min_win_rate: float = typer.Option(0.55, "--min-win-rate"),
    top: int = typer.Option(10, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Beli Pagi Jual Sore screener."""
    from saham_id.screener.intraday import bpjs

    src = get_source(source)
    result = bpjs.screen(
        universe=universe,
        lookback_days=lookback,
        min_win_rate=min_win_rate,
        top_n=top,
        source=src,
    )
    _print_screen_result(result, title=f"BPJS screener — {universe}")


@screen_app.command("bsjp")
def cmd_bsjp(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    lookback: int = typer.Option(60, "--lookback"),
    min_gap_up_rate: float = typer.Option(0.55, "--min-gap-up-rate"),
    top: int = typer.Option(10, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Beli Sore Jual Pagi screener."""
    from saham_id.screener.intraday import bsjp

    src = get_source(source)
    result = bsjp.screen(
        universe=universe,
        lookback_days=lookback,
        min_gap_up_rate=min_gap_up_rate,
        top_n=top,
        source=src,
    )
    _print_screen_result(result, title=f"BSJP screener — {universe}")


@screen_app.command("swing-breakout")
def cmd_swing_breakout(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    top: int = typer.Option(20, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Swing breakout screener."""
    from saham_id.screener.swing import breakout

    src = get_source(source)
    result = breakout.screen(universe=universe, top_n=top, source=src)
    _print_screen_result(result, title=f"Swing Breakout — {universe}")


@screen_app.command("swing-pullback")
def cmd_swing_pullback(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    top: int = typer.Option(15, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Swing pullback screener."""
    from saham_id.screener.swing import pullback

    src = get_source(source)
    result = pullback.screen(universe=universe, top_n=top, source=src)
    _print_screen_result(result, title=f"Swing Pullback — {universe}")


@screen_app.command("swing-reversal")
def cmd_swing_reversal(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    top: int = typer.Option(15, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Swing reversal screener (oversold bounce)."""
    from saham_id.screener.swing import reversal

    src = get_source(source)
    result = reversal.screen(universe=universe, top_n=top, source=src)
    _print_screen_result(result, title=f"Swing Reversal — {universe}")


@screen_app.command("scalping")
def cmd_scalping(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    min_atr_pct: float = typer.Option(0.015, "--min-atr-pct"),
    min_rvol: float = typer.Option(2.0, "--min-rvol"),
    top: int = typer.Option(10, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Scalping screener (high volatility + high RVOL)."""
    from saham_id.screener.intraday import scalping

    src = get_source(source)
    result = scalping.screen(
        universe=universe,
        min_atr_pct=min_atr_pct,
        min_rvol=min_rvol,
        top_n=top,
        source=src,
    )
    _print_screen_result(result, title=f"Scalping — {universe}")


@screen_app.command("unusual")
def cmd_unusual(
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    top: int = typer.Option(20, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Unusual volume / price activity detector."""
    from saham_id.market import unusual_activity

    src = get_source(source)
    result = unusual_activity.detect(universe=universe, top_n=top, source=src)
    _print_screen_result(result, title=f"Unusual Activity — {universe}")


# ---------------------------------------------------------------------------
# Signal & analysis commands
# ---------------------------------------------------------------------------
@app.command()
def signals(
    universe: str = typer.Option("IDX30", "--universe", "-u"),
    engine_type: str = typer.Option("swing_buy", "--engine", "-e", help="swing_buy|swing_sell|scalping"),
    top: int = typer.Option(10, "--top", "-n"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Generate buy/sell signals using composite indicator engine."""
    from saham_id.signals import generate_signals, swing_buy_engine, swing_sell_engine, scalping_engine, Action
    from saham_id.data.universe import get_universe

    engines = {"swing_buy": swing_buy_engine, "swing_sell": swing_sell_engine, "scalping": scalping_engine}
    engine_fn = engines.get(engine_type)
    if not engine_fn:
        console.print(f"[red]Unknown engine: {engine_type}. Use: swing_buy, swing_sell, scalping[/]")
        raise typer.Exit(1)

    src = get_source(source)
    tickers = get_universe(universe)
    engine = engine_fn()

    with console.status(f"Generating signals for {len(tickers)} stocks..."):
        sigs = generate_signals(tickers, engine=engine, source=src)

    # Filter actionable signals
    actionable = [s for s in sigs if s.action != Action.HOLD][:top]

    if not actionable:
        console.print(f"[yellow]No actionable signals for {universe}[/]")
        return

    table = Table(title=f"Signals ({engine_type}) — {universe}")
    table.add_column("Ticker", style="cyan")
    table.add_column("Action")
    table.add_column("Confidence", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Reasons")
    for sig in actionable:
        color = "green" if sig.action == Action.BUY else "red"
        table.add_row(
            sig.ticker,
            f"[{color}]{sig.action.value}[/]",
            f"{sig.confidence:.0%}",
            f"{sig.score:+.3f}",
            "; ".join(sig.reasons[:3]),
        )
    console.print(table)


@app.command()
def mtf(
    ticker: str = typer.Argument(..., help="IDX ticker, e.g. BBCA"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Multi-timeframe analysis for a single ticker."""
    from saham_id.analysis.mtf import multi_timeframe_analysis

    src = get_source(source)
    with console.status(f"Analyzing {ticker} across timeframes..."):
        result = multi_timeframe_analysis(ticker, source=src)

    color = {"BULLISH": "green", "BEARISH": "red", "NEUTRAL": "yellow"}[result.consensus]
    console.print(f"\n[bold]{ticker}[/] — [{color}]{result.consensus}[/] "
                  f"(alignment: {result.alignment_score:.0%})")
    console.print(f"  {result.recommendation}\n")

    table = Table(title="Timeframe Analysis")
    table.add_column("Timeframe")
    table.add_column("Bias")
    table.add_column("Trend")
    table.add_column("RSI", justify="right")
    table.add_column("MACD")
    table.add_column("Notes")
    for name, view in result.timeframes.items():
        bias_color = {"BULLISH": "green", "BEARISH": "red", "NEUTRAL": "yellow"}[view.bias]
        table.add_row(
            name,
            f"[{bias_color}]{view.bias}[/]",
            view.trend or "-",
            f"{view.rsi:.1f}" if view.rsi else "-",
            view.macd_signal or "-",
            "; ".join(view.notes[:2]) if view.notes else "-",
        )
    console.print(table)


@app.command("position-size")
def cmd_position_size(
    capital: float = typer.Option(100_000_000, "--capital", "-c", help="Total capital (Rp)"),
    entry: float = typer.Option(..., "--entry", help="Entry price per share"),
    stop: float = typer.Option(..., "--stop", help="Stop-loss price per share"),
    risk_pct: float = typer.Option(0.02, "--risk", "-r", help="Max risk % (e.g. 0.02 = 2%)"),
) -> None:
    """Calculate position size using fixed-fractional method."""
    from saham_id.portfolio.sizing import fixed_fractional

    result = fixed_fractional(
        capital=capital, risk_pct=risk_pct,
        entry_price=entry, stop_loss_price=stop,
    )

    table = Table(title="Position Size")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Shares", f"{result.shares:,}")
    table.add_row("Lots", f"{result.lots:,}")
    table.add_row("Capital Required", f"Rp {result.capital_required:,.0f}")
    table.add_row("Risk Amount", f"Rp {result.risk_amount:,.0f}")
    table.add_row("Risk % of Capital", f"{result.risk_pct_of_capital:.2%}")
    table.add_row("Stop Loss", f"Rp {result.stop_loss_price:,.0f}" if result.stop_loss_price else "-")
    console.print(table)


# ---------------------------------------------------------------------------
# Cache sub-app
# ---------------------------------------------------------------------------
@cache_app.command("stats")
def cmd_cache_stats() -> None:
    """Show cache statistics (memory + disk usage)."""
    from saham_id.cache import cache

    stats = cache.stats()
    table = Table(title="Cache Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Memory Items", f"{stats['memory_items']:,}")
    table.add_row("Memory Max Size", f"{stats['memory_maxsize']:,}")
    table.add_row("Disk Items", f"{stats['disk_items']:,}")
    table.add_row("Disk Size", _human_bytes(stats['disk_size_bytes']))
    table.add_row("Disk Enabled", "Yes" if stats['disk_enabled'] else "No")
    table.add_row("Cache Dir", stats['cache_dir'])
    console.print(table)


@cache_app.command("clear")
def cmd_cache_clear(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
) -> None:
    """Clear all cached data (memory + disk)."""
    from saham_id.cache import cache

    if not confirm:
        stats = cache.stats()
        total_items = stats['memory_items'] + stats['disk_items']
        if total_items == 0:
            console.print("[yellow]Cache is already empty.[/]")
            return
        msg = f"Clear {total_items} cached items ({_human_bytes(stats['disk_size_bytes'])} on disk)?"
        if not typer.confirm(msg):
            console.print("[dim]Cancelled.[/]")
            return

    cache.clear()
    console.print("[green]Cache cleared successfully.[/]")


def _human_bytes(n: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024  # type: ignore
    return f"{n:.1f} TB"


# ---------------------------------------------------------------------------
# Chart command
# ---------------------------------------------------------------------------
@app.command()
def chart(
    ticker: str = typer.Argument(..., help="IDX ticker, e.g. BBCA"),
    period: str = typer.Option("6mo", "--period", "-p", help="Data period (1mo/3mo/6mo/1y/2y/5y)"),
    interval: str = typer.Option("1d", "--interval", "-i", help="Data interval (1d/1wk/1mo)"),
    indicators: Optional[str] = typer.Option(
        None, "--indicators", "-I",
        help="Comma-separated indicators: rsi,macd,bollinger,stochastic,atr,volume",
    ),
    ma: Optional[str] = typer.Option(
        "20,50", "--ma", "-m",
        help="Moving average periods (comma-separated, e.g. 20,50,200)",
    ),
    chart_type: str = typer.Option(
        "candlestick", "--type", "-t", help="Chart type: candlestick or ohlc",
    ),
    dark: bool = typer.Option(True, "--dark/--light", help="Dark or light theme"),
    export: Optional[str] = typer.Option(
        None, "--export", "-o",
        help="Export chart to file (HTML or PNG). E.g. chart_bbca.html",
    ),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Generate an interactive technical chart and optionally export to file."""
    from saham_id.charting.candlestick import candlestick_chart, ohlc_chart
    from saham_id.charting.indicators import multi_indicator_chart

    src = get_source(source)

    with console.status(f"Fetching {ticker} data ({period}, {interval})..."):
        df = src.get_ohlc(ticker, period=period, interval=interval)  # type: ignore[arg-type]

    if df.empty:
        console.print(f"[red]No data for {ticker}[/]")
        raise typer.Exit(1)

    # Parse MA periods
    ma_periods = None
    if ma:
        try:
            ma_periods = [int(x.strip()) for x in ma.split(",") if x.strip()]
        except ValueError:
            console.print("[red]Invalid --ma format. Use comma-separated integers: 20,50,200[/]")
            raise typer.Exit(1)

    # Parse indicators
    indicator_list = []
    if indicators:
        indicator_list = [x.strip().lower() for x in indicators.split(",") if x.strip()]

    # Generate main chart
    if chart_type.lower() == "ohlc":
        fig = ohlc_chart(df, ticker=ticker, show_volume=True, dark=dark)
    else:
        fig = candlestick_chart(
            df, ticker=ticker, ma_periods=ma_periods,
            show_volume=True, dark=dark,
        )

    # If indicators requested, generate multi-panel instead
    if indicator_list:
        fig = multi_indicator_chart(
            df, indicators=indicator_list, ticker=ticker, dark=dark,
        )

    # Export or display info
    if export:
        export_path = export.strip()
        if export_path.endswith(".html"):
            fig.write_html(export_path)
            console.print(f"[green]Chart exported to {export_path}[/]")
        elif export_path.endswith(".png"):
            fig.write_image(export_path)
            console.print(f"[green]Chart exported to {export_path}[/]")
        else:
            fig.write_html(export_path)
            console.print(f"[green]Chart exported to {export_path} (HTML)[/]")
    else:
        # Show summary since we can't open a browser in CLI
        last = df["close"].iloc[-1]
        prev = df["close"].iloc[-2] if len(df) > 1 else last
        change_pct = (last - prev) / prev * 100
        console.print(f"\n[bold cyan]{ticker}[/] — {chart_type.title()}")
        console.print(f"  Last: {format_rupiah(last)}  Change: {change_pct:+.2f}%")
        console.print(f"  Period: {period}  Interval: {interval}  Bars: {len(df)}")
        if ma_periods:
            console.print(f"  MAs: {ma_periods}")
        if indicator_list:
            console.print(f"  Indicators: {', '.join(indicator_list)}")
        console.print("\n[dim]Tip: Use --export chart.html to save the interactive chart.[/]")


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def _print_movers(movers: list, title: str) -> None:
    if not movers:
        console.print(f"[yellow]{title}: no results[/]")
        return
    table = Table(title=title)
    table.add_column("#", justify="right")
    table.add_column("Ticker", style="cyan")
    table.add_column("Last", justify="right")
    table.add_column("Change %", justify="right")
    table.add_column("Volume", justify="right")
    table.add_column("Value (Rp)", justify="right")
    for i, m in enumerate(movers, start=1):
        chg_color = "green" if m.change_pct >= 0 else "red"
        table.add_row(
            str(i),
            m.ticker,
            format_rupiah(m.last),
            f"[{chg_color}]{format_pct(m.change_pct)}[/]",
            f"{m.volume:,}",
            format_rupiah(m.value),
        )
    console.print(table)


def _print_screen_result(result, title: str) -> None:
    df = result.to_dataframe()
    if df.empty:
        console.print(f"[yellow]{title}: no matches[/]")
        return
    table = Table(title=title)
    for col in df.columns:
        table.add_column(col, justify="right" if col != "ticker" else "left",
                         style="cyan" if col == "ticker" else None)
    for _, row in df.iterrows():
        table.add_row(*[_fmt_cell(row[c]) for c in df.columns])
    console.print(table)


def _fmt_cell(v) -> str:
    if isinstance(v, float):
        return f"{v:,.4f}" if abs(v) < 1 else f"{v:,.2f}"
    return str(v)


if __name__ == "__main__":  # pragma: no cover
    app()
