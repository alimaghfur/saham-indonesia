"""Shared fixtures for the test suite.

The core idea: tests run with a deterministic in-memory ``FakeSource`` so
every screener/analyzer can be exercised without network access.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Iterable, Optional

import numpy as np
import pandas as pd
import pytest

from saham_id.data.models import Quote
from saham_id.data.sources.base import DataSource, Interval, NotImplementedForSource, Period


# ---------------------------------------------------------------------------
# Deterministic OHLC generator
# ---------------------------------------------------------------------------
def make_ohlc(
    start: str = "2024-01-01",
    bars: int = 120,
    seed: int = 0,
    start_price: float = 1000.0,
    trend: float = 0.0002,
    noise: float = 0.01,
    intraday_bias: float = 0.0,
    overnight_bias: float = 0.0,
    volume_mean: int = 1_000_000,
    volume_std: int = 100_000,
    freq: str = "B",
) -> pd.DataFrame:
    """Generate a synthetic OHLCV DataFrame.

    ``trend`` and ``noise`` act on daily log-returns. ``intraday_bias`` nudges
    (close-open) within each bar. ``overnight_bias`` nudges the next bar's
    open relative to the previous close so BSJP tests have a signal.
    """
    rng = np.random.default_rng(seed)
    index = pd.date_range(start=start, periods=bars, freq=freq, name="timestamp")
    log_rets = rng.normal(loc=trend, scale=noise, size=bars)
    closes = start_price * np.exp(np.cumsum(log_rets))

    opens = np.empty_like(closes)
    opens[0] = start_price
    for i in range(1, bars):
        opens[i] = closes[i - 1] * (1.0 + overnight_bias + rng.normal(0, noise / 4))
        # apply intraday bias by tilting close relative to open
        closes[i] = opens[i] * (1.0 + intraday_bias + rng.normal(trend, noise))

    highs = np.maximum(opens, closes) * (1 + np.abs(rng.normal(0, noise / 2, bars)))
    lows = np.minimum(opens, closes) * (1 - np.abs(rng.normal(0, noise / 2, bars)))
    volumes = np.maximum(
        1, rng.normal(volume_mean, volume_std, bars).astype(int)
    )

    return pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
        },
        index=index,
    )


# ---------------------------------------------------------------------------
# FakeSource — plugs into the DataSource registry in tests
# ---------------------------------------------------------------------------
class FakeSource(DataSource):
    """In-memory DataSource that returns pre-canned OHLC DataFrames."""

    name = "fake"
    typical_delay_minutes = 0
    supports_realtime = True

    def __init__(
        self,
        ohlc_by_ticker: Optional[dict[str, pd.DataFrame]] = None,
        default_bars: int = 120,
    ) -> None:
        self._data = dict(ohlc_by_ticker) if ohlc_by_ticker else {}
        self._default_bars = default_bars
        self.call_log: list[tuple[str, str, str, str]] = []

    # ------ test helpers ------
    def add(self, ticker: str, df: pd.DataFrame) -> "FakeSource":
        self._data[ticker.upper()] = df
        return self

    def populate(self, tickers: Iterable[str], **kwargs) -> "FakeSource":
        for i, t in enumerate(tickers):
            if t.upper() not in self._data:
                self._data[t.upper()] = make_ohlc(seed=i, **kwargs)
        return self

    # ------ DataSource API ------
    def get_quote(self, ticker: str) -> Quote:
        df = self._get_df_or_raise(ticker)
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        return Quote(
            ticker=ticker.upper(),
            timestamp=datetime.utcnow(),
            last=Decimal(str(round(float(last["close"]), 2))),
            open=Decimal(str(round(float(last["open"]), 2))),
            high=Decimal(str(round(float(last["high"]), 2))),
            low=Decimal(str(round(float(last["low"]), 2))),
            prev_close=Decimal(str(round(float(prev["close"]), 2))),
            volume=int(last["volume"]),
            delayed_minutes=0,
            source=self.name,
        )

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        self.call_log.append((ticker, period, interval, "ohlc"))
        df = self._get_df_or_raise(ticker)
        return df.copy()

    def _get_df_or_raise(self, ticker: str) -> pd.DataFrame:
        key = ticker.upper().removesuffix(".JK")
        if key not in self._data:
            raise NotImplementedForSource(f"FakeSource: ticker '{ticker}' not registered")
        return self._data[key]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def ohlc_trending_up() -> pd.DataFrame:
    """120 daily bars with a steady uptrend and positive intraday bias."""
    return make_ohlc(seed=1, trend=0.002, noise=0.008, intraday_bias=0.003)


@pytest.fixture
def ohlc_range_bound() -> pd.DataFrame:
    """120 daily bars with no trend (mean reversion)."""
    return make_ohlc(seed=2, trend=0.0, noise=0.005)


@pytest.fixture
def ohlc_gapping_up() -> pd.DataFrame:
    """120 daily bars with positive overnight gap bias (BSJP signal)."""
    return make_ohlc(seed=3, trend=0.0005, noise=0.006, overnight_bias=0.0025)


@pytest.fixture
def fake_source() -> FakeSource:
    """Empty FakeSource — tests populate it as needed."""
    return FakeSource()


@pytest.fixture
def populated_fake_source(
    ohlc_trending_up: pd.DataFrame,
    ohlc_range_bound: pd.DataFrame,
    ohlc_gapping_up: pd.DataFrame,
) -> FakeSource:
    """Pre-populated FakeSource with 3 named tickers + 5 auto-generated ones."""
    src = FakeSource()
    src.add("TRND", ohlc_trending_up)
    src.add("FLAT", ohlc_range_bound)
    src.add("GAPU", ohlc_gapping_up)
    src.populate(["BBCA", "BBRI", "TLKM", "ASII", "BMRI"])
    return src


@pytest.fixture
def today() -> datetime:
    return datetime(2024, 6, 17, 10, 30)  # Monday, during session 1
