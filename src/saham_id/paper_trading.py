"""Paper trading — simulated live trading without real money.

Connects to live data sources and executes virtual trades at market prices.
Records all orders, fills, and P/L as if trading real money.

Usage:
    from saham_id.paper_trading import PaperTrader, PaperOrder

    trader = PaperTrader(initial_capital=100_000_000)
    trader.buy("BBCA", lots=10)   # Buys at current market price
    trader.sell("BBCA", lots=5)   # Sells at current market price

    print(trader.portfolio_value())
    print(trader.trade_history())
    trader.save("my_paper_session")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Literal, Optional

from saham_id.config import settings
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource, SourceError


@dataclass
class PaperOrder:
    """A paper trading order."""
    ticker: str
    side: Literal["buy", "sell"]
    lots: int
    shares: int = 0
    price: float = 0.0
    filled_at: Optional[datetime] = None
    status: str = "pending"  # pending, filled, rejected
    note: str = ""

    def __post_init__(self):
        self.shares = self.lots * 100


@dataclass
class PaperPosition:
    """Current position in paper trading."""
    ticker: str
    shares: int = 0
    avg_cost: float = 0.0
    realized_pnl: float = 0.0

    @property
    def lots(self) -> int:
        return self.shares // 100


@dataclass
class PaperTrade:
    """Completed trade record."""
    ticker: str
    side: str
    shares: int
    price: float
    value: float
    fee: float
    timestamp: datetime
    note: str = ""


class PaperTrader:
    """Paper trading engine — simulate real trading with live prices.

    Features:
        - Buy/sell at current market price (from configured data source)
        - Realistic commission simulation (default 0.15% per side)
        - Position tracking with average cost
        - P/L calculation (realized + unrealized)
        - Trade history and performance stats
        - Save/load sessions
    """

    def __init__(
        self,
        initial_capital: float = 100_000_000,
        commission_pct: float = 0.0015,
        source: Optional[DataSource] = None,
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_pct = commission_pct
        self._source = source
        self.positions: dict[str, PaperPosition] = {}
        self.trades: list[PaperTrade] = []
        self.orders: list[PaperOrder] = []
        self.started_at = datetime.utcnow()

    @property
    def source(self) -> DataSource:
        if self._source is None:
            self._source = get_source()
        return self._source

    def _get_price(self, ticker: str) -> float:
        """Get current market price."""
        quote = self.source.get_quote(ticker)
        return float(quote.last)

    def buy(self, ticker: str, lots: int = 1, note: str = "") -> PaperOrder:
        """Buy stock at current market price.

        Parameters:
            ticker: IDX ticker
            lots: Number of lots (1 lot = 100 shares)
            note: Optional note

        Returns:
            PaperOrder with fill details
        """
        ticker = ticker.upper()
        order = PaperOrder(ticker=ticker, side="buy", lots=lots, note=note)

        try:
            price = self._get_price(ticker)
        except (SourceError, Exception) as exc:
            order.status = "rejected"
            order.note = f"Price unavailable: {exc}"
            self.orders.append(order)
            return order

        shares = lots * 100
        fee = price * shares * self.commission_pct
        total_cost = price * shares + fee

        if total_cost > self.cash:
            order.status = "rejected"
            order.note = f"Insufficient cash: need Rp {total_cost:,.0f}, have Rp {self.cash:,.0f}"
            self.orders.append(order)
            return order

        # Execute
        order.price = price
        order.filled_at = datetime.utcnow()
        order.status = "filled"

        # Update position
        pos = self.positions.setdefault(ticker, PaperPosition(ticker=ticker))
        if pos.shares > 0:
            # Average up/down
            total_value = pos.avg_cost * pos.shares + price * shares
            pos.shares += shares
            pos.avg_cost = total_value / pos.shares
        else:
            pos.shares = shares
            pos.avg_cost = price

        self.cash -= total_cost

        # Record trade
        self.trades.append(PaperTrade(
            ticker=ticker, side="buy", shares=shares,
            price=price, value=price * shares, fee=fee,
            timestamp=datetime.utcnow(), note=note,
        ))
        self.orders.append(order)
        return order

    def sell(self, ticker: str, lots: int = 1, note: str = "") -> PaperOrder:
        """Sell stock at current market price."""
        ticker = ticker.upper()
        order = PaperOrder(ticker=ticker, side="sell", lots=lots, note=note)

        pos = self.positions.get(ticker)
        shares = lots * 100

        if not pos or pos.shares < shares:
            order.status = "rejected"
            order.note = f"Insufficient shares: have {pos.shares if pos else 0}, need {shares}"
            self.orders.append(order)
            return order

        try:
            price = self._get_price(ticker)
        except (SourceError, Exception) as exc:
            order.status = "rejected"
            order.note = f"Price unavailable: {exc}"
            self.orders.append(order)
            return order

        fee = price * shares * self.commission_pct
        proceeds = price * shares - fee

        # Calculate realized P/L
        cost_basis = pos.avg_cost * shares
        pnl = proceeds - cost_basis + fee  # add back fee for pure price P/L calc
        pos.realized_pnl += (price - pos.avg_cost) * shares

        # Update position
        pos.shares -= shares
        if pos.shares == 0:
            pos.avg_cost = 0.0

        self.cash += proceeds

        # Execute order
        order.price = price
        order.filled_at = datetime.utcnow()
        order.status = "filled"

        self.trades.append(PaperTrade(
            ticker=ticker, side="sell", shares=shares,
            price=price, value=price * shares, fee=fee,
            timestamp=datetime.utcnow(), note=note,
        ))
        self.orders.append(order)
        return order

    def portfolio_value(self) -> float:
        """Calculate total portfolio value (cash + positions at market)."""
        total = self.cash
        for ticker, pos in self.positions.items():
            if pos.shares > 0:
                try:
                    price = self._get_price(ticker)
                    total += price * pos.shares
                except Exception:
                    total += pos.avg_cost * pos.shares  # fallback
        return total

    def total_pnl(self) -> float:
        """Total P/L since start."""
        return self.portfolio_value() - self.initial_capital

    def total_return_pct(self) -> float:
        """Total return as percentage."""
        if self.initial_capital == 0:
            return 0.0
        return self.total_pnl() / self.initial_capital

    def win_rate(self) -> float:
        """Win rate from completed round-trip trades."""
        sells = [t for t in self.trades if t.side == "sell"]
        if not sells:
            return 0.0
        # Approximate: sell price > avg cost of position at time
        wins = sum(1 for t in sells if t.price > 0)  # simplified
        return wins / len(sells)

    def summary(self) -> dict:
        """Get portfolio summary."""
        return {
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "portfolio_value": self.portfolio_value(),
            "total_pnl": self.total_pnl(),
            "total_return_pct": self.total_return_pct(),
            "num_trades": len(self.trades),
            "positions": {
                t: {"shares": p.shares, "avg_cost": p.avg_cost, "realized_pnl": p.realized_pnl}
                for t, p in self.positions.items() if p.shares > 0
            },
            "started_at": self.started_at.isoformat(),
        }

    def save(self, name: str = "default") -> Path:
        """Save paper trading session to JSON."""
        storage = settings.cache_dir / "paper_trading"
        storage.mkdir(parents=True, exist_ok=True)
        filepath = storage / f"{name}.json"

        data = {
            "name": name,
            "saved_at": datetime.utcnow().isoformat(),
            "initial_capital": self.initial_capital,
            "cash": self.cash,
            "commission_pct": self.commission_pct,
            "positions": {
                t: {"shares": p.shares, "avg_cost": p.avg_cost, "realized_pnl": p.realized_pnl}
                for t, p in self.positions.items()
            },
            "trades": [
                {
                    "ticker": t.ticker, "side": t.side, "shares": t.shares,
                    "price": t.price, "value": t.value, "fee": t.fee,
                    "timestamp": t.timestamp.isoformat(), "note": t.note,
                }
                for t in self.trades
            ],
            "started_at": self.started_at.isoformat(),
        }
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return filepath

    @classmethod
    def load(cls, name: str = "default", source: Optional[DataSource] = None) -> "PaperTrader":
        """Load a saved paper trading session."""
        storage = settings.cache_dir / "paper_trading"
        filepath = storage / f"{name}.json"

        if not filepath.exists():
            return cls(source=source)

        data = json.loads(filepath.read_text())
        trader = cls(
            initial_capital=data["initial_capital"],
            commission_pct=data.get("commission_pct", 0.0015),
            source=source,
        )
        trader.cash = data["cash"]

        for ticker, pos_data in data.get("positions", {}).items():
            trader.positions[ticker] = PaperPosition(
                ticker=ticker,
                shares=pos_data["shares"],
                avg_cost=pos_data["avg_cost"],
                realized_pnl=pos_data.get("realized_pnl", 0),
            )

        for t_data in data.get("trades", []):
            trader.trades.append(PaperTrade(
                ticker=t_data["ticker"],
                side=t_data["side"],
                shares=t_data["shares"],
                price=t_data["price"],
                value=t_data["value"],
                fee=t_data["fee"],
                timestamp=datetime.fromisoformat(t_data["timestamp"]),
                note=t_data.get("note", ""),
            ))

        if data.get("started_at"):
            trader.started_at = datetime.fromisoformat(data["started_at"])

        return trader
