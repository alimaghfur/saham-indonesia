"""Tests for signal generator module."""
from saham_id.signals import (
    Action, Condition, Signal, SignalEngine,
    swing_buy_engine, swing_sell_engine, scalping_engine,
)


class TestCondition:
    def test_describe_default(self):
        c = Condition(indicator="rsi", op="<", threshold=30, weight=2.0)
        assert "rsi" in c.describe()
        assert "<" in c.describe()

    def test_describe_custom(self):
        c = Condition(indicator="rsi", op="<", threshold=30, description="RSI oversold")
        assert c.describe() == "RSI oversold"


class TestSignal:
    def test_bullish(self):
        s = Signal(ticker="BBCA", action=Action.BUY, confidence=0.8, score=0.6)
        assert s.is_bullish is True
        assert s.is_bearish is False

    def test_bearish(self):
        s = Signal(ticker="BBCA", action=Action.SELL, confidence=0.7, score=-0.5)
        assert s.is_bearish is True
        assert s.is_bullish is False

    def test_hold(self):
        s = Signal(ticker="BBCA", action=Action.HOLD, confidence=0.5, score=0.0)
        assert s.is_bullish is False
        assert s.is_bearish is False


class TestSignalEngine:
    def test_empty_engine(self):
        import pandas as pd
        engine = SignalEngine()
        df = pd.DataFrame({
            "open": [100]*30, "high": [105]*30, "low": [95]*30,
            "close": [102]*30, "volume": [1000000]*30,
        })
        signal = engine.evaluate(df, ticker="TEST")
        assert signal.action == Action.HOLD

    def test_check_condition_less_than(self):
        engine = SignalEngine()
        assert engine._check_condition(25.0, "<", 30.0) is True
        assert engine._check_condition(35.0, "<", 30.0) is False

    def test_check_condition_greater_than(self):
        engine = SignalEngine()
        assert engine._check_condition(75.0, ">", 70.0) is True
        assert engine._check_condition(65.0, ">", 70.0) is False

    def test_add_and_clear(self):
        engine = SignalEngine()
        engine.add_condition(Condition("rsi", "<", 30))
        engine.add_condition(Condition("macd_bullish", "==", 1.0))
        assert len(engine.conditions) == 2
        engine.clear_conditions()
        assert len(engine.conditions) == 0


class TestPrebuiltEngines:
    def test_swing_buy_engine(self):
        engine = swing_buy_engine()
        assert len(engine.conditions) >= 4
        # All conditions should be bullish
        for c in engine.conditions:
            assert c.direction == "bullish"

    def test_swing_sell_engine(self):
        engine = swing_sell_engine()
        assert len(engine.conditions) >= 4
        for c in engine.conditions:
            assert c.direction == "bearish"

    def test_scalping_engine(self):
        engine = scalping_engine()
        assert len(engine.conditions) >= 3
