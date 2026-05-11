"""Market regime detection — classify current market conditions.

Determines whether the market is in:
    - TRENDING_UP: strong bullish, follow momentum
    - TRENDING_DOWN: strong bearish, defensive/short
    - SIDEWAYS: range-bound, mean-reversion strategies
    - HIGH_VOLATILITY: crisis/euphoria, reduce position size
    - LOW_VOLATILITY: calm, breakout potential

Usage:
    from saham_id.market.regime import detect_regime, MarketRegime

    regime = detect_regime(source=src)
    print(regime.state)         # "TRENDING_UP"
    print(regime.confidence)    # 0.85
    print(regime.recommended_strategies)  # ["swing_breakout", "bpjs"]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


class RegimeState(str, Enum):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"


# Strategy recommendations per regime
REGIME_STRATEGIES: dict[RegimeState, list[str]] = {
    RegimeState.TRENDING_UP: ["swing_breakout", "bpjs", "momentum", "dip_buying"],
    RegimeState.TRENDING_DOWN: ["swing_reversal", "defensive", "reduce_exposure"],
    RegimeState.SIDEWAYS: ["swing_pullback", "mean_reversion", "range_trading"],
    RegimeState.HIGH_VOLATILITY: ["scalping", "reduce_size", "hedging"],
    RegimeState.LOW_VOLATILITY: ["breakout_watch", "accumulate", "increase_size"],
}


@dataclass
class MarketRegime:
    """Current market regime assessment."""

    state: RegimeState
    confidence: float  # 0.0 - 1.0
    breadth_score: float = 0.0  # A/D ratio normalized
    trend_score: float = 0.0  # price vs MAs
    volatility_score: float = 0.0  # current vol vs historical
    momentum_score: float = 0.0  # overall market momentum
    description: str = ""
    timestamp: Optional[datetime] = None
    details: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    @property
    def recommended_strategies(self) -> list[str]:
        return REGIME_STRATEGIES.get(self.state, [])

    @property
    def position_size_multiplier(self) -> float:
        """Suggested position size adjustment based on regime."""
        multipliers = {
            RegimeState.TRENDING_UP: 1.0,
            RegimeState.TRENDING_DOWN: 0.5,
            RegimeState.SIDEWAYS: 0.75,
            RegimeState.HIGH_VOLATILITY: 0.5,
            RegimeState.LOW_VOLATILITY: 1.0,
        }
        return multipliers.get(self.state, 0.75)


def detect_regime(
    index_ticker: str = "^JKSE",
    universe: str = "LQ45",
    lookback: int = 60,
    source: Optional[DataSource] = None,
) -> MarketRegime:
    """Detect current market regime using IHSG + breadth analysis.

    Methodology:
        1. Trend: IHSG price vs SMA20/SMA50 alignment
        2. Breadth: % of LQ45 stocks above their SMA20
        3. Volatility: current ATR% vs 60-day average
        4. Momentum: IHSG 20-day return percentile

    Parameters:
        index_ticker: Market index to analyze (default: ^JKSE = IHSG)
        universe: Stock universe for breadth calculation
        lookback: Days for historical context
        source: DataSource instance
    """
    from saham_id.analysis.indicators import atr, sma
    from saham_id.data.universe import get_universe

    src = source or get_source()

    # --- 1. Index trend analysis ---
    trend_score = 0.0
    try:
        idx_df = src.get_ohlc(index_ticker, period="1y", interval="1d")
        if not idx_df.empty and len(idx_df) >= 50:
            close = idx_df["close"]
            sma_20 = sma(close, 20)
            sma_50 = sma(close, 50)

            last_close = float(close.iloc[-1]) if close.iloc[-1] else 0
            last_sma20 = float(sma_20.iloc[-1]) if sma_20.iloc[-1] else 0
            last_sma50 = float(sma_50.iloc[-1]) if sma_50.iloc[-1] else 0

            if last_sma20 > 0 and last_sma50 > 0:
                # Close above both MAs = bullish
                if last_close > last_sma20 > last_sma50:
                    trend_score = 1.0
                elif last_close > last_sma20:
                    trend_score = 0.5
                elif last_close < last_sma20 < last_sma50:
                    trend_score = -1.0
                elif last_close < last_sma20:
                    trend_score = -0.5
    except Exception:
        pass

    # --- 2. Volatility analysis ---
    volatility_score = 0.0
    try:
        if not idx_df.empty and len(idx_df) >= lookback:
            atr_series = atr(idx_df["high"], idx_df["low"], idx_df["close"], window=14)
            last_atr = atr_series.iloc[-1]
            last_close_val = float(idx_df["close"].iloc[-1]) if idx_df["close"].iloc[-1] else 1
            if last_atr is not None and last_close_val > 0:
                current_atr_pct = float(last_atr) / last_close_val

                # Compare to historical ATR%
                historical_atrs = []
                for i in range(max(0, len(atr_series) - lookback), len(atr_series) - 1):
                    a = atr_series.iloc[i]
                    c = idx_df["close"].iloc[i]
                    if a is not None and c is not None and float(c) > 0:
                        historical_atrs.append(float(a) / float(c))

                if historical_atrs:
                    avg_atr_pct = sum(historical_atrs) / len(historical_atrs)
                    if avg_atr_pct > 0:
                        vol_ratio = current_atr_pct / avg_atr_pct
                        if vol_ratio > 1.5:
                            volatility_score = 1.0  # high vol
                        elif vol_ratio > 1.2:
                            volatility_score = 0.5
                        elif vol_ratio < 0.7:
                            volatility_score = -1.0  # low vol
                        elif vol_ratio < 0.85:
                            volatility_score = -0.5
    except Exception:
        pass

    # --- 3. Breadth analysis ---
    breadth_score = 0.0
    try:
        tickers = get_universe(universe)
        above_sma20 = 0
        total_checked = 0

        for ticker in tickers[:20]:  # Check first 20 for speed
            try:
                df = src.get_ohlc(ticker, period="3mo", interval="1d")
                if df.empty or len(df) < 25:
                    continue
                close_t = df["close"]
                sma_20_t = sma(close_t, 20)
                last_c = close_t.iloc[-1]
                last_s = sma_20_t.iloc[-1]
                if last_c is not None and last_s is not None:
                    total_checked += 1
                    if float(last_c) > float(last_s):
                        above_sma20 += 1
            except Exception:
                continue

        if total_checked > 0:
            pct_above = above_sma20 / total_checked
            breadth_score = (pct_above - 0.5) * 2  # normalize: 0.5 -> 0, 1.0 -> 1, 0 -> -1
    except Exception:
        pass

    # --- 4. Momentum score ---
    momentum_score = 0.0
    try:
        if not idx_df.empty and len(idx_df) >= 20:
            close = idx_df["close"]
            last_c = float(close.iloc[-1]) if close.iloc[-1] else 0
            prev_20 = float(close.iloc[-21]) if close.iloc[-21] else 0
            if prev_20 > 0:
                ret_20d = (last_c - prev_20) / prev_20
                if ret_20d > 0.05:
                    momentum_score = 1.0
                elif ret_20d > 0.02:
                    momentum_score = 0.5
                elif ret_20d < -0.05:
                    momentum_score = -1.0
                elif ret_20d < -0.02:
                    momentum_score = -0.5
    except Exception:
        pass

    # --- Determine regime ---
    composite = trend_score * 0.35 + breadth_score * 0.25 + momentum_score * 0.25 + (-abs(volatility_score)) * 0.15

    # High volatility overrides trend
    if volatility_score >= 1.0:
        state = RegimeState.HIGH_VOLATILITY
        confidence = min(1.0, volatility_score * 0.7)
        description = "Market experiencing elevated volatility — reduce position sizes"
    elif volatility_score <= -1.0:
        state = RegimeState.LOW_VOLATILITY
        confidence = min(1.0, abs(volatility_score) * 0.6)
        description = "Low volatility environment — watch for breakouts"
    elif composite >= 0.4:
        state = RegimeState.TRENDING_UP
        confidence = min(1.0, composite * 0.8)
        description = "Bullish trend — momentum strategies favored"
    elif composite <= -0.4:
        state = RegimeState.TRENDING_DOWN
        confidence = min(1.0, abs(composite) * 0.8)
        description = "Bearish trend — defensive positioning recommended"
    else:
        state = RegimeState.SIDEWAYS
        confidence = max(0.3, 1.0 - abs(composite) * 2)
        description = "Range-bound market — mean-reversion strategies favored"

    return MarketRegime(
        state=state,
        confidence=confidence,
        breadth_score=breadth_score,
        trend_score=trend_score,
        volatility_score=volatility_score,
        momentum_score=momentum_score,
        description=description,
        details={
            "trend": trend_score,
            "breadth": breadth_score,
            "volatility": volatility_score,
            "momentum": momentum_score,
            "composite": composite,
        },
    )
