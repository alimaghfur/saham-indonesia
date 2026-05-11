"""Broker fee & tax calculator — hitung biaya trading IDX per broker.

IDX transaction costs:
    - Broker commission: varies per broker (buy + sell)
    - Levy (IDX + KPEI + KSEI): 0.043%
    - Pajak final penjualan: 0.1% of sell value
    - PPN (VAT) on commission: 11%

Usage:
    from saham_id.broker_fees import calculate_fees, BROKERS

    result = calculate_fees(price=9500, lots=10, broker="bca_sekuritas")
    print(result.total_buy_cost)
    print(result.total_sell_proceeds)
    print(result.breakeven_price)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# Broker commission rates (as fraction, e.g. 0.0015 = 0.15%)
BROKERS: dict[str, dict] = {
    "bca_sekuritas": {"name": "BCA Sekuritas", "buy_fee": 0.0015, "sell_fee": 0.0025},
    "mandiri_sekuritas": {"name": "Mandiri Sekuritas", "buy_fee": 0.0015, "sell_fee": 0.0025},
    "indo_premier": {"name": "Indo Premier (IPOT)", "buy_fee": 0.0019, "sell_fee": 0.0029},
    "mirae_asset": {"name": "Mirae Asset Sekuritas", "buy_fee": 0.0015, "sell_fee": 0.0025},
    "phillip_sekuritas": {"name": "Phillip Sekuritas", "buy_fee": 0.0018, "sell_fee": 0.0028},
    "ajaib": {"name": "Ajaib Sekuritas", "buy_fee": 0.0015, "sell_fee": 0.0025},
    "stockbit": {"name": "Stockbit (Bibit Sekuritas)", "buy_fee": 0.0010, "sell_fee": 0.0020},
    "most": {"name": "Mandiri e-Trading (MOST)", "buy_fee": 0.0015, "sell_fee": 0.0025},
    "rdn": {"name": "RDN (average)", "buy_fee": 0.0015, "sell_fee": 0.0025},
}

# IDX standard levies
IDX_LEVY = 0.00043  # 0.043% (IDX + KPEI + KSEI)
SELL_TAX = 0.001    # 0.1% pajak final penjualan
VAT_RATE = 0.11     # 11% PPN on commission


@dataclass
class FeeResult:
    """Complete fee breakdown for a trade."""

    # Input
    price: float
    lots: int
    shares: int
    broker: str

    # Buy side
    buy_commission: float
    buy_levy: float
    buy_vat: float
    total_buy_fee: float
    total_buy_cost: float  # price * shares + all fees

    # Sell side
    sell_commission: float
    sell_levy: float
    sell_tax: float
    sell_vat: float
    total_sell_fee: float
    total_sell_proceeds: float  # price * shares - all fees

    # Round-trip
    round_trip_fee: float
    round_trip_fee_pct: float
    breakeven_price: float  # minimum sell price to break even
    breakeven_ticks: int  # how many ticks above entry to break even


def calculate_fees(
    price: float,
    lots: int,
    broker: str = "bca_sekuritas",
    lot_size: int = 100,
) -> FeeResult:
    """Calculate complete fee breakdown for buying and selling.

    Parameters:
        price: Price per share (Rp)
        lots: Number of lots
        broker: Broker name key (see BROKERS dict)
        lot_size: Shares per lot (default: 100)

    Returns:
        FeeResult with detailed buy/sell/round-trip breakdown
    """
    shares = lots * lot_size
    value = price * shares

    broker_info = BROKERS.get(broker, BROKERS["bca_sekuritas"])
    buy_rate = broker_info["buy_fee"]
    sell_rate = broker_info["sell_fee"]

    # Buy fees
    buy_commission = value * buy_rate
    buy_levy = value * IDX_LEVY
    buy_vat = buy_commission * VAT_RATE
    total_buy_fee = buy_commission + buy_levy + buy_vat
    total_buy_cost = value + total_buy_fee

    # Sell fees
    sell_commission = value * sell_rate
    sell_levy = value * IDX_LEVY
    sell_tax = value * SELL_TAX
    sell_vat = sell_commission * VAT_RATE
    total_sell_fee = sell_commission + sell_levy + sell_tax + sell_vat
    total_sell_proceeds = value - total_sell_fee

    # Round-trip
    round_trip = total_buy_fee + total_sell_fee
    round_trip_pct = round_trip / value if value > 0 else 0

    # Breakeven: total_buy_cost = sell_price * shares - sell_fees_at_new_price
    # Approximate: breakeven_price ≈ price * (1 + round_trip_pct)
    breakeven = price * (1 + round_trip_pct) if price > 0 else 0

    # IDX tick size logic (simplified)
    tick = _get_tick_size(price)
    breakeven_ticks = int((breakeven - price) / tick) + 1 if tick > 0 else 0

    return FeeResult(
        price=price, lots=lots, shares=shares, broker=broker_info["name"],
        buy_commission=round(buy_commission, 0), buy_levy=round(buy_levy, 0),
        buy_vat=round(buy_vat, 0), total_buy_fee=round(total_buy_fee, 0),
        total_buy_cost=round(total_buy_cost, 0),
        sell_commission=round(sell_commission, 0), sell_levy=round(sell_levy, 0),
        sell_tax=round(sell_tax, 0), sell_vat=round(sell_vat, 0),
        total_sell_fee=round(total_sell_fee, 0),
        total_sell_proceeds=round(total_sell_proceeds, 0),
        round_trip_fee=round(round_trip, 0),
        round_trip_fee_pct=round(round_trip_pct, 5),
        breakeven_price=round(breakeven, 0),
        breakeven_ticks=breakeven_ticks,
    )


def compare_brokers(price: float, lots: int) -> list[FeeResult]:
    """Compare fees across all brokers for the same trade."""
    results = []
    for broker_key in BROKERS:
        results.append(calculate_fees(price, lots, broker=broker_key))
    results.sort(key=lambda r: r.round_trip_fee)
    return results


def _get_tick_size(price: float) -> float:
    """IDX tick size based on price range (per POJK rules)."""
    if price < 200:
        return 1
    elif price < 500:
        return 2
    elif price < 2000:
        return 5
    elif price < 5000:
        return 10
    else:
        return 25


def list_brokers() -> list[dict]:
    """List all supported brokers with their fee rates."""
    return [
        {
            "key": key,
            "name": info["name"],
            "buy_fee_pct": f"{info['buy_fee']*100:.2f}%",
            "sell_fee_pct": f"{info['sell_fee']*100:.2f}%",
        }
        for key, info in BROKERS.items()
    ]
