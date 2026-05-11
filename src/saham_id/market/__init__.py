"""Market snapshot — movers, trending, unusual activity, breadth.

Public API:
    from saham_id.market import movers, trending, unusual_activity, breadth

    movers.top_gainers(universe="LQ45")
    movers.top_losers(universe="LQ45")
    trending.detect(universe="LQ45")
    unusual_activity.detect(universe="LQ45")
    breadth.snapshot(universe="LQ45")
"""

from saham_id.market import breadth, movers, trending, unusual_activity

__all__ = ["movers", "trending", "unusual_activity", "breadth"]
