"""Signal generator — combines multiple indicators into buy/sell signals.

A Signal is a composite decision system that evaluates a stock's current
state across multiple technical conditions and produces a BUY/SELL/HOLD
recommendation with confidence level.

Usage:
    from saham_id.signals import SignalEngine, Condition, Signal

    engine = SignalEngine()
    engine.add_condition(Condition("rsi", "<", 30, weight=2.0))
    engine.add_condition(Condition("macd_crossover", "==", True, weight=1.5))
    engine.add_condition(Condition("close_above_sma50", "==", True, weight=1.0))

    signal = engine.evaluate(df)
    print(signal.action)      # "BUY" / "SELL" / "HOLD"
    print(signal.confidence)  # 0.0 - 1.0
    print(signal.reasons)     # ["RSI oversold (25.3)", "MACD bullish crossover"]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Literal, Optional

import pandas as pd

from saham_id.analysis.indicators import (
    atr,
    bollinger_bands,
    ema,
    macd,
    obv,
    rsi,
    rvol,
    sma,
    stoch,
)


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Signal:
    """Result of signal evaluation."""

    ticker: str
    action: Action
    confidence: float  # 0.0 to 1.0
    score: float  # raw weighted score (positive = bullish, negative = bearish)
    reasons: list[str] = field(default_factory=list)
    timestamp: Optional[datetime] = None
    indicators: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    @property
    def is_bullish(self) -> bool:
        return self.action == Action.BUY

    @property
    def is_bearish(self) -> bool:
        return self.action == Action.SELL


@dataclass
class Condition:
    """A single condition in the signal engine.

    Parameters:
        indicator: Name of indicator/metric to evaluate
        op: Comparison operator
        threshold: Value to compare against
        weight: Importance weight (higher = more influence on signal)
        direction: Whether this condition is bullish or bearish when triggered
    """

    indicator: str
    op: Literal["<", "<=", ">", ">=", "==", "!=", "cross_above", "cross_below"]
    threshold: float | bool
    weight: float = 1.0
    direction: Literal["bullish", "bearish"] = "bullish"
    description: str = ""

    def describe(self) -> str:
        if self.description:
            return self.description
        return f"{self.indicator} {self.op} {self.threshold}"


# --- Pre-built indicator extractors ---

def _extract_indicators(df: pd.DataFrame) -> dict[str, float]:
    """Compute all standard indicators from OHLCV DataFrame."""
    if len(df) < 30:
        return {}

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"]

    indicators: dict[str, float] = {}

    # Trend
    sma_20 = sma(close, 20)
    sma_50 = sma(close, 50)
    ema_12 = ema(close, 12)
    ema_26 = ema(close, 26)

    last_close = close.iloc[-1]
    indicators["close"] = float(last_close) if last_close is not None else 0.0
    indicators["sma_20"] = float(sma_20.iloc[-1]) if sma_20.iloc[-1] is not None else 0.0
    indicators["sma_50"] = float(sma_50.iloc[-1]) if sma_50.iloc[-1] is not None else 0.0
    indicators["ema_12"] = float(ema_12.iloc[-1]) if ema_12.iloc[-1] is not None else 0.0
    indicators["ema_26"] = float(ema_26.iloc[-1]) if ema_26.iloc[-1] is not None else 0.0

    # Close above/below MAs
    if indicators["sma_20"] > 0:
        indicators["close_above_sma20"] = 1.0 if indicators["close"] > indicators["sma_20"] else 0.0
    if indicators["sma_50"] > 0:
        indicators["close_above_sma50"] = 1.0 if indicators["close"] > indicators["sma_50"] else 0.0

    # Golden/Death cross
    if indicators["sma_20"] > 0 and indicators["sma_50"] > 0:
        indicators["sma20_above_sma50"] = 1.0 if indicators["sma_20"] > indicators["sma_50"] else 0.0

    # Momentum
    rsi_14 = rsi(close, 14)
    indicators["rsi"] = float(rsi_14.iloc[-1]) if rsi_14.iloc[-1] is not None else 50.0

    # MACD
    macd_df = macd(close, 12, 26, 9)
    macd_val = macd_df["macd"].iloc[-1]
    signal_val = macd_df["signal"].iloc[-1]
    hist_val = macd_df["histogram"].iloc[-1]
    indicators["macd"] = float(macd_val) if macd_val is not None else 0.0
    indicators["macd_signal"] = float(signal_val) if signal_val is not None else 0.0
    indicators["macd_histogram"] = float(hist_val) if hist_val is not None else 0.0
    indicators["macd_bullish"] = 1.0 if indicators["macd"] > indicators["macd_signal"] else 0.0

    # MACD crossover detection
    if len(macd_df) >= 2:
        prev_macd = macd_df["macd"].iloc[-2]
        prev_signal = macd_df["signal"].iloc[-2]
        if prev_macd is not None and prev_signal is not None:
            prev_above = float(prev_macd) > float(prev_signal)
            curr_above = indicators["macd"] > indicators["macd_signal"]
            indicators["macd_crossover_bull"] = 1.0 if (not prev_above and curr_above) else 0.0
            indicators["macd_crossover_bear"] = 1.0 if (prev_above and not curr_above) else 0.0

    # Stochastic
    st = stoch(high, low, close, 14, 3)
    k_val = st["k"].iloc[-1]
    d_val = st["d"].iloc[-1]
    indicators["stoch_k"] = float(k_val) if k_val is not None else 50.0
    indicators["stoch_d"] = float(d_val) if d_val is not None else 50.0

    # Bollinger Bands
    bb = bollinger_bands(close, 20, 2.0)
    percent_b = bb["percent_b"].iloc[-1]
    indicators["bb_percent_b"] = float(percent_b) if percent_b is not None else 0.5
    bandwidth = bb["bandwidth"].iloc[-1]
    indicators["bb_bandwidth"] = float(bandwidth) if bandwidth is not None else 0.0

    # Volume
    rv = rvol(volume, 20)
    indicators["rvol"] = float(rv.iloc[-1]) if rv.iloc[-1] is not None else 1.0

    # ATR %
    atr_val = atr(high, low, close, 14)
    last_atr = atr_val.iloc[-1]
    if last_atr is not None and indicators["close"] > 0:
        indicators["atr_pct"] = float(last_atr) / indicators["close"]
    else:
        indicators["atr_pct"] = 0.0

    # Price momentum (5-day return)
    if len(close) >= 6:
        prev5 = close.iloc[-6]
        if prev5 is not None and float(prev5) > 0:
            indicators["momentum_5d"] = (indicators["close"] - float(prev5)) / float(prev5)
        else:
            indicators["momentum_5d"] = 0.0

    return indicators


class SignalEngine:
    """Evaluates multiple conditions to produce a composite signal.

    The engine scores each condition and produces a weighted composite:
    - Positive score = bullish bias
    - Negative score = bearish bias
    - Near zero = neutral (HOLD)
    """

    def __init__(
        self,
        buy_threshold: float = 0.3,
        sell_threshold: float = -0.3,
    ):
        self.conditions: list[Condition] = []
        self.buy_threshold = buy_threshold
        self.sell_threshold = sell_threshold

    def add_condition(self, condition: Condition) -> None:
        """Add a condition to the engine."""
        self.conditions.append(condition)

    def clear_conditions(self) -> None:
        """Remove all conditions."""
        self.conditions = []

    def evaluate(self, df: pd.DataFrame, ticker: str = "") -> Signal:
        """Evaluate all conditions against the DataFrame.

        Returns a Signal with action, confidence, and reasons.
        """
        indicators = _extract_indicators(df)
        if not indicators:
            return Signal(ticker=ticker, action=Action.HOLD, confidence=0.0, score=0.0,
                         reasons=["Insufficient data"])

        total_weight = sum(abs(c.weight) for c in self.conditions) or 1.0
        raw_score = 0.0
        reasons: list[str] = []

        for cond in self.conditions:
            actual = indicators.get(cond.indicator)
            if actual is None:
                continue

            triggered = self._check_condition(actual, cond.op, cond.threshold)
            if triggered:
                direction_sign = 1.0 if cond.direction == "bullish" else -1.0
                raw_score += cond.weight * direction_sign
                reasons.append(f"{cond.describe()} [actual={actual:.3f}]")

        # Normalize score to [-1, 1]
        normalized_score = raw_score / total_weight

        # Determine action
        if normalized_score >= self.buy_threshold:
            action = Action.BUY
        elif normalized_score <= self.sell_threshold:
            action = Action.SELL
        else:
            action = Action.HOLD

        # Confidence = how far from threshold (capped at 1.0)
        if action == Action.BUY:
            confidence = min(1.0, (normalized_score - self.buy_threshold) / (1.0 - self.buy_threshold) + 0.5)
        elif action == Action.SELL:
            confidence = min(1.0, (self.sell_threshold - normalized_score) / (1.0 + self.sell_threshold) + 0.5)
        else:
            confidence = 1.0 - abs(normalized_score) / max(abs(self.buy_threshold), 0.01)

        return Signal(
            ticker=ticker,
            action=action,
            confidence=max(0.0, min(1.0, confidence)),
            score=normalized_score,
            reasons=reasons,
            indicators=indicators,
        )

    def _check_condition(self, actual: float, op: str, threshold: float | bool) -> bool:
        """Check if a condition is met."""
        thr = float(threshold) if isinstance(threshold, bool) else threshold
        ops = {
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: abs(a - b) < 0.001,
            "!=": lambda a, b: abs(a - b) >= 0.001,
            "cross_above": lambda a, b: a > b,  # simplified
            "cross_below": lambda a, b: a < b,  # simplified
        }
        fn = ops.get(op)
        if fn is None:
            return False
        return fn(actual, thr)


# --- Pre-built signal engines ---


def swing_buy_engine() -> SignalEngine:
    """Pre-configured engine for swing buy signals.

    Conditions:
        - RSI in oversold zone (< 35) -> strong bullish
        - Price above SMA50 (uptrend) -> moderate bullish
        - MACD bullish crossover -> strong bullish
        - Bollinger %B < 0.2 (near lower band) -> moderate bullish
        - RVOL > 1.5 (volume confirmation) -> mild bullish
    """
    engine = SignalEngine(buy_threshold=0.25, sell_threshold=-0.25)
    engine.add_condition(Condition("rsi", "<", 35, weight=2.0, direction="bullish",
                                   description="RSI oversold"))
    engine.add_condition(Condition("close_above_sma50", "==", 1.0, weight=1.5, direction="bullish",
                                   description="Price above SMA50 (uptrend)"))
    engine.add_condition(Condition("macd_crossover_bull", "==", 1.0, weight=2.0, direction="bullish",
                                   description="MACD bullish crossover"))
    engine.add_condition(Condition("bb_percent_b", "<", 0.2, weight=1.5, direction="bullish",
                                   description="Near lower Bollinger Band"))
    engine.add_condition(Condition("rvol", ">", 1.5, weight=1.0, direction="bullish",
                                   description="Volume above average"))
    return engine


def swing_sell_engine() -> SignalEngine:
    """Pre-configured engine for swing sell signals."""
    engine = SignalEngine(buy_threshold=0.25, sell_threshold=-0.25)
    engine.add_condition(Condition("rsi", ">", 70, weight=2.0, direction="bearish",
                                   description="RSI overbought"))
    engine.add_condition(Condition("close_above_sma50", "==", 0.0, weight=1.5, direction="bearish",
                                   description="Price below SMA50 (downtrend)"))
    engine.add_condition(Condition("macd_crossover_bear", "==", 1.0, weight=2.0, direction="bearish",
                                   description="MACD bearish crossover"))
    engine.add_condition(Condition("bb_percent_b", ">", 0.8, weight=1.5, direction="bearish",
                                   description="Near upper Bollinger Band"))
    engine.add_condition(Condition("momentum_5d", "<", -0.03, weight=1.0, direction="bearish",
                                   description="Negative 5-day momentum"))
    return engine


def scalping_engine() -> SignalEngine:
    """Pre-configured engine for scalping entry signals."""
    engine = SignalEngine(buy_threshold=0.3, sell_threshold=-0.3)
    engine.add_condition(Condition("rvol", ">", 2.0, weight=2.5, direction="bullish",
                                   description="High relative volume (>2x)"))
    engine.add_condition(Condition("atr_pct", ">", 0.02, weight=2.0, direction="bullish",
                                   description="High volatility (ATR >2%)"))
    engine.add_condition(Condition("momentum_5d", ">", 0.01, weight=1.5, direction="bullish",
                                   description="Positive short-term momentum"))
    engine.add_condition(Condition("stoch_k", "<", 30, weight=1.0, direction="bullish",
                                   description="Stochastic oversold"))
    return engine


def generate_signals(
    tickers: list[str],
    engine: Optional[SignalEngine] = None,
    source=None,
) -> list[Signal]:
    """Generate signals for multiple tickers.

    Parameters:
        tickers: List of IDX tickers
        engine: SignalEngine to use (default: swing_buy_engine)
        source: DataSource instance

    Returns:
        List of Signal objects, sorted by confidence descending
    """
    from saham_id.data.sources import get_source

    src = source or get_source()
    eng = engine or swing_buy_engine()
    signals: list[Signal] = []

    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period="6mo", interval="1d")
            if df.empty or len(df) < 30:
                continue
            signal = eng.evaluate(df, ticker=ticker)
            signals.append(signal)
        except Exception:
            continue

    # Sort by confidence (strongest signals first), only actionable ones
    signals.sort(key=lambda s: (s.action != Action.HOLD, s.confidence), reverse=True)
    return signals
