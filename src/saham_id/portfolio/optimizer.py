"""Portfolio optimizer — correlation-weighted allocation.

Uses Modern Portfolio Theory concepts to suggest allocation weights
that minimize risk for a given return target, using correlation data.

Usage:
    from saham_id.portfolio.optimizer import optimize_allocation, equal_weight

    # Equal weight (baseline)
    weights = equal_weight(["BBCA", "BBRI", "TLKM", "ASII"])

    # Risk-parity (inverse volatility)
    weights = risk_parity(["BBCA", "BBRI", "TLKM"], source=src)

    # Min-correlation (diversification)
    weights = min_correlation_allocation(["BBCA", "BBRI", "TLKM", "ASII"], source=src)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Optional

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


@dataclass
class AllocationResult:
    """Result of portfolio optimization."""

    tickers: list[str]
    weights: dict[str, float]  # ticker -> weight (sums to 1.0)
    method: str
    metrics: dict[str, float] = field(default_factory=dict)

    @property
    def top_allocations(self) -> list[tuple[str, float]]:
        """Sorted allocations (highest weight first)."""
        return sorted(self.weights.items(), key=lambda x: x[1], reverse=True)

    def allocation_pct(self, capital: float) -> dict[str, float]:
        """Convert weights to IDR amounts."""
        return {t: w * capital for t, w in self.weights.items()}


def equal_weight(tickers: Iterable[str]) -> AllocationResult:
    """Equal-weight allocation — simplest diversification.

    Each stock gets 1/N of the portfolio.
    """
    ticker_list = list(tickers)
    n = len(ticker_list)
    if n == 0:
        return AllocationResult(tickers=[], weights={}, method="equal_weight")

    weight = 1.0 / n
    weights = {t: weight for t in ticker_list}

    return AllocationResult(
        tickers=ticker_list,
        weights=weights,
        method="equal_weight",
        metrics={"n_stocks": n, "max_weight": weight},
    )


def risk_parity(
    tickers: Iterable[str],
    period: str = "1y",
    source: Optional[DataSource] = None,
) -> AllocationResult:
    """Risk-parity allocation — inverse volatility weighting.

    Stocks with lower volatility get higher allocation, so each
    position contributes roughly equal risk.
    """
    src = source or get_source()
    ticker_list = list(tickers)

    volatilities: dict[str, float] = {}
    for ticker in ticker_list:
        try:
            df = src.get_ohlc(ticker, period=period, interval="1d")
            if df.empty or len(df) < 30:
                continue
            returns = df["close"].pct_change().dropna()
            vol = returns.std()
            if vol and vol > 0:
                volatilities[ticker] = vol
        except Exception:
            continue

    if not volatilities:
        return equal_weight(ticker_list)

    # Inverse volatility weights
    inv_vols = {t: 1.0 / v for t, v in volatilities.items()}
    total_inv = sum(inv_vols.values())

    weights = {t: iv / total_inv for t, iv in inv_vols.items()}

    return AllocationResult(
        tickers=list(weights.keys()),
        weights=weights,
        method="risk_parity",
        metrics={
            "n_stocks": len(weights),
            "max_weight": max(weights.values()),
            "min_weight": min(weights.values()),
            "avg_volatility": sum(volatilities.values()) / len(volatilities),
        },
    )


def min_correlation_allocation(
    tickers: Iterable[str],
    period: str = "1y",
    source: Optional[DataSource] = None,
) -> AllocationResult:
    """Minimum-correlation allocation — favors uncorrelated stocks.

    Combines inverse-volatility with a correlation penalty:
    stocks that are highly correlated to others get reduced weight.
    """
    from saham_id.analysis.correlation import correlation_matrix

    src = source or get_source()
    ticker_list = list(tickers)

    # First get volatilities
    volatilities: dict[str, float] = {}
    for ticker in ticker_list:
        try:
            df = src.get_ohlc(ticker, period=period, interval="1d")
            if df.empty or len(df) < 30:
                continue
            returns = df["close"].pct_change().dropna()
            vol = returns.std()
            if vol and vol > 0:
                volatilities[ticker] = vol
        except Exception:
            continue

    valid_tickers = list(volatilities.keys())
    if len(valid_tickers) < 2:
        return equal_weight(valid_tickers)

    # Get correlation matrix
    corr_result = correlation_matrix(valid_tickers, period=period, source=src)

    # Compute average correlation for each stock
    avg_correlations: dict[str, float] = {}
    for ticker in valid_tickers:
        if ticker in corr_result.matrix:
            corrs = [
                abs(v) for k, v in corr_result.matrix[ticker].items()
                if k != ticker
            ]
            avg_correlations[ticker] = sum(corrs) / len(corrs) if corrs else 0.5
        else:
            avg_correlations[ticker] = 0.5

    # Score = inverse_vol * (1 - avg_correlation)
    # Higher score = lower vol AND lower correlation = better diversifier
    scores: dict[str, float] = {}
    for ticker in valid_tickers:
        inv_vol = 1.0 / volatilities[ticker]
        corr_bonus = 1.0 - avg_correlations[ticker]  # lower correlation = higher bonus
        scores[ticker] = inv_vol * (0.5 + corr_bonus)  # blend

    total_score = sum(scores.values())
    if total_score == 0:
        return equal_weight(valid_tickers)

    weights = {t: s / total_score for t, s in scores.items()}

    return AllocationResult(
        tickers=list(weights.keys()),
        weights=weights,
        method="min_correlation",
        metrics={
            "n_stocks": len(weights),
            "max_weight": max(weights.values()),
            "min_weight": min(weights.values()),
            "avg_correlation": sum(avg_correlations.values()) / len(avg_correlations),
        },
    )


def max_diversification(
    tickers: Iterable[str],
    capital: float,
    max_per_stock_pct: float = 0.25,
    min_per_stock_pct: float = 0.05,
    period: str = "1y",
    source: Optional[DataSource] = None,
) -> AllocationResult:
    """Maximum diversification allocation with constraints.

    Allocates using min-correlation method but enforces:
    - Max X% per stock (default 25%)
    - Min Y% per stock (default 5%)
    - Removes stocks that would get < min allocation
    """
    result = min_correlation_allocation(tickers, period=period, source=source)

    if not result.weights:
        return result

    # Apply constraints
    constrained: dict[str, float] = {}
    for ticker, weight in result.weights.items():
        if weight < min_per_stock_pct:
            continue  # Skip stocks with too-low allocation
        constrained[ticker] = min(weight, max_per_stock_pct)

    # Re-normalize
    if constrained:
        total = sum(constrained.values())
        constrained = {t: w / total for t, w in constrained.items()}

    return AllocationResult(
        tickers=list(constrained.keys()),
        weights=constrained,
        method="max_diversification",
        metrics={
            **result.metrics,
            "max_per_stock_pct": max_per_stock_pct,
            "min_per_stock_pct": min_per_stock_pct,
            "capital": capital,
        },
    )
