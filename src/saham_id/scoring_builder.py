"""Scoring model builder — create custom scoring formulas via config.

Build screeners without writing code. Define scoring rules in a simple
dict/YAML format and the builder compiles them into executable screeners.

Usage:
    from saham_id.scoring_builder import ScoringModel, ScoringRule

    model = ScoringModel(name="my_screener")
    model.add_rule(ScoringRule(indicator="rsi", condition="<", value=30, points=20))
    model.add_rule(ScoringRule(indicator="macd_bullish", condition="==", value=True, points=15))
    model.add_rule(ScoringRule(indicator="close_above_sma50", condition="==", value=True, points=10))

    result = model.run(universe="LQ45", source=src)
    print(result.to_dataframe())
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from saham_id.config import settings
from saham_id.data.sources import get_source
from saham_id.data.sources.base import DataSource
from saham_id.data.universe import get_universe
from saham_id.screener.engine import ScreenResult, ScreenRow
from saham_id.signals import _extract_indicators


@dataclass
class ScoringRule:
    """A single rule in a scoring model."""

    indicator: str  # from _extract_indicators keys
    condition: str  # "<", "<=", ">", ">=", "==", "!="
    value: float | bool  # threshold
    points: float = 10.0  # points awarded if condition met
    description: str = ""

    def evaluate(self, indicators: dict[str, float]) -> float:
        """Return points if condition met, else 0."""
        actual = indicators.get(self.indicator)
        if actual is None:
            return 0.0

        threshold = float(self.value) if isinstance(self.value, bool) else self.value
        ops = {
            "<": lambda a, b: a < b,
            "<=": lambda a, b: a <= b,
            ">": lambda a, b: a > b,
            ">=": lambda a, b: a >= b,
            "==": lambda a, b: abs(a - b) < 0.001,
            "!=": lambda a, b: abs(a - b) >= 0.001,
        }
        fn = ops.get(self.condition)
        if fn and fn(actual, threshold):
            return self.points
        return 0.0

    def describe(self) -> str:
        if self.description:
            return self.description
        return f"{self.indicator} {self.condition} {self.value} (+{self.points}pts)"


@dataclass
class ScoringModel:
    """Custom scoring model — configurable screener without code.

    Define rules, set thresholds, and run against any universe.
    Models can be saved/loaded as JSON for sharing.
    """

    name: str = "custom"
    rules: list[ScoringRule] = field(default_factory=list)
    min_score: float = 50.0
    max_results: int = 20
    description: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()

    def add_rule(self, rule: ScoringRule) -> None:
        """Add a scoring rule."""
        self.rules.append(rule)

    def remove_rule(self, index: int) -> None:
        """Remove rule by index."""
        if 0 <= index < len(self.rules):
            self.rules.pop(index)

    @property
    def max_possible_score(self) -> float:
        """Maximum achievable score if all rules trigger."""
        return sum(r.points for r in self.rules)

    def run(
        self,
        universe: str | list[str] = "LQ45",
        source: Optional[DataSource] = None,
    ) -> ScreenResult:
        """Execute the scoring model against a stock universe.

        For each stock:
            1. Fetch OHLCV data
            2. Compute all indicators
            3. Evaluate each rule
            4. Sum points -> composite score
        """
        src = source or get_source()
        tickers = list(universe) if isinstance(universe, list) else get_universe(universe)
        universe_name = universe if isinstance(universe, str) else "custom"

        rows: list[ScreenRow] = []
        for ticker in tickers:
            try:
                df = src.get_ohlc(ticker, period="6mo", interval="1d")
                if df.empty or len(df) < 30:
                    continue

                indicators = _extract_indicators(df)
                if not indicators:
                    continue

                # Score each rule
                total_score = 0.0
                triggered_rules: list[str] = []
                for rule in self.rules:
                    pts = rule.evaluate(indicators)
                    if pts > 0:
                        total_score += pts
                        triggered_rules.append(rule.describe())

                if total_score < self.min_score:
                    continue

                rows.append(ScreenRow(
                    ticker=ticker,
                    score=round(total_score, 2),
                    metrics={
                        "rules_triggered": len(triggered_rules),
                        "max_possible": self.max_possible_score,
                        "pct_score": round(total_score / max(self.max_possible_score, 1) * 100, 1),
                        "close": indicators.get("close", 0),
                        "rsi": round(indicators.get("rsi", 0), 1),
                        "rvol": round(indicators.get("rvol", 0), 2),
                    },
                ))
            except Exception:
                continue

        rows.sort(key=lambda r: r.score, reverse=True)
        return ScreenResult(
            strategy=f"custom:{self.name}",
            universe=universe_name,
            as_of=datetime.utcnow(),
            rows=rows[:self.max_results],
            params={"model_name": self.name, "min_score": self.min_score, "num_rules": len(self.rules)},
        )

    def save(self, name: Optional[str] = None) -> Path:
        """Save model to JSON file."""
        model_name = name or self.name
        storage = settings.cache_dir / "scoring_models"
        storage.mkdir(parents=True, exist_ok=True)
        filepath = storage / f"{model_name}.json"

        data = {
            "name": model_name,
            "description": self.description,
            "created_at": self.created_at,
            "min_score": self.min_score,
            "max_results": self.max_results,
            "rules": [
                {
                    "indicator": r.indicator,
                    "condition": r.condition,
                    "value": r.value,
                    "points": r.points,
                    "description": r.description,
                }
                for r in self.rules
            ],
        }
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return filepath

    @classmethod
    def load(cls, name: str) -> "ScoringModel":
        """Load model from JSON file."""
        storage = settings.cache_dir / "scoring_models"
        filepath = storage / f"{name}.json"

        if not filepath.exists():
            return cls(name=name)

        try:
            data = json.loads(filepath.read_text())
            model = cls(
                name=data.get("name", name),
                description=data.get("description", ""),
                min_score=data.get("min_score", 50.0),
                max_results=data.get("max_results", 20),
                created_at=data.get("created_at", ""),
            )
            for r in data.get("rules", []):
                model.add_rule(ScoringRule(
                    indicator=r["indicator"],
                    condition=r["condition"],
                    value=r["value"],
                    points=r.get("points", 10),
                    description=r.get("description", ""),
                ))
            return model
        except (json.JSONDecodeError, KeyError):
            return cls(name=name)

    @classmethod
    def list_models(cls) -> list[str]:
        """List saved model names."""
        storage = settings.cache_dir / "scoring_models"
        if not storage.exists():
            return []
        return [f.stem for f in storage.glob("*.json")]


# --- Pre-built models ---


def oversold_bounce_model() -> ScoringModel:
    """Pre-built model: find oversold stocks ready to bounce."""
    model = ScoringModel(name="oversold_bounce", description="Oversold stocks with volume confirmation")
    model.add_rule(ScoringRule("rsi", "<", 30, points=25, description="RSI oversold (<30)"))
    model.add_rule(ScoringRule("bb_percent_b", "<", 0.1, points=20, description="Near lower BB"))
    model.add_rule(ScoringRule("rvol", ">", 1.5, points=15, description="Volume above average"))
    model.add_rule(ScoringRule("close_above_sma50", "==", 1.0, points=15, description="Still above SMA50"))
    model.add_rule(ScoringRule("macd_crossover_bull", "==", 1.0, points=25, description="MACD bullish cross"))
    model.min_score = 40
    return model


def momentum_model() -> ScoringModel:
    """Pre-built model: find stocks with strong momentum."""
    model = ScoringModel(name="momentum", description="Strong upward momentum with volume")
    model.add_rule(ScoringRule("close_above_sma20", "==", 1.0, points=15, description="Above SMA20"))
    model.add_rule(ScoringRule("sma20_above_sma50", "==", 1.0, points=15, description="SMA20 > SMA50"))
    model.add_rule(ScoringRule("rsi", ">", 50, points=10, description="RSI bullish (>50)"))
    model.add_rule(ScoringRule("rsi", "<", 70, points=10, description="RSI not overbought (<70)"))
    model.add_rule(ScoringRule("macd_bullish", "==", 1.0, points=15, description="MACD above signal"))
    model.add_rule(ScoringRule("rvol", ">", 1.2, points=10, description="Increasing volume"))
    model.add_rule(ScoringRule("momentum_5d", ">", 0.01, points=15, description="Positive 5-day momentum"))
    model.min_score = 50
    return model


def value_dip_model() -> ScoringModel:
    """Pre-built model: quality stocks on a pullback."""
    model = ScoringModel(name="value_dip", description="Fundamentally strong stocks in a pullback")
    model.add_rule(ScoringRule("rsi", "<", 40, points=20, description="RSI approaching oversold"))
    model.add_rule(ScoringRule("close_above_sma50", "==", 1.0, points=20, description="Still in uptrend"))
    model.add_rule(ScoringRule("bb_percent_b", "<", 0.3, points=15, description="Near lower Bollinger"))
    model.add_rule(ScoringRule("rvol", "<", 1.0, points=10, description="Low volume (no panic)"))
    model.add_rule(ScoringRule("macd_histogram", "<", 0, points=10, description="MACD weakening"))
    model.min_score = 40
    return model
