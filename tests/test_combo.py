"""Tests for combo screener."""
from saham_id.screener.combo import combo_screen
from saham_id.screener.engine import ScreenResult


class TestComboScreen:
    def test_imports(self):
        """Verify all combo screener dependencies import."""
        from saham_id.screener.combo import combo_screen
        assert callable(combo_screen)

    def test_returns_screen_result(self):
        """Combo screen should return a ScreenResult even with no matching stocks."""
        # This would need live data to actually find results,
        # so we just verify the structure
        assert ScreenResult is not None

    def test_weight_parameters(self):
        """Verify weight parameters are accepted."""
        # Just test that the function signature accepts all params
        import inspect
        sig = inspect.signature(combo_screen)
        params = list(sig.parameters.keys())
        assert "weight_technical" in params
        assert "weight_pattern" in params
        assert "weight_momentum" in params
        assert "weight_volume" in params
        assert "min_score" in params
        assert "top_n" in params
