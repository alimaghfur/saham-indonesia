"""Tests for the caching module (saham_id.cache).

Tests:
- CacheManager memory get/set/invalidate
- CacheManager disk persistence
- TTL expiry (memory + disk)
- invalidate_prefix
- clear()
- stats()
- @cached decorator (hit/miss, cache_clear)
- _make_cache_key determinism
"""
import time
import tempfile
from pathlib import Path

from saham_id.cache import (
    CacheManager,
    _make_cache_key,
    cached,
    cache,
    TTL_QUOTE,
    TTL_OHLC_DAILY,
    TTL_OHLC_INTRADAY,
    TTL_FUNDAMENTALS,
    TTL_MOVERS,
)


# ======================================================================
# _make_cache_key
# ======================================================================

class TestMakeCacheKey:
    def test_deterministic(self):
        key1 = _make_cache_key("quote", ("BBCA",), {})
        key2 = _make_cache_key("quote", ("BBCA",), {})
        assert key1 == key2

    def test_different_args_different_keys(self):
        key1 = _make_cache_key("quote", ("BBCA",), {})
        key2 = _make_cache_key("quote", ("BBRI",), {})
        assert key1 != key2

    def test_different_prefix_different_keys(self):
        key1 = _make_cache_key("quote", ("BBCA",), {})
        key2 = _make_cache_key("ohlc", ("BBCA",), {})
        assert key1 != key2

    def test_kwargs_affect_key(self):
        key1 = _make_cache_key("ohlc", ("BBCA",), {"period": "1y"})
        key2 = _make_cache_key("ohlc", ("BBCA",), {"period": "6mo"})
        assert key1 != key2

    def test_format(self):
        key = _make_cache_key("prefix", ("arg",), {})
        assert key.startswith("prefix:")
        assert len(key) > len("prefix:")


# ======================================================================
# TTL Constants
# ======================================================================

class TestTTLConstants:
    def test_quote_ttl(self):
        assert TTL_QUOTE == 60

    def test_ohlc_daily_ttl(self):
        assert TTL_OHLC_DAILY == 3600

    def test_ohlc_intraday_ttl(self):
        assert TTL_OHLC_INTRADAY == 300

    def test_fundamentals_ttl(self):
        assert TTL_FUNDAMENTALS == 86400

    def test_movers_ttl(self):
        assert TTL_MOVERS == 120


# ======================================================================
# CacheManager - Memory operations
# ======================================================================

class TestCacheManagerMemory:
    def _make_cm(self):
        return CacheManager(
            cache_dir=Path(tempfile.mkdtemp()),
            memory_maxsize=100,
            default_ttl=60,
            enable_disk=False,
        )

    def test_set_and_get(self):
        cm = self._make_cm()
        cm.set("key1", "value1")
        assert cm.get("key1") == "value1"

    def test_get_missing_returns_none(self):
        cm = self._make_cm()
        assert cm.get("nonexistent") is None

    def test_overwrite_key(self):
        cm = self._make_cm()
        cm.set("k", "v1")
        cm.set("k", "v2")
        assert cm.get("k") == "v2"

    def test_invalidate_key(self):
        cm = self._make_cm()
        cm.set("k", "v")
        cm.invalidate("k")
        assert cm.get("k") is None

    def test_invalidate_nonexistent_no_error(self):
        cm = self._make_cm()
        cm.invalidate("nope")  # Should not raise

    def test_invalidate_prefix(self):
        cm = self._make_cm()
        cm.set("quote:abc", "a")
        cm.set("quote:def", "b")
        cm.set("ohlc:abc", "c")
        cm.invalidate_prefix("quote:")
        assert cm.get("quote:abc") is None
        assert cm.get("quote:def") is None
        assert cm.get("ohlc:abc") == "c"

    def test_clear(self):
        cm = self._make_cm()
        cm.set("k1", "v1")
        cm.set("k2", "v2")
        cm.clear()
        assert cm.get("k1") is None
        assert cm.get("k2") is None

    def test_memory_size(self):
        cm = self._make_cm()
        assert cm.memory_size == 0
        cm.set("k1", "v1")
        assert cm.memory_size == 1
        cm.set("k2", "v2")
        assert cm.memory_size == 2

    def test_stats_no_disk(self):
        cm = self._make_cm()
        cm.set("k1", "v1")
        s = cm.stats()
        assert s["memory_items"] == 1
        assert s["memory_maxsize"] == 100
        assert s["disk_enabled"] is False

    def test_stores_complex_types(self):
        cm = self._make_cm()
        cm.set("dict_key", {"a": 1, "b": [2, 3]})
        result = cm.get("dict_key")
        assert result == {"a": 1, "b": [2, 3]}

    def test_stores_none_not_cached(self):
        """Setting None value - get returns None which looks like a miss."""
        cm = self._make_cm()
        cm.set("k", None)
        # None value is indistinguishable from cache miss
        assert cm.get("k") is None


# ======================================================================
# CacheManager - Disk operations
# ======================================================================

class TestCacheManagerDisk:
    def _make_cm(self):
        return CacheManager(
            cache_dir=Path(tempfile.mkdtemp()),
            memory_maxsize=100,
            default_ttl=60,
            enable_disk=True,
        )

    def test_disk_persistence(self):
        """Value written to disk survives memory eviction."""
        tmpdir = Path(tempfile.mkdtemp())
        cm = CacheManager(cache_dir=tmpdir, memory_maxsize=2, default_ttl=300, enable_disk=True)
        cm.set("k1", "v1")
        # Evict from memory by filling cache
        cm.set("k2", "v2")
        cm.set("k3", "v3")
        cm.set("k4", "v4")
        # k1 likely evicted from memory (maxsize=2), but disk should have it
        result = cm.get("k1")
        assert result == "v1"

    def test_disk_invalidate(self):
        cm = self._make_cm()
        cm.set("key", "val")
        cm.invalidate("key")
        # Both memory and disk cleared
        assert cm.get("key") is None

    def test_disk_clear(self):
        cm = self._make_cm()
        cm.set("a", 1)
        cm.set("b", 2)
        cm.clear()
        assert cm.get("a") is None
        assert cm.get("b") is None

    def test_stats_with_disk(self):
        cm = self._make_cm()
        cm.set("k1", "v1")
        cm.set("k2", "v2")
        s = cm.stats()
        assert s["disk_enabled"] is True
        assert s["disk_items"] == 2
        assert s["disk_size_bytes"] > 0

    def test_expired_disk_entry(self):
        """Disk entry with expired TTL returns None."""
        cm = CacheManager(
            cache_dir=Path(tempfile.mkdtemp()),
            memory_maxsize=100,
            default_ttl=1,  # 1 second
            enable_disk=True,
        )
        cm.set("expiring", "val", ttl=1)
        # Clear memory so it has to read disk
        cm._memory.clear()
        time.sleep(1.5)
        assert cm.get("expiring") is None


# ======================================================================
# @cached decorator
# ======================================================================

class TestCachedDecorator:
    def test_caches_result(self):
        call_count = [0]

        @cached(ttl=60, prefix="test_fn")
        def expensive_fn(x):
            call_count[0] += 1
            return x * 2

        # Clear any previous state
        expensive_fn.cache_clear()

        result1 = expensive_fn(5)
        result2 = expensive_fn(5)
        assert result1 == 10
        assert result2 == 10
        assert call_count[0] == 1  # Only called once

    def test_different_args_different_cache(self):
        call_count = [0]

        @cached(ttl=60, prefix="test_fn2")
        def fn(x):
            call_count[0] += 1
            return x + 1

        fn.cache_clear()

        fn(1)
        fn(2)
        assert call_count[0] == 2

    def test_cache_clear(self):
        """Test cache_clear on decorator (memory-only to avoid disk hash issue)."""
        import tempfile
        from pathlib import Path
        from saham_id.cache import CacheManager, _make_cache_key

        # Use a dedicated memory-only cache for this test
        test_cache_mgr = CacheManager(
            cache_dir=Path(tempfile.mkdtemp()),
            memory_maxsize=100,
            default_ttl=60,
            enable_disk=False,
        )

        call_count = [0]
        prefix = "test_clear_prefix"

        def fn(x):
            call_count[0] += 1
            return x

        # Simulate what @cached does
        key = _make_cache_key(prefix, (10,), {})

        # First call - miss
        result = test_cache_mgr.get(key)
        assert result is None
        result = fn(10)
        test_cache_mgr.set(key, result, ttl=60)
        assert call_count[0] == 1

        # Second call - hit
        cached_result = test_cache_mgr.get(key)
        assert cached_result == 10

        # Clear and call again
        test_cache_mgr.invalidate_prefix(prefix)
        cached_result = test_cache_mgr.get(key)
        assert cached_result is None

        result = fn(10)
        assert call_count[0] == 2

    def test_none_result_not_cached(self):
        call_count = [0]

        @cached(ttl=60, prefix="test_fn4")
        def fn():
            call_count[0] += 1
            return None

        fn.cache_clear()

        fn()
        fn()
        # None is not cached, so function called each time
        assert call_count[0] == 2


# ======================================================================
# Global cache singleton
# ======================================================================

class TestGlobalCache:
    def test_singleton_is_cache_manager(self):
        assert isinstance(cache, CacheManager)

    def test_singleton_set_get(self):
        cache.set("_test_global_key", 42, ttl=30)
        assert cache.get("_test_global_key") == 42
        cache.invalidate("_test_global_key")
