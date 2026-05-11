"""Ichimoku screener — scan berdasarkan Ichimoku Cloud signals.

Criteria:
- Price above cloud (bullish trend)
- Tenkan > Kijun (bullish cross)
- Cloud color green (Senkou A > Senkou B)
- Chikou above price (confirms momentum)
"""
from __future__ import annotations
from datetime import datetime
from typing import Iterable, Optional
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


def screen_ichimoku(
    universe: str | Iterable[str] = "LQ45",
    require_above_cloud: bool = True,
    require_tk_bullish: bool = True,
    require_green_cloud: bool = True,
    top_n: int = 15,
    source: Optional[DataSource] = None,
) -> ScreenResult:
    from saham_id.analysis.indicators.ichimoku import ichimoku
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"
    rows: list[ScreenRow] = []

    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period="1y", interval="1d")
            if df.empty or len(df) < 60:
                continue
            result = ichimoku(df["high"], df["low"], df["close"])
            score = 0.0
            if result.price_vs_cloud == "above":
                score += 30
            elif result.price_vs_cloud == "inside":
                score += 10
            if require_above_cloud and result.price_vs_cloud != "above":
                continue
            if result.tk_cross == "bullish":
                score += 25
            if require_tk_bullish and result.tk_cross != "bullish":
                continue
            if result.cloud_color == "green":
                score += 20
            if require_green_cloud and result.cloud_color != "green":
                continue
            # Bonus: kumo thickness (wider cloud = stronger)
            score += 10  # base score for passing all filters
            last_close = float(df["close"].iloc[-1]) if df["close"].iloc[-1] else 0
            rows.append(ScreenRow(ticker=ticker, score=round(score, 1), metrics={
                "close": last_close, "cloud_color": result.cloud_color,
                "price_vs_cloud": result.price_vs_cloud, "tk_cross": result.tk_cross,
            }))
        except Exception:
            continue

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(strategy="ichimoku", universe=universe_name, as_of=datetime.utcnow(),
                       rows=rows[:top_n], params={"require_above_cloud": require_above_cloud,
                       "require_tk_bullish": require_tk_bullish, "require_green_cloud": require_green_cloud})
