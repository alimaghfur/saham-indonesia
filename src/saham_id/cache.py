"""Caching layer for saham-indonesia.

Provides both in-memory (TTLCache) and disk-based caching with configurable TTL.
Designed to reduce API calls and improve responsiveness.

Usage:
    from saham_id.cache import cache, cached

    # Decorator-based caching
    @cached(ttl=300, prefix="ohlc")
    def get_ohlc(ticker: str, period: str) -> pd.DataFrame:
        ...

    # Manual cache operations
    cache.set("key", value, ttl=60)
    value = cache.get("key")
    cache.invalidate("key")
    cache.clear()
"""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar

from cachetools import TTLCache

from saham_id.config import settings

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Default TTLs (seconds)
TTL_QUOTE = 60  # 1 minute for realtime quotes
TTL_OHLC_INTRADAY = 300  # 5 minutes for intraday OHLC
TTL_OHLC_DAILY = 3600  # 1 hour for daily OHLC
TTL_FUNDAMENTALS = 86400  # 24 hours for fundamentals
TTL_MOVERS = 120  # 2 minutes for movers


def _make_cache_key(prefix: str, args: tuple, kwargs: dict) -> str:
    """Generate a stable cache key from function arguments."""
    key_data = json.dumps({"prefix": prefix, "args": str(args), "kwargs": str(sorted(kwargs.items()))})
    return f"{prefix}:{hashlib.md5(key_data.encode()).hexdigest()}"


class CacheManager:
    """Hybrid memory + disk cache manager.

    - Memory cache (TTLCache) for hot data with automatic expiry.
    - Disk cache (pickle files) for persistence across restarts.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        memory_maxsize: int = 1024,
        default_ttl: int = 300,
        enable_disk: bool = True,
    ) -> None:
        self._cache_dir = cache_dir or settings.cache_dir
        self._default_ttl = default_ttl
        self._enable_disk = enable_disk
        self._memory: TTLCache = TTLCache(maxsize=memory_maxsize, ttl=default_ttl)
        self._disk_meta: dict[str, float] = {}  # key -> expiry timestamp

        if self._enable_disk:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Disk cache directory: {self._cache_dir}")

    @property
    def memory_size(self) -> int:
        """Current number of items in memory cache."""
        return len(self._memory)

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache (memory first, then disk)."""
        # Try memory first
        value = self._memory.get(key)
        if value is not None:
            logger.debug(f"Cache HIT (memory): {key}")
            return value

        # Try disk
        if self._enable_disk:
            value = self._disk_get(key)
            if value is not None:
                logger.debug(f"Cache HIT (disk): {key}")
                # Promote to memory
                try:
                    self._memory[key] = value
                except ValueError:
                    pass  # TTLCache full or TTL issue
                return value

        logger.debug(f"Cache MISS: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store a value in both memory and disk cache."""
        ttl = ttl or self._default_ttl

        # Store in memory
        try:
            self._memory[key] = value
        except ValueError:
            pass

        # Store on disk
        if self._enable_disk:
            self._disk_set(key, value, ttl)

    def invalidate(self, key: str) -> None:
        """Remove a specific key from both caches."""
        self._memory.pop(key, None)
        if self._enable_disk:
            self._disk_delete(key)

    def invalidate_prefix(self, prefix: str) -> None:
        """Remove all keys starting with a given prefix."""
        # Memory
        keys_to_remove = [k for k in list(self._memory.keys()) if k.startswith(prefix)]
        for k in keys_to_remove:
            self._memory.pop(k, None)

        # Disk
        if self._enable_disk:
            for path in self._cache_dir.glob(f"{prefix}*"):
                try:
                    path.unlink()
                except OSError:
                    pass

    def clear(self) -> None:
        """Clear all cached data (memory + disk)."""
        self._memory.clear()
        self._disk_meta.clear()
        if self._enable_disk:
            for path in self._cache_dir.glob("*.cache"):
                try:
                    path.unlink()
                except OSError:
                    pass
        logger.info("Cache cleared")

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        disk_count = 0
        disk_size = 0
        if self._enable_disk and self._cache_dir.exists():
            for path in self._cache_dir.glob("*.cache"):
                disk_count += 1
                disk_size += path.stat().st_size

        return {
            "memory_items": len(self._memory),
            "memory_maxsize": self._memory.maxsize,
            "disk_items": disk_count,
            "disk_size_bytes": disk_size,
            "disk_enabled": self._enable_disk,
            "cache_dir": str(self._cache_dir),
        }

    # ------------------------------------------------------------------
    # Disk operations
    # ------------------------------------------------------------------
    def _disk_path(self, key: str) -> Path:
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return self._cache_dir / f"{safe_key}.cache"

    def _disk_get(self, key: str) -> Optional[Any]:
        path = self._disk_path(key)
        if not path.exists():
            return None
        try:
            with open(path, "rb") as f:
                entry = pickle.load(f)
            if entry["expires_at"] < time.time():
                path.unlink(missing_ok=True)
                return None
            return entry["value"]
        except (pickle.UnpicklingError, OSError, KeyError, EOFError) as exc:
            logger.warning(f"Disk cache read error for {key}: {exc}")
            path.unlink(missing_ok=True)
            return None

    def _disk_set(self, key: str, value: Any, ttl: int) -> None:
        path = self._disk_path(key)
        entry = {
            "key": key,
            "value": value,
            "created_at": time.time(),
            "expires_at": time.time() + ttl,
        }
        try:
            with open(path, "wb") as f:
                pickle.dump(entry, f, protocol=pickle.HIGHEST_PROTOCOL)
        except (OSError, pickle.PicklingError) as exc:
            logger.warning(f"Disk cache write error for {key}: {exc}")

    def _disk_delete(self, key: str) -> None:
        path = self._disk_path(key)
        path.unlink(missing_ok=True)


# ------------------------------------------------------------------
# Global singleton
# ------------------------------------------------------------------
cache = CacheManager()


# ------------------------------------------------------------------
# Decorator
# ------------------------------------------------------------------
def cached(ttl: int = 300, prefix: str = "") -> Callable[[F], F]:
    """Decorator to cache function results.

    Args:
        ttl: Time-to-live in seconds.
        prefix: Key prefix for grouping/invalidation.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_prefix = prefix or func.__qualname__
            key = _make_cache_key(key_prefix, args, kwargs)
            result = cache.get(key)
            if result is not None:
                return result
            result = func(*args, **kwargs)
            if result is not None:
                cache.set(key, result, ttl=ttl)
            return result

        # Expose invalidation helper
        wrapper.cache_clear = lambda: cache.invalidate_prefix(prefix or func.__qualname__)  # type: ignore
        return wrapper  # type: ignore

    return decorator
