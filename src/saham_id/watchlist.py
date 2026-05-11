"""Watchlist system — save favorite stocks + alert conditions.

Usage:
    from saham_id.watchlist import Watchlist, AlertCondition

    wl = Watchlist.load("my_watchlist")   # or Watchlist()
    wl.add("BBCA", notes="Banking leader")
    wl.add("TLKM", alerts=[AlertCondition(field="rsi", op="<", value=30)])
    wl.save("my_watchlist")

    # Check alerts
    triggered = wl.check_alerts(source=src)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional

from saham_id.config import settings
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource


ComparisonOp = Literal["<", "<=", ">", ">=", "==", "!="]


@dataclass
class AlertCondition:
    """A single alert condition on a stock metric.

    Examples:
        AlertCondition(field="rsi", op="<", value=30)  -> RSI oversold
        AlertCondition(field="change_pct", op=">", value=0.05)  -> +5% move
        AlertCondition(field="volume", op=">", value=50_000_000)  -> high volume
    """

    field: str        # "rsi", "change_pct", "last", "volume", "atr_pct"
    op: ComparisonOp  # comparison operator
    value: float      # threshold value
    message: str = ""  # optional custom alert message

    def evaluate(self, actual_value: float) -> bool:
        """Check if the condition is triggered."""
        ops = {
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: abs(a - b) < 1e-9,
            "!=": lambda a, b: abs(a - b) >= 1e-9,
        }
        return ops[self.op](actual_value, self.value)

    def describe(self) -> str:
        """Human-readable description."""
        if self.message:
            return self.message
        return f"{self.field} {self.op} {self.value}"


@dataclass
class WatchlistItem:
    """A single stock in the watchlist."""

    ticker: str
    added_at: str = ""  # ISO timestamp
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    alerts: list[AlertCondition] = field(default_factory=list)
    target_buy: Optional[float] = None   # target buy price
    target_sell: Optional[float] = None  # target sell price
    stop_loss: Optional[float] = None    # stop loss price

    def __post_init__(self):
        if not self.added_at:
            self.added_at = datetime.utcnow().isoformat()


@dataclass
class AlertResult:
    """Result of checking alerts for one stock."""

    ticker: str
    triggered_alerts: list[str]  # descriptions of triggered alerts
    current_values: dict[str, float]  # actual metric values
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class Watchlist:
    """Persistent watchlist with alert conditions.

    Stores watchlist as JSON files in the cache directory.
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self.items: dict[str, WatchlistItem] = {}
        self._storage_dir = settings.cache_dir / "watchlists"

    @property
    def tickers(self) -> list[str]:
        """All tickers in the watchlist."""
        return list(self.items.keys())

    def __len__(self) -> int:
        return len(self.items)

    def __contains__(self, ticker: str) -> bool:
        return ticker.upper() in self.items

    # --- CRUD ---

    def add(
        self,
        ticker: str,
        notes: str = "",
        tags: Optional[list[str]] = None,
        alerts: Optional[list[AlertCondition]] = None,
        target_buy: Optional[float] = None,
        target_sell: Optional[float] = None,
        stop_loss: Optional[float] = None,
    ) -> WatchlistItem:
        """Add a ticker to the watchlist."""
        key = ticker.upper()
        item = WatchlistItem(
            ticker=key,
            notes=notes,
            tags=tags or [],
            alerts=alerts or [],
            target_buy=target_buy,
            target_sell=target_sell,
            stop_loss=stop_loss,
        )
        self.items[key] = item
        return item

    def remove(self, ticker: str) -> bool:
        """Remove a ticker. Returns True if it was present."""
        key = ticker.upper()
        if key in self.items:
            del self.items[key]
            return True
        return False

    def get(self, ticker: str) -> Optional[WatchlistItem]:
        """Get item by ticker."""
        return self.items.get(ticker.upper())

    def update_notes(self, ticker: str, notes: str) -> None:
        """Update notes for a ticker."""
        key = ticker.upper()
        if key in self.items:
            self.items[key].notes = notes

    def add_alert(self, ticker: str, alert: AlertCondition) -> None:
        """Add an alert condition to a ticker."""
        key = ticker.upper()
        if key in self.items:
            self.items[key].alerts.append(alert)

    def clear_alerts(self, ticker: str) -> None:
        """Remove all alerts for a ticker."""
        key = ticker.upper()
        if key in self.items:
            self.items[key].alerts = []

    def filter_by_tag(self, tag: str) -> list[WatchlistItem]:
        """Get all items with a specific tag."""
        return [item for item in self.items.values() if tag in item.tags]

    # --- Alert checking ---

    def check_alerts(self, source: Optional[DataSource] = None) -> list[AlertResult]:
        """Check all alert conditions against live data.

        Returns a list of AlertResult for stocks with triggered alerts.
        """
        src = source or get_source()
        results: list[AlertResult] = []

        for ticker, item in self.items.items():
            if not item.alerts and item.target_buy is None and item.target_sell is None and item.stop_loss is None:
                continue

            try:
                quote = src.get_quote(ticker)
            except Exception:
                continue

            # Build metric values
            values: dict[str, float] = {
                "last": float(quote.last),
                "volume": float(quote.volume or 0),
            }
            if quote.change_pct is not None:
                values["change_pct"] = quote.change_pct
            if quote.prev_close:
                values["prev_close"] = float(quote.prev_close)

            # Check custom alerts
            triggered: list[str] = []
            for alert in item.alerts:
                actual = values.get(alert.field)
                if actual is not None and alert.evaluate(actual):
                    triggered.append(alert.describe())

            # Check target/stop levels
            last = float(quote.last)
            if item.target_buy and last <= item.target_buy:
                triggered.append(f"Price Rp {last:,.0f} hit buy target Rp {item.target_buy:,.0f}")
            if item.target_sell and last >= item.target_sell:
                triggered.append(f"Price Rp {last:,.0f} hit sell target Rp {item.target_sell:,.0f}")
            if item.stop_loss and last <= item.stop_loss:
                triggered.append(f"STOP LOSS: Rp {last:,.0f} <= Rp {item.stop_loss:,.0f}")

            if triggered:
                results.append(AlertResult(
                    ticker=ticker,
                    triggered_alerts=triggered,
                    current_values=values,
                ))

        return results

    # --- Persistence ---

    def save(self, name: Optional[str] = None) -> Path:
        """Save watchlist to JSON file."""
        wl_name = name or self.name
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        filepath = self._storage_dir / f"{wl_name}.json"

        data = {
            "name": wl_name,
            "updated_at": datetime.utcnow().isoformat(),
            "items": {
                ticker: _item_to_dict(item)
                for ticker, item in self.items.items()
            },
        }
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return filepath

    @classmethod
    def load(cls, name: str = "default") -> "Watchlist":
        """Load watchlist from JSON file. Returns empty if not found."""
        wl = cls(name=name)
        filepath = wl._storage_dir / f"{name}.json"

        if not filepath.exists():
            return wl

        try:
            data = json.loads(filepath.read_text())
            for ticker, item_data in data.get("items", {}).items():
                alerts = [
                    AlertCondition(**a) for a in item_data.get("alerts", [])
                ]
                wl.items[ticker] = WatchlistItem(
                    ticker=ticker,
                    added_at=item_data.get("added_at", ""),
                    notes=item_data.get("notes", ""),
                    tags=item_data.get("tags", []),
                    alerts=alerts,
                    target_buy=item_data.get("target_buy"),
                    target_sell=item_data.get("target_sell"),
                    stop_loss=item_data.get("stop_loss"),
                )
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # Return empty watchlist on parse error

        return wl

    @classmethod
    def list_saved(cls) -> list[str]:
        """List all saved watchlist names."""
        storage = settings.cache_dir / "watchlists"
        if not storage.exists():
            return []
        return [f.stem for f in storage.glob("*.json")]


def _item_to_dict(item: WatchlistItem) -> dict[str, Any]:
    """Convert WatchlistItem to serializable dict."""
    return {
        "ticker": item.ticker,
        "added_at": item.added_at,
        "notes": item.notes,
        "tags": item.tags,
        "alerts": [asdict(a) for a in item.alerts],
        "target_buy": item.target_buy,
        "target_sell": item.target_sell,
        "stop_loss": item.stop_loss,
    }
