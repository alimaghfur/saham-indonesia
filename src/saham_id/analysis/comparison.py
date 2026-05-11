"""Stock comparison — head-to-head analysis of 2-5 stocks.

Compare returns, volatility, risk metrics, and indicators side-by-side.

Usage:
    from saham_id.analysis.comparison import compare_stocks

    result = compare_stocks(["BBCA", "BBRI", "BMRI"], period="1y")
    print(result.to_dataframe())
    print(result.winner)  # Best performer
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Literal, Optional

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


@dataclass
class StockMetrics:
    """Metrics for one stock in a comparison."""

    ticker: str
    period_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe: float = 0.0
    max_drawdown: float = 0.0
    avg_volume: float = 0.0
    beta: float = 0.0
    last_price: float = 0.0
    rsi: Optional[float] = None


@dataclass
class ComparisonResult:
    """Result of comparing multiple stocks."""

    tickers: list[str]
    period: str
    metrics: dict[str, StockMetrics]
    as_of: datetime = field(default_factory=datetime.utcnow)

    @property
    def winner(self) -> str:
        """Best performer by period return."""
        if not self.metrics:
            return ""
        return max(self.metrics.items(), key=lambda x: x[1].period_return)[0]

    @property
    def lowest_risk(self) -> str:
        """Lowest volatility stock."""
        if not self.metrics:
            return ""
        return min(self.metrics.items(), key=lambda x: x[1].volatility)[0]

    @property
    def best_risk_adjusted(self) -> str:
        """Best Sharpe ratio."""
        if not self.metrics:
            return ""
        return max(self.metrics.items(), key=lambda x: x[1].sharpe)[0]

    def ranking(self, by: str = "period_return") -> list[tuple[str, float]]:
        """Rank stocks by a metric."""
        reverse = by != "volatility" and by != "max_drawdown"
        items = [(t, getattr(m, by, 0.0)) for t, m in self.metrics.items()]
        items.sort(key=lambda x: x[1], reverse=reverse)
        return items

    def to_dataframe(self):
        """Convert to pandas DataFrame for display."""
        import pandas as pd

        rows = []
        for ticker, m in self.metrics.items():
            rows.append({
                "ticker": ticker,
                "return": f"{m.period_return*100:.2f}%",
                "ann_return": f"{m.annualized_return*100:.2f}%",
                "volatility": f"{m.volatility*100:.2f}%",
                "sharpe": f"{m.sharpe:.2f}",
                "max_dd": f"{m.max_drawdown*100:.2f}%",
                "avg_volume": f"{m.avg_volume:,.0f}",
                "last_price": f"{m.last_price:,.0f}",
                "rsi": f"{m.rsi:.1f}" if m.rsi else "-",
            })
        return pd.DataFrame(rows)


def compare_stocks(
    tickers: Iterable[str],
    period: str = "1y",
    benchmark: str = "^JKSE",
    source: Optional[DataSource] = None,
) -> ComparisonResult:
    """Compare multiple stocks head-to-head.

    Computes return, volatility, Sharpe, max drawdown, and other
    metrics for each stock over the given period.

    Parameters:
        tickers: List of IDX tickers to compare (2-10)
        period: Historical period (e.g. "6mo", "1y", "2y")
        benchmark: Market index for beta calculation
        source: DataSource instance
    """
    from saham_id.analysis.indicators import rsi
    from saham_id.analysis.risk import max_drawdown, sharpe, volatility

    src = source or get_source()
    ticker_list = list(tickers)
    metrics: dict[str, StockMetrics] = {}

    # Fetch benchmark returns for beta
    benchmark_returns = None
    try:
        bench_df = src.get_ohlc(benchmark, period=period, interval="1d")
        if not bench_df.empty and len(bench_df) > 30:
            benchmark_returns = bench_df["close"].pct_change().dropna()
    except Exception:
        pass

    for ticker in ticker_list:
        try:
            df = src.get_ohlc(ticker, period=period, interval="1d")
            if df.empty or len(df) < 20:
                continue

            close = df["close"]
            returns = close.pct_change().dropna()

            # Period return
            first_close = float(close.iloc[0])
            last_close = float(close.iloc[-1])
            period_ret = (last_close - first_close) / first_close if first_close > 0 else 0.0

            # Annualized return (approximate)
            n_days = len(df)
            years = n_days / 252.0
            ann_ret = (1 + period_ret) ** (1 / max(years, 0.01)) - 1 if period_ret > -1 else 0.0

            # Risk metrics
            vol = volatility(returns)
            sh = sharpe(returns)
            mdd = max_drawdown(close)

            # Average volume
            avg_vol = float(df["volume"].mean()) if "volume" in df.columns else 0.0

            # RSI
            rsi_series = rsi(close, 14)
            rsi_val = rsi_series.iloc[-1]
            rsi_float = float(rsi_val) if rsi_val is not None else None

            # Beta vs benchmark
            beta_val = 0.0
            if benchmark_returns is not None:
                from saham_id.analysis.risk import beta
                beta_val = beta(returns, benchmark_returns)

            metrics[ticker] = StockMetrics(
                ticker=ticker,
                period_return=period_ret,
                annualized_return=ann_ret,
                volatility=vol,
                sharpe=sh,
                max_drawdown=mdd,
                avg_volume=avg_vol,
                beta=beta_val,
                last_price=last_close,
                rsi=rsi_float,
            )
        except Exception:
            continue

    return ComparisonResult(
        tickers=list(metrics.keys()),
        period=period,
        metrics=metrics,
    )
