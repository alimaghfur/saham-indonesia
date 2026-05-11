"""Unit tests for the iTick adapter's parsing helpers.

These tests do NOT hit the network; they feed canned response shapes into
the pure-Python parsing code to verify canonicalization into our `Quote`
and OHLC DataFrame models.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from saham_id.data.models import Quote
from saham_id.data.sources.base import SourceError
from saham_id.data.sources.itick import ITickSource, _INTERVAL_TO_KTYPE, _period_to_bar_count


class TestIntervalMapping:
    def test_known_intervals_map_to_ktype(self):
        assert _INTERVAL_TO_KTYPE["1m"] == 1
        assert _INTERVAL_TO_KTYPE["1d"] == 8
        assert _INTERVAL_TO_KTYPE["1wk"] == 9

    def test_period_to_bar_count_1y_1d(self):
        # ~247 trading days per year, 1 bar per day => ~247 bars
        n = _period_to_bar_count("1y", "1d")
        assert n >= 200

    def test_period_to_bar_count_1d_1m(self):
        # 1 day of 1m bars ~ 4 * 60 = 240 bars floor; enforced min 50
        n = _period_to_bar_count("1d", "1m")
        assert n >= 50


class TestExtract:
    def test_extract_quote_from_wrapped(self):
        payload = {"code": 0, "data": {"ld": 1000}}
        assert ITickSource._extract_quote_payload(payload) == {"ld": 1000}

    def test_extract_quote_from_list(self):
        payload = {"code": 0, "data": [{"ld": 500}]}
        assert ITickSource._extract_quote_payload(payload) == {"ld": 500}

    def test_extract_quote_empty_list_returns_none(self):
        assert ITickSource._extract_quote_payload({"data": []}) is None

    def test_extract_quote_from_bare_dict(self):
        payload = {"ld": 1200}
        assert ITickSource._extract_quote_payload(payload) == payload

    def test_extract_list_from_data_list(self):
        payload = {"data": [{"t": 1, "o": 1}, {"t": 2, "o": 2}]}
        assert len(ITickSource._extract_list_payload(payload)) == 2

    def test_extract_list_from_nested(self):
        payload = {"data": {"klines": [{"t": 1}]}}
        assert ITickSource._extract_list_payload(payload) == [{"t": 1}]

    def test_extract_list_from_empty(self):
        assert ITickSource._extract_list_payload({}) == []
        assert ITickSource._extract_list_payload(None) == []  # type: ignore[arg-type]


class TestParseQuote:
    def test_basic_fields(self):
        data = {
            "ld": 9000, "o": 8950, "h": 9100, "l": 8900,
            "pc": 8900, "v": 1_000_000, "t": 1_700_000_000,
        }
        q = ITickSource._parse_quote("BBCA", data)
        assert isinstance(q, Quote)
        assert q.ticker == "BBCA"
        assert q.last == Decimal("9000")
        assert q.open == Decimal("8950")
        assert q.prev_close == Decimal("8900")
        assert q.volume == 1_000_000
        assert q.source == "itick"
        assert q.delayed_minutes == 0
        # change_pct should be computable
        assert q.change_pct == pytest.approx((9000 - 8900) / 8900)

    def test_alternative_keys(self):
        # Test fallbacks: `last` instead of `ld`, `open` instead of `o`, etc.
        data = {"last": 5000, "open": 4950, "close": None, "previousClose": 4900}
        q = ITickSource._parse_quote("BBRI", data)
        assert q.last == Decimal("5000")
        assert q.open == Decimal("4950")
        assert q.prev_close == Decimal("4900")

    def test_missing_last_raises(self):
        with pytest.raises(SourceError):
            ITickSource._parse_quote("BBCA", {"o": 1000})

    def test_ticker_normalization_strips_jk_suffix(self):
        q = ITickSource._parse_quote("BBCA.JK", {"ld": 9000})
        assert q.ticker == "BBCA"


class TestParseKline:
    def test_converts_to_ohlc_dataframe(self):
        items = [
            {"t": 1_700_000_000, "o": 100, "h": 110, "l": 95, "c": 105, "v": 1000},
            {"t": 1_700_086_400, "o": 105, "h": 115, "l": 100, "c": 112, "v": 1200},
        ]
        df = ITickSource._parse_kline(items)
        assert len(df) == 2
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]
        assert df.iloc[0]["close"] == 105
        assert df.iloc[1]["volume"] == 1200

    def test_sorts_by_timestamp_ascending(self):
        items = [
            {"t": 1_700_086_400, "o": 105, "h": 115, "l": 100, "c": 112, "v": 1200},
            {"t": 1_700_000_000, "o": 100, "h": 110, "l": 95, "c": 105, "v": 1000},
        ]
        df = ITickSource._parse_kline(items)
        assert df.index[0] < df.index[1]

    def test_empty_items_returns_empty_df(self):
        df = ITickSource._parse_kline([])
        assert df.empty
        assert list(df.columns) == ["open", "high", "low", "close", "volume"]


class TestParseTimestamp:
    def test_epoch_seconds(self):
        dt = ITickSource._parse_timestamp(1_700_000_000)
        assert isinstance(dt, datetime)
        assert dt.year == 2023

    def test_epoch_millis(self):
        dt = ITickSource._parse_timestamp(1_700_000_000_000)
        assert dt.year == 2023

    def test_iso_string(self):
        dt = ITickSource._parse_timestamp("2024-06-17T10:30:00Z")
        assert dt.year == 2024
        assert dt.month == 6
        assert dt.day == 17

    def test_none_returns_now(self):
        dt = ITickSource._parse_timestamp(None)
        assert isinstance(dt, datetime)


class TestSourceConfiguration:
    def test_missing_key_raises_on_get_quote(self):
        src = ITickSource(api_key="")
        try:
            with pytest.raises(SourceError):
                src.get_quote("BBCA")
        finally:
            src.close()

    def test_headers_include_token_when_key_present(self):
        src = ITickSource(api_key="fake-test-key")
        try:
            headers = src._build_headers()
            assert headers["token"] == "fake-test-key"
        finally:
            src.close()

    def test_headers_omit_token_when_key_missing(self):
        src = ITickSource(api_key="")
        try:
            headers = src._build_headers()
            assert "token" not in headers
        finally:
            src.close()
