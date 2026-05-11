"""Auto-Rebalancing — calculate trades to reach target allocation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


@dataclass
class RebalanceOrder:
    ticker: str
    action: Literal["buy", "sell", "hold"]
    shares: int
    lots: int
    price: float
    current_weight: float
    target_weight: float
    deviation: float
    estimated_cost: float = 0.0

    @property
    def is_actionable(self) -> bool:
        return self.action != "hold" and self.lots > 0


@dataclass
class RebalanceResult:
    orders: list[RebalanceOrder] = field(default_factory=list)
    total_buy_cost: float = 0.0
    total_sell_proceeds: float = 0.0
    net_cash_needed: float = 0.0

    @property
    def actionable_orders(self) -> list[RebalanceOrder]:
        return [o for o in self.orders if o.is_actionable]

    @property
    def num_buys(self) -> int:
        return sum(1 for o in self.orders if o.action == "buy" and o.lots > 0)

    @property
    def num_sells(self) -> int:
        return sum(1 for o in self.orders if o.action == "sell" and o.lots > 0)


def rebalance(current_positions: dict[str, int], target_weights: dict[str, float],
              total_capital: Optional[float] = None, tolerance: float = 0.02,
              source: Optional[DataSource] = None) -> RebalanceResult:
    src = source or get_source()
    prices: dict[str, float] = {}
    for ticker in set(list(current_positions.keys()) + list(target_weights.keys())):
        try:
            quote = src.get_quote(ticker)
            prices[ticker] = float(quote.last)
        except Exception:
            prices[ticker] = 0.0

    if total_capital is None:
        total_capital = sum(shares * prices.get(t, 0) for t, shares in current_positions.items())
    if total_capital <= 0:
        return RebalanceResult()

    orders: list[RebalanceOrder] = []
    total_buy = total_sell = 0.0
    all_tickers = sorted(set(list(current_positions.keys()) + list(target_weights.keys())))

    for ticker in all_tickers:
        shares = current_positions.get(ticker, 0)
        price = prices.get(ticker, 0)
        current_w = (shares * price) / total_capital if total_capital > 0 else 0
        target_w = target_weights.get(ticker, 0.0)
        deviation = target_w - current_w

        if price <= 0 or abs(deviation) < tolerance:
            orders.append(RebalanceOrder(ticker=ticker, action="hold", shares=0, lots=0,
                                        price=price, current_weight=current_w,
                                        target_weight=target_w, deviation=deviation))
            continue

        value_diff = total_capital * target_w - shares * price
        shares_diff = int(value_diff / price)
        lots_diff = abs(shares_diff) // 100

        if shares_diff > 0:
            action, cost = "buy", lots_diff * 100 * price
            total_buy += cost
        elif shares_diff < 0:
            action, cost = "sell", lots_diff * 100 * price
            total_sell += cost
        else:
            action, cost = "hold", 0

        orders.append(RebalanceOrder(
            ticker=ticker, action=action, shares=lots_diff * 100, lots=lots_diff,
            price=price, current_weight=round(current_w, 4),
            target_weight=round(target_w, 4), deviation=round(deviation, 4),
            estimated_cost=cost,
        ))

    orders.sort(key=lambda o: (0 if o.action == "sell" else 1, -abs(o.deviation)))
    return RebalanceResult(orders=orders, total_buy_cost=total_buy,
                          total_sell_proceeds=total_sell, net_cash_needed=total_buy - total_sell)
