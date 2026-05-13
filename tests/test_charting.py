"""Tests for the charting module (saham_id.charting).

Smoke tests that verify chart functions produce valid Figure objects
without errors. Uses plotly stub so does not require real plotly.

Tests:
- candlestick_chart with various options
- ohlc_chart
- indicator_chart (all supported types)
- multi_indicator_chart
- equity_curve
- drawdown_chart
- allocation_pie
- portfolio_dashboard
- apply_theme
- styles constants
"""
import pandas as pd

from saham_id.charting.styles import (
    COLORS,
    LINE_COLORS,
    IDX_THEME,
    apply_theme,
    register_idx_template,
)
from saham_id.charting.candlestick import candlestick_chart, ohlc_chart
from saham_id.charting.indicators import (
    indicator_chart,
    multi_indicator_chart,
    _compute_rsi,
    _compute_macd,
    _compute_bollinger,
    _compute_stochastic,
    _compute_atr,
)
from saham_id.charting.portfolio import (
    equity_curve,
    drawdown_chart,
    allocation_pie,
    portfolio_dashboard,
)


def _sample_ohlcv(n=50):
    """Generate sample OHLCV DataFrame."""
    import math
    close_data = [10000 + 500 * math.sin(i * 0.3) + i * 50 for i in range(n)]
    open_data = [c - 50 + (i % 3) * 30 for i, c in enumerate(close_data)]
    high_data = [max(o, c) + 100 for o, c in zip(open_data, close_data)]
    low_data = [min(o, c) - 80 for o, c in zip(open_data, close_data)]
    volume_data = [5_000_000 + i * 100_000 for i in range(n)]
    index = list(range(n))

    df = pd.DataFrame({
        "open": open_data,
        "high": high_data,
        "low": low_data,
        "close": close_data,
        "volume": volume_data,
    }, index=index)
    return df


def _sample_returns(n=100):
    """Generate sample daily returns Series."""
    import math
    data = [0.01 * math.sin(i * 0.1) + 0.001 for i in range(n)]
    return pd.Series(data, index=list(range(n)))


# ======================================================================
# Styles
# ======================================================================

class TestStyles:
    def test_colors_has_required_keys(self):
        required = ["green", "red", "blue", "orange", "grey", "dark_bg", "light_bg"]
        for key in required:
            assert key in COLORS

    def test_line_colors_is_list(self):
        assert isinstance(LINE_COLORS, list)
        assert len(LINE_COLORS) >= 5

    def test_idx_theme_has_layout(self):
        assert "layout" in IDX_THEME
        assert "paper_bgcolor" in IDX_THEME["layout"]

    def test_apply_theme_dark(self):
        from plotly.graph_objects import Figure
        fig = Figure()
        result = apply_theme(fig, dark=True)
        assert result is fig  # Modified in-place

    def test_apply_theme_light(self):
        from plotly.graph_objects import Figure
        fig = Figure()
        result = apply_theme(fig, dark=False)
        assert result is fig

    def test_register_idx_template(self):
        # Should not raise
        register_idx_template()


# ======================================================================
# Candlestick charts
# ======================================================================

class TestCandlestickChart:
    def test_basic(self):
        df = _sample_ohlcv()
        fig = candlestick_chart(df, ticker="BBCA")
        assert fig is not None

    def test_with_ma(self):
        df = _sample_ohlcv()
        fig = candlestick_chart(df, ticker="BBCA", ma_periods=[20, 50])
        assert fig is not None

    def test_without_volume(self):
        df = _sample_ohlcv()
        fig = candlestick_chart(df, ticker="BBCA", show_volume=False)
        assert fig is not None

    def test_with_support_resistance(self):
        df = _sample_ohlcv()
        fig = candlestick_chart(
            df, ticker="BBCA",
            support_levels=[9500, 9000],
            resistance_levels=[10500, 11000],
        )
        assert fig is not None

    def test_light_mode(self):
        df = _sample_ohlcv()
        fig = candlestick_chart(df, dark=False)
        assert fig is not None

    def test_custom_height(self):
        df = _sample_ohlcv()
        fig = candlestick_chart(df, height=800)
        assert fig is not None

    def test_custom_title(self):
        df = _sample_ohlcv()
        fig = candlestick_chart(df, title="My Chart")
        assert fig is not None


class TestOHLCChart:
    def test_basic(self):
        df = _sample_ohlcv()
        fig = ohlc_chart(df, ticker="BBRI")
        assert fig is not None

    def test_without_volume(self):
        df = _sample_ohlcv()
        fig = ohlc_chart(df, show_volume=False)
        assert fig is not None

    def test_light_mode(self):
        df = _sample_ohlcv()
        fig = ohlc_chart(df, dark=False)
        assert fig is not None


# ======================================================================
# Indicator computation helpers
# ======================================================================

class TestIndicatorComputation:
    def test_compute_rsi(self):
        df = _sample_ohlcv(50)
        rsi = _compute_rsi(df["close"], period=14)
        assert len(rsi) == 50
        # RSI should be between 0 and 100 for valid values
        valid = [v for v in rsi._data if v is not None and v == v]  # filter NaN
        for v in valid:
            assert 0 <= v <= 100

    def test_compute_macd(self):
        df = _sample_ohlcv(50)
        macd_line, signal, hist = _compute_macd(df["close"])
        assert len(macd_line) == 50
        assert len(signal) == 50
        assert len(hist) == 50

    def test_compute_bollinger(self):
        df = _sample_ohlcv(50)
        upper, sma, lower = _compute_bollinger(df["close"], period=20)
        assert len(upper) == 50
        # Upper > SMA > Lower for valid values
        for u, m, l in zip(upper._data, sma._data, lower._data):
            if u is not None and m is not None and l is not None:
                if u == u and m == m and l == l:  # skip NaN
                    assert u >= m >= l

    def test_compute_stochastic(self):
        df = _sample_ohlcv(50)
        k, d = _compute_stochastic(df, period=14)
        assert len(k) == 50
        assert len(d) == 50

    def test_compute_atr(self):
        df = _sample_ohlcv(50)
        result = _compute_atr(df, period=14)
        assert len(result) == 50
        # ATR should be non-negative
        valid = [v for v in result._data if v is not None and v == v]
        for v in valid:
            assert v >= 0


# ======================================================================
# Indicator charts
# ======================================================================

class TestIndicatorChart:
    def test_rsi_chart(self):
        df = _sample_ohlcv()
        fig = indicator_chart(df, indicator="rsi", ticker="BBCA")
        assert fig is not None

    def test_macd_chart(self):
        df = _sample_ohlcv()
        fig = indicator_chart(df, indicator="macd", ticker="BBCA")
        assert fig is not None

    def test_bollinger_chart(self):
        df = _sample_ohlcv()
        fig = indicator_chart(df, indicator="bollinger", ticker="BBCA")
        assert fig is not None

    def test_stochastic_chart(self):
        df = _sample_ohlcv()
        fig = indicator_chart(df, indicator="stochastic", ticker="BBCA")
        assert fig is not None

    def test_atr_chart(self):
        df = _sample_ohlcv()
        fig = indicator_chart(df, indicator="atr", ticker="BBCA")
        assert fig is not None

    def test_generic_indicator(self):
        df = _sample_ohlcv()
        fig = indicator_chart(df, indicator="custom_col", ticker="TEST")
        assert fig is not None

    def test_light_mode(self):
        df = _sample_ohlcv()
        fig = indicator_chart(df, indicator="rsi", dark=False)
        assert fig is not None


class TestMultiIndicatorChart:
    def test_basic(self):
        df = _sample_ohlcv()
        fig = multi_indicator_chart(df, indicators=["rsi", "macd"], ticker="BBCA")
        assert fig is not None

    def test_single_indicator(self):
        df = _sample_ohlcv()
        fig = multi_indicator_chart(df, indicators=["rsi"])
        assert fig is not None

    def test_with_volume(self):
        df = _sample_ohlcv()
        fig = multi_indicator_chart(df, indicators=["rsi", "volume"], ticker="BBRI")
        assert fig is not None

    def test_all_indicators(self):
        df = _sample_ohlcv()
        fig = multi_indicator_chart(
            df, indicators=["rsi", "macd", "volume", "atr"], ticker="TLKM"
        )
        assert fig is not None


# ======================================================================
# Portfolio charts
# ======================================================================

class TestEquityCurve:
    def test_basic(self):
        returns = _sample_returns()
        fig = equity_curve(returns, title="Test Equity")
        assert fig is not None

    def test_with_benchmark(self):
        returns = _sample_returns()
        bench = _sample_returns(100)
        fig = equity_curve(returns, benchmark=bench)
        assert fig is not None

    def test_custom_capital(self):
        returns = _sample_returns()
        fig = equity_curve(returns, initial_capital=50_000_000)
        assert fig is not None


class TestDrawdownChart:
    def test_basic(self):
        returns = _sample_returns()
        fig = drawdown_chart(returns)
        assert fig is not None

    def test_light_mode(self):
        returns = _sample_returns()
        fig = drawdown_chart(returns, dark=False)
        assert fig is not None


class TestAllocationPie:
    def test_basic(self):
        holdings = {"BBCA": 30_000_000, "BBRI": 20_000_000, "TLKM": 10_000_000}
        fig = allocation_pie(holdings)
        assert fig is not None

    def test_single_holding(self):
        holdings = {"BBCA": 50_000_000}
        fig = allocation_pie(holdings)
        assert fig is not None


class TestPortfolioDashboard:
    def test_basic(self):
        returns = _sample_returns()
        holdings = {"BBCA": 30_000_000, "BBRI": 20_000_000}
        fig = portfolio_dashboard(returns, holdings)
        assert fig is not None

    def test_with_benchmark(self):
        returns = _sample_returns()
        bench = _sample_returns()
        holdings = {"BBCA": 30_000_000}
        fig = portfolio_dashboard(returns, holdings, benchmark=bench)
        assert fig is not None
