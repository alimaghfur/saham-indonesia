"""Scalping screener — high-frequency momentum scanner.

Identifies stocks with optimal characteristics for intraday scalping:
    1. High liquidity (volume & transaction value)
    2. Sufficient volatility (ATR% > threshold)
    3. Elevated relative volume (RVOL > 2x)
    4. Tight price movement patterns (momentum bursts)

Data requirement:
    Intraday bars (1m or 5m). Works best with iTick or similar realtime source.
    Falls back to daily data from yfinance for approximate screening.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from saham_id.analysis.indicators import atr, rvol
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource, NotImplementedForSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow


def _compute_atr_pct(df, window: int = 14) -> float | None:
    """Compute ATR as a percentage of close price."""
    if len(df) < window + 1:
        return None
    atr_series = atr(df["high"], df["low"], df["close"], window=window)
    last_atr = atr_series.iloc[-1]
    last_close = df["close"].iloc[-1]
    if last_atr is None or last_close is None or last_close == 0:
        return None
    return float(last_atr) / float(last_close)


def _compute_rvol(df, window: int = 20) -> float | None:
    """Compute relative volume (current vs N-period average)."""
    if len(df) < window + 1:
        return None
    rv = rvol(df["volume"], window=window)
    last_rv = rv.iloc[-1]
    if last_rv is None:
        return None
    return float(last_rv)


def _compute_momentum_score(df, lookback: int = 5) -> float:
    """Compute short-term momentum score.

    Combines:
        - Price velocity (rate of recent price change)
        - Volume acceleration (recent volume vs prior volume)
        - Consecutive direction bars
    """
    if len(df) < lookback + 1:
        return 0.0

    # Price velocity: return over last N bars
    close_data = df["close"]
    price_now = close_data.iloc[-1]
    price_prev = close_data.iloc[-lookback - 1]
    if price_prev is None or price_prev == 0 or price_now is None:
        return 0.0
    price_velocity = abs(float(price_now) - float(price_prev)) / float(price_prev)

    # Volume acceleration: last bar volume vs average of prior bars
    vol_data = df["volume"]
    last_vol = vol_data.iloc[-1]
    if last_vol is None:
        return price_velocity * 100

    prior_vols = [vol_data.iloc[-(i + 2)] for i in range(min(lookback, len(df) - 1))]
    prior_vols = [v for v in prior_vols if v is not None and v > 0]
    avg_prior_vol = sum(prior_vols) / len(prior_vols) if prior_vols else 1
    vol_accel = float(last_vol) / avg_prior_vol if avg_prior_vol > 0 else 1.0

    # Consecutive direction: count bars in same direction
    consecutive = 0
    for i in range(1, min(lookback + 1, len(df))):
        curr = close_data.iloc[-i]
        prev = close_data.iloc[-i - 1] if i + 1 <= len(df) else None
        if curr is None or prev is None:
            break
        if (float(curr) - float(prev)) * (float(price_now) - float(price_prev)) > 0:
            consecutive += 1
        else:
            break

    # Composite momentum score
    score = (price_velocity * 100) * 0.4 + (vol_accel - 1.0) * 0.4 + consecutive * 0.2
    return max(0.0, score)


def screen(
    universe: str | Iterable[str] = "LQ45",
    min_avg_volume: int = 10_000_000,
    min_transaction_value: float = 50_000_000_000,
    min_atr_pct: float = 0.015,
    min_rvol: float = 2.0,
    lookback_momentum: int = 5,
    top_n: int = 10,
    source: DataSource | None = None,
) -> ScreenResult:
    """Screen for scalping candidates using intraday or daily data.

    Scoring formula:
        score = w_vol * normalized_rvol
              + w_atr * normalized_atr_pct
              + w_mom * momentum_score
              + w_liq * liquidity_bonus

    Parameters:
        universe: Stock universe or list of tickers
        min_avg_volume: Minimum average daily volume (shares)
        min_transaction_value: Minimum avg daily transaction value (IDR)
        min_atr_pct: Minimum ATR as % of price (e.g. 0.015 = 1.5%)
        min_rvol: Minimum relative volume vs 20-day average
        lookback_momentum: Bars to look back for momentum calculation
        top_n: Number of top candidates to return
        source: DataSource instance (default: from config)
    """
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    universe_name = universe if isinstance(universe, str) else "custom"

    # Try intraday first (5m bars, last 5 days), fall back to daily
    use_intraday = True
    test_interval = "5m"
    test_period = "5d"

    rows: list[ScreenRow] = []
    for ticker in tickers:
        try:
            # Attempt intraday data
            if use_intraday:
                try:
                    df = src.get_ohlc(ticker, period=test_period, interval=test_interval)
                except NotImplementedForSource:
                    # Source doesn't support intraday — switch to daily for all
                    use_intraday = False
                    df = src.get_ohlc(ticker, period="3mo", interval="1d")
                except Exception:
                    df = src.get_ohlc(ticker, period="3mo", interval="1d")
            else:
                df = src.get_ohlc(ticker, period="3mo", interval="1d")
        except Exception:
            continue

        if df.empty or len(df) < 25:
            continue

        df = df.copy()

        # --- Filter 1: Liquidity ---
        avg_volume = df["volume"].mean()
        if avg_volume is None or avg_volume < min_avg_volume:
            continue

        # Approximate transaction value = close * volume
        last_close = df["close"].iloc[-1]
        if last_close is None or last_close == 0:
            continue
        avg_value = float(avg_volume) * float(last_close)
        if avg_value < min_transaction_value:
            continue

        # --- Filter 2: Volatility (ATR%) ---
        atr_pct = _compute_atr_pct(df, window=14)
        if atr_pct is None or atr_pct < min_atr_pct:
            continue

        # --- Filter 3: Relative Volume ---
        current_rvol = _compute_rvol(df, window=20)
        if current_rvol is None or current_rvol < min_rvol:
            continue

        # --- Scoring ---
        momentum = _compute_momentum_score(df, lookback=lookback_momentum)

        # Normalize components for scoring
        rvol_normalized = min(current_rvol / 5.0, 1.0)  # Cap at 5x
        atr_normalized = min(atr_pct / 0.05, 1.0)  # Cap at 5%
        momentum_normalized = min(momentum / 5.0, 1.0)  # Cap score
        liquidity_bonus = min(avg_value / 500_000_000_000, 1.0)  # Cap at 500B

        score = (
            rvol_normalized * 30.0
            + atr_normalized * 25.0
            + momentum_normalized * 30.0
            + liquidity_bonus * 15.0
        )

        rows.append(
            ScreenRow(
                ticker=ticker,
                score=round(score, 2),
                metrics={
                    "close": round(float(last_close), 0),
                    "rvol": round(current_rvol, 2),
                    "atr_pct": round(atr_pct * 100, 3),
                    "momentum": round(momentum, 3),
                    "avg_volume": round(float(avg_volume), 0),
                    "avg_value": round(avg_value, 0),
                    "data_type": "intraday" if use_intraday else "daily",
                },
            )
        )

    rows.sort(key=lambda r: r.score, reverse=True)
    return ScreenResult(
        strategy="scalping",
        universe=universe_name,
        as_of=datetime.utcnow(),
        rows=rows[:top_n],
        params={
            "min_avg_volume": min_avg_volume,
            "min_transaction_value": min_transaction_value,
            "min_atr_pct": min_atr_pct,
            "min_rvol": min_rvol,
            "lookback_momentum": lookback_momentum,
        },
    )
