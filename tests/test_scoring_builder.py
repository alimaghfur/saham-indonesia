"""Tests for scoring model builder."""
import tempfile
from pathlib import Path

from saham_id.scoring_builder import (
    ScoringModel, ScoringRule,
    oversold_bounce_model, momentum_model, value_dip_model,
)


class TestScoringRule:
    def test_evaluate_less_than(self):
        rule = ScoringRule(indicator="rsi", condition="<", value=30, points=20)
        assert rule.evaluate({"rsi": 25}) == 20
        assert rule.evaluate({"rsi": 35}) == 0

    def test_evaluate_greater_than(self):
        rule = ScoringRule(indicator="rvol", condition=">", value=1.5, points=15)
        assert rule.evaluate({"rvol": 2.0}) == 15
        assert rule.evaluate({"rvol": 1.0}) == 0

    def test_evaluate_equals(self):
        rule = ScoringRule(indicator="macd_bullish", condition="==", value=1.0, points=10)
        assert rule.evaluate({"macd_bullish": 1.0}) == 10
        assert rule.evaluate({"macd_bullish": 0.0}) == 0

    def test_evaluate_missing_indicator(self):
        rule = ScoringRule(indicator="nonexistent", condition="<", value=30, points=20)
        assert rule.evaluate({"rsi": 25}) == 0

    def test_describe(self):
        rule = ScoringRule(indicator="rsi", condition="<", value=30, points=20)
        desc = rule.describe()
        assert "rsi" in desc
        assert "<" in desc

    def test_custom_description(self):
        rule = ScoringRule(indicator="rsi", condition="<", value=30, points=20,
                          description="Oversold!")
        assert rule.describe() == "Oversold!"


class TestScoringModel:
    def test_create(self):
        model = ScoringModel(name="test")
        assert model.name == "test"
        assert len(model.rules) == 0

    def test_add_remove_rules(self):
        model = ScoringModel(name="test")
        model.add_rule(ScoringRule("rsi", "<", 30, 20))
        model.add_rule(ScoringRule("rvol", ">", 1.5, 15))
        assert len(model.rules) == 2

        model.remove_rule(0)
        assert len(model.rules) == 1
        assert model.rules[0].indicator == "rvol"

    def test_max_possible_score(self):
        model = ScoringModel(name="test")
        model.add_rule(ScoringRule("rsi", "<", 30, 20))
        model.add_rule(ScoringRule("rvol", ">", 1.5, 15))
        model.add_rule(ScoringRule("macd_bullish", "==", 1.0, 10))
        assert model.max_possible_score == 45

    def test_save_and_load(self):
        tmp = Path(tempfile.mkdtemp())

        model = ScoringModel(name="test_persist")
        model.add_rule(ScoringRule("rsi", "<", 30, 20, description="Oversold"))
        model.add_rule(ScoringRule("rvol", ">", 2.0, 15))

        # Override storage path
        import saham_id.config
        original_cache = saham_id.config.settings.cache_dir
        saham_id.config.settings.cache_dir = tmp

        try:
            model.save()
            filepath = tmp / "scoring_models" / "test_persist.json"
            assert filepath.exists()

            # Load back
            import json
            data = json.loads(filepath.read_text())
            assert data["name"] == "test_persist"
            assert len(data["rules"]) == 2
            assert data["rules"][0]["description"] == "Oversold"
        finally:
            saham_id.config.settings.cache_dir = original_cache


class TestPrebuiltModels:
    def test_oversold_bounce(self):
        model = oversold_bounce_model()
        assert model.name == "oversold_bounce"
        assert len(model.rules) >= 4
        assert model.min_score == 40

    def test_momentum(self):
        model = momentum_model()
        assert model.name == "momentum"
        assert len(model.rules) >= 5
        assert model.max_possible_score > 50

    def test_value_dip(self):
        model = value_dip_model()
        assert model.name == "value_dip"
        assert len(model.rules) >= 4
