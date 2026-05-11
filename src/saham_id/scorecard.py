"""Stock Score Card — complete single-stock analysis summary."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


@dataclass
class ScoreCard:
    ticker: str
    last_price: float = 0.0
    overall_score: float = 0.0
    recommendation: str = ""
    technical_score: float = 0.0
    bandar_score: float = 0.0
    foreign_flow_score: float = 0.0
    rsi: float = 0.0
    trend: str = ""
    bandar_phase: str = ""
    foreign_activity: str = ""
    support: list[float] = field(default_factory=list)
    resistance: list[float] = field(default_factory=list)
    patterns_detected: list[str] = field(default_factory=list)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()


def generate_scorecard(ticker: str, period: str = "6mo", source: Optional[DataSource] = None) -> ScoreCard:
    src = source or get_source()
    card = ScoreCard(ticker=ticker.upper())
    try:
        df = src.get_ohlc(ticker, period=period, interval="1d")
    except Exception:
        card.recommendation = "Data tidak tersedia"
        return card
    if df.empty or len(df) < 30:
        card.recommendation = "Data tidak cukup"
        return card
    card.last_price = float(df["close"].iloc[-1]) if df["close"].iloc[-1] else 0
    from saham_id.signals import _extract_indicators
    indicators = _extract_indicators(df)
    card.rsi = indicators.get("rsi", 50)
    card.trend = "uptrend" if indicators.get("close_above_sma50") == 1.0 else "downtrend"
    card.technical_score = 70 if card.trend == "uptrend" else 30
    try:
        from saham_id.analysis.bandarmology import bandar_score as bs_fn
        bs = bs_fn(ticker, source=src)
        card.bandar_score = bs.score
        card.bandar_phase = bs.phase.value
    except Exception:
        card.bandar_score = 50
    try:
        from saham_id.analysis.foreign_flow import estimate_foreign_flow
        ff = estimate_foreign_flow(df, ticker=ticker)
        card.foreign_activity = ff.activity.value
        card.foreign_flow_score = {"HEAVY_BUYING": 90, "BUYING": 70, "NEUTRAL": 50, "SELLING": 30, "HEAVY_SELLING": 10}.get(ff.activity.value, 50)
    except Exception:
        card.foreign_flow_score = 50
    try:
        from saham_id.analysis.support_resistance import find_nearest_levels
        levels = find_nearest_levels(df, n=3)
        card.support = levels.get("support", [])
        card.resistance = levels.get("resistance", [])
    except Exception:
        pass
    card.overall_score = round(card.technical_score * 0.35 + card.bandar_score * 0.35 + card.foreign_flow_score * 0.30, 1)
    if card.overall_score >= 70: card.recommendation = "STRONG BUY"
    elif card.overall_score >= 55: card.recommendation = "BUY"
    elif card.overall_score >= 40: card.recommendation = "HOLD"
    else: card.recommendation = "SELL"
    return card
