"""Fundamental analysis helpers — ratios, scoring.

Skeleton: consumes a `FundamentalSnapshot` (provided by a data source)
and derives derived metrics / scores.
"""

from __future__ import annotations

from saham_id.data.models import FundamentalSnapshot


def value_score(snap: FundamentalSnapshot) -> float:
    """Simple 0–100 "value" score (lower PER + lower PBV + higher yield).

    TODO: calibrate weights vs sector medians; handle NaN gracefully.
    """
    score = 50.0
    if snap.per and snap.per > 0:
        # Cap contribution so extreme negatives don't dominate.
        score += max(-25.0, min(25.0, (15.0 - snap.per) * 1.5))
    if snap.pbv and snap.pbv > 0:
        score += max(-15.0, min(15.0, (2.0 - snap.pbv) * 5.0))
    if snap.dividend_yield:
        score += min(10.0, snap.dividend_yield * 100.0)
    return max(0.0, min(100.0, score))


def quality_score(snap: FundamentalSnapshot) -> float:
    """Simple 0–100 "quality" score (ROE, margin, solvency).

    TODO: add debt-coverage ratios, interest coverage.
    """
    score = 50.0
    if snap.roe:
        score += min(25.0, snap.roe * 100.0 / 2)
    if snap.net_margin:
        score += min(15.0, snap.net_margin * 100.0 / 2)
    if snap.der is not None:
        # Lower DER is better; penalize > 2.0.
        score += max(-10.0, min(10.0, (1.0 - snap.der) * 5.0))
    return max(0.0, min(100.0, score))
