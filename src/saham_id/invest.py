"""Investment Decision Engine — multi-factor analysis for smart investing.

Combines technical, fundamental, bandarmology, foreign flow, and risk analysis
into a single actionable recommendation. Designed to prevent losses by:

1. Only recommending entries with favorable Risk:Reward (>= 2:1)
2. Checking market regime before any buy recommendation
3. Calculating proper position size based on conviction level
4. Providing clear exit rules (stop-loss + trailing + target)

Usage:
    from saham_id.invest import analyze_investment, InvestmentDecision

    decision = analyze_investment("BBCA", budget=50_000_000)
    print(decision.verdict)        # "STRONG BUY" / "BUY" / "WAIT" / "AVOID"
    print(decision.entry_score)    # 0-100
    print(decision.risk_reward)    # e.g. 2.5 (risk:reward ratio)
    print(decision.conviction)     # "HIGH" / "MEDIUM" / "LOW"
    print(decision.position_size)  # How many lots to buy
    print(decision.stop_loss)      # Where to put stop-loss
    print(decision.targets)        # [target1, target2, target3]
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource

logger = logging.getLogger(__name__)


class Verdict(str, Enum):
    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    WAIT = "WAIT"
    AVOID = "AVOID"
    SELL = "SELL"


class Conviction(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MarketRegime(str, Enum):
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"


@dataclass
class RiskRewardAnalysis:
    """Risk/Reward calculation result."""
    entry_price: float = 0.0
    stop_loss: float = 0.0
    target_1: float = 0.0
    target_2: float = 0.0
    target_3: float = 0.0
    risk_amount: float = 0.0
    reward_amount: float = 0.0
    risk_reward_ratio: float = 0.0
    risk_pct: float = 0.0
    reward_pct: float = 0.0
    is_favorable: bool = False  # True if R:R >= 2.0


@dataclass
class PositionSizing:
    """Position size recommendation."""
    lots: int = 0
    shares: int = 0
    capital_required: float = 0.0
    risk_per_trade: float = 0.0
    max_loss: float = 0.0
    pct_of_portfolio: float = 0.0


@dataclass
class ExitPlan:
    """When and how to exit."""
    stop_loss: float = 0.0
    trailing_stop_pct: float = 0.0
    target_1: float = 0.0
    target_2: float = 0.0
    target_3: float = 0.0
    time_stop_days: int = 0  # Exit if no movement after N days
    exit_conditions: list[str] = field(default_factory=list)


@dataclass
class InvestmentDecision:
    """Complete investment decision with all analysis."""
    ticker: str
    verdict: Verdict
    entry_score: float  # 0-100
    conviction: Conviction
    market_regime: MarketRegime

    # Price info
    current_price: float = 0.0
    fair_value_estimate: float = 0.0

    # Risk/Reward
    risk_reward: RiskRewardAnalysis = field(default_factory=RiskRewardAnalysis)

    # Position sizing
    position: PositionSizing = field(default_factory=PositionSizing)

    # Exit plan
    exit_plan: ExitPlan = field(default_factory=ExitPlan)

    # Component scores (0-100 each)
    trend_score: float = 0.0
    momentum_score: float = 0.0
    bandar_score: float = 0.0
    foreign_flow_score: float = 0.0
    support_resistance_score: float = 0.0
    volume_score: float = 0.0

    # Reasons
    bullish_reasons: list[str] = field(default_factory=list)
    bearish_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    # Meta
    timestamp: Optional[datetime] = None
    analysis_period: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()

    @property
    def summary(self) -> str:
        """One-line summary."""
        return (
            f"{self.ticker}: {self.verdict.value} "
            f"(Score: {self.entry_score:.0f}/100, "
            f"R:R {self.risk_reward.risk_reward_ratio:.1f}:1, "
            f"Conviction: {self.conviction.value})"
        )

    @property
    def should_buy(self) -> bool:
        return self.verdict in (Verdict.STRONG_BUY, Verdict.BUY)

    @property
    def stop_loss(self) -> float:
        return self.exit_plan.stop_loss

    @property
    def targets(self) -> list[float]:
        return [self.exit_plan.target_1, self.exit_plan.target_2, self.exit_plan.target_3]


def analyze_investment(
    ticker: str,
    budget: float = 100_000_000,
    risk_tolerance: float = 0.02,
    period: str = "6mo",
    source: Optional[DataSource] = None,
) -> InvestmentDecision:
    """Run complete investment analysis for a ticker.

    Args:
        ticker: IDX stock ticker (e.g. "BBCA")
        budget: Available capital in IDR
        risk_tolerance: Max risk per trade as fraction (0.02 = 2%)
        period: Historical data period for analysis
        source: Data source (uses default if None)

    Returns:
        InvestmentDecision with complete recommendation
    """
    ticker = ticker.upper()
    src = source or get_source()
    decision = InvestmentDecision(
        ticker=ticker,
        verdict=Verdict.WAIT,
        entry_score=0,
        conviction=Conviction.LOW,
        market_regime=MarketRegime.NEUTRAL,
        analysis_period=period,
    )

    # --- Fetch data ---
    try:
        df = src.get_ohlc(ticker, period=period, interval="1d")
    except Exception as exc:
        decision.warnings.append(f"Data fetch failed: {exc}")
        decision.verdict = Verdict.AVOID
        return decision

    if df.empty or len(df) < 50:
        decision.warnings.append("Insufficient data (need >= 50 bars)")
        decision.verdict = Verdict.AVOID
        return decision

    close = df["close"]
    high = df["high"]
    low = df["low"]
    volume = df["volume"] if "volume" in df.columns else None

    current_price = float(close.iloc[-1])
    decision.current_price = current_price

    # === 1. TREND ANALYSIS (0-100) ===
    decision.trend_score = _analyze_trend(df)

    # === 2. MOMENTUM ANALYSIS (0-100) ===
    decision.momentum_score = _analyze_momentum(df)

    # === 3. VOLUME ANALYSIS (0-100) ===
    decision.volume_score = _analyze_volume(df)

    # === 4. BANDAR ANALYSIS (0-100) ===
    decision.bandar_score = _analyze_bandar(ticker, src)

    # === 5. FOREIGN FLOW ANALYSIS (0-100) ===
    decision.foreign_flow_score = _analyze_foreign_flow(df, ticker)

    # === 6. SUPPORT/RESISTANCE SCORE (0-100) ===
    decision.support_resistance_score = _analyze_support_resistance(df)

    # === 7. MARKET REGIME ===
    decision.market_regime = _detect_market_regime(df)

    # === 8. COMPUTE ENTRY SCORE ===
    weights = {
        "trend": 0.25,
        "momentum": 0.20,
        "bandar": 0.20,
        "foreign_flow": 0.15,
        "support_resistance": 0.10,
        "volume": 0.10,
    }
    decision.entry_score = (
        decision.trend_score * weights["trend"]
        + decision.momentum_score * weights["momentum"]
        + decision.bandar_score * weights["bandar"]
        + decision.foreign_flow_score * weights["foreign_flow"]
        + decision.support_resistance_score * weights["support_resistance"]
        + decision.volume_score * weights["volume"]
    )

    # === 9. RISK/REWARD CALCULATION ===
    decision.risk_reward = _calculate_risk_reward(df, current_price)

    # === 10. EXIT PLAN ===
    decision.exit_plan = _create_exit_plan(df, current_price, decision.risk_reward)

    # === 11. CONVICTION LEVEL ===
    decision.conviction = _determine_conviction(decision)

    # === 12. POSITION SIZING ===
    decision.position = _calculate_position_size(
        current_price=current_price,
        stop_loss=decision.exit_plan.stop_loss,
        budget=budget,
        risk_tolerance=risk_tolerance,
        conviction=decision.conviction,
    )

    # === 13. BUILD REASONS ===
    _build_reasons(decision)

    # === 14. FINAL VERDICT ===
    decision.verdict = _determine_verdict(decision)

    return decision


# ======================================================================
# Component analyzers
# ======================================================================

def _analyze_trend(df) -> float:
    """Trend score 0-100. Higher = stronger uptrend."""
    from saham_id.analysis.indicators import sma, ema

    close = df["close"]
    score = 50.0  # neutral

    # Price vs MAs
    sma20 = sma(close, 20)
    sma50 = sma(close, 50)
    sma200 = sma(close, 200) if len(df) >= 200 else sma50

    last = float(close.iloc[-1])
    ma20 = float(sma20.iloc[-1]) if sma20.iloc[-1] is not None else last
    ma50 = float(sma50.iloc[-1]) if sma50.iloc[-1] is not None else last
    ma200 = float(sma200.iloc[-1]) if sma200.iloc[-1] is not None else last

    # Above all MAs = strong uptrend
    if last > ma20 > ma50:
        score += 25
    elif last > ma50:
        score += 15
    elif last < ma20 < ma50:
        score -= 25

    # MA slope (20-day)
    if len(sma20) >= 5:
        ma20_5ago = float(sma20.iloc[-5]) if sma20.iloc[-5] is not None else ma20
        if ma20 > ma20_5ago:
            score += 10
        elif ma20 < ma20_5ago:
            score -= 10

    # Higher highs and higher lows (last 20 bars)
    recent = df.tail(20)
    if len(recent) >= 10:
        mid = len(recent) // 2
        first_half_high = float(recent["high"].iloc[:mid].max())
        second_half_high = float(recent["high"].iloc[mid:].max())
        first_half_low = float(recent["low"].iloc[:mid].min())
        second_half_low = float(recent["low"].iloc[mid:].min())

        if second_half_high > first_half_high and second_half_low > first_half_low:
            score += 15  # Higher highs + higher lows
        elif second_half_high < first_half_high and second_half_low < first_half_low:
            score -= 15  # Lower highs + lower lows

    return max(0, min(100, score))


def _analyze_momentum(df) -> float:
    """Momentum score 0-100. Combines RSI, MACD, Stochastic."""
    from saham_id.analysis.indicators import rsi, macd, stoch

    close = df["close"]
    score = 50.0

    # RSI
    rsi_val = rsi(close, 14)
    current_rsi = float(rsi_val.iloc[-1]) if rsi_val.iloc[-1] is not None else 50

    if current_rsi < 30:
        score += 20  # Oversold = buying opportunity
    elif current_rsi < 40:
        score += 10
    elif current_rsi > 70:
        score -= 15  # Overbought = risky to enter
    elif current_rsi > 80:
        score -= 25

    # MACD
    macd_result = macd(close, fast=12, slow=26, signal=9)
    if hasattr(macd_result, 'histogram'):
        hist = macd_result.histogram
    else:
        # Fallback: compute manually
        macd_line = close.ewm(span=12).mean() - close.ewm(span=26).mean()
        signal_line = macd_line.ewm(span=9).mean()
        hist = macd_line - signal_line

    if len(hist) >= 2:
        last_hist = float(hist.iloc[-1]) if hist.iloc[-1] is not None else 0
        prev_hist = float(hist.iloc[-2]) if hist.iloc[-2] is not None else 0

        if last_hist > 0 and last_hist > prev_hist:
            score += 15  # Bullish & increasing
        elif last_hist > 0:
            score += 5
        elif last_hist < 0 and last_hist < prev_hist:
            score -= 15  # Bearish & increasing
        elif last_hist < 0:
            score -= 5

    # Stochastic
    stoch_result = stoch(df["high"], df["low"], close, k_window=14)
    if hasattr(stoch_result, 'k'):
        k_val = float(stoch_result.k.iloc[-1]) if stoch_result.k.iloc[-1] is not None else 50
    else:
        k_val = 50

    if k_val < 20:
        score += 10
    elif k_val > 80:
        score -= 10

    return max(0, min(100, score))


def _analyze_volume(df) -> float:
    """Volume score 0-100. High volume on up days = bullish."""
    if "volume" not in df.columns:
        return 50.0

    score = 50.0
    vol = df["volume"]
    close = df["close"]

    # Average volume (20 days)
    avg_vol = float(vol.tail(20).mean()) if len(vol) >= 20 else float(vol.mean())
    last_vol = float(vol.iloc[-1]) if vol.iloc[-1] is not None else avg_vol

    # Relative volume
    rvol_val = last_vol / avg_vol if avg_vol > 0 else 1.0

    # Price direction today
    if len(close) >= 2:
        price_up = float(close.iloc[-1]) > float(close.iloc[-2])
    else:
        price_up = True

    # Volume increasing on up day = bullish
    if price_up and rvol_val > 1.5:
        score += 25
    elif price_up and rvol_val > 1.0:
        score += 10
    elif not price_up and rvol_val > 1.5:
        score -= 20  # Heavy selling
    elif not price_up and rvol_val > 1.0:
        score -= 10

    # Volume trend (5-day avg vs 20-day avg)
    if len(vol) >= 20:
        vol_5 = float(vol.tail(5).mean())
        vol_20 = float(vol.tail(20).mean())
        if vol_20 > 0 and vol_5 / vol_20 > 1.3:
            score += 10  # Increasing interest

    return max(0, min(100, score))


def _analyze_bandar(ticker: str, src: DataSource) -> float:
    """Bandar score 0-100 from bandarmology module."""
    try:
        from saham_id.analysis.bandarmology import bandar_score as bs_fn
        result = bs_fn(ticker, source=src)
        return float(result.score)
    except Exception:
        return 50.0


def _analyze_foreign_flow(df, ticker: str) -> float:
    """Foreign flow score 0-100."""
    try:
        from saham_id.analysis.foreign_flow import estimate_foreign_flow
        ff = estimate_foreign_flow(df, ticker=ticker)
        mapping = {
            "HEAVY_BUYING": 90,
            "BUYING": 70,
            "NEUTRAL": 50,
            "SELLING": 30,
            "HEAVY_SELLING": 10,
        }
        return float(mapping.get(ff.activity.value, 50))
    except Exception:
        return 50.0


def _analyze_support_resistance(df) -> float:
    """Score based on proximity to support (good) vs resistance (bad)."""
    score = 50.0
    close = df["close"]
    current = float(close.iloc[-1])

    recent = df.tail(60)
    high_60 = float(recent["high"].max())
    low_60 = float(recent["low"].min())

    if high_60 == low_60:
        return 50.0

    # Position in range (0 = at support, 1 = at resistance)
    position_in_range = (current - low_60) / (high_60 - low_60)

    # Near support = good entry, near resistance = risky
    if position_in_range < 0.3:
        score += 25  # Near support
    elif position_in_range < 0.5:
        score += 10
    elif position_in_range > 0.8:
        score -= 20  # Near resistance
    elif position_in_range > 0.9:
        score -= 30  # Very near top

    return max(0, min(100, score))


def _detect_market_regime(df) -> MarketRegime:
    """Detect overall market regime from price action."""
    from saham_id.analysis.indicators import sma, atr

    close = df["close"]

    # Simple regime: price vs SMA50
    sma50 = sma(close, 50)
    last_price = float(close.iloc[-1])
    ma50_val = float(sma50.iloc[-1]) if sma50.iloc[-1] is not None else last_price

    # ATR for volatility check
    atr_val = atr(df["high"], df["low"], close, 14)
    last_atr = float(atr_val.iloc[-1]) if atr_val.iloc[-1] is not None else 0
    atr_pct = last_atr / last_price if last_price > 0 else 0

    # High volatility regime
    if atr_pct > 0.04:  # > 4% daily ATR
        return MarketRegime.HIGH_VOLATILITY

    # Trend regime
    if last_price > ma50_val * 1.02:
        return MarketRegime.BULLISH
    elif last_price < ma50_val * 0.98:
        return MarketRegime.BEARISH
    else:
        return MarketRegime.NEUTRAL


def _calculate_risk_reward(df, current_price: float) -> RiskRewardAnalysis:
    """Calculate Risk:Reward based on support/resistance levels."""
    recent = df.tail(60)
    high_60 = float(recent["high"].max())
    low_60 = float(recent["low"].min())

    # ATR for stop-loss distance
    from saham_id.analysis.indicators import atr
    atr_val = atr(df["high"], df["low"], df["close"], 14)
    last_atr = float(atr_val.iloc[-1]) if atr_val.iloc[-1] is not None else current_price * 0.02

    # Stop-loss: 1.5x ATR below current price
    stop_loss = current_price - (last_atr * 1.5)

    # Targets based on range
    range_size = high_60 - low_60
    target_1 = current_price + (last_atr * 2)      # 2x ATR
    target_2 = current_price + (last_atr * 3.5)    # 3.5x ATR
    target_3 = current_price + (range_size * 0.5)   # Half the range above

    risk_amount = current_price - stop_loss
    reward_amount = target_2 - current_price  # Use T2 as primary target

    rr_ratio = reward_amount / risk_amount if risk_amount > 0 else 0

    return RiskRewardAnalysis(
        entry_price=current_price,
        stop_loss=round(stop_loss, 0),
        target_1=round(target_1, 0),
        target_2=round(target_2, 0),
        target_3=round(target_3, 0),
        risk_amount=round(risk_amount, 0),
        reward_amount=round(reward_amount, 0),
        risk_reward_ratio=round(rr_ratio, 2),
        risk_pct=round(risk_amount / current_price * 100, 2),
        reward_pct=round(reward_amount / current_price * 100, 2),
        is_favorable=rr_ratio >= 2.0,
    )


def _create_exit_plan(df, current_price: float, rr: RiskRewardAnalysis) -> ExitPlan:
    """Create clear exit rules."""
    exit_conditions = []

    # Stop-loss
    exit_conditions.append(f"Hard stop-loss di Rp {rr.stop_loss:,.0f} (-{rr.risk_pct:.1f}%)")

    # Trailing stop after profit
    exit_conditions.append("Trailing stop 5% setelah profit > 5%")

    # Time stop
    exit_conditions.append("Review jika tidak bergerak > 20 hari kerja")

    # Target exits
    exit_conditions.append(f"Take profit 30% di T1 Rp {rr.target_1:,.0f}")
    exit_conditions.append(f"Take profit 40% di T2 Rp {rr.target_2:,.0f}")
    exit_conditions.append(f"Final exit di T3 Rp {rr.target_3:,.0f}")

    return ExitPlan(
        stop_loss=rr.stop_loss,
        trailing_stop_pct=5.0,
        target_1=rr.target_1,
        target_2=rr.target_2,
        target_3=rr.target_3,
        time_stop_days=20,
        exit_conditions=exit_conditions,
    )


def _determine_conviction(decision: InvestmentDecision) -> Conviction:
    """Determine conviction based on analysis alignment."""
    score = decision.entry_score
    rr_favorable = decision.risk_reward.is_favorable
    regime_ok = decision.market_regime in (MarketRegime.BULLISH, MarketRegime.NEUTRAL)

    high_scores = sum(1 for s in [
        decision.trend_score, decision.momentum_score,
        decision.bandar_score, decision.foreign_flow_score,
    ] if s >= 65)

    if score >= 70 and rr_favorable and regime_ok and high_scores >= 3:
        return Conviction.HIGH
    elif score >= 55 and rr_favorable and regime_ok:
        return Conviction.MEDIUM
    else:
        return Conviction.LOW


def _calculate_position_size(
    current_price: float,
    stop_loss: float,
    budget: float,
    risk_tolerance: float,
    conviction: Conviction,
) -> PositionSizing:
    """Calculate how many lots to buy based on conviction and risk."""
    # Adjust risk by conviction
    risk_multiplier = {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4}
    adjusted_risk = risk_tolerance * risk_multiplier.get(conviction.value, 0.5)

    # Maximum loss allowed
    max_loss = budget * adjusted_risk

    # Risk per share
    risk_per_share = current_price - stop_loss
    if risk_per_share <= 0:
        return PositionSizing()

    # Shares based on risk
    shares_by_risk = int(max_loss / risk_per_share)

    # Round down to lots (100 shares)
    lots = shares_by_risk // 100
    shares = lots * 100

    # Capital needed
    capital_required = shares * current_price
    # Ensure we don't exceed budget
    if capital_required > budget * 0.25:  # Max 25% of budget per position
        lots = int((budget * 0.25) / (current_price * 100))
        shares = lots * 100
        capital_required = shares * current_price

    actual_max_loss = shares * risk_per_share
    pct_of_portfolio = capital_required / budget if budget > 0 else 0

    return PositionSizing(
        lots=lots,
        shares=shares,
        capital_required=round(capital_required, 0),
        risk_per_trade=round(adjusted_risk * 100, 2),
        max_loss=round(actual_max_loss, 0),
        pct_of_portfolio=round(pct_of_portfolio * 100, 2),
    )


def _build_reasons(decision: InvestmentDecision) -> None:
    """Build human-readable reasons for the recommendation."""
    # Bullish reasons
    if decision.trend_score >= 65:
        decision.bullish_reasons.append("Uptrend kuat (price > MA20 > MA50)")
    if decision.momentum_score >= 65:
        decision.bullish_reasons.append("Momentum positif (RSI + MACD bullish)")
    if decision.bandar_score >= 65:
        decision.bullish_reasons.append("Indikasi akumulasi bandar")
    if decision.foreign_flow_score >= 65:
        decision.bullish_reasons.append("Asing net buy (foreign inflow)")
    if decision.volume_score >= 65:
        decision.bullish_reasons.append("Volume meningkat pada kenaikan harga")
    if decision.support_resistance_score >= 65:
        decision.bullish_reasons.append("Posisi dekat support (entry area)")
    if decision.risk_reward.is_favorable:
        decision.bullish_reasons.append(
            f"Risk:Reward favorable ({decision.risk_reward.risk_reward_ratio:.1f}:1)"
        )

    # Bearish reasons
    if decision.trend_score <= 35:
        decision.bearish_reasons.append("Downtrend (price < MA20 < MA50)")
    if decision.momentum_score <= 35:
        decision.bearish_reasons.append("Momentum negatif (RSI/MACD bearish)")
    if decision.bandar_score <= 35:
        decision.bearish_reasons.append("Indikasi distribusi bandar")
    if decision.foreign_flow_score <= 35:
        decision.bearish_reasons.append("Asing net sell (foreign outflow)")
    if decision.volume_score <= 35:
        decision.bearish_reasons.append("Volume tinggi pada penurunan (distribusi)")
    if decision.support_resistance_score <= 35:
        decision.bearish_reasons.append("Posisi dekat resistance (risky entry)")

    # Warnings
    if decision.market_regime == MarketRegime.BEARISH:
        decision.warnings.append("PASAR BEARISH — hindari entry baru kecuali sangat yakin")
    if decision.market_regime == MarketRegime.HIGH_VOLATILITY:
        decision.warnings.append("VOLATILITAS TINGGI — kurangi ukuran posisi")
    if not decision.risk_reward.is_favorable:
        decision.warnings.append(
            f"Risk:Reward tidak ideal ({decision.risk_reward.risk_reward_ratio:.1f}:1, butuh >= 2:1)"
        )
    if decision.position.lots == 0:
        decision.warnings.append("Posisi terlalu kecil — budget tidak cukup atau risk terlalu tinggi")


def _determine_verdict(decision: InvestmentDecision) -> Verdict:
    """Final verdict based on all factors."""
    score = decision.entry_score
    rr_ok = decision.risk_reward.is_favorable
    regime = decision.market_regime
    conviction = decision.conviction

    # AVOID conditions (hard filters)
    if regime == MarketRegime.BEARISH and score < 70:
        return Verdict.AVOID
    if not rr_ok and score < 80:
        return Verdict.WAIT
    if score < 40:
        return Verdict.AVOID

    # STRONG BUY
    if score >= 75 and rr_ok and conviction == Conviction.HIGH:
        return Verdict.STRONG_BUY

    # BUY
    if score >= 60 and rr_ok and conviction in (Conviction.HIGH, Conviction.MEDIUM):
        return Verdict.BUY

    # WAIT (conditions not met yet)
    if score >= 50:
        return Verdict.WAIT

    return Verdict.AVOID
