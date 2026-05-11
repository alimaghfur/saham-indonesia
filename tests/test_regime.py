"""Tests for market regime detection."""
from saham_id.market.regime import (
    MarketRegime, RegimeState, REGIME_STRATEGIES,
)


class TestRegimeState:
    def test_all_states_have_strategies(self):
        for state in RegimeState:
            assert state in REGIME_STRATEGIES
            assert len(REGIME_STRATEGIES[state]) >= 2


class TestMarketRegime:
    def test_create(self):
        regime = MarketRegime(state=RegimeState.TRENDING_UP, confidence=0.8)
        assert regime.state == RegimeState.TRENDING_UP
        assert regime.confidence == 0.8
        assert regime.timestamp is not None

    def test_recommended_strategies(self):
        regime = MarketRegime(state=RegimeState.TRENDING_UP, confidence=0.8)
        strats = regime.recommended_strategies
        assert "swing_breakout" in strats
        assert "bpjs" in strats

    def test_position_size_multiplier(self):
        up = MarketRegime(state=RegimeState.TRENDING_UP, confidence=0.8)
        assert up.position_size_multiplier == 1.0

        down = MarketRegime(state=RegimeState.TRENDING_DOWN, confidence=0.7)
        assert down.position_size_multiplier == 0.5

        volatile = MarketRegime(state=RegimeState.HIGH_VOLATILITY, confidence=0.9)
        assert volatile.position_size_multiplier == 0.5

    def test_sideways(self):
        regime = MarketRegime(state=RegimeState.SIDEWAYS, confidence=0.6)
        assert "swing_pullback" in regime.recommended_strategies
        assert regime.position_size_multiplier == 0.75

    def test_low_volatility(self):
        regime = MarketRegime(state=RegimeState.LOW_VOLATILITY, confidence=0.5)
        assert "breakout_watch" in regime.recommended_strategies
