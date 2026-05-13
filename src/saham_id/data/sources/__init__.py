"""Data source registry.

Usage:
    from saham_id.data import get_source

    src = get_source("yahoo")          # explicit (cached by default)
    src = get_source()                 # from SAHAM_ID_DATA_SOURCES chain
    src = get_source("yahoo", cached=False)  # bypass caching
    quote = src.get_quote("BBCA")
"""

from __future__ import annotations

import logging
from typing import Optional

from saham_id.config import settings
from saham_id.data.sources.base import DataSource
from saham_id.data.sources.cached import CachedDataSource
from saham_id.data.sources.goapi import GoApiSource
from saham_id.data.sources.itick import ITickSource
from saham_id.data.sources.rti_scraper import RtiScraperSource
from saham_id.data.sources.sectors_app import SectorsAppSource
from saham_id.data.sources.yahoo_finance import YahooFinanceSource

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, type[DataSource]] = {
    "yahoo": YahooFinanceSource,
    "yfinance": YahooFinanceSource,
    "rti": RtiScraperSource,
    "pasardana": RtiScraperSource,
    "itick": ITickSource,
    "goapi": GoApiSource,
    "sectors": SectorsAppSource,
}


def list_sources() -> list[str]:
    """Names that can be passed to `get_source()`."""
    return sorted(set(_REGISTRY))


def get_source(name: Optional[str] = None, cached: bool = True) -> DataSource:
    """Return a `DataSource` instance.

    When `name` is None, uses the first entry in `SAHAM_ID_DATA_SOURCES`.
    When `cached` is True (default), wraps the source with CachedDataSource
    for automatic caching and enhanced error handling.
    """
    if name is None:
        chain = settings.data_source_chain or ["yahoo"]
        name = chain[0]
    key = name.lower()
    if key not in _REGISTRY:
        valid = ", ".join(list_sources())
        raise ValueError(f"Unknown data source '{name}'. Valid: {valid}")

    source = _REGISTRY[key]()

    if cached and settings.cache_enabled:
        source = CachedDataSource(source)
        logger.debug(f"Created cached source: {source}")

    return source


__all__ = ["CachedDataSource", "DataSource", "get_source", "list_sources"]
