"""Correlation analysis — inter-stock and sector correlations.

Useful for:
    - Portfolio diversification (find uncorrelated stocks)
    - Pair trading (find highly correlated stocks)
    - Sector rotation analysis
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

import pandas as pd

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


@dataclass
class CorrelationResult:
    """Result of a correlation analysis."""

    tickers: list[str]
    period: str
    matrix: dict[str, dict[str, float]]  # ticker -> ticker -> correlation
    highest_pairs: list[tuple[str, str, float]] = field(default_factory=list)
    lowest_pairs: list[tuple[str, str, float]] = field(default_factory=list)


def correlation_matrix(
    tickers: Iterable[str],
    period: str = "1y",
    source: Optional[DataSource] = None,
) -> CorrelationResult:
    """Compute pairwise Pearson correlation of daily returns.

    Parameters:
        tickers: List of IDX tickers to compare
        period: Historical period (e.g. "6mo", "1y", "2y")
        source: DataSource instance (default: from config)

    Returns:
        CorrelationResult with full matrix and sorted pairs
    """
    src = source or get_source()
    ticker_list = list(tickers)

    # Fetch returns for each ticker
    returns_data: dict[str, list[float]] = {}
    valid_tickers: list[str] = []

    for ticker in ticker_list:
        try:
            df = src.get_ohlc(ticker, period=period, interval="1d")
            if df.empty or len(df) < 30:
                continue
            # Compute daily returns
            close = df["close"]
            rets = close.pct_change().dropna()
            returns_data[ticker] = list(rets._data) if hasattr(rets, '_data') else list(rets)
            valid_tickers.append(ticker)
        except Exception:
            continue

    if len(valid_tickers) < 2:
        return CorrelationResult(
            tickers=valid_tickers,
            period=period,
            matrix={},
        )

    # Align lengths (use shortest common period)
    min_len = min(len(v) for v in returns_data.values())
    for t in valid_tickers:
        returns_data[t] = returns_data[t][-min_len:]

    # Compute correlation matrix
    matrix: dict[str, dict[str, float]] = {}
    pairs: list[tuple[str, str, float]] = []

    for i, t1 in enumerate(valid_tickers):
        matrix[t1] = {}
        for j, t2 in enumerate(valid_tickers):
            if i == j:
                matrix[t1][t2] = 1.0
            elif j < i:
                # Already computed
                matrix[t1][t2] = matrix[t2][t1]
            else:
                corr = _pearson_correlation(returns_data[t1], returns_data[t2])
                matrix[t1][t2] = corr
                pairs.append((t1, t2, corr))

    # Sort pairs
    pairs.sort(key=lambda x: x[2], reverse=True)
    highest = pairs[:10]
    lowest = list(reversed(pairs[-10:])) if len(pairs) >= 10 else list(reversed(pairs))

    return CorrelationResult(
        tickers=valid_tickers,
        period=period,
        matrix=matrix,
        highest_pairs=highest,
        lowest_pairs=lowest,
    )


def find_uncorrelated(
    target_ticker: str,
    universe: str | Iterable[str] = "LQ45",
    period: str = "1y",
    max_correlation: float = 0.3,
    top_n: int = 10,
    source: Optional[DataSource] = None,
) -> list[tuple[str, float]]:
    """Find stocks with low correlation to a target ticker.

    Useful for portfolio diversification.

    Returns:
        List of (ticker, correlation) sorted by absolute correlation ascending.
    """
    from saham_id.data.universe import get_universe

    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)

    # Remove target from universe
    tickers = [t for t in tickers if t.upper() != target_ticker.upper()]

    # Get target returns
    try:
        target_df = src.get_ohlc(target_ticker, period=period, interval="1d")
        target_rets = target_df["close"].pct_change().dropna()
        target_data = list(target_rets._data) if hasattr(target_rets, '_data') else list(target_rets)
    except Exception:
        return []

    # Compare with each ticker in universe
    results: list[tuple[str, float]] = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period=period, interval="1d")
            if df.empty or len(df) < 30:
                continue
            rets = df["close"].pct_change().dropna()
            rets_data = list(rets._data) if hasattr(rets, '_data') else list(rets)

            # Align lengths
            n = min(len(target_data), len(rets_data))
            corr = _pearson_correlation(target_data[-n:], rets_data[-n:])

            if abs(corr) <= max_correlation:
                results.append((ticker, corr))
        except Exception:
            continue

    results.sort(key=lambda x: abs(x[1]))
    return results[:top_n]


def find_correlated(
    target_ticker: str,
    universe: str | Iterable[str] = "LQ45",
    period: str = "1y",
    min_correlation: float = 0.7,
    top_n: int = 10,
    source: Optional[DataSource] = None,
) -> list[tuple[str, float]]:
    """Find stocks highly correlated with a target ticker.

    Useful for pair trading or finding substitutes.

    Returns:
        List of (ticker, correlation) sorted by correlation descending.
    """
    from saham_id.data.universe import get_universe

    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    tickers = [t for t in tickers if t.upper() != target_ticker.upper()]

    try:
        target_df = src.get_ohlc(target_ticker, period=period, interval="1d")
        target_rets = target_df["close"].pct_change().dropna()
        target_data = list(target_rets._data) if hasattr(target_rets, '_data') else list(target_rets)
    except Exception:
        return []

    results: list[tuple[str, float]] = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period=period, interval="1d")
            if df.empty or len(df) < 30:
                continue
            rets = df["close"].pct_change().dropna()
            rets_data = list(rets._data) if hasattr(rets, '_data') else list(rets)

            n = min(len(target_data), len(rets_data))
            corr = _pearson_correlation(target_data[-n:], rets_data[-n:])

            if corr >= min_correlation:
                results.append((ticker, corr))
        except Exception:
            continue

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def _pearson_correlation(x: list[float], y: list[float]) -> float:
    """Compute Pearson correlation between two equal-length lists."""
    n = min(len(x), len(y))
    if n < 5:
        return 0.0

    x = x[:n]
    y = y[:n]

    # Filter out None/NaN
    valid = [
        (a, b) for a, b in zip(x, y)
        if a is not None and b is not None
        and not (isinstance(a, float) and a != a)
        and not (isinstance(b, float) and b != b)
    ]
    if len(valid) < 5:
        return 0.0

    xs, ys = zip(*valid)
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n

    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / n
    sx = (sum((a - mx) ** 2 for a in xs) / n) ** 0.5
    sy = (sum((b - my) ** 2 for b in ys) / n) ** 0.5

    if sx == 0 or sy == 0:
        return 0.0

    return cov / (sx * sy)
