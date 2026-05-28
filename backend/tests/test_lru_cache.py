"""Tests for the backend LRU cache implementation."""

from __future__ import annotations

import threading
import time

import pytest

from app.cache import CacheEntry, LRUCache


def test_basic_get_and_set_operations():
    cache = LRUCache(max_size=2)

    cache.set("first", "value")

    assert cache.get("first") == "value"
    assert cache.size() == 1


def test_missing_key_returns_none_and_records_miss():
    cache = LRUCache()

    assert cache.get("missing") is None
    assert cache.get_stats()["misses"] == 1


def test_lru_eviction_removes_oldest_entry():
    cache = LRUCache(max_size=2)
    cache.set("first", 1)
    cache.set("second", 2)

    cache.get("first")
    cache.set("third", 3)

    assert cache.get("second") is None
    assert cache.get("first") == 1
    assert cache.get("third") == 3
    assert cache.get_stats()["evictions"] == 1


def test_duplicate_key_updates_value_without_growing_cache():
    cache = LRUCache(max_size=2)

    cache.set("key", "old")
    cache.set("key", "new")

    assert cache.get("key") == "new"
    assert cache.size() == 1
    assert cache.get_stats()["evictions"] == 0


def test_updated_key_becomes_most_recently_used():
    cache = LRUCache(max_size=2)
    cache.set("first", 1)
    cache.set("second", 2)

    cache.set("first", 10)
    cache.set("third", 3)

    assert cache.get("second") is None
    assert cache.get("first") == 10
    assert cache.get("third") == 3


def test_ttl_expiration_removes_entry_on_access():
    cache = LRUCache(max_size=2)

    cache.set("short", "value", ttl=0.01)
    time.sleep(0.03)

    assert cache.get("short") is None
    assert cache.size() == 0
    assert cache.get_stats()["misses"] == 1


def test_default_ttl_is_used_when_entry_ttl_is_not_provided():
    cache = LRUCache(default_ttl=0.01)

    cache.set("short", "value")
    time.sleep(0.03)

    assert cache.get("short") is None


def test_entry_with_no_ttl_does_not_expire():
    now = time.monotonic()
    entry = CacheEntry(
        key="persistent",
        value="value",
        created_at=now,
        accessed_at=now,
        ttl=None,
    )

    assert entry.is_expired() is False


def test_delete_removes_existing_entry_and_reports_result():
    cache = LRUCache()
    cache.set("key", "value")

    assert cache.delete("key") is True
    assert cache.delete("key") is False
    assert cache.get("key") is None


def test_clear_removes_entries_but_preserves_statistics():
    cache = LRUCache(max_size=1)
    cache.set("first", 1)
    cache.get("first")
    cache.set("second", 2)

    cache.clear()

    stats = cache.get_stats()
    assert cache.size() == 0
    assert stats["hits"] == 1
    assert stats["evictions"] == 1


def test_statistics_tracking_counts_hits_misses_evictions_and_size():
    cache = LRUCache(max_size=1)

    cache.set("first", 1)
    assert cache.get("first") == 1
    assert cache.get("missing") is None
    cache.set("second", 2)

    assert cache.get_stats() == {
        "hits": 1,
        "misses": 1,
        "evictions": 1,
        "size": 1,
    }


def test_none_value_is_supported_as_cached_value():
    cache = LRUCache()

    cache.set("none", None)

    assert cache.get("none") is None
    assert cache.get_stats()["hits"] == 1


def test_empty_cache_delete_clear_and_size_are_stable():
    cache = LRUCache()

    cache.clear()

    assert cache.delete("missing") is False
    assert cache.size() == 0
    assert cache.get_stats()["size"] == 0


def test_invalid_sizes_and_ttls_are_rejected():
    with pytest.raises(ValueError):
        LRUCache(max_size=0)
    with pytest.raises(ValueError):
        LRUCache(default_ttl=-1)

    cache = LRUCache()
    with pytest.raises(ValueError):
        cache.set("key", "value", ttl=-1)


def test_memory_efficiency_with_large_dataset_respects_max_size():
    cache = LRUCache(max_size=100)

    for index in range(1_000):
        cache.set(f"key-{index}", index)

    assert cache.size() == 100
    assert cache.get("key-899") is None
    assert cache.get("key-900") == 900
    assert cache.get_stats()["evictions"] == 900


def test_thread_safety():
    cache = LRUCache(max_size=75, default_ttl=10)
    errors: list[BaseException] = []
    start = threading.Barrier(11)

    def worker(worker_id: int) -> None:
        try:
            start.wait()
            for index in range(250):
                key = f"key-{(worker_id * 250 + index) % 150}"
                cache.set(key, (worker_id, index))
                cache.get(key)
                if index % 5 == 0:
                    cache.delete(f"key-{(index + worker_id) % 150}")
        except BaseException as exc:  # pragma: no cover - surfaced by assertion
            errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=(worker_id,))
        for worker_id in range(10)
    ]

    for thread in threads:
        thread.start()
    start.wait()
    for thread in threads:
        thread.join()

    assert errors == []
    assert cache.size() <= 75
    stats = cache.get_stats()
    assert stats["hits"] > 0
    assert stats["evictions"] > 0
    assert stats["size"] == cache.size()
