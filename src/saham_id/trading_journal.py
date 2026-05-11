"""Trading Journal — catat alasan trading + lesson learned.

Record setiap trade dengan konteks: alasan masuk, target, hasil, dan pelajaran.

Usage:
    from saham_id.trading_journal import TradingJournal, JournalEntry

    journal = TradingJournal("2025")
    journal.add_entry(JournalEntry(
        ticker="BBCA", side="buy", price=9500, lots=10,
        reason="RSI oversold + bandar akumulasi",
        target_price=10500, stop_loss=9000,
    ))
    journal.close_trade("BBCA", exit_price=10200, lesson="Hold longer next time")
    journal.save()
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional
from saham_id.config import settings


@dataclass
class JournalEntry:
    ticker: str
    side: Literal["buy", "sell"]
    price: float
    lots: int = 0
    reason: str = ""
    strategy: str = ""
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    tags: list[str] = field(default_factory=list)
    screenshot_path: str = ""
    entry_time: str = ""
    exit_price: Optional[float] = None
    exit_time: str = ""
    pnl: float = 0.0
    pnl_pct: float = 0.0
    lesson: str = ""
    rating: int = 0  # 1-5 self-rating
    status: str = "open"  # open, closed, cancelled
    notes: str = ""

    def __post_init__(self):
        if not self.entry_time:
            self.entry_time = datetime.utcnow().isoformat()

    @property
    def is_winner(self) -> Optional[bool]:
        if self.status != "closed":
            return None
        return self.pnl > 0

    def close(self, exit_price: float, lesson: str = "", rating: int = 0) -> None:
        self.exit_price = exit_price
        self.exit_time = datetime.utcnow().isoformat()
        self.status = "closed"
        shares = self.lots * 100
        if self.side == "buy":
            self.pnl = (exit_price - self.price) * shares
            self.pnl_pct = (exit_price - self.price) / self.price if self.price > 0 else 0
        else:
            self.pnl = (self.price - exit_price) * shares
            self.pnl_pct = (self.price - exit_price) / self.price if self.price > 0 else 0
        self.lesson = lesson
        if rating:
            self.rating = rating


class TradingJournal:
    def __init__(self, name: str = "default"):
        self.name = name
        self.entries: list[JournalEntry] = []
        self._storage_dir = settings.cache_dir / "journals"

    def add_entry(self, entry: JournalEntry) -> None:
        self.entries.append(entry)

    def close_trade(self, ticker: str, exit_price: float, lesson: str = "", rating: int = 0) -> Optional[JournalEntry]:
        for entry in reversed(self.entries):
            if entry.ticker.upper() == ticker.upper() and entry.status == "open":
                entry.close(exit_price, lesson, rating)
                return entry
        return None

    def open_trades(self) -> list[JournalEntry]:
        return [e for e in self.entries if e.status == "open"]

    def closed_trades(self) -> list[JournalEntry]:
        return [e for e in self.entries if e.status == "closed"]

    def winners(self) -> list[JournalEntry]:
        return [e for e in self.closed_trades() if e.is_winner]

    def losers(self) -> list[JournalEntry]:
        return [e for e in self.closed_trades() if e.is_winner is False]

    def stats(self) -> dict:
        closed = self.closed_trades()
        wins = self.winners()
        losses = self.losers()
        total_pnl = sum(e.pnl for e in closed)
        return {
            "total_entries": len(self.entries),
            "open": len(self.open_trades()),
            "closed": len(closed),
            "winners": len(wins),
            "losers": len(losses),
            "win_rate": len(wins) / max(len(closed), 1),
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / max(len(closed), 1),
            "avg_winner": sum(e.pnl for e in wins) / max(len(wins), 1),
            "avg_loser": sum(e.pnl for e in losses) / max(len(losses), 1),
            "best_trade": max((e.pnl for e in closed), default=0),
            "worst_trade": min((e.pnl for e in closed), default=0),
            "avg_rating": sum(e.rating for e in closed if e.rating) / max(sum(1 for e in closed if e.rating), 1),
        }

    def lessons(self) -> list[str]:
        return [e.lesson for e in self.entries if e.lesson]

    def by_strategy(self) -> dict[str, list[JournalEntry]]:
        result: dict[str, list[JournalEntry]] = {}
        for e in self.entries:
            result.setdefault(e.strategy or "untagged", []).append(e)
        return result

    def save(self) -> Path:
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        filepath = self._storage_dir / f"{self.name}.json"
        data = {"name": self.name, "saved_at": datetime.utcnow().isoformat(),
                "entries": [vars(e) for e in self.entries]}
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        return filepath

    @classmethod
    def load(cls, name: str = "default") -> "TradingJournal":
        journal = cls(name=name)
        filepath = journal._storage_dir / f"{name}.json"
        if not filepath.exists():
            return journal
        try:
            data = json.loads(filepath.read_text())
            for e_data in data.get("entries", []):
                journal.entries.append(JournalEntry(**{k: v for k, v in e_data.items() if k != "is_winner"}))
        except (json.JSONDecodeError, TypeError):
            pass
        return journal
