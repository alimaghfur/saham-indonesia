"""Download daily OHLCV data for a universe and cache to Parquet.

Useful for:
    - One-shot local backtesting (avoid re-fetching per run)
    - Offline development / test fixtures
    - Batched updates outside market hours

Usage:
    # Download LQ45, last 2 years, to data/cache/
    python scripts/download_daily_data.py --universe LQ45 --period 2y

    # Specific tickers from a file
    python scripts/download_daily_data.py \\
        --tickers-file my_watchlist.txt --period 5y --source yahoo

    # Update (merge new bars into existing parquet files)
    python scripts/download_daily_data.py --universe LQ45 --update
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from saham_id.config import settings
from saham_id.data.sources import get_source, list_sources
from saham_id.data.universe import UNIVERSES, get_universe


def _ticker_path(cache_dir: Path, ticker: str, interval: str) -> Path:
    return cache_dir / interval / f"{ticker.upper()}.parquet"


def _download_one(
    source_name: str,
    ticker: str,
    period: str,
    interval: str,
    cache_dir: Path,
    update: bool,
) -> tuple[str, int, str]:
    """Worker: download a single ticker. Returns (ticker, rows, status)."""
    out_path = _ticker_path(cache_dir, ticker, interval)
    try:
        src = get_source(source_name)
        df = src.get_ohlc(ticker, period=period, interval=interval)  # type: ignore[arg-type]
        if df is None or df.empty:
            return (ticker, 0, "empty")

        if update and out_path.exists():
            existing = pd.read_parquet(out_path)
            combined = pd.concat([existing, df])
            combined = combined[~combined.index.duplicated(keep="last")].sort_index()
            df = combined

        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_path)
        return (ticker, len(df), "ok")
    except Exception as exc:
        return (ticker, 0, f"error: {exc}")


def _resolve_tickers(args: argparse.Namespace) -> list[str]:
    if args.tickers:
        return [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    if args.tickers_file:
        path = Path(args.tickers_file)
        if not path.exists():
            print(f"Error: {path} does not exist", file=sys.stderr)
            sys.exit(2)
        return [ln.strip().upper() for ln in path.read_text().splitlines() if ln.strip()]
    if args.universe:
        return get_universe(args.universe)
    # Default: LQ45
    return get_universe("LQ45")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch-download daily OHLC to Parquet cache.",
    )
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--universe", choices=list(UNIVERSES), help="Use a built-in universe")
    g.add_argument("--tickers", help="Comma-separated tickers (e.g. BBCA,BBRI,TLKM)")
    g.add_argument("--tickers-file", help="File with one ticker per line")

    parser.add_argument(
        "--source",
        choices=list_sources(),
        default=settings.data_source_chain[0] if settings.data_source_chain else "yahoo",
        help="Data source to use",
    )
    parser.add_argument(
        "--period",
        default="2y",
        help="History window (1mo / 3mo / 6mo / 1y / 2y / 5y / ytd / max)",
    )
    parser.add_argument("--interval", default="1d", help="Bar interval (1d/1wk/1mo/1h/...)")
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=settings.cache_dir,
        help="Parquet cache directory",
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Parallel download workers"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Merge new bars into existing parquet files instead of overwriting",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.1,
        help="Seconds to sleep between task submissions (politeness delay)",
    )
    args = parser.parse_args()

    tickers = _resolve_tickers(args)
    if not tickers:
        print("No tickers to download.", file=sys.stderr)
        return 2

    args.cache_dir.mkdir(parents=True, exist_ok=True)
    print(
        f"Downloading {len(tickers)} tickers from '{args.source}' "
        f"period={args.period} interval={args.interval} "
        f"(cache={args.cache_dir}, workers={args.workers}, update={args.update})"
    )

    ok, empty, errs = 0, 0, 0
    total_rows = 0
    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futures = {}
        for t in tickers:
            futures[
                ex.submit(
                    _download_one,
                    args.source, t, args.period, args.interval,
                    args.cache_dir, args.update,
                )
            ] = t
            if args.sleep > 0:
                time.sleep(args.sleep)

        for fut in as_completed(futures):
            ticker, rows, status = fut.result()
            if status == "ok":
                ok += 1
                total_rows += rows
                print(f"  [OK]    {ticker:<12} {rows} rows")
            elif status == "empty":
                empty += 1
                print(f"  [EMPTY] {ticker}")
            else:
                errs += 1
                print(f"  [ERR]   {ticker}: {status}")

    print(
        f"\nDone. ok={ok} empty={empty} errors={errs} "
        f"total_rows={total_rows} cache={args.cache_dir}"
    )
    return 0 if errs == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
