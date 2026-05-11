"""Alert CLI helper — manage price alerts from terminal.

Used by CLI commands: saham alert add/list/check/remove

Usage:
    from saham_id.alert_cli import add_alert, list_alerts, check_alerts, remove_alert
"""
from __future__ import annotations
from typing import Optional
from saham_id.watchlist import Watchlist, AlertCondition
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


def add_alert(ticker: str, field: str = "last", op: str = "<", value: float = 0,
              watchlist_name: str = "alerts", message: str = "") -> str:
    """Add a price alert. Returns confirmation message."""
    wl = Watchlist.load(watchlist_name)
    if ticker.upper() not in wl:
        wl.add(ticker.upper())
    wl.add_alert(ticker.upper(), AlertCondition(field=field, op=op, value=value, message=message))
    wl.save(watchlist_name)
    return f"Alert added: {ticker.upper()} {field} {op} {value}"


def list_alerts(watchlist_name: str = "alerts") -> list[dict]:
    """List all alerts. Returns list of dicts."""
    wl = Watchlist.load(watchlist_name)
    results = []
    for ticker in wl.tickers:
        item = wl.get(ticker)
        for alert in item.alerts:
            results.append({"ticker": ticker, "condition": alert.describe(), "field": alert.field, "op": alert.op, "value": alert.value})
        if item.target_buy:
            results.append({"ticker": ticker, "condition": f"target_buy <= {item.target_buy}", "field": "target_buy", "op": "<=", "value": item.target_buy})
        if item.target_sell:
            results.append({"ticker": ticker, "condition": f"target_sell >= {item.target_sell}", "field": "target_sell", "op": ">=", "value": item.target_sell})
        if item.stop_loss:
            results.append({"ticker": ticker, "condition": f"stop_loss <= {item.stop_loss}", "field": "stop_loss", "op": "<=", "value": item.stop_loss})
    return results


def check_alerts(watchlist_name: str = "alerts", source: Optional[DataSource] = None) -> list[dict]:
    """Check all alerts against live data. Returns triggered alerts."""
    wl = Watchlist.load(watchlist_name)
    src = source or get_source()
    results = wl.check_alerts(source=src)
    return [{"ticker": r.ticker, "alerts": r.triggered_alerts, "values": r.current_values} for r in results]


def remove_alert(ticker: str, watchlist_name: str = "alerts") -> str:
    """Remove all alerts for a ticker."""
    wl = Watchlist.load(watchlist_name)
    if ticker.upper() in wl:
        wl.clear_alerts(ticker.upper())
        wl.save(watchlist_name)
        return f"Alerts cleared for {ticker.upper()}"
    return f"{ticker.upper()} not in watchlist"
