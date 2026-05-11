"""Risk Manager — automated stop-loss, trailing stop, and circuit breakers.

Provides real-time risk management rules that can be applied to positions:
    - Fixed stop-loss
    - Trailing stop (locks in profit as price moves up)
    - Time-based stop (exit after N days)
    - Max portfolio drawdown circuit breaker
    - Daily loss limit

Usage:
    from saham_id.risk_manager import RiskManager, StopRule, TrailingStop

    rm = RiskManager(max_portfolio_drawdown=0.10, daily_loss_limit=0.03)
    rm.add_stop(StopRule(ticker="BBCA", entry=9500, stop=9000, trailing_pct=0.05))

    # Check stops against current prices
    triggers = rm.check_stops(source=src)
    for t in triggers:
        print(f"STOP TRIGGERED: {t.ticker} — {t.reason}")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Literal, Optional

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


@dataclass
class StopRule:
    """A stop-loss rule for a position."""

    ticker: str
    entry_price: float
    stop_price: float  # initial stop
    trailing_pct: float = 0.0  # 0 = no trail, 0.05 = 5% trailing
    time_limit_days: int = 0  # 0 = no time limit
    entry_date: Optional[date] = None
    highest_since_entry: float = 0.0  # for trailing stop tracking
    shares: int = 0
    note: str = ""

    def __post_init__(self):
        if self.highest_since_entry == 0:
            self.highest_since_entry = self.entry_price
        if self.entry_date is None:
            self.entry_date = date.today()

    @property
    def current_stop(self) -> float:
        """Effective stop price (accounts for trailing)."""
        if self.trailing_pct > 0 and self.highest_since_entry > self.entry_price:
            trailing_stop = self.highest_since_entry * (1 - self.trailing_pct)
            return max(self.stop_price, trailing_stop)
        return self.stop_price

    @property
    def risk_pct(self) -> float:
        """Risk as % of entry price."""
        if self.entry_price == 0:
            return 0.0
        return (self.entry_price - self.current_stop) / self.entry_price

    @property
    def days_held(self) -> int:
        """Days since entry."""
        if self.entry_date is None:
            return 0
        return (date.today() - self.entry_date).days


@dataclass
class StopTrigger:
    """A triggered stop-loss event."""

    ticker: str
    reason: str  # "stop_loss", "trailing_stop", "time_limit", "circuit_breaker"
    entry_price: float
    stop_price: float
    current_price: float
    loss_pct: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RiskManager:
    """Portfolio-level risk management system.

    Features:
        - Per-position stop-losses (fixed and trailing)
        - Time-based exits
        - Daily loss limit (pause trading if exceeded)
        - Max portfolio drawdown circuit breaker
        - Position-level risk tracking
    """

    def __init__(
        self,
        max_portfolio_drawdown: float = 0.10,  # 10% max DD -> halt
        daily_loss_limit: float = 0.03,  # 3% daily loss -> pause
        max_single_loss: float = 0.05,  # 5% max loss per position
    ):
        self.max_portfolio_drawdown = max_portfolio_drawdown
        self.daily_loss_limit = daily_loss_limit
        self.max_single_loss = max_single_loss
        self.stops: dict[str, StopRule] = {}
        self.triggers: list[StopTrigger] = []
        self.daily_pnl: float = 0.0
        self.peak_portfolio_value: float = 0.0
        self.is_halted: bool = False

    def add_stop(self, rule: StopRule) -> None:
        """Add or update a stop-loss rule for a position."""
        self.stops[rule.ticker.upper()] = rule

    def remove_stop(self, ticker: str) -> None:
        """Remove stop for a ticker."""
        self.stops.pop(ticker.upper(), None)

    def update_high(self, ticker: str, price: float) -> None:
        """Update highest price since entry (for trailing stops)."""
        key = ticker.upper()
        if key in self.stops:
            self.stops[key].highest_since_entry = max(
                self.stops[key].highest_since_entry, price
            )

    def check_stops(self, source: Optional[DataSource] = None) -> list[StopTrigger]:
        """Check all stop rules against current prices.

        Returns list of triggered stops.
        """
        src = source or get_source()
        triggered: list[StopTrigger] = []

        if self.is_halted:
            return [StopTrigger(
                ticker="PORTFOLIO", reason="circuit_breaker",
                entry_price=0, stop_price=0, current_price=0,
                loss_pct=0, timestamp=datetime.utcnow(),
            )]

        for ticker, rule in list(self.stops.items()):
            try:
                quote = src.get_quote(ticker)
                current_price = float(quote.last)
            except Exception:
                continue

            # Update trailing stop high watermark
            self.update_high(ticker, current_price)

            # Check stop-loss
            effective_stop = rule.current_stop
            if current_price <= effective_stop:
                loss_pct = (current_price - rule.entry_price) / rule.entry_price
                reason = "trailing_stop" if rule.trailing_pct > 0 and effective_stop > rule.stop_price else "stop_loss"
                trigger = StopTrigger(
                    ticker=ticker, reason=reason,
                    entry_price=rule.entry_price, stop_price=effective_stop,
                    current_price=current_price, loss_pct=loss_pct,
                )
                triggered.append(trigger)
                self.triggers.append(trigger)

            # Check time limit
            if rule.time_limit_days > 0 and rule.days_held >= rule.time_limit_days:
                loss_pct = (current_price - rule.entry_price) / rule.entry_price
                trigger = StopTrigger(
                    ticker=ticker, reason="time_limit",
                    entry_price=rule.entry_price, stop_price=effective_stop,
                    current_price=current_price, loss_pct=loss_pct,
                )
                triggered.append(trigger)
                self.triggers.append(trigger)

            # Check max single loss
            current_loss = (rule.entry_price - current_price) / rule.entry_price
            if current_loss >= self.max_single_loss:
                trigger = StopTrigger(
                    ticker=ticker, reason="max_single_loss",
                    entry_price=rule.entry_price, stop_price=effective_stop,
                    current_price=current_price, loss_pct=-current_loss,
                )
                triggered.append(trigger)
                self.triggers.append(trigger)

        return triggered

    def check_circuit_breaker(self, current_portfolio_value: float) -> bool:
        """Check if portfolio drawdown exceeds limit.

        Returns True if circuit breaker is triggered (should halt trading).
        """
        if current_portfolio_value > self.peak_portfolio_value:
            self.peak_portfolio_value = current_portfolio_value

        if self.peak_portfolio_value == 0:
            return False

        drawdown = (self.peak_portfolio_value - current_portfolio_value) / self.peak_portfolio_value

        if drawdown >= self.max_portfolio_drawdown:
            self.is_halted = True
            return True
        return False

    def check_daily_limit(self, daily_pnl: float, capital: float) -> bool:
        """Check if daily loss limit is exceeded.

        Returns True if should stop trading for the day.
        """
        if capital == 0:
            return False
        daily_loss_pct = abs(daily_pnl) / capital if daily_pnl < 0 else 0
        return daily_loss_pct >= self.daily_loss_limit

    def reset_daily(self) -> None:
        """Reset daily counters (call at start of each trading day)."""
        self.daily_pnl = 0.0

    def reset_circuit_breaker(self) -> None:
        """Manually reset the circuit breaker."""
        self.is_halted = False

    def summary(self) -> dict:
        """Get risk manager status summary."""
        return {
            "is_halted": self.is_halted,
            "active_stops": len(self.stops),
            "total_triggers": len(self.triggers),
            "max_portfolio_dd": self.max_portfolio_drawdown,
            "daily_loss_limit": self.daily_loss_limit,
            "max_single_loss": self.max_single_loss,
            "stops": {
                ticker: {
                    "entry": rule.entry_price,
                    "current_stop": rule.current_stop,
                    "trailing": rule.trailing_pct,
                    "days_held": rule.days_held,
                    "risk_pct": f"{rule.risk_pct:.2%}",
                }
                for ticker, rule in self.stops.items()
            },
        }
