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

from pathlib import Path
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
alert_app = typer.Typer(help="Price alerts & Telegram notifications.", no_args_is_help=True)
app.add_typer(movers_app, name="movers")
app.add_typer(screen_app, name="screen")
app.add_typer(cache_app, name="cache")
app.add_typer(alert_app, name="alert")


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
# Backtest optimize command
# ---------------------------------------------------------------------------
@app.command("backtest-optimize")
def cmd_backtest_optimize(
    ticker: str = typer.Argument(..., help="IDX ticker to optimize on"),
    strategy: str = typer.Option(
        "rsi", "--strategy", "-S",
        help="Strategy to optimize: rsi, ma_crossover",
    ),
    metric: str = typer.Option(
        "sharpe", "--metric", "-m",
        help="Metric to maximize: sharpe, sortino, total_return, win_rate, profit_factor",
    ),
    period: str = typer.Option("2y", "--period", "-p", help="Data period for backtest"),
    top: int = typer.Option(5, "--top", "-n", help="Show top N parameter sets"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Optimize strategy parameters via grid search.

    Runs all parameter combinations and ranks by chosen metric.

    Examples:
        saham backtest-optimize BBCA --strategy rsi --metric sharpe
        saham backtest-optimize BBRI --strategy ma_crossover --metric total_return --period 3y
    """
    from saham_id.backtest.optimizer import optimize_rsi_strategy, optimize_ma_crossover

    src = get_source(source)

    with console.status(f"Fetching {ticker} data ({period})..."):
        df = src.get_ohlc(ticker, period=period, interval="1d")  # type: ignore[arg-type]

    if df.empty:
        console.print(f"[red]No data for {ticker}[/]")
        raise typer.Exit(1)

    console.print(f"[dim]Data: {len(df)} bars, optimizing {strategy} by {metric}...[/]")

    with console.status("Running grid search optimization..."):
        if strategy == "rsi":
            result = optimize_rsi_strategy(df, metric=metric, ticker=ticker)
        elif strategy in ("ma_crossover", "ma"):
            result = optimize_ma_crossover(df, metric=metric, ticker=ticker)
        else:
            console.print(f"[red]Unknown strategy: {strategy}. Use: rsi, ma_crossover[/]")
            raise typer.Exit(1)

    # Summary
    console.print(f"\n[bold]{ticker}[/] — Strategy: {strategy}, Metric: {metric}")
    console.print(
        f"  Runs: {result.total_runs} total, {result.successful_runs} successful\n"
    )

    if result.best_run:
        console.print(f"  [green]Best {metric}: {result.best_score:.4f}[/]")
        console.print(f"  Best params: {result.best_params}")
        if result.best_metrics:
            bm = result.best_metrics
            console.print(
                f"  Return: {bm.total_return:.2%} | Sharpe: {bm.sharpe:.2f} | "
                f"MaxDD: {bm.max_drawdown:.2%} | Trades: {bm.num_trades} | "
                f"Win: {bm.win_rate:.0%}"
            )
    else:
        console.print("[yellow]No successful runs (all parameter sets failed or too few trades).[/]")
        return

    # Top N table
    console.print()
    top_runs = result.top_n(top)
    table = Table(title=f"Top {top} Parameter Sets")
    # Dynamic columns from param keys
    param_keys = list(result.best_params.keys())
    for key in param_keys:
        table.add_column(key, justify="right", style="cyan")
    table.add_column(metric, justify="right", style="green")
    table.add_column("Return", justify="right")
    table.add_column("Sharpe", justify="right")
    table.add_column("MaxDD", justify="right")
    table.add_column("Trades", justify="right")

    for run in top_runs:
        if run.metrics is None:
            continue
        row = [str(run.params.get(k, "")) for k in param_keys]
        row.append(f"{run.score:.4f}")
        row.append(f"{run.metrics.total_return:.2%}")
        row.append(f"{run.metrics.sharpe:.2f}")
        row.append(f"{run.metrics.max_drawdown:.2%}")
        row.append(str(run.metrics.num_trades))
        table.add_row(*row)

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
# Alert sub-app
# ---------------------------------------------------------------------------
@alert_app.command("setup")
def cmd_alert_setup(
    telegram_token: Optional[str] = typer.Option(None, "--token", "-t", help="Telegram Bot token"),
    chat_id: Optional[str] = typer.Option(None, "--chat-id", "-c", help="Telegram chat ID"),
) -> None:
    """Setup or verify Telegram notification credentials.

    If --token and --chat-id provided, tests the connection.
    Otherwise shows current configuration status.
    """
    from saham_id.config import settings as _settings

    if telegram_token and chat_id:
        # Test the connection
        from saham_id.notifications import TelegramBackend, Notification

        backend = TelegramBackend(bot_token=telegram_token, chat_id=chat_id)
        test_notif = Notification(
            title="Setup Test",
            message="saham-indonesia alert berhasil terkoneksi!",
            level="info",
        )

        with console.status("Testing Telegram connection..."):
            success = backend.send(test_notif)

        if success:
            console.print("[green]Telegram connected successfully![/]")
            console.print(
                f"\nTambahkan ke `.env`:\n"
                f"  SAHAM_ID_TELEGRAM_TOKEN={telegram_token}\n"
                f"  SAHAM_ID_TELEGRAM_CHAT_ID={chat_id}\n"
            )
        else:
            console.print("[red]Telegram connection failed.[/]")
            console.print("Pastikan bot token dan chat_id benar.")
            raise typer.Exit(1)
    else:
        # Show current status
        table = Table(title="Alert Configuration")
        table.add_column("Backend", style="cyan")
        table.add_column("Status")
        table.add_column("Config")

        # Telegram
        tg_token = getattr(_settings, "telegram_token", "") or ""
        tg_chat = getattr(_settings, "telegram_chat_id", "") or ""
        if tg_token and tg_chat:
            table.add_row("Telegram", "[green]Configured[/]", f"chat_id={tg_chat[:8]}...")
        else:
            table.add_row("Telegram", "[yellow]Not configured[/]", "Set SAHAM_ID_TELEGRAM_TOKEN & CHAT_ID")

        # Discord
        discord_url = getattr(_settings, "discord_webhook", "") or ""
        if discord_url:
            table.add_row("Discord", "[green]Configured[/]", f"webhook=...{discord_url[-20:]}")
        else:
            table.add_row("Discord", "[yellow]Not configured[/]", "Set SAHAM_ID_DISCORD_WEBHOOK")

        console.print(table)
        console.print("\nGunakan `saham alert setup --token <BOT_TOKEN> --chat-id <CHAT_ID>` untuk test.")


@alert_app.command("test")
def cmd_alert_test(
    message: str = typer.Option("Test alert dari saham-indonesia CLI", "--message", "-m"),
    level: str = typer.Option("alert", "--level", "-l", help="info|alert|critical"),
    backend_name: str = typer.Option("all", "--backend", "-b", help="telegram|discord|all"),
) -> None:
    """Send a test notification to configured backends."""
    from saham_id.notifications import NotificationManager, TelegramBackend, DiscordBackend, ConsoleBackend, Notification
    from saham_id.config import settings as _settings

    manager = NotificationManager()
    manager.add_backend(ConsoleBackend())

    # Add Telegram if configured
    tg_token = getattr(_settings, "telegram_token", "") or ""
    tg_chat = getattr(_settings, "telegram_chat_id", "") or ""
    if tg_token and tg_chat and backend_name in ("telegram", "all"):
        manager.add_backend(TelegramBackend(bot_token=tg_token, chat_id=tg_chat))

    # Add Discord if configured
    discord_url = getattr(_settings, "discord_webhook", "") or ""
    if discord_url and backend_name in ("discord", "all"):
        manager.add_backend(DiscordBackend(webhook_url=discord_url))

    if len(manager.backends) <= 1:  # Only console
        console.print("[yellow]No notification backends configured (only console).[/]")
        console.print("Run `saham alert setup` untuk configure Telegram/Discord.")

    notif = Notification(title="Test Alert", message=message, level=level)  # type: ignore
    results = manager.send_all(notif)

    for backend, success in results.items():
        status = "[green]sent[/]" if success else "[red]failed[/]"
        console.print(f"  {backend}: {status}")


@alert_app.command("add")
def cmd_alert_add(
    ticker: str = typer.Argument(..., help="IDX ticker, e.g. BBCA"),
    field: str = typer.Option("last", "--field", "-f", help="Field to monitor: last, rsi, volume"),
    op: str = typer.Option("<", "--op", help="Operator: <, >, <=, >=, =="),
    value: float = typer.Option(..., "--value", "-v", help="Threshold value"),
    message: str = typer.Option("", "--message", "-m", help="Custom alert message"),
) -> None:
    """Add a price/indicator alert for a ticker."""
    from saham_id.alert_cli import add_alert

    result = add_alert(ticker=ticker, field=field, op=op, value=value, message=message)
    console.print(f"[green]{result}[/]")


@alert_app.command("list")
def cmd_alert_list() -> None:
    """List all active alerts."""
    from saham_id.alert_cli import list_alerts

    alerts = list_alerts()
    if not alerts:
        console.print("[yellow]No alerts configured. Use `saham alert add` to create one.[/]")
        return

    table = Table(title="Active Alerts")
    table.add_column("Ticker", style="cyan")
    table.add_column("Condition")
    table.add_column("Value", justify="right")
    for a in alerts:
        table.add_row(a["ticker"], a["condition"], f"{a['value']:,.2f}")
    console.print(table)


@alert_app.command("check")
def cmd_alert_check(
    notify: bool = typer.Option(False, "--notify", "-n", help="Send notifications for triggered alerts"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Check all alerts against live data and optionally notify."""
    from saham_id.alert_cli import check_alerts

    src = get_source(source) if source else None

    with console.status("Checking alerts against live data..."):
        triggered = check_alerts(source=src)

    if not triggered:
        console.print("[green]No alerts triggered.[/]")
        return

    table = Table(title="Triggered Alerts")
    table.add_column("Ticker", style="cyan")
    table.add_column("Triggered")
    table.add_column("Values")
    for t in triggered:
        table.add_row(
            t["ticker"],
            "; ".join(str(a) for a in t["alerts"][:3]),
            str(t.get("values", {})),
        )
    console.print(table)

    # Send notifications if requested
    if notify and triggered:
        from saham_id.notifications import NotificationManager, TelegramBackend, ConsoleBackend, Notification
        from saham_id.config import settings as _settings

        manager = NotificationManager()
        tg_token = getattr(_settings, "telegram_token", "") or ""
        tg_chat = getattr(_settings, "telegram_chat_id", "") or ""
        if tg_token and tg_chat:
            manager.add_backend(TelegramBackend(bot_token=tg_token, chat_id=tg_chat))
        else:
            manager.add_backend(ConsoleBackend())

        for t in triggered:
            notif = Notification(
                title=f"Alert: {t['ticker']}",
                message="; ".join(str(a) for a in t["alerts"][:3]),
                level="alert",
                ticker=t["ticker"],
            )
            manager.send_all(notif)

        console.print(f"[green]Sent {len(triggered)} notification(s).[/]")


@alert_app.command("remove")
def cmd_alert_remove(
    ticker: str = typer.Argument(..., help="Ticker to remove alerts for"),
) -> None:
    """Remove all alerts for a ticker."""
    from saham_id.alert_cli import remove_alert

    result = remove_alert(ticker)
    console.print(f"[green]{result}[/]")


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
# Schedule sub-app
# ---------------------------------------------------------------------------
schedule_app = typer.Typer(help="Automated scheduled scanning.", no_args_is_help=True)
app.add_typer(schedule_app, name="schedule")


@schedule_app.command("run")
def cmd_schedule_run(
    action: str = typer.Option("check_alerts", "--action", "-a",
        help="check_alerts|screen_bpjs|screen_breakout|generate_signals"),
    universe: str = typer.Option("LQ45", "--universe", "-u"),
    notify: bool = typer.Option(True, "--notify/--no-notify"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Run a scheduled action once (for cron/systemd integration)."""
    from saham_id.scheduler import Scheduler, ScheduledTask

    task = ScheduledTask(
        name=f"cli_{action}",
        interval_minutes=0,
        action=action,  # type: ignore
        params={"universe": universe, "source": source},
        notify_on_results=notify,
    )

    scheduler = Scheduler()
    scheduler.add_task(task)

    with console.status(f"Running {action}..."):
        results = scheduler.run_due_tasks()

    for r in results:
        status = "[green]OK[/]" if r.success else "[red]FAIL[/]"
        console.print(f"  {r.task_name}: {status} — {r.message}")


@schedule_app.command("list")
def cmd_schedule_list() -> None:
    """Show available scheduled actions."""
    actions = [
        ("check_alerts", "Check watchlist alerts against live data"),
        ("screen_bpjs", "Run BPJS screener"),
        ("screen_bsjp", "Run BSJP screener"),
        ("screen_breakout", "Run swing breakout screener"),
        ("screen_pullback", "Run swing pullback screener"),
        ("screen_reversal", "Run swing reversal screener"),
        ("screen_scalping", "Run scalping screener"),
        ("generate_signals", "Generate composite BUY/SELL signals"),
        ("market_breadth", "Get market breadth snapshot"),
    ]
    table = Table(title="Available Scheduled Actions")
    table.add_column("Action", style="cyan")
    table.add_column("Description")
    for action, desc in actions:
        table.add_row(action, desc)
    console.print(table)
    console.print("\n[dim]Usage: saham schedule run --action screen_bpjs --universe LQ45[/]")
    console.print("[dim]For cron: */30 * * * 1-5 saham schedule run --action check_alerts --notify[/]")


# ---------------------------------------------------------------------------
# Report command
# ---------------------------------------------------------------------------
@app.command()
def report(
    ticker: str = typer.Argument(..., help="IDX ticker for full report"),
    period: str = typer.Option("6mo", "--period", "-p"),
    output: str = typer.Option("", "--output", "-o", help="Output HTML file (default: report_{ticker}.html)"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Generate a comprehensive HTML report for a single stock.

    Includes: price chart, indicators, scorecard, signals, support/resistance.
    """
    from saham_id.charting.candlestick import candlestick_chart
    from saham_id.charting.indicators import multi_indicator_chart
    from datetime import datetime

    src = get_source(source)
    out_path = output or f"report_{ticker.lower()}.html"

    with console.status(f"Generating report for {ticker}..."):
        df = src.get_ohlc(ticker, period=period, interval="1d")  # type: ignore

        if df.empty:
            console.print(f"[red]No data for {ticker}[/]")
            raise typer.Exit(1)

        # Generate charts
        fig_price = candlestick_chart(df, ticker=ticker, ma_periods=[20, 50, 200], show_volume=True)
        fig_ind = multi_indicator_chart(df, indicators=["rsi", "macd", "volume"], ticker=ticker)

        # Build HTML
        price_html = fig_price.to_html(full_html=False, include_plotlyjs="cdn")
        ind_html = fig_ind.to_html(full_html=False, include_plotlyjs=False)

        last = df["close"].iloc[-1]
        prev = df["close"].iloc[-2] if len(df) > 1 else last
        change_pct = (last - prev) / prev * 100

        html = f"""<!DOCTYPE html>
<html><head>
<title>Report: {ticker}</title>
<meta charset="utf-8">
<style>
body {{ font-family: 'Inter', sans-serif; background: #1e1e2e; color: #cdd6f4; padding: 20px; }}
h1, h2 {{ color: #89b4fa; }}
.metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; }}
.metric {{ background: #2d2d3d; padding: 15px; border-radius: 8px; text-align: center; }}
.metric .value {{ font-size: 1.5em; font-weight: bold; }}
.metric .label {{ font-size: 0.8em; color: #888; }}
.section {{ margin: 30px 0; }}
footer {{ margin-top: 40px; color: #666; font-size: 0.8em; }}
</style>
</head><body>
<h1>Stock Report: {ticker}</h1>
<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Period: {period} | Bars: {len(df)}</p>

<div class="metrics">
  <div class="metric"><div class="value">Rp {last:,.0f}</div><div class="label">Last Price</div></div>
  <div class="metric"><div class="value" style="color:{'#26a69a' if change_pct >= 0 else '#ef5350'}">{change_pct:+.2f}%</div><div class="label">Change</div></div>
  <div class="metric"><div class="value">Rp {df['high'].max():,.0f}</div><div class="label">Period High</div></div>
  <div class="metric"><div class="value">Rp {df['low'].min():,.0f}</div><div class="label">Period Low</div></div>
</div>

<div class="section">
<h2>Price Chart</h2>
{price_html}
</div>

<div class="section">
<h2>Technical Indicators</h2>
{ind_html}
</div>

<footer>
saham-indonesia — Generated by <code>saham report {ticker}</code>
</footer>
</body></html>"""

        Path(out_path).write_text(html, encoding="utf-8")

    console.print(f"[green]Report saved to {out_path}[/]")
    console.print(f"  {ticker}: Rp {last:,.0f} ({change_pct:+.2f}%) | {len(df)} bars")


# ---------------------------------------------------------------------------
# Paper trading sub-app
# ---------------------------------------------------------------------------
paper_app = typer.Typer(help="Paper trading simulation.", no_args_is_help=True)
app.add_typer(paper_app, name="paper")


@paper_app.command("buy")
def cmd_paper_buy(
    ticker: str = typer.Argument(..., help="IDX ticker to buy"),
    lots: int = typer.Option(1, "--lots", "-l", help="Number of lots (1 lot = 100 shares)"),
    session: str = typer.Option("default", "--session", help="Paper trading session name"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Buy stock at current market price (paper trading)."""
    from saham_id.paper_trading import PaperTrader

    src = get_source(source)
    trader = PaperTrader.load(session, source=src)

    order = trader.buy(ticker, lots=lots)
    trader.save(session)

    if order.status == "filled":
        console.print(
            f"[green]BUY {ticker} {lots} lot @ Rp {order.price:,.0f}[/] "
            f"(Total: Rp {order.price * order.shares:,.0f})"
        )
        console.print(f"  Cash remaining: Rp {trader.cash:,.0f}")
    else:
        console.print(f"[red]Order rejected: {order.note}[/]")


@paper_app.command("sell")
def cmd_paper_sell(
    ticker: str = typer.Argument(..., help="IDX ticker to sell"),
    lots: int = typer.Option(1, "--lots", "-l", help="Number of lots to sell"),
    session: str = typer.Option("default", "--session", help="Paper trading session name"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Sell stock at current market price (paper trading)."""
    from saham_id.paper_trading import PaperTrader

    src = get_source(source)
    trader = PaperTrader.load(session, source=src)

    order = trader.sell(ticker, lots=lots)
    trader.save(session)

    if order.status == "filled":
        console.print(
            f"[red]SELL {ticker} {lots} lot @ Rp {order.price:,.0f}[/] "
            f"(Proceeds: Rp {order.price * order.shares:,.0f})"
        )
        console.print(f"  Cash: Rp {trader.cash:,.0f}")
    else:
        console.print(f"[red]Order rejected: {order.note}[/]")


@paper_app.command("portfolio")
def cmd_paper_portfolio(
    session: str = typer.Option("default", "--session", help="Paper trading session name"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Show paper trading portfolio summary."""
    from saham_id.paper_trading import PaperTrader

    src = get_source(source)
    trader = PaperTrader.load(session, source=src)
    summary = trader.summary()

    # Portfolio overview
    table = Table(title=f"Paper Trading — {session}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")
    table.add_row("Initial Capital", f"Rp {summary['initial_capital']:,.0f}")
    table.add_row("Cash", f"Rp {summary['cash']:,.0f}")
    table.add_row("Portfolio Value", f"Rp {summary['portfolio_value']:,.0f}")

    pnl = summary['total_pnl']
    pnl_color = "green" if pnl >= 0 else "red"
    table.add_row("Total P/L", f"[{pnl_color}]Rp {pnl:,.0f}[/]")
    table.add_row("Return", f"[{pnl_color}]{summary['total_return_pct']:.2%}[/]")
    table.add_row("Trades", str(summary['num_trades']))
    console.print(table)

    # Positions
    if summary['positions']:
        pos_table = Table(title="Open Positions")
        pos_table.add_column("Ticker", style="cyan")
        pos_table.add_column("Shares", justify="right")
        pos_table.add_column("Avg Cost", justify="right")
        pos_table.add_column("Realized P/L", justify="right")
        for ticker, pos in summary['positions'].items():
            rpnl = pos['realized_pnl']
            rpnl_color = "green" if rpnl >= 0 else "red"
            pos_table.add_row(
                ticker,
                f"{pos['shares']:,}",
                f"Rp {pos['avg_cost']:,.0f}",
                f"[{rpnl_color}]Rp {rpnl:,.0f}[/]",
            )
        console.print(pos_table)
    else:
        console.print("[dim]No open positions.[/]")


@paper_app.command("history")
def cmd_paper_history(
    session: str = typer.Option("default", "--session"),
    tail: int = typer.Option(20, "--tail", "-n", help="Show last N trades"),
) -> None:
    """Show paper trading trade history."""
    from saham_id.paper_trading import PaperTrader

    trader = PaperTrader.load(session)

    if not trader.trades:
        console.print("[yellow]No trades yet.[/]")
        return

    table = Table(title=f"Trade History — {session} (last {tail})")
    table.add_column("Time")
    table.add_column("Ticker", style="cyan")
    table.add_column("Side")
    table.add_column("Shares", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Value", justify="right")
    table.add_column("Fee", justify="right")

    for trade in trader.trades[-tail:]:
        side_color = "green" if trade.side == "buy" else "red"
        table.add_row(
            trade.timestamp.strftime("%m/%d %H:%M"),
            trade.ticker,
            f"[{side_color}]{trade.side.upper()}[/]",
            f"{trade.shares:,}",
            f"Rp {trade.price:,.0f}",
            f"Rp {trade.value:,.0f}",
            f"Rp {trade.fee:,.0f}",
        )
    console.print(table)


@paper_app.command("reset")
def cmd_paper_reset(
    session: str = typer.Option("default", "--session"),
    capital: float = typer.Option(100_000_000, "--capital", "-c"),
    confirm: bool = typer.Option(False, "--yes", "-y"),
) -> None:
    """Reset paper trading session (clear all positions and trades)."""
    from saham_id.paper_trading import PaperTrader

    if not confirm:
        if not typer.confirm(f"Reset session '{session}'? All trades will be lost."):
            console.print("[dim]Cancelled.[/]")
            return

    trader = PaperTrader(initial_capital=capital)
    trader.save(session)
    console.print(f"[green]Session '{session}' reset. Capital: Rp {capital:,.0f}[/]")


# ---------------------------------------------------------------------------
# Compare command
# ---------------------------------------------------------------------------
@app.command()
def compare(
    tickers: str = typer.Argument(..., help="Tickers to compare (comma-separated), e.g. BBCA,BBRI,BMRI"),
    period: str = typer.Option("6mo", "--period", "-p"),
    export: Optional[str] = typer.Option(None, "--export", "-o", help="Export chart to HTML"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Compare performance of multiple stocks (rebased to 100)."""
    from saham_id.charting.comparison import comparison_chart

    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if len(ticker_list) < 2:
        console.print("[red]Provide at least 2 tickers separated by comma.[/]")
        raise typer.Exit(1)

    src = get_source(source)
    dataframes = {}

    with console.status(f"Fetching data for {', '.join(ticker_list)}..."):
        for ticker in ticker_list:
            try:
                df = src.get_ohlc(ticker, period=period, interval="1d")  # type: ignore
                if not df.empty:
                    dataframes[ticker] = df
            except Exception as e:
                console.print(f"[yellow]Skipped {ticker}: {e}[/]")

    if len(dataframes) < 2:
        console.print("[red]Need at least 2 tickers with data.[/]")
        raise typer.Exit(1)

    fig = comparison_chart(dataframes, title=f"Comparison: {', '.join(dataframes.keys())}")

    if export:
        fig.write_html(export)
        console.print(f"[green]Chart exported to {export}[/]")
    else:
        # Print summary
        console.print(f"\n[bold]Comparison ({period})[/]")
        for ticker, df in dataframes.items():
            first = df["close"].iloc[0]
            last = df["close"].iloc[-1]
            ret = (last - first) / first * 100 if first else 0
            color = "green" if ret >= 0 else "red"
            console.print(f"  [{color}]{ticker}: {ret:+.2f}%[/] (Rp {first:,.0f} → Rp {last:,.0f})")
        console.print("\n[dim]Tip: Use --export compare.html to save chart.[/]")


# ---------------------------------------------------------------------------
# Invest command (Investment Decision Engine)
# ---------------------------------------------------------------------------
invest_app = typer.Typer(help="Investment analysis & decision engine.", no_args_is_help=True)
app.add_typer(invest_app, name="invest")


@invest_app.command("analyze")
def cmd_invest_analyze(
    ticker: str = typer.Argument(..., help="IDX ticker to analyze, e.g. BBCA"),
    budget: float = typer.Option(50_000_000, "--budget", "-b", help="Available capital (Rp)"),
    risk: float = typer.Option(2.0, "--risk", "-r", help="Max risk per trade (%)"),
    period: str = typer.Option("6mo", "--period", "-p", help="Analysis period"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Full investment analysis with entry/exit recommendation.

    Combines trend, momentum, bandar, asing, volume, support/resistance
    into a single actionable verdict: STRONG BUY / BUY / WAIT / AVOID.

    Examples:
        saham invest analyze BBCA
        saham invest analyze BBRI --budget 100000000 --risk 1.5
    """
    from saham_id.invest import analyze_investment, Verdict

    src = get_source(source)

    with console.status(f"Analyzing {ticker} for investment decision..."):
        decision = analyze_investment(
            ticker=ticker,
            budget=budget,
            risk_tolerance=risk / 100,
            period=period,
            source=src,
        )

    # --- Verdict ---
    verdict_color = {
        "STRONG BUY": "green", "BUY": "green",
        "WAIT": "yellow", "AVOID": "red", "SELL": "red",
    }
    vc = verdict_color.get(decision.verdict.value, "white")
    console.print(f"\n[bold {vc}]{'=' * 50}[/]")
    console.print(f"[bold {vc}]  {decision.verdict.value}  —  {ticker}[/]")
    console.print(f"[bold {vc}]{'=' * 50}[/]")
    console.print(f"\n  {decision.summary}\n")

    # --- Score Table ---
    table = Table(title="Component Scores")
    table.add_column("Component", style="cyan")
    table.add_column("Score", justify="right")
    table.add_column("Status")
    components = [
        ("Trend", decision.trend_score),
        ("Momentum", decision.momentum_score),
        ("Volume", decision.volume_score),
        ("Bandar", decision.bandar_score),
        ("Foreign Flow", decision.foreign_flow_score),
        ("Support/Resistance", decision.support_resistance_score),
    ]
    for name, score in components:
        status_color = "green" if score >= 65 else "yellow" if score >= 45 else "red"
        status = "BULLISH" if score >= 65 else "NEUTRAL" if score >= 45 else "BEARISH"
        table.add_row(name, f"{score:.0f}/100", f"[{status_color}]{status}[/]")
    table.add_row("─" * 20, "─" * 8, "─" * 10)
    table.add_row("[bold]ENTRY SCORE[/]", f"[bold]{decision.entry_score:.0f}/100[/]", f"[bold]Conviction: {decision.conviction.value}[/]")
    console.print(table)

    # --- Risk/Reward ---
    rr = decision.risk_reward
    console.print(f"\n[bold]Risk / Reward:[/]")
    console.print(f"  Entry:     Rp {rr.entry_price:,.0f}")
    console.print(f"  Stop-Loss: Rp {rr.stop_loss:,.0f} [dim](-{rr.risk_pct:.1f}%)[/]")
    console.print(f"  Target 1:  Rp {rr.target_1:,.0f}")
    console.print(f"  Target 2:  Rp {rr.target_2:,.0f} [dim](+{rr.reward_pct:.1f}%)[/]")
    console.print(f"  Target 3:  Rp {rr.target_3:,.0f}")
    rr_color = "green" if rr.is_favorable else "red"
    console.print(f"  R:R Ratio: [{rr_color}]{rr.risk_reward_ratio:.1f}:1[/] {'(FAVORABLE)' if rr.is_favorable else '(kurang ideal)'}")

    # --- Position Sizing ---
    pos = decision.position
    if pos.lots > 0:
        console.print(f"\n[bold]Position Size:[/]")
        console.print(f"  Beli: {pos.lots} lot ({pos.shares:,} lembar)")
        console.print(f"  Modal: Rp {pos.capital_required:,.0f} ({pos.pct_of_portfolio:.1f}% portfolio)")
        console.print(f"  Max Loss: Rp {pos.max_loss:,.0f} ({pos.risk_per_trade:.1f}% risk)")

    # --- Exit Plan ---
    console.print(f"\n[bold]Exit Plan:[/]")
    for cond in decision.exit_plan.exit_conditions:
        console.print(f"  - {cond}")

    # --- Reasons ---
    if decision.bullish_reasons:
        console.print(f"\n[green][bold]Bullish:[/][/]")
        for r in decision.bullish_reasons:
            console.print(f"  [green]+ {r}[/]")
    if decision.bearish_reasons:
        console.print(f"\n[red][bold]Bearish:[/][/]")
        for r in decision.bearish_reasons:
            console.print(f"  [red]- {r}[/]")
    if decision.warnings:
        console.print(f"\n[yellow][bold]Warnings:[/][/]")
        for w in decision.warnings:
            console.print(f"  [yellow]! {w}[/]")

    console.print()


@invest_app.command("quick")
def cmd_invest_quick(
    tickers: str = typer.Argument(..., help="Tickers to scan (comma-separated)"),
    budget: float = typer.Option(50_000_000, "--budget", "-b"),
    source: Optional[str] = typer.Option(None, "--source", "-s"),
) -> None:
    """Quick scan multiple tickers — show verdict summary table.

    Examples:
        saham invest quick BBCA,BBRI,TLKM,ASII,BMRI
    """
    from saham_id.invest import analyze_investment

    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    src = get_source(source)

    table = Table(title="Investment Quick Scan")
    table.add_column("Ticker", style="cyan")
    table.add_column("Verdict")
    table.add_column("Score", justify="right")
    table.add_column("R:R", justify="right")
    table.add_column("Conviction")
    table.add_column("Action")

    with console.status(f"Scanning {len(ticker_list)} tickers..."):
        for ticker in ticker_list:
            try:
                d = analyze_investment(ticker, budget=budget, source=src)
                v_color = "green" if d.should_buy else "yellow" if d.verdict.value == "WAIT" else "red"
                action = f"Beli {d.position.lots} lot" if d.should_buy else "—"
                table.add_row(
                    ticker,
                    f"[{v_color}]{d.verdict.value}[/]",
                    f"{d.entry_score:.0f}",
                    f"{d.risk_reward.risk_reward_ratio:.1f}:1",
                    d.conviction.value,
                    action,
                )
            except Exception as exc:
                table.add_row(ticker, "[red]ERROR[/]", "—", "—", "—", str(exc)[:30])

    console.print(table)


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
