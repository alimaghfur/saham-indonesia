"""Comprehensive error handling for saham-indonesia.

Provides:
- Exception hierarchy for all domain errors.
- Retry decorator with exponential backoff (wraps tenacity).
- Error context manager for graceful degradation.
- Structured error logging utilities.

Usage:
    from saham_id.errors import (
        SahamError, DataSourceError, RateLimitError,
        retry_on_failure, error_boundary,
    )

    @retry_on_failure(max_retries=3, retry_on=(DataSourceError,))
    def fetch_data():
        ...

    with error_boundary("fetching quote", default=None):
        quote = source.get_quote("BBCA")
"""

from __future__ import annotations

import logging
import traceback
from contextlib import contextmanager
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Generator, Optional, Sequence, Type, TypeVar

from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ======================================================================
# Exception hierarchy
# ======================================================================


class SahamError(Exception):
    """Base exception for all saham-indonesia errors."""

    def __init__(self, message: str, code: Optional[str] = None, details: Optional[dict] = None):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Serialize error for logging or API responses."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


# --- Data source errors ---


class DataSourceError(SahamError):
    """Error originating from a data source (network, parsing, etc.)."""

    def __init__(self, message: str, source: str = "unknown", **kwargs):
        self.source = source
        super().__init__(message, details={"source": source, **kwargs.get("details", {})}, **{k: v for k, v in kwargs.items() if k != "details"})


class ConnectionError(DataSourceError):
    """Network connectivity issue."""

    def __init__(self, message: str, source: str = "unknown", url: Optional[str] = None):
        super().__init__(message, source=source, details={"url": url})


class TimeoutError(DataSourceError):
    """Request timed out."""

    def __init__(self, message: str, source: str = "unknown", timeout_seconds: Optional[float] = None):
        super().__init__(message, source=source, details={"timeout_seconds": timeout_seconds})


class RateLimitError(DataSourceError):
    """Rate limit exceeded for a data source."""

    def __init__(self, message: str, source: str = "unknown", retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(message, source=source, details={"retry_after_seconds": retry_after})


class AuthenticationError(DataSourceError):
    """API key invalid or missing."""

    def __init__(self, message: str, source: str = "unknown"):
        super().__init__(message, source=source)


class DataNotFoundError(DataSourceError):
    """Requested data does not exist (e.g., invalid ticker)."""

    def __init__(self, message: str, source: str = "unknown", ticker: Optional[str] = None):
        super().__init__(message, source=source, details={"ticker": ticker})


class DataParsingError(DataSourceError):
    """Failed to parse response from data source."""

    def __init__(self, message: str, source: str = "unknown", raw_data: Optional[str] = None):
        # Truncate raw_data for safety
        truncated = raw_data[:500] if raw_data else None
        super().__init__(message, source=source, details={"raw_data_preview": truncated})


# --- Validation errors ---


class ValidationError(SahamError):
    """Input validation failed."""

    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        super().__init__(message, details={"field": field, "value": str(value)[:100]})


class InvalidTickerError(ValidationError):
    """Ticker symbol is invalid or not recognized."""

    def __init__(self, ticker: str):
        super().__init__(f"Invalid ticker: {ticker!r}", field="ticker", value=ticker)


class InvalidPeriodError(ValidationError):
    """Period or interval is not supported."""

    def __init__(self, period: str, valid_periods: Optional[list[str]] = None):
        msg = f"Invalid period: {period!r}"
        if valid_periods:
            msg += f". Valid: {', '.join(valid_periods)}"
        super().__init__(msg, field="period", value=period)


# --- Analysis/computation errors ---


class AnalysisError(SahamError):
    """Error during analysis or computation."""


class InsufficientDataError(AnalysisError):
    """Not enough data points to perform the analysis."""

    def __init__(self, message: str, required: Optional[int] = None, available: Optional[int] = None):
        super().__init__(message, details={"required": required, "available": available})


class CalculationError(AnalysisError):
    """Numerical computation failed (overflow, division by zero, etc.)."""


# --- Backtest errors ---


class BacktestError(SahamError):
    """Error during backtesting."""


class StrategyError(BacktestError):
    """Error in a trading strategy implementation."""


# --- Configuration errors ---


class ConfigurationError(SahamError):
    """Configuration or environment issue."""


# ======================================================================
# Retry decorator (wraps tenacity)
# ======================================================================


def retry_on_failure(
    max_retries: int = 3,
    retry_on: Sequence[Type[Exception]] = (DataSourceError,),
    min_wait: float = 1.0,
    max_wait: float = 30.0,
    log_retries: bool = True,
) -> Callable[[F], F]:
    """Decorator for automatic retry with exponential backoff.

    Args:
        max_retries: Maximum number of attempts (includes first try).
        retry_on: Exception types that trigger a retry.
        min_wait: Minimum wait time between retries (seconds).
        max_wait: Maximum wait time between retries (seconds).
        log_retries: Whether to log retry attempts.
    """

    def decorator(func: F) -> F:
        @retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=min_wait, max=max_wait),
            retry=retry_if_exception_type(tuple(retry_on)),
            reraise=True,
        )
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        @wraps(func)
        def outer(*args, **kwargs):
            try:
                return wrapper(*args, **kwargs)
            except RetryError as exc:
                if log_retries:
                    logger.error(
                        f"{func.__qualname__} failed after {max_retries} retries: {exc.last_attempt.exception()}"
                    )
                # Re-raise the original exception
                raise exc.last_attempt.exception() from exc

        return outer  # type: ignore

    return decorator


# ======================================================================
# Error boundary context manager
# ======================================================================


@contextmanager
def error_boundary(
    operation: str,
    default: Any = None,
    log_level: int = logging.WARNING,
    reraise: bool = False,
    suppress: Sequence[Type[Exception]] = (SahamError, Exception),
) -> Generator[None, None, None]:
    """Context manager for graceful error handling.

    Args:
        operation: Description of the operation (for logging).
        default: This is stored for the caller's reference only; yield always returns None.
        log_level: Logging level for caught exceptions.
        reraise: If True, re-raises the exception after logging.
        suppress: Exception types to suppress.

    Usage:
        with error_boundary("fetching quote", default=None):
            result = source.get_quote("BBCA")
    """
    try:
        yield
    except tuple(suppress) as exc:
        logger.log(log_level, f"Error in '{operation}': {exc}")
        logger.debug(traceback.format_exc())
        if reraise:
            raise


# ======================================================================
# Error collection for batch operations
# ======================================================================


class ErrorCollector:
    """Collect errors during batch operations without stopping execution.

    Usage:
        collector = ErrorCollector()
        for ticker in tickers:
            with collector.catch(ticker):
                process(ticker)
        if collector.has_errors:
            logger.warning(f"Failed: {collector.summary()}")
    """

    def __init__(self) -> None:
        self._errors: list[dict[str, Any]] = []

    @contextmanager
    def catch(self, context: str = "") -> Generator[None, None, None]:
        """Catch and record exceptions without stopping."""
        try:
            yield
        except Exception as exc:
            self._errors.append({
                "context": context,
                "error": type(exc).__name__,
                "message": str(exc),
                "timestamp": datetime.utcnow().isoformat(),
            })
            logger.debug(f"ErrorCollector caught in '{context}': {exc}")

    @property
    def has_errors(self) -> bool:
        return len(self._errors) > 0

    @property
    def error_count(self) -> int:
        return len(self._errors)

    @property
    def errors(self) -> list[dict[str, Any]]:
        return self._errors.copy()

    def summary(self) -> str:
        """Human-readable summary of collected errors."""
        if not self._errors:
            return "No errors"
        lines = [f"{len(self._errors)} error(s):"]
        for err in self._errors[:10]:
            lines.append(f"  [{err['context']}] {err['error']}: {err['message']}")
        if len(self._errors) > 10:
            lines.append(f"  ... and {len(self._errors) - 10} more")
        return "\n".join(lines)

    def clear(self) -> None:
        self._errors.clear()
