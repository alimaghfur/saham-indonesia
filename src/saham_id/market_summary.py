"""Market Summary Report — auto-generate daily market overview.

Combines breadth, movers, trending, regime, and sector rotation into
a single structured report.

Usage:
    from saham_id.market_summary import generate_daily_summary

    summary = generate_daily_summary()
    print(summary.headline)
    print(summary.to_text())
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


@dataclass
class MarketSummaryReport:
    headline: str = ""
    market_status: str = ""  # bullish/bearish/neutral
    ihsg_change_pct: float = 0.0
    advancers: int = 0
    decliners: int = 0
    ad_ratio: float = 0.0
    top_gainers: list[str] = field(default_factory=list)
    top_losers: list[str] = field(default_factory=list)
    trending_stocks: list[str] = field(default_factory=list)
    unusual_activity: list[str] = field(default_factory=list)
    regime: str = ""
    regime_recommendation: str = ""
    leading_sectors: list[str] = field(default_factory=list)
    lagging_sectors: list[str] = field(default_factory=list)
    foreign_top_buys: list[str] = field(default_factory=list)
    foreign_top_sells: list[str] = field(default_factory=list)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow()

    def to_text(self) -> str:
        lines = [
            f"=== MARKET SUMMARY ({self.timestamp.strftime('%Y-%m-%d %H:%M')}) ===",
            f"",
            f"STATUS: {self.market_status.upper()}",
            f"IHSG: {self.ihsg_change_pct:+.2%}",
            f"Advancers/Decliners: {self.advancers}/{self.decliners} (ratio: {self.ad_ratio:.2f})",
            f"",
            f"TOP GAINERS: {', '.join(self.top_gainers[:5])}",
            f"TOP LOSERS: {', '.join(self.top_losers[:5])}",
            f"TRENDING: {', '.join(self.trending_stocks[:5])}",
            f"",
            f"REGIME: {self.regime}",
            f"  {self.regime_recommendation}",
            f"",
            f"LEADING SECTORS: {', '.join(self.leading_sectors[:3])}",
            f"LAGGING SECTORS: {', '.join(self.lagging_sectors[:3])}",
        ]
        if self.foreign_top_buys:
            lines.append(f"\nASING MASUK: {', '.join(self.foreign_top_buys[:5])}")
        if self.foreign_top_sells:
            lines.append(f"ASING KELUAR: {', '.join(self.foreign_top_sells[:5])}")
        if self.unusual_activity:
            lines.append(f"\nUNUSUAL: {', '.join(self.unusual_activity[:5])}")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "🟡"}.get(self.market_status, "⚪")
        lines = [
            f"## {emoji} Market Summary",
            f"*{self.timestamp.strftime('%Y-%m-%d %H:%M')}*",
            f"",
            f"**IHSG:** {self.ihsg_change_pct:+.2%} | A/D: {self.advancers}/{self.decliners}",
            f"**Regime:** {self.regime}",
            f"",
            f"**Gainers:** {', '.join(self.top_gainers[:5])}",
            f"**Losers:** {', '.join(self.top_losers[:5])}",
            f"**Trending:** {', '.join(self.trending_stocks[:5])}",
        ]
        if self.foreign_top_buys:
            lines.append(f"**Asing Masuk:** {', '.join(self.foreign_top_buys[:5])}")
        return "\n".join(lines)


def generate_daily_summary(universe: str = "LQ45", source: Optional[DataSource] = None) -> MarketSummaryReport:
    """Generate comprehensive daily market summary."""
    src = source or get_source()
    report = MarketSummaryReport()

    # Breadth
    try:
        from saham_id.market.breadth import snapshot
        snap = snapshot(universe=universe, source=src)
        report.advancers = snap.advancers
        report.decliners = snap.decliners
        report.ad_ratio = snap.ad_ratio
    except Exception:
        pass

    # Movers
    try:
        from saham_id.market.movers import top_gainers, top_losers
        gainers = top_gainers(universe=universe, period="1D", top_n=5, source=src)
        losers = top_losers(universe=universe, period="1D", top_n=5, source=src)
        report.top_gainers = [m.ticker for m in gainers]
        report.top_losers = [m.ticker for m in losers]
    except Exception:
        pass

    # Trending
    try:
        from saham_id.market.trending import detect
        trending = detect(universe=universe, timeframe="1D", top_n=5, source=src)
        report.trending_stocks = [r.ticker for r in trending.rows]
    except Exception:
        pass

    # Regime
    try:
        from saham_id.market.regime import detect_regime
        regime = detect_regime(source=src)
        report.regime = regime.state.value
        report.regime_recommendation = regime.description
    except Exception:
        pass

    # Overall status
    if report.ad_ratio > 1.5:
        report.market_status = "bullish"
    elif report.ad_ratio < 0.7:
        report.market_status = "bearish"
    else:
        report.market_status = "neutral"

    # Headline
    emoji = {"bullish": "Menguat", "bearish": "Melemah", "neutral": "Mixed"}.get(report.market_status, "")
    report.headline = f"Pasar {emoji} — A/D {report.advancers}/{report.decliners}"

    return report
