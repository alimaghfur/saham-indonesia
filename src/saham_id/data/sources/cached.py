"""Cached data source wrapper.

Wraps any DataSource with caching and enhanced error handling.
Transparent to consumers — same interface, better performance.

Usage:
    from saham_id.data.sources.cached import CachedDataSource
    from saham_id.data.sources.yahoo_finance import YahooFinanceSource

    source = CachedDataSource(YahooFinanceSource())
    quote = source.get_quote("BBCA")  # cached for 60s
"""

from __future__ import annotations

import logging
from typing import Iterable, Optional

import pandas as pd

from saham_id.cache import (
    TTL_FUNDAMENTALS,
    TTL_MOVERS,
    TTL_OHLC_DAILY,
    TTL_OHLC_INTRADAY,
    TTL_QUOTE,
    cache,
    _make_cache_key,
)
from saham_id.config import settings as _settings
from saham_id.data.models import FundamentalSnapshot, Mover, Quote
from saham_id.data.sources.base import (
    DataSource,
    Interval,
    MoverKind,
    Period,
    SourceError,
)
from saham_id.errors import (
    ConnectionError as SahamConnectionError,
    DataNotFoundError,
    DataSourceError,
    ErrorCollector,
    RateLimitError,
    TimeoutError as SahamTimeoutError,
    retry_on_failure,
)

logger = logging.getLogger(__name__)


def _ohlc_ttl(interval: str) -> int:
    """Determine TTL based on data interval."""
    intraday = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"}
    return TTL_OHLC_INTRADAY if interval in intraday else TTL_OHLC_DAILY


def _wrap_source_error(exc: Exception, source_name: str, ticker: str = "") -> DataSourceError:
    """Convert generic exceptions to structured error types."""
    msg = str(exc)
    lower_msg = msg.lower()

    if "timeout" in lower_msg or "timed out" in lower_msg:
        return SahamTimeoutError(msg, source=source_name)
    elif "rate limit" in lower_msg or "too many requests" in lower_msg or "429" in msg:
        return RateLimitError(msg, source=source_name)
    elif "connection" in lower_msg or "network" in lower_msg or "unreachable" in lower_msg:
        return SahamConnectionError(msg, source=source_name)
    elif "not found" in lower_msg or "no data" in lower_msg or "no quote" in lower_msg:
        return DataNotFoundError(msg, source=source_name, ticker=ticker)
    else:
        return DataSourceError(msg, source=source_name)


class CachedDataSource(DataSource):
    """Wrapper that adds caching + error handling to any DataSource.

    Features:
    - Automatic caching with interval-aware TTLs
    - Retry with exponential backoff on transient errors
    - Structured error conversion
    - Cache bypass option for forced refresh
    """

    def __init__(
        self,
        inner: DataSource,
        enable_cache: bool = True,
        max_retries: Optional[int] = None,
    ) -> None:
        from saham_id.config import settings as _settings

        self._inner = inner
        self._enable_cache = enable_cache
        self._max_retries = max_retries if max_retries is not None else _settings.retry_max_attempts

    @property
    def name(self) -> str:
        return self._inner.name

    @property
    def typical_delay_minutes(self) -> int:
        return self._inner.typical_delay_minutes

    @property
    def supports_realtime(self) -> bool:
        return self._inner.supports_realtime

    # ------------------------------------------------------------------
    # Quotes (with caching + retry)
    # ------------------------------------------------------------------

    def get_quote(self, ticker: str, bypass_cache: bool = False) -> Quote:
        """Get quote with caching and error handling."""
        cache_key = _make_cache_key(f"quote:{self.name}", (ticker,), {})

        if self._enable_cache and not bypass_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        quote = self._fetch_quote_with_retry(ticker)

        if self._enable_cache:
            cache.set(cache_key, quote, ttl=TTL_QUOTE)

        return quote

    @retry_on_failure(
        max_retries=_settings.retry_max_attempts,
        retry_on=(DataSourceError, SourceError),
        min_wait=_settings.retry_min_wait,
        max_wait=_settings.retry_max_wait,
    )
    def _fetch_quote_with_retry(self, ticker: str) -> Quote:
        try:
            return self._inner.get_quote(ticker)
        except SourceError as exc:
            raise _wrap_source_error(exc, self.name, ticker) from exc
        except Exception as exc:
            raise _wrap_source_error(exc, self.name, ticker) from exc

    def get_quotes(self, tickers: Iterable[str], bypass_cache: bool = False) -> list[Quote]:
        """Batch quote fetch with per-ticker caching and error collection."""
        tickers_list = list(tickers)
        results: list[Quote] = []
        to_fetch: list[str] = []

        # Check cache first
        if self._enable_cache and not bypass_cache:
            for ticker in tickers_list:
                cache_key = _make_cache_key(f"quote:{self.name}", (ticker,), {})
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    results.append(cached_result)
                else:
                    to_fetch.append(ticker)
        else:
            to_fetch = tickers_list

        # Fetch missing quotes
        if to_fetch:
            collector = ErrorCollector()
            try:
                fetched = self._inner.get_quotes(to_fetch)
                for quote in fetched:
                    if self._enable_cache:
                        cache_key = _make_cache_key(f"quote:{self.name}", (quote.ticker,), {})
                        cache.set(cache_key, quote, ttl=TTL_QUOTE)
                    results.append(quote)
            except Exception as exc:
                # Fallback: fetch individually
                logger.warning(f"Batch quote failed, falling back to individual: {exc}")
                for ticker in to_fetch:
                    with collector.catch(ticker):
                        quote = self.get_quote(ticker, bypass_cache=True)
                        results.append(quote)

            if collector.has_errors:
                logger.warning(f"Quote fetch errors: {collector.summary()}")

        return results

    # ------------------------------------------------------------------
    # OHLC (with caching + retry)
    # ------------------------------------------------------------------

    def get_ohlc(
        self,
        ticker: str,
        period: Period = "1y",
        interval: Interval = "1d",
        bypass_cache: bool = False,
    ) -> pd.DataFrame:
        """Get OHLC data with interval-aware caching."""
        cache_key = _make_cache_key(
            f"ohlc:{self.name}", (ticker, period, interval), {}
        )

        if self._enable_cache and not bypass_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        df = self._fetch_ohlc_with_retry(ticker, period, interval)

        if self._enable_cache:
            ttl = _ohlc_ttl(interval)
            cache.set(cache_key, df, ttl=ttl)

        return df

    @retry_on_failure(
        max_retries=_settings.retry_max_attempts,
        retry_on=(DataSourceError, SourceError),
        min_wait=_settings.retry_min_wait,
        max_wait=_settings.retry_max_wait,
    )
    def _fetch_ohlc_with_retry(
        self, ticker: str, period: Period, interval: Interval
    ) -> pd.DataFrame:
        try:
            return self._inner.get_ohlc(ticker, period=period, interval=interval)
        except SourceError as exc:
            raise _wrap_source_error(exc, self.name, ticker) from exc
        except Exception as exc:
            raise _wrap_source_error(exc, self.name, ticker) from exc

    # ------------------------------------------------------------------
    # Market movers (with caching)
    # ------------------------------------------------------------------

    def get_movers(
        self,
        kind: MoverKind = "gainer",
        universe: Optional[Iterable[str]] = None,
        top_n: int = 20,
        bypass_cache: bool = False,
    ) -> list[Mover]:
        """Get market movers with caching."""
        universe_key = str(sorted(universe)) if universe else "all"
        cache_key = _make_cache_key(
            f"movers:{self.name}", (kind, universe_key, top_n), {}
        )

        if self._enable_cache and not bypass_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        try:
            movers = self._inner.get_movers(kind=kind, universe=universe, top_n=top_n)
        except SourceError as exc:
            raise _wrap_source_error(exc, self.name) from exc

        if self._enable_cache:
            cache.set(cache_key, movers, ttl=TTL_MOVERS)

        return movers

    # ------------------------------------------------------------------
    # Fundamentals (with caching)
    # ------------------------------------------------------------------

    def get_fundamentals(self, ticker: str, bypass_cache: bool = False) -> FundamentalSnapshot:
        """Get fundamentals with long-lived caching."""
        cache_key = _make_cache_key(f"fund:{self.name}", (ticker,), {})

        if self._enable_cache and not bypass_cache:
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        try:
            result = self._inner.get_fundamentals(ticker)
        except SourceError as exc:
            raise _wrap_source_error(exc, self.name, ticker) from exc

        if self._enable_cache:
            cache.set(cache_key, result, ttl=TTL_FUNDAMENTALS)

        return result

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def clear_cache(self, ticker: Optional[str] = None) -> None:
        """Clear cache for a specific ticker or all data from this source."""
        if ticker:
            # Clear all cache entries for this ticker
            for prefix in ("quote", "ohlc", "fund"):
                key = _make_cache_key(f"{prefix}:{self.name}", (ticker,), {})
                cache.invalidate(key)
            logger.info(f"Cache cleared for {ticker} on {self.name}")
        else:
            # Clear all entries for this source
            for prefix in ("quote", "ohlc", "movers", "fund"):
                cache.invalidate_prefix(f"{prefix}:{self.name}")
            logger.info(f"Cache cleared for source {self.name}")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._inner.close()

    def __repr__(self) -> str:
        return (
            f"<CachedDataSource inner={self._inner.name!r} "
            f"cache={'on' if self._enable_cache else 'off'}>"
        )
