"""Tests for the error handling module (saham_id.errors).

Tests:
- Exception hierarchy and inheritance
- SahamError serialization (to_dict)
- retry_on_failure decorator behavior
- error_boundary context manager
- ErrorCollector batch error handling
"""
from saham_id.errors import (
    SahamError,
    DataSourceError,
    ConnectionError,
    TimeoutError,
    RateLimitError,
    AuthenticationError,
    DataNotFoundError,
    DataParsingError,
    ValidationError,
    InvalidTickerError,
    InvalidPeriodError,
    AnalysisError,
    InsufficientDataError,
    CalculationError,
    BacktestError,
    StrategyError,
    ConfigurationError,
    retry_on_failure,
    error_boundary,
    ErrorCollector,
)


# ======================================================================
# Exception hierarchy
# ======================================================================

class TestExceptionHierarchy:
    def test_saham_error_is_base(self):
        assert issubclass(DataSourceError, SahamError)
        assert issubclass(ValidationError, SahamError)
        assert issubclass(AnalysisError, SahamError)
        assert issubclass(BacktestError, SahamError)
        assert issubclass(ConfigurationError, SahamError)

    def test_data_source_subtypes(self):
        assert issubclass(ConnectionError, DataSourceError)
        assert issubclass(TimeoutError, DataSourceError)
        assert issubclass(RateLimitError, DataSourceError)
        assert issubclass(AuthenticationError, DataSourceError)
        assert issubclass(DataNotFoundError, DataSourceError)
        assert issubclass(DataParsingError, DataSourceError)

    def test_validation_subtypes(self):
        assert issubclass(InvalidTickerError, ValidationError)
        assert issubclass(InvalidPeriodError, ValidationError)

    def test_analysis_subtypes(self):
        assert issubclass(InsufficientDataError, AnalysisError)
        assert issubclass(CalculationError, AnalysisError)

    def test_backtest_subtypes(self):
        assert issubclass(StrategyError, BacktestError)

    def test_all_inherit_exception(self):
        assert issubclass(SahamError, Exception)

    def test_catch_by_base(self):
        """Can catch specific errors using base class."""
        try:
            raise RateLimitError("429", source="yahoo")
        except DataSourceError as exc:
            assert "429" in str(exc)
        except Exception:
            assert False, "Should have been caught by DataSourceError"


# ======================================================================
# SahamError serialization
# ======================================================================

class TestSahamErrorSerialization:
    def test_to_dict_basic(self):
        err = SahamError("something went wrong")
        d = err.to_dict()
        assert d["error"] == "SahamError"
        assert d["message"] == "something went wrong"
        assert "timestamp" in d
        assert isinstance(d["details"], dict)

    def test_to_dict_with_code(self):
        err = SahamError("fail", code="CUSTOM_CODE")
        d = err.to_dict()
        assert d["error"] == "CUSTOM_CODE"

    def test_data_source_error_has_source(self):
        err = DataSourceError("timeout", source="itick")
        assert err.source == "itick"
        d = err.to_dict()
        assert d["details"]["source"] == "itick"

    def test_rate_limit_error_retry_after(self):
        err = RateLimitError("too fast", source="rti", retry_after=60)
        assert err.retry_after == 60
        d = err.to_dict()
        assert d["details"]["retry_after_seconds"] == 60

    def test_data_not_found_ticker(self):
        err = DataNotFoundError("no data", source="yahoo", ticker="XXXX")
        d = err.to_dict()
        assert d["details"]["ticker"] == "XXXX"

    def test_invalid_ticker_error(self):
        err = InvalidTickerError("ZZZZ")
        assert "ZZZZ" in err.message
        d = err.to_dict()
        assert d["details"]["field"] == "ticker"

    def test_invalid_period_error(self):
        err = InvalidPeriodError("99y", valid_periods=["1y", "6mo"])
        assert "99y" in err.message
        assert "1y" in err.message

    def test_insufficient_data_error(self):
        err = InsufficientDataError("need more", required=100, available=5)
        d = err.to_dict()
        assert d["details"]["required"] == 100
        assert d["details"]["available"] == 5

    def test_data_parsing_error_truncates(self):
        long_data = "x" * 1000
        err = DataParsingError("parse failed", source="rti", raw_data=long_data)
        d = err.to_dict()
        assert len(d["details"]["raw_data_preview"]) == 500


# ======================================================================
# retry_on_failure
# ======================================================================

class TestRetryOnFailure:
    def test_succeeds_first_try(self):
        call_count = [0]

        @retry_on_failure(max_retries=3, retry_on=(DataSourceError,))
        def fn():
            call_count[0] += 1
            return "ok"

        result = fn()
        assert result == "ok"
        assert call_count[0] == 1

    def test_retries_on_matching_exception(self):
        call_count = [0]

        @retry_on_failure(max_retries=3, retry_on=(DataSourceError,))
        def fn():
            call_count[0] += 1
            if call_count[0] < 3:
                raise DataSourceError("transient", source="test")
            return "recovered"

        result = fn()
        assert result == "recovered"
        assert call_count[0] == 3

    def test_raises_after_max_retries(self):
        call_count = [0]

        @retry_on_failure(max_retries=2, retry_on=(DataSourceError,))
        def fn():
            call_count[0] += 1
            raise DataSourceError("always fails", source="test")

        try:
            fn()
            assert False, "Should have raised"
        except DataSourceError as exc:
            assert "always fails" in str(exc)
        assert call_count[0] == 2

    def test_does_not_retry_non_matching_exception(self):
        call_count = [0]

        @retry_on_failure(max_retries=3, retry_on=(DataSourceError,))
        def fn():
            call_count[0] += 1
            raise ValueError("not retryable")

        try:
            fn()
            assert False, "Should have raised"
        except ValueError:
            pass
        assert call_count[0] == 1

    def test_retries_subtypes(self):
        """Should retry on subclasses of retry_on types."""
        call_count = [0]

        @retry_on_failure(max_retries=3, retry_on=(DataSourceError,))
        def fn():
            call_count[0] += 1
            if call_count[0] < 2:
                raise RateLimitError("429", source="test")
            return "ok"

        result = fn()
        assert result == "ok"
        assert call_count[0] == 2


# ======================================================================
# error_boundary
# ======================================================================

class TestErrorBoundary:
    def test_suppresses_exception(self):
        """Exception is suppressed; code after the context exits normally."""
        result = "before"
        with error_boundary("test op", default="fallback"):
            raise DataSourceError("boom", source="test")
        result = "after"
        assert result == "after"

    def test_no_exception_runs_normally(self):
        with error_boundary("test op"):
            x = 42
        assert x == 42

    def test_reraise_option(self):
        try:
            with error_boundary("test op", reraise=True):
                raise DataSourceError("boom", source="test")
            assert False, "Should have reraised"
        except DataSourceError:
            pass

    def test_suppresses_generic_exception(self):
        with error_boundary("test op"):
            raise RuntimeError("generic")
        # Should not raise

    def test_suppress_only_matching_types(self):
        """Only suppresses specified types."""
        try:
            with error_boundary("test op", suppress=(DataSourceError,)):
                raise ValueError("not suppressed")
            assert False, "Should have raised"
        except ValueError:
            pass


# ======================================================================
# ErrorCollector
# ======================================================================

class TestErrorCollector:
    def test_no_errors_initially(self):
        ec = ErrorCollector()
        assert ec.has_errors is False
        assert ec.error_count == 0
        assert ec.errors == []

    def test_catch_records_error(self):
        ec = ErrorCollector()
        with ec.catch("BBCA"):
            raise DataSourceError("fail", source="test")
        assert ec.has_errors is True
        assert ec.error_count == 1
        assert ec.errors[0]["context"] == "BBCA"
        assert ec.errors[0]["error"] == "DataSourceError"

    def test_catch_no_exception(self):
        ec = ErrorCollector()
        with ec.catch("BBCA"):
            x = 1 + 1
        assert ec.has_errors is False

    def test_multiple_errors(self):
        ec = ErrorCollector()
        with ec.catch("BBCA"):
            raise ValueError("err1")
        with ec.catch("BBRI"):
            raise RuntimeError("err2")
        with ec.catch("TLKM"):
            pass  # success

        assert ec.error_count == 2
        contexts = [e["context"] for e in ec.errors]
        assert "BBCA" in contexts
        assert "BBRI" in contexts
        assert "TLKM" not in contexts

    def test_summary_format(self):
        ec = ErrorCollector()
        assert ec.summary() == "No errors"

        with ec.catch("BBCA"):
            raise ValueError("bad value")

        summary = ec.summary()
        assert "1 error(s)" in summary
        assert "BBCA" in summary
        assert "ValueError" in summary

    def test_clear(self):
        ec = ErrorCollector()
        with ec.catch("X"):
            raise RuntimeError("oops")
        assert ec.has_errors is True
        ec.clear()
        assert ec.has_errors is False
        assert ec.error_count == 0

    def test_summary_truncates_at_10(self):
        ec = ErrorCollector()
        for i in range(15):
            with ec.catch(f"item_{i}"):
                raise RuntimeError(f"err_{i}")
        summary = ec.summary()
        assert "15 error(s)" in summary
        assert "and 5 more" in summary
