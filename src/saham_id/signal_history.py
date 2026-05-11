"""Signal history — record and track accuracy of generated signals.

Saves signals with timestamps, then allows follow-up analysis:
"If I followed this signal, what happened N days later?"

Usage:
    from saham_id.signal_history import SignalHistoryTracker

    tracker = SignalHistoryTracker()
    tracker.record_signal(signal)
    tracker.record_signals(signal_list)

    accuracy = tracker.evaluate_accuracy(days_after=5, source=src)
    print(accuracy.win_rate)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from saham_id.config import settings
from saham_id.signals import Signal, Action


@dataclass
class RecordedSignal:
    """A signal saved with context for future evaluation."""

    ticker: str
    action: str
    confidence: float
    score: float
    price_at_signal: float
    reasons: list[str]
    timestamp: str
    engine: str = ""
    evaluated: bool = False
    price_after_5d: Optional[float] = None
    return_5d: Optional[float] = None

    @property
    def was_correct(self) -> Optional[bool]:
        if self.return_5d is None:
            return None
        if self.action == "BUY":
            return self.return_5d > 0
        elif self.action == "SELL":
            return self.return_5d < 0
        return None


@dataclass
class AccuracyReport:
    """Accuracy evaluation of historical signals."""

    total_signals: int
    evaluated_signals: int
    correct_signals: int
    win_rate: float
    avg_return_5d: float
    avg_return_10d: float = 0.0
    best_signal: Optional[RecordedSignal] = None
    worst_signal: Optional[RecordedSignal] = None
    by_confidence: dict[str, float] = field(default_factory=dict)


class SignalHistoryTracker:
    """Track signal history for accuracy evaluation."""

    def __init__(self, name: str = "default"):
        self.name = name
        self.signals: list[RecordedSignal] = []
        self._storage_dir = settings.cache_dir / "signal_history"

    def record_signal(self, signal: Signal, price: float = 0.0, engine: str = "") -> RecordedSignal:
        """Record a single signal."""
        price_at = price or signal.indicators.get("close", 0.0)
        recorded = RecordedSignal(
            ticker=signal.ticker, action=signal.action.value,
            confidence=signal.confidence, score=signal.score,
            price_at_signal=price_at, reasons=signal.reasons[:5],
            timestamp=datetime.utcnow().isoformat(), engine=engine,
        )
        self.signals.append(recorded)
        return recorded

    def record_signals(self, signals: list[Signal], engine: str = "") -> int:
        """Record multiple signals. Skips HOLD. Returns count."""
        count = 0
        for sig in signals:
            if sig.action != Action.HOLD:
                self.record_signal(sig, engine=engine)
                count += 1
        return count

    def evaluate_accuracy(self, source=None) -> AccuracyReport:
        """Evaluate signal accuracy."""
        evaluated = sum(1 for s in self.signals if s.evaluated)
        correct = sum(1 for s in self.signals if s.was_correct)
        returns = [s.return_5d for s in self.signals if s.return_5d is not None]
        avg_ret = sum(returns) / len(returns) if returns else 0.0

        evaluated_sigs = [s for s in self.signals if s.evaluated and s.return_5d is not None]
        best = max(evaluated_sigs, key=lambda s: s.return_5d or 0) if evaluated_sigs else None
        worst = min(evaluated_sigs, key=lambda s: s.return_5d or 0) if evaluated_sigs else None

        return AccuracyReport(
            total_signals=len(self.signals), evaluated_signals=evaluated,
            correct_signals=correct, win_rate=correct / max(evaluated, 1),
            avg_return_5d=avg_ret, best_signal=best, worst_signal=worst,
        )

    def stats(self) -> dict:
        """Quick stats."""
        buy_count = sum(1 for s in self.signals if s.action == "BUY")
        sell_count = sum(1 for s in self.signals if s.action == "SELL")
        evaluated_count = sum(1 for s in self.signals if s.evaluated)
        correct_count = sum(1 for s in self.signals if s.was_correct)
        unique_tickers = len(set(s.ticker for s in self.signals))
        return {
            "total_signals": len(self.signals), "buy_signals": buy_count,
            "sell_signals": sell_count, "evaluated": evaluated_count,
            "correct": correct_count, "win_rate": correct_count / max(evaluated_count, 1),
            "unique_tickers": unique_tickers,
        }

    def save(self) -> Path:
        """Save to JSON."""
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        filepath = self._storage_dir / f"{self.name}.json"
        data = {"name": self.name, "saved_at": datetime.utcnow().isoformat(),
                "signals": [{"ticker": s.ticker, "action": s.action, "confidence": s.confidence,
                            "score": s.score, "price_at_signal": s.price_at_signal,
                            "reasons": s.reasons, "timestamp": s.timestamp, "engine": s.engine,
                            "evaluated": s.evaluated, "return_5d": s.return_5d} for s in self.signals]}
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return filepath

    @classmethod
    def load(cls, name: str = "default") -> "SignalHistoryTracker":
        """Load from JSON."""
        tracker = cls(name=name)
        filepath = tracker._storage_dir / f"{name}.json"
        if not filepath.exists():
            return tracker
        try:
            data = json.loads(filepath.read_text())
            for s in data.get("signals", []):
                tracker.signals.append(RecordedSignal(
                    ticker=s["ticker"], action=s["action"], confidence=s["confidence"],
                    score=s["score"], price_at_signal=s["price_at_signal"],
                    reasons=s.get("reasons", []), timestamp=s["timestamp"],
                    engine=s.get("engine", ""), evaluated=s.get("evaluated", False),
                    return_5d=s.get("return_5d"),
                ))
        except (json.JSONDecodeError, KeyError):
            pass
        return tracker
