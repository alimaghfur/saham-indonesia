"""Tests for technical indicators."""
import pandas as pd

from saham_id.analysis.indicators import (
    atr,
    bollinger_bands,
    ema,
    macd,
    obv,
    rsi,
    rvol,
    sma,
    stoch,
    vwap,
    williams_r,
)


def _sample_data(n=30):
    """Generate sample price/volume data."""
    import math
    close_data = [100 + 10 * math.sin(i * 0.5) + i * 0.5 for i in range(n)]
    high_data = [c + 2 for c in close_data]
    low_data = [c - 1.5 for c in close_data]
    volume_data = [1_000_000 + i * 50_000 for i in range(n)]
    return (
        pd.Series(close_data),
        pd.Series(high_data),
        pd.Series(low_data),
        pd.Series(volume_data),
    )


class TestSMA:
    def test_sma_basic(self):
        close = pd.Series([10, 20, 30, 40, 50])
        result = sma(close, window=3)
        # Last value: avg(30,40,50) = 40
        assert abs(result.iloc[-1] - 40.0) < 0.01

    def test_sma_window_larger_than_data(self):
        close = pd.Series([10, 20, 30])
        result = sma(close, window=5)
        # Not enough data for window=5
        assert result.iloc[-1] is None or result.iloc[0] is None


class TestEMA:
    def test_ema_basic(self):
        close = pd.Series([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        result = ema(close, window=5)
        # EMA should lag less than SMA
        last_ema = result.iloc[-1]
        assert last_ema is not None
        assert last_ema > 50  # uptrend


class TestMACD:
    def test_macd_structure(self):
        close, _, _, _ = _sample_data(50)
        result = macd(close, fast=12, slow=26, signal=9)
        assert "macd" in result.columns
        assert "signal" in result.columns
        assert "histogram" in result.columns

    def test_macd_histogram_equals_diff(self):
        close, _, _, _ = _sample_data(50)
        result = macd(close, fast=5, slow=10, signal=3)
        last_hist = result["histogram"].iloc[-1]
        last_macd = result["macd"].iloc[-1]
        last_signal = result["signal"].iloc[-1]
        if last_hist is not None and last_macd is not None and last_signal is not None:
            assert abs(last_hist - (last_macd - last_signal)) < 0.001


class TestRSI:
    def test_rsi_range(self):
        # Mixed data so both gains and losses exist
        close = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107,
                          109, 111, 110, 112, 114, 113, 115, 117, 116, 118, 120])
        result = rsi(close, window=5)
        last_rsi = result.iloc[-1]
        if last_rsi is not None:
            assert 0 <= last_rsi <= 100

    def test_rsi_uptrend_high(self):
        # Mostly up with occasional small dips
        close = pd.Series([100, 103, 102, 105, 104, 108, 107, 111, 110, 114,
                          113, 117, 116, 120, 119, 123, 122, 126, 125, 129])
        result = rsi(close, window=5)
        last_rsi = result.iloc[-1]
        if last_rsi is not None:
            assert last_rsi > 50  # Should be bullish

    def test_rsi_downtrend_low(self):
        # Mostly down with occasional small rallies
        close = pd.Series([200, 197, 198, 195, 196, 192, 193, 189, 190, 186,
                          187, 183, 184, 180, 181, 177, 178, 174, 175, 171])
        result = rsi(close, window=5)
        last_rsi = result.iloc[-1]
        if last_rsi is not None:
            assert last_rsi < 50  # Should be bearish


class TestStoch:
    def test_stoch_structure(self):
        _, high, low, _ = _sample_data()
        close = pd.Series([h - 1 for h in high._data])
        result = stoch(high, low, close, k_window=5, d_window=3)
        assert "k" in result.columns
        assert "d" in result.columns

    def test_stoch_range(self):
        close = pd.Series([100 + i for i in range(20)])
        high = pd.Series([c + 2 for c in close._data])
        low = pd.Series([c - 2 for c in close._data])
        result = stoch(high, low, close, k_window=5, d_window=3)
        k_last = result["k"].iloc[-1]
        if k_last is not None:
            assert 0 <= k_last <= 100


class TestWilliamsR:
    def test_williams_range(self):
        close = pd.Series([100 + i for i in range(20)])
        high = pd.Series([c + 3 for c in close._data])
        low = pd.Series([c - 2 for c in close._data])
        result = williams_r(high, low, close, window=5)
        wr_last = result.iloc[-1]
        if wr_last is not None:
            assert -100 <= wr_last <= 0


class TestATR:
    def test_atr_positive(self):
        close, high, low, _ = _sample_data()
        result = atr(high, low, close, window=5)
        last_atr = result.iloc[-1]
        if last_atr is not None:
            assert last_atr > 0


class TestBollingerBands:
    def test_bb_structure(self):
        close, _, _, _ = _sample_data()
        result = bollinger_bands(close, window=10, num_std=2.0)
        assert "middle" in result.columns
        assert "upper" in result.columns
        assert "lower" in result.columns
        assert "bandwidth" in result.columns
        assert "percent_b" in result.columns

    def test_bb_ordering(self):
        close = pd.Series([100 + i for i in range(30)])
        result = bollinger_bands(close, window=5, num_std=2.0)
        mid = result["middle"].iloc[-1]
        upper = result["upper"].iloc[-1]
        lower = result["lower"].iloc[-1]
        if mid and upper and lower:
            assert upper > mid > lower


class TestOBV:
    def test_obv_uptrend(self):
        close = pd.Series([100, 102, 104, 106, 108])
        volume = pd.Series([1000, 2000, 1500, 3000, 2500])
        result = obv(close, volume)
        # All up moves, so OBV should be positive
        assert result.iloc[-1] > 0


class TestVWAP:
    def test_vwap_positive(self):
        close = pd.Series([100, 102, 104, 103, 105])
        high = pd.Series([103, 105, 106, 105, 108])
        low = pd.Series([99, 100, 102, 101, 103])
        volume = pd.Series([1000, 2000, 1500, 3000, 2500])
        result = vwap(high, low, close, volume)
        assert result.iloc[-1] > 0


class TestRVOL:
    def test_rvol_normal(self):
        volume = pd.Series([1000] * 25)
        result = rvol(volume, window=20)
        last = result.iloc[-1]
        if last is not None:
            assert abs(last - 1.0) < 0.01  # Constant volume => RVOL ≈ 1

    def test_rvol_spike(self):
        volume = pd.Series([1000] * 20 + [5000])
        result = rvol(volume, window=20)
        last = result.iloc[-1]
        if last is not None:
            assert last > 1.0  # Spike
