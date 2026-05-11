"""Simple event-driven backtesting engine.

Minimal design for v0: a Strategy callable receives each bar plus the
current portfolio state, and returns zero or more `Order` objects.
The engine records `Trade`s and produces an equity curve.

Scope (v0):
    - Long-only, single asset at a time
    - Next-bar open fill
    - Fixed commission (bps)
Scope (future):
    - Multi-asset portfolios
    - Slippage model
    - Stop-loss / take-profit orders
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Literal, Optional

import pandas as pd

Side = Literal["buy", "sell"]


@dataclass
class Order:
    side: Side
    quantity: int
    note: str = ""


@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    pnl: float = 0.0
    pnl_pct: float = 0.0


@dataclass
class BacktestResult:
    trades: list[Trade]
    equity_curve: pd.Series
    initial_capital: float
    final_capital: float

    @property
    def total_return(self) -> float:
        if self.initial_capital == 0:
            return 0.0
        return (self.final_capital - self.initial_capital) / self.initial_capital


Strategy = Callable[[pd.Series, dict], list[Order]]
"""A strategy is a callable: (bar, state) -> list[Order].

`bar` is a pandas Series for the current row (open/high/low/close/volume).
`state` is a mutable dict with at least ``position`` (int) and ``cash``.
"""


@dataclass
class Backtester:
    strategy: Strategy
    initial_capital: float = 100_000_000.0    # Rp 100 juta default
    commission_bps: float = 15.0              # 15 bps = 0.15% per side (round-trip ~0.3%)
    slippage_bps: float = 0.0
    trades: list[Trade] = field(default_factory=list)

    def run(self, ohlc: pd.DataFrame) -> BacktestResult:
        """Execute the strategy against a daily OHLC DataFrame.

        Assumes columns: open, high, low, close, volume, indexed by timestamp.
        """
        if ohlc.empty:
            raise ValueError("OHLC data is empty")

        cash = self.initial_capital
        position = 0
        avg_cost = 0.0
        equity: list[tuple[datetime, float]] = []
        open_trade: Optional[Trade] = None

        for i in range(len(ohlc) - 1):
            bar = ohlc.iloc[i]
            next_bar = ohlc.iloc[i + 1]
            state = {"position": position, "cash": cash, "avg_cost": avg_cost}
            orders = self.strategy(bar, state) or []
            fill_price = float(next_bar["open"])

            for order in orders:
                fee = fill_price * order.quantity * self.commission_bps / 10_000
                if order.side == "buy" and order.quantity > 0:
                    cost = fill_price * order.quantity + fee
                    if cost > cash:
                        continue
                    avg_cost = (
                        (avg_cost * position + fill_price * order.quantity)
                        / (position + order.quantity)
                    )
                    position += order.quantity
                    cash -= cost
                    if open_trade is None:
                        open_trade = Trade(
                            entry_time=next_bar.name,
                            exit_time=None,
                            entry_price=fill_price,
                            exit_price=None,
                            quantity=order.quantity,
                        )
                elif order.side == "sell" and order.quantity > 0 and position >= order.quantity:
                    proceeds = fill_price * order.quantity - fee
                    cash += proceeds
                    position -= order.quantity
                    if open_trade is not None and position == 0:
                        open_trade.exit_time = next_bar.name
                        open_trade.exit_price = fill_price
                        open_trade.pnl = (
                            (fill_price - open_trade.entry_price) * open_trade.quantity
                        )
                        open_trade.pnl_pct = (
                            (fill_price - open_trade.entry_price) / open_trade.entry_price
                        )
                        self.trades.append(open_trade)
                        open_trade = None
                        avg_cost = 0.0

            mtm = cash + position * float(bar["close"])
            equity.append((bar.name, mtm))

        # Final bar — mark to close
        final_bar = ohlc.iloc[-1]
        final_equity = cash + position * float(final_bar["close"])
        equity.append((final_bar.name, final_equity))

        idx, values = zip(*equity)
        return BacktestResult(
            trades=list(self.trades),
            equity_curve=pd.Series(values, index=idx, name="equity"),
            initial_capital=self.initial_capital,
            final_capital=final_equity,
        )
