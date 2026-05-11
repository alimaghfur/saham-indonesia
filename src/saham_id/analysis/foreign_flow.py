"""Foreign Flow Analysis — track aktivitas investor asing di IDX.

Menganalisis saham mana yang sedang diakumulasi atau didistribusi oleh
investor asing (foreign broker). Foreign flow adalah indikator penting
karena asing sering menjadi "smart money" yang menggerakkan IHSG.

Data source yang bisa digunakan:
    - RTI Business (free, delayed): foreign net buy per saham
    - Sectors.app (premium): real-time foreign flow
    - GoAPI: foreign buy/sell breakdown

Untuk estimasi tanpa data foreign-specific, kita gunakan proxy dari OHLCV.

Usage:
    from saham_id.analysis.foreign_flow import (
        estimate_foreign_flow, foreign_scan, foreign_trend
    )

    summary = estimate_foreign_flow(df, ticker="BBCA")
    print(summary.activity)         # HEAVY_BUYING / BUYING / NEUTRAL / ...
    print(summary.total_net_20d)    # Net foreign flow 20 hari

    top_accumulated = foreign_net_buy_top(universe="LQ45", days=20, top_n=10)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Iterable, Optional

import pandas as pd

from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


class ForeignActivity(str, Enum):
    HEAVY_BUYING = "HEAVY_BUYING"
    BUYING = "BUYING"
    NEUTRAL = "NEUTRAL"
    SELLING = "SELLING"
    HEAVY_SELLING = "HEAVY_SELLING"


ACTIVITY_DESCRIPTIONS = {
    ForeignActivity.HEAVY_BUYING: "Asing masuk DERAS — akumulasi kuat",
    ForeignActivity.BUYING: "Asing masuk — akumulasi moderat",
    ForeignActivity.NEUTRAL: "Aktivitas asing netral — tidak ada pola dominan",
    ForeignActivity.SELLING: "Asing keluar — distribusi moderat",
    ForeignActivity.HEAVY_SELLING: "Asing keluar DERAS — distribusi kuat, waspada",
}


@dataclass
class ForeignFlowData:
    ticker: str
    date: date
    net_foreign: float
    foreign_buy_value: float = 0.0
    foreign_sell_value: float = 0.0
    foreign_buy_volume: int = 0
    foreign_sell_volume: int = 0
    total_value: float = 0.0

    @property
    def is_net_buy(self) -> bool:
        return self.net_foreign > 0

    @property
    def foreign_dominance(self) -> float:
        if self.total_value <= 0:
            return 0.0
        total_foreign = abs(self.foreign_buy_value) + abs(self.foreign_sell_value)
        return total_foreign / self.total_value


@dataclass
class ForeignFlowSummary:
    ticker: str
    period_days: int = 20
    as_of: Optional[datetime] = None
    total_net_20d: float = 0.0
    total_net_5d: float = 0.0
    avg_daily_net: float = 0.0
    accumulation_days: int = 0
    distribution_days: int = 0
    flow_consistency: float = 0.0
    activity: ForeignActivity = ForeignActivity.NEUTRAL
    description: str = ""
    daily_flows: list[ForeignFlowData] = field(default_factory=list)

    def __post_init__(self):
        if not self.as_of:
            self.as_of = datetime.utcnow()
        if not self.description:
            self.description = ACTIVITY_DESCRIPTIONS.get(self.activity, "")

    @property
    def is_accumulation(self) -> bool:
        return self.activity in (ForeignActivity.HEAVY_BUYING, ForeignActivity.BUYING)

    @property
    def is_distribution(self) -> bool:
        return self.activity in (ForeignActivity.HEAVY_SELLING, ForeignActivity.SELLING)


def classify_foreign_activity(net_flow_20d: float, flow_consistency: float, avg_daily_net: float) -> ForeignActivity:
    heavy_threshold = 5_000_000_000
    moderate_threshold = 1_000_000_000
    if net_flow_20d > heavy_threshold and flow_consistency > 0.6:
        return ForeignActivity.HEAVY_BUYING
    if net_flow_20d > moderate_threshold and flow_consistency > 0.5:
        return ForeignActivity.BUYING
    if net_flow_20d < -heavy_threshold and flow_consistency > 0.6:
        return ForeignActivity.HEAVY_SELLING
    if net_flow_20d < -moderate_threshold and flow_consistency > 0.5:
        return ForeignActivity.SELLING
    return ForeignActivity.NEUTRAL


def compute_foreign_dominance(foreign_value: float, total_value: float) -> float:
    if total_value <= 0:
        return 0.0
    return foreign_value / total_value


def _estimate_daily_net(bar) -> float:
    """Estimasi net foreign flow dari 1 bar OHLCV menggunakan MF formula."""
    o = float(bar["open"]) if bar["open"] is not None else 0
    h = float(bar["high"]) if bar["high"] is not None else 0
    l = float(bar["low"]) if bar["low"] is not None else 0
    c = float(bar["close"]) if bar["close"] is not None else 0
    v = float(bar["volume"]) if bar["volume"] is not None else 0
    if h == l or v == 0 or c == 0:
        return 0.0
    mfm = ((c - l) - (h - c)) / (h - l)
    return mfm * v * c


def estimate_foreign_flow(df: pd.DataFrame, ticker: str = "", period_days: int = 20) -> ForeignFlowSummary:
    if df.empty or len(df) < period_days:
        return ForeignFlowSummary(ticker=ticker, period_days=period_days)

    recent = df.tail(period_days)
    daily_flows = []
    accumulation = distribution = 0

    for i in range(len(recent)):
        bar = {
            "open": recent["open"].iloc[i], "high": recent["high"].iloc[i],
            "low": recent["low"].iloc[i], "close": recent["close"].iloc[i],
            "volume": recent["volume"].iloc[i],
        }
        flow = _estimate_daily_net(bar)
        daily_flows.append(flow)
        if flow > 0:
            accumulation += 1
        elif flow < 0:
            distribution += 1

    total_net = sum(daily_flows)
    total_5d = sum(daily_flows[-5:]) if len(daily_flows) >= 5 else total_net
    avg_daily = total_net / len(daily_flows) if daily_flows else 0

    total_days = accumulation + distribution
    consistency = max(accumulation, distribution) / total_days if total_days > 0 else 0.0

    activity = classify_foreign_activity(total_net, consistency, avg_daily)

    return ForeignFlowSummary(
        ticker=ticker, period_days=period_days,
        total_net_20d=total_net, total_net_5d=total_5d, avg_daily_net=avg_daily,
        accumulation_days=accumulation, distribution_days=distribution,
        flow_consistency=round(consistency, 3), activity=activity,
    )


def foreign_trend(df: pd.DataFrame, ticker: str = "", lookback: int = 20) -> dict:
    if df.empty or len(df) < lookback:
        return {"ticker": ticker, "trend": "stable", "change_pct": 0.0,
                "first_half_net": 0.0, "second_half_net": 0.0}

    recent = df.tail(lookback)
    mid = len(recent) // 2

    first_half = [_estimate_daily_net({
        "open": recent["open"].iloc[i], "high": recent["high"].iloc[i],
        "low": recent["low"].iloc[i], "close": recent["close"].iloc[i],
        "volume": recent["volume"].iloc[i],
    }) for i in range(mid)]
    second_half = [_estimate_daily_net({
        "open": recent["open"].iloc[i], "high": recent["high"].iloc[i],
        "low": recent["low"].iloc[i], "close": recent["close"].iloc[i],
        "volume": recent["volume"].iloc[i],
    }) for i in range(mid, len(recent))]

    first_net = sum(first_half)
    second_net = sum(second_half)

    if abs(first_net) < 1e-6:
        change_pct = 0.0 if abs(second_net) < 1e-6 else 1.0
    else:
        change_pct = (second_net - first_net) / abs(first_net)

    if change_pct > 0.3:
        trend = "increasing"
    elif change_pct < -0.3:
        trend = "decreasing"
    else:
        trend = "stable"

    return {
        "ticker": ticker, "trend": trend, "change_pct": round(change_pct, 3),
        "first_half_net": first_net, "second_half_net": second_net,
    }


def foreign_scan(universe="LQ45", days: int = 20, min_net_buy: float = 1_000_000_000,
                activity_filter=None, top_n: int = 15, source=None):
    from saham_id.data.universe import get_universe
    src = source or get_source()
    tickers = list(universe) if not isinstance(universe, str) else get_universe(universe)
    results = []
    for ticker in tickers:
        try:
            df = src.get_ohlc(ticker, period="3mo", interval="1d")
            if df.empty or len(df) < days:
                continue
            summary = estimate_foreign_flow(df, ticker=ticker, period_days=days)
            if abs(summary.total_net_20d) < min_net_buy:
                continue
            if activity_filter and summary.activity != activity_filter:
                continue
            results.append(summary)
        except Exception:
            continue
    results.sort(key=lambda r: abs(r.total_net_20d), reverse=True)
    return results[:top_n]


def foreign_net_buy_top(universe="LQ45", days: int = 20, top_n: int = 10, source=None):
    """Top saham yang diakumulasi asing (net buy terbesar)."""
    results = foreign_scan(universe=universe, days=days, top_n=top_n * 3, source=source)
    buyers = [r for r in results if r.total_net_20d > 0]
    buyers.sort(key=lambda r: r.total_net_20d, reverse=True)
    return buyers[:top_n]


def foreign_net_sell_top(universe="LQ45", days: int = 20, top_n: int = 10, source=None):
    """Top saham yang didistribusi asing (net sell terbesar)."""
    results = foreign_scan(universe=universe, days=days, top_n=top_n * 3, source=source)
    sellers = [r for r in results if r.total_net_20d < 0]
    sellers.sort(key=lambda r: r.total_net_20d)
    return sellers[:top_n]
