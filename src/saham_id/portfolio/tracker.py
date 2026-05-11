"""Minimal portfolio tracker — positions, transactions, unrealized P/L.

Designed to plug into any DataSource for current-quote lookups, so the
same code works whether you're using yfinance (delayed) or a paid
realtime provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal

import pandas as pd

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource

TxSide = Literal["buy", "sell"]


@dataclass
class Transaction:
    ticker: str
    side: TxSide
    quantity: int
    price: Decimal
    timestamp: datetime
    fee: Decimal = Decimal(0)
    note: str = ""


@dataclass
class Position:
    ticker: str
    quantity: int = 0
    avg_cost: Decimal = Decimal(0)       # cost basis per share
    realized_pnl: Decimal = Decimal(0)

    def apply(self, tx: Transaction) -> None:
        if tx.side == "buy":
            total_cost = self.avg_cost * self.quantity + tx.price * tx.quantity + tx.fee
            self.quantity += tx.quantity
            self.avg_cost = total_cost / Decimal(self.quantity) if self.quantity else Decimal(0)
        else:
            if tx.quantity > self.quantity:
                raise ValueError(
                    f"Sell {tx.quantity} exceeds position {self.quantity} for {self.ticker}"
                )
            proceeds = tx.price * tx.quantity - tx.fee
            cost_out = self.avg_cost * tx.quantity
            self.realized_pnl += proceeds - cost_out
            self.quantity -= tx.quantity
            if self.quantity == 0:
                self.avg_cost = Decimal(0)


@dataclass
class Portfolio:
    cash: Decimal = Decimal(0)
    positions: dict[str, Position] = field(default_factory=dict)
    transactions: list[Transaction] = field(default_factory=list)

    def record(self, tx: Transaction) -> None:
        """Record a transaction and update the affected position."""
        pos = self.positions.setdefault(tx.ticker, Position(ticker=tx.ticker))
        pos.apply(tx)
        if tx.side == "buy":
            self.cash -= tx.price * tx.quantity + tx.fee
        else:
            self.cash += tx.price * tx.quantity - tx.fee
        self.transactions.append(tx)

    def snapshot(self, source: DataSource | None = None) -> pd.DataFrame:
        """Return a DataFrame with current position values and unrealized P/L."""
        src = source or get_source()
        rows: list[dict] = []
        for ticker, pos in self.positions.items():
            if pos.quantity == 0:
                continue
            try:
                q = src.get_quote(ticker)
                last = q.last
            except Exception:
                last = pos.avg_cost  # fallback if quote unavailable
            market_value = last * pos.quantity
            unrealized = (last - pos.avg_cost) * pos.quantity
            rows.append(
                {
                    "ticker": ticker,
                    "quantity": pos.quantity,
                    "avg_cost": float(pos.avg_cost),
                    "last": float(last),
                    "market_value": float(market_value),
                    "unrealized_pnl": float(unrealized),
                    "realized_pnl": float(pos.realized_pnl),
                }
            )
        df = pd.DataFrame(rows)
        if not df.empty:
            df["weight"] = df["market_value"] / df["market_value"].sum()
        return df

    def total_value(self, source: DataSource | None = None) -> Decimal:
        snap = self.snapshot(source)
        mv = Decimal(str(snap["market_value"].sum())) if not snap.empty else Decimal(0)
        return self.cash + mv
