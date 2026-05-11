"""Tests for Ichimoku screener."""
from saham_id.screener.ichimoku_screener import screen_ichimoku


class TestIchimokuScreener:
    def test_imports(self):
        assert callable(screen_ichimoku)

    def test_parameters(self):
        import inspect
        sig = inspect.signature(screen_ichimoku)
        params = list(sig.parameters.keys())
        assert "universe" in params
        assert "require_above_cloud" in params
        assert "require_tk_bullish" in params
        assert "require_green_cloud" in params
        assert "top_n" in params
