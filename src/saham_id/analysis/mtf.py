"""Multi-Timeframe Analysis (MTF) — evaluate a stock across multiple timeframes.

Principle: Higher timeframes define the trend, lower timeframes define entry.
When multiple timeframes align, the signal is stronger.

Usage:
    from saham_id.analysis.mtf import multi_timeframe_analysis

    result = multi_timeframe_analysis("BBCA", source=src)
    print(result.consensus)          # "BULLISH" / "BEARISH" / "NEUTRAL"
    print(result.alignment_score)    # 0.0 - 1.0
    print(result.timeframes["1d"])   # TimeframeView for daily
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

import pandas as pd

from saham_id.analysis.indicators import ema, macd, rsi, sma
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource

Bias = Literal["BULLISH", "BEARISH", "NEUTRAL"]

# Timeframe configurations
TIMEFRAMES: dict[str, dict] = {
    "weekly": {"period": "2y", "interval": "1wk", "weight": 3.0},
    "daily": {"period": "1y", "interval": "1d", "weight": 2.0},
    "4h": {"period": "3mo", "interval": "1h", "weight": 1.5},  # approximate 4h
    "1h": {"period": "1mo", "interval": "1h", "weight": 1.0},
}


@dataclass
class TimeframeView:
    """Analysis for a single timeframe."""

    name: str
    bias: Bias
    confidence: float  # 0.0 - 1.0
    rsi: Optional[float] = None
    trend: str = ""  # "uptrend", "downtrend", "sideways"
    close_vs_sma20: Optional[float] = None  # % above/below SMA20
    macd_signal: str = ""  # "bullish", "bearish", "neutral"
    notes: list[str] = field(default_factory=list)


@dataclass
class MTFResult:
    """Multi-timeframe analysis result."""

    ticker: str
    consensus: Bias
    alignment_score: float  # 0.0 = conflicting, 1.0 = all timeframes agree
    timeframes: dict[str, TimeframeView] = field(default_factory=dict)
    recommendation: str = ""
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


def _analyze_single_timeframe(df: pd.DataFrame, name: str) -> TimeframeView:
    """Analyze a single timeframe DataFrame."""
    if df.empty or len(df) < 20:
        return TimeframeView(name=name, bias="NEUTRAL", confidence=0.0,
                            notes=["Insufficient data"])

    close = df["close"]
    notes: list[str] = []

    # Trend: close vs SMA20 and SMA50
    sma_20 = sma(close, 20)
    last_close = close.iloc[-1]
    last_sma20 = sma_20.iloc[-1]

    if last_close is None or last_sma20 is None or float(last_sma20) == 0:
        return TimeframeView(name=name, bias="NEUTRAL", confidence=0.0,
                            notes=["Cannot compute indicators"])

    close_val = float(last_close)
    sma20_val = float(last_sma20)
    close_vs_sma20 = (close_val - sma20_val) / sma20_val

    # Determine trend
    if len(df) >= 50:
        sma_50 = sma(close, 50)
        last_sma50 = sma_50.iloc[-1]
        if last_sma50 is not None and float(last_sma50) > 0:
            sma50_val = float(last_sma50)
            if close_val > sma20_val > sma50_val:
                trend = "uptrend"
                notes.append("Price > SMA20 > SMA50")
            elif close_val < sma20_val < sma50_val:
                trend = "downtrend"
                notes.append("Price < SMA20 < SMA50")
            else:
                trend = "sideways"
                notes.append("Mixed MA alignment")
        else:
            trend = "sideways"
    else:
        trend = "uptrend" if close_vs_sma20 > 0.02 else ("downtrend" if close_vs_sma20 < -0.02 else "sideways")

    # RSI
    rsi_14 = rsi(close, 14)
    rsi_val = rsi_14.iloc[-1]
    rsi_float = float(rsi_val) if rsi_val is not None else 50.0

    if rsi_float < 30:
        notes.append(f"RSI oversold ({rsi_float:.1f})")
    elif rsi_float > 70:
        notes.append(f"RSI overbought ({rsi_float:.1f})")

    # MACD
    macd_df = macd(close, 12, 26, 9)
    macd_val = macd_df["macd"].iloc[-1]
    signal_val = macd_df["signal"].iloc[-1]
    if macd_val is not None and signal_val is not None:
        if float(macd_val) > float(signal_val):
            macd_signal = "bullish"
            notes.append("MACD above signal")
        else:
            macd_signal = "bearish"
            notes.append("MACD below signal")
    else:
        macd_signal = "neutral"

    # Compute bias score
    score = 0.0
    # Trend contribution
    if trend == "uptrend":
        score += 1.0
    elif trend == "downtrend":
        score -= 1.0

    # RSI contribution
    if rsi_float < 30:
        score += 0.5  # oversold = potential bounce
    elif rsi_float > 70:
        score -= 0.5  # overbought = potential pullback
    elif 40 <= rsi_float <= 60:
        pass  # neutral
    elif rsi_float > 50:
        score += 0.2
    else:
        score -= 0.2

    # MACD contribution
    if macd_signal == "bullish":
        score += 0.5
    elif macd_signal == "bearish":
        score -= 0.5

    # Determine bias
    if score >= 0.8:
        bias: Bias = "BULLISH"
        confidence = min(1.0, score / 2.0)
    elif score <= -0.8:
        bias = "BEARISH"
        confidence = min(1.0, abs(score) / 2.0)
    else:
        bias = "NEUTRAL"
        confidence = 1.0 - abs(score) / 2.0

    return TimeframeView(
        name=name,
        bias=bias,
        confidence=confidence,
        rsi=rsi_float,
        trend=trend,
        close_vs_sma20=close_vs_sma20,
        macd_signal=macd_signal,
        notes=notes,
    )


def multi_timeframe_analysis(
    ticker: str,
    timeframes: Optional[dict[str, dict]] = None,
    source: Optional[DataSource] = None,
) -> MTFResult:
    """Perform multi-timeframe analysis on a single ticker.

    Evaluates the stock across weekly, daily, and intraday timeframes
    to determine overall bias and alignment.

    Parameters:
        ticker: IDX ticker (e.g. "BBCA")
        timeframes: Custom timeframe config (default: weekly/daily/4h/1h)
        source: DataSource instance

    Returns:
        MTFResult with consensus bias and per-timeframe analysis
    """
    src = source or get_source()
    tf_config = timeframes or TIMEFRAMES
    views: dict[str, TimeframeView] = {}

    total_weight = 0.0
    weighted_score = 0.0

    for tf_name, config in tf_config.items():
        try:
            df = src.get_ohlc(
                ticker,
                period=config["period"],
                interval=config["interval"],
            )
            view = _analyze_single_timeframe(df, tf_name)
        except Exception:
            view = TimeframeView(name=tf_name, bias="NEUTRAL", confidence=0.0,
                                notes=["Data unavailable"])

        views[tf_name] = view
        weight = config.get("weight", 1.0)
        total_weight += weight

        # Convert bias to numeric
        if view.bias == "BULLISH":
            weighted_score += weight * view.confidence
        elif view.bias == "BEARISH":
            weighted_score -= weight * view.confidence

    # Compute consensus
    if total_weight == 0:
        normalized = 0.0
    else:
        normalized = weighted_score / total_weight

    if normalized >= 0.3:
        consensus: Bias = "BULLISH"
    elif normalized <= -0.3:
        consensus = "BEARISH"
    else:
        consensus = "NEUTRAL"

    # Alignment: do all timeframes agree?
    biases = [v.bias for v in views.values() if v.bias != "NEUTRAL"]
    if biases:
        dominant = max(set(biases), key=biases.count)
        alignment = biases.count(dominant) / len(biases)
    else:
        alignment = 0.0

    # Recommendation
    if consensus == "BULLISH" and alignment >= 0.7:
        recommendation = f"Strong BUY signal — {int(alignment*100)}% timeframe alignment"
    elif consensus == "BEARISH" and alignment >= 0.7:
        recommendation = f"Strong SELL signal — {int(alignment*100)}% timeframe alignment"
    elif consensus == "BULLISH":
        recommendation = "Cautious BUY — mixed timeframe signals"
    elif consensus == "BEARISH":
        recommendation = "Cautious SELL — mixed timeframe signals"
    else:
        recommendation = "HOLD — no clear direction across timeframes"

    return MTFResult(
        ticker=ticker,
        consensus=consensus,
        alignment_score=alignment,
        timeframes=views,
        recommendation=recommendation,
    )
