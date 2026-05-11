"""Position sizing — Kelly criterion, fixed-fractional, and risk-based methods.

Determines how much capital to allocate per trade based on risk tolerance,
win rate, and other parameters.

Usage:
    from saham_id.portfolio.sizing import kelly_size, fixed_fractional, risk_based

    # Kelly Criterion
    size = kelly_size(win_rate=0.6, avg_win=0.05, avg_loss=0.03)

    # Fixed Fractional
    shares = fixed_fractional(capital=100_000_000, risk_pct=0.02, entry=9500, stop=9000)

    # Risk-Based (ATR stop)
    shares = risk_based(capital=100_000_000, risk_pct=0.01, entry=9500, atr=150, atr_multiplier=2.0)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PositionSize:
    """Result of a position sizing calculation."""

    shares: int
    lots: int  # IDX lot = 100 shares
    capital_required: float
    risk_amount: float  # max loss in IDR
    risk_pct_of_capital: float
    stop_loss_price: Optional[float] = None
    method: str = ""


def kelly_size(
    win_rate: float,
    avg_win: float,
    avg_loss: float,
    fraction: float = 0.5,
) -> float:
    """Kelly Criterion — optimal bet size as fraction of capital.

    f* = (p * b - q) / b
    where:
        p = probability of win
        q = probability of loss (1 - p)
        b = ratio of avg_win / avg_loss

    Parameters:
        win_rate: Historical win rate (0-1)
        avg_win: Average winning trade return (e.g. 0.05 for 5%)
        avg_loss: Average losing trade return (positive number, e.g. 0.03 for 3%)
        fraction: Kelly fraction (0.5 = half-Kelly, conservative)

    Returns:
        Recommended fraction of capital to risk (0-1).
        Returns 0 if edge is negative.
    """
    if avg_loss <= 0 or win_rate <= 0 or win_rate >= 1:
        return 0.0

    p = win_rate
    q = 1.0 - p
    b = avg_win / avg_loss

    kelly = (p * b - q) / b
    if kelly <= 0:
        return 0.0

    # Apply fraction (half-Kelly is common for safety)
    return min(kelly * fraction, 0.25)  # Cap at 25% per trade


def fixed_fractional(
    capital: float,
    risk_pct: float,
    entry_price: float,
    stop_loss_price: float,
    commission_pct: float = 0.003,
) -> PositionSize:
    """Fixed-fractional position sizing — risk a fixed % of capital per trade.

    Calculates the number of shares to buy such that if the stop-loss is hit,
    the total loss equals `risk_pct` of capital.

    Parameters:
        capital: Total trading capital (IDR)
        risk_pct: Max risk per trade as fraction (e.g. 0.02 = 2%)
        entry_price: Entry price per share
        stop_loss_price: Stop-loss price per share
        commission_pct: Round-trip commission (e.g. 0.003 = 0.3%)

    Returns:
        PositionSize with shares, lots, and risk details.
    """
    if entry_price <= 0 or stop_loss_price <= 0:
        return PositionSize(shares=0, lots=0, capital_required=0, risk_amount=0,
                           risk_pct_of_capital=0, method="fixed_fractional")

    risk_per_share = abs(entry_price - stop_loss_price)
    if risk_per_share == 0:
        return PositionSize(shares=0, lots=0, capital_required=0, risk_amount=0,
                           risk_pct_of_capital=0, method="fixed_fractional")

    # Include commission in risk
    commission_per_share = entry_price * commission_pct
    total_risk_per_share = risk_per_share + commission_per_share

    max_risk_amount = capital * risk_pct
    raw_shares = max_risk_amount / total_risk_per_share

    # Round down to nearest lot (100 shares)
    lots = int(raw_shares // 100)
    shares = lots * 100

    if shares == 0:
        return PositionSize(shares=0, lots=0, capital_required=0, risk_amount=0,
                           risk_pct_of_capital=0, stop_loss_price=stop_loss_price,
                           method="fixed_fractional")

    capital_required = shares * entry_price * (1 + commission_pct / 2)
    risk_amount = shares * total_risk_per_share
    actual_risk_pct = risk_amount / capital

    return PositionSize(
        shares=shares,
        lots=lots,
        capital_required=capital_required,
        risk_amount=risk_amount,
        risk_pct_of_capital=actual_risk_pct,
        stop_loss_price=stop_loss_price,
        method="fixed_fractional",
    )


def risk_based(
    capital: float,
    risk_pct: float,
    entry_price: float,
    atr: float,
    atr_multiplier: float = 2.0,
    commission_pct: float = 0.003,
) -> PositionSize:
    """Risk-based sizing using ATR for stop-loss placement.

    Stop = entry - (ATR * multiplier)
    Then uses fixed-fractional logic to determine size.

    Parameters:
        capital: Total trading capital (IDR)
        risk_pct: Max risk per trade as fraction
        entry_price: Entry price per share
        atr: Average True Range value
        atr_multiplier: How many ATRs below entry for stop-loss (default: 2.0)
        commission_pct: Round-trip commission

    Returns:
        PositionSize with ATR-based stop-loss.
    """
    if atr <= 0 or entry_price <= 0:
        return PositionSize(shares=0, lots=0, capital_required=0, risk_amount=0,
                           risk_pct_of_capital=0, method="risk_based_atr")

    stop_loss = entry_price - (atr * atr_multiplier)
    if stop_loss <= 0:
        stop_loss = entry_price * 0.9  # fallback: 10% max stop

    result = fixed_fractional(
        capital=capital,
        risk_pct=risk_pct,
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        commission_pct=commission_pct,
    )
    result.method = "risk_based_atr"
    result.stop_loss_price = stop_loss
    return result


def max_shares_for_capital(
    capital: float,
    price: float,
    max_allocation_pct: float = 0.20,
    commission_pct: float = 0.0015,
) -> PositionSize:
    """Calculate maximum shares affordable with capital allocation limit.

    Simple sizing: allocate at most X% of capital to one stock.

    Parameters:
        capital: Total capital
        price: Price per share
        max_allocation_pct: Max % of capital for this position (default: 20%)
        commission_pct: Buy commission
    """
    if price <= 0 or capital <= 0:
        return PositionSize(shares=0, lots=0, capital_required=0, risk_amount=0,
                           risk_pct_of_capital=0, method="max_allocation")

    available = capital * max_allocation_pct
    cost_per_share = price * (1 + commission_pct)
    raw_shares = available / cost_per_share

    lots = int(raw_shares // 100)
    shares = lots * 100

    capital_required = shares * cost_per_share
    return PositionSize(
        shares=shares,
        lots=lots,
        capital_required=capital_required,
        risk_amount=0,  # no stop defined
        risk_pct_of_capital=0,
        method="max_allocation",
    )


def portfolio_heat(
    positions: list[dict],
    capital: float,
) -> float:
    """Calculate total portfolio heat (sum of all position risks).

    Each position dict should have:
        {"shares": int, "entry": float, "stop_loss": float}

    Returns:
        Total risk as fraction of capital. Ideally < 6% total.
    """
    total_risk = 0.0
    for pos in positions:
        shares = pos.get("shares", 0)
        entry = pos.get("entry", 0)
        stop = pos.get("stop_loss", 0)
        if shares > 0 and entry > 0 and stop > 0:
            risk = shares * abs(entry - stop)
            total_risk += risk

    return total_risk / capital if capital > 0 else 0.0
