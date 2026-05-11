"""Lot calculator — hitung berapa lot bisa dibeli dengan budget tertentu.

Usage:
    from saham_id.lot_calculator import calculate_lots, LotResult
    result = calculate_lots(budget=10_000_000, price=9500)
    print(f"{result.lots} lot ({result.shares} lembar), total Rp {result.total_cost:,.0f}")
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class LotResult:
    lots: int
    shares: int
    price: float
    total_cost: float
    fee: float
    total_with_fee: float
    remaining_cash: float
    budget: float

    @property
    def fee_pct(self) -> float:
        return self.fee / self.total_cost if self.total_cost > 0 else 0.0


def calculate_lots(budget: float, price: float, fee_pct: float = 0.0015, lot_size: int = 100) -> LotResult:
    if price <= 0 or budget <= 0:
        return LotResult(lots=0, shares=0, price=price, total_cost=0, fee=0, total_with_fee=0, remaining_cash=budget, budget=budget)
    cost_per_lot = price * lot_size * (1 + fee_pct)
    lots = int(budget // cost_per_lot)
    shares = lots * lot_size
    total_cost = shares * price
    fee = total_cost * fee_pct
    total_with_fee = total_cost + fee
    remaining = budget - total_with_fee
    return LotResult(lots=lots, shares=shares, price=price, total_cost=total_cost, fee=fee, total_with_fee=total_with_fee, remaining_cash=remaining, budget=budget)


def lots_for_target_allocation(portfolio_value: float, target_pct: float, price: float, fee_pct: float = 0.0015) -> LotResult:
    budget = portfolio_value * target_pct
    return calculate_lots(budget=budget, price=price, fee_pct=fee_pct)


def multi_stock_allocation(budget: float, stocks: list[dict], fee_pct: float = 0.0015) -> list[LotResult]:
    """Hitung lot untuk multiple stocks. stocks = [{"ticker": "BBCA", "price": 9500, "weight": 0.4}, ...]"""
    results = []
    for s in stocks:
        alloc = budget * s.get("weight", 1.0 / len(stocks))
        results.append(calculate_lots(budget=alloc, price=s["price"], fee_pct=fee_pct))
    return results
