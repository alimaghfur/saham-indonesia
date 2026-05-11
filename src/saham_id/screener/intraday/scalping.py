"""Scalping screener — short-timeframe momentum + liquidity + volatility scan.

Scalping needs three things at once:
    1. LIQUIDITY — tight spreads, plenty of volume (can enter/exit instantly)
    2. VOLATILITY — enough movement per bar to profit after fees
    3. MOMENTUM — a directional push right now

Data requirement:
    Intraday bars (1m/5m). Works with any DataSource that implements
    `get_ohlc(..., interval="1m" or "5m")`. yfinance supports only 7 days
    of 1m bars — for production use iTick/RTI/paid provider.

Score formula:
    score = w_mom  * zscore(recent_return)
          + w_rvol * relative_volume_excess
          + w_vol  * atr_pct
          + w_brk  * (distance above recent high, z-scored)

Filters:
    - min average volume per bar (likuiditas)
    - min average transaction value (Rp/bar)
    - min ATR% (movement per bar — otherwise fees eat returns)
    - min relative volume (is there action *right now*?)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Literal

import numpy as np
import pandas as pd

from saham_id.analysis.indicators import atr, rvol
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource, NotImplementedForSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


# Default ~24 x 1m bars = ~24 minutes of action; short enough to react,
# long enough to compute statistics.
DEFAULT_MOMENTUM_LOOKBACK = 24
DEFAULT_RVOL_WINDOW = 60


@dataclass
class ScalpingWeights:
    momentum: float = 0.35
    rvol: float = 0.30
    volatility: float = 0.20
    breakout: float = 0.15


def _zscore_last(series: pd.Series, window: int = 60) -> float:
    tail = series.dropna().tail(window)
    if len(tail) < 10:
        return 0.0
    mean = float(tail.mean())
    std = float(tail.std(ddof=0))
    if std == 0:
        return 0.0
    return (float(series.iloc[-1]) - mean) / std


def _compute_metrics(df: pd.DataFrame, momentum_lookback: int, rvol_window: int) -> dict | None:
    """Compute the per-ticker scalping feature set, or return None if insufficient data."""
    if df.empty or len(df) < max(momentum_lookback, rvol_window) + 5:
        return None

    df = df.copy()
    # Fee-free return over `momentum_lookback` bars
    df["ret_n"] = df["close"].pct_change(momentum_lookback)

    # ATR% relative to price — captures per-bar movement
    atr_series = atr(df["high"], df["low"], df["close"], window=14)
    atr_pct = float(atr_series.iloc[-1] / df["close"].iloc[-1]) if atr_series.iloc[-1] else 0.0

    # Relative volume (last bar vs rolling average)
    rv = rvol(df["volume"], window=20)
    rvol_now = float(rv.iloc[-1]) if rv.iloc[-1] and not np.isnan(rv.iloc[-1]) else 0.0

    # Liquidity proxies
    avg_value = float((df["close"] * df["volume"]).tail(rvol_window).mean())
    avg_volume = float(df["volume"].tail(rvol_window).mean())

    # Breakout z-score — distance above the 20-bar rolling high
    rolling_high = df["high"].rolling(20).max().shift(1)
    brk_series = (df["close"] - rolling_high) / rolling_high
    brk_z = _zscore_last(brk_series, window=60)

    # Momentum z-score
    mom_z = _zscore_last(df["ret_n"], window=60)

    return {
        "last": float(df["close"].iloc[-1]),
        "momentum_z": mom_z,
        "rvol": rvol_now,
        "atr_pct": atr_pct,
        "breakout_z": brk_z,
        "avg_volume_per_bar": avg_volume,
        "avg_value_per_bar": avg_value,
        "bars_used": int(len(df)),
    }


def _composite_score(metrics: dict, weights: ScalpingWeights) -> float:
    # rvol contributes only the part above 1.0 ("normal" baseline)
    rvol_excess = max(0.0, metrics["rvol"] - 1.0)
    return (
        weights.momentum * metrics["momentum_z"]
        + weights.rvol * rvol_excess
        + weights.volatility * metrics["atr_pct"] * 100  # scale to comparable range
        + weights.breakout * metrics["breakout_z"]
    )


def screen(
    universe: str | Iterable[str] = "LQ45",
    interval: Literal["1m", "5m"] = "5m",
    period: str = "5d",
    min_avg_volume_per_bar: int = 10_000,
    min_avg_value_per_bar: float = 50_000_000.0,   # Rp 50M per bar
    min_atr_pct: float = 0.005,                    # ATR at least 0.5% of price
    min_rvol: float = 1.2,
    momentum_lookback: int = DEFAULT_MOMENTUM_LOOKBACK,
    rvol_window: int = DEFAULT_RVOL_WINDOW,
    weights: ScalpingWeights | None = None,
    top_n: int = 10,
    source: DataSource | None = None,
) -> ScreenResult:
    """Screen for scalping candidates using intraday bars.

    Raises:
        NotImplementedForSource: if the chosen source cannot deliver the
            requested intraday interval (e.g. a skeleton adapter).
    """
    src = source or get_source()
    w = weights or ScalpingWeights()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    rows: list[ScreenRow] = []
    unsupported_source_error: NotImplementedForSource | None = None

    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period=period, interval=interval)  # type: ignore[arg-type]
        except NotImplementedForSource as exc:
            # The source flat-out doesn't support intraday. Remember and bail.
            unsupported_source_error = exc
            break
        except Exception:
            continue

        metrics = _compute_metrics(df, momentum_lookback, rvol_window)
        if metrics is None:
            continue

        # Liquidity & volatility gates
        if metrics["avg_volume_per_bar"] < min_avg_volume_per_bar:
            continue
        if metrics["avg_value_per_bar"] < min_avg_value_per_bar:
            continue
        if metrics["atr_pct"] < min_atr_pct:
            continue
        if metrics["rvol"] < min_rvol:
            continue

        score = _composite_score(metrics, w)
        if np.isnan(score) or np.isinf(score):
            continue

        rows.append(
            ScreenRow(
                ticker=ticker,
                score=float(score),
                metrics={
                    "last": round(metrics["last"], 2),
                    "momentum_z": round(metrics["momentum_z"], 3),
                    "rvol": round(metrics["rvol"], 2),
                    "atr_pct": round(metrics["atr_pct"], 5),
                    "breakout_z": round(metrics["breakout_z"], 3),
                    "avg_value_per_bar": round(metrics["avg_value_per_bar"], 0),
                    "bars_used": metrics["bars_used"],
                },
            )
        )

    if unsupported_source_error is not None and not rows:
        # Re-raise so caller knows to switch to a realtime-capable source
        raise unsupported_source_error

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(
        strategy="scalping",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "interval": interval,
            "period": period,
            "min_avg_volume_per_bar": min_avg_volume_per_bar,
            "min_avg_value_per_bar": min_avg_value_per_bar,
            "min_atr_pct": min_atr_pct,
            "min_rvol": min_rvol,
            "momentum_lookback": momentum_lookback,
            "rvol_window": rvol_window,
            "weights": w.__dict__,
        },
    )
