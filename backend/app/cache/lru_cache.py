"""Thread-safe LRU cache with TTL support."""

from __future__ import annotations

from collections import OrderedDict
from threading import Lock
from time import monotonic
from typing import Any

from app.cache.cache_entry import CacheEntry


class LRUCache:
    """A bounded, thread-safe LRU cache with optional TTL expiration."""

    def __init__(self, max_size: int = 100, default_ttl: float | None = None):
        if max_size <= 0:
            raise ValueError("max_size must be greater than 0")
        if default_ttl is not None and default_ttl < 0:
            raise ValueError("default_ttl must be non-negative or None")

        self._max_size = max_size
        self._default_ttl = default_ttl
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Any | None:
        """Return a cached value, or None when the key is missing or expired."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired():
                del self._entries[key]
                self._misses += 1
                return None

            entry.accessed_at = monotonic()
            self._entries.move_to_end(key)
            self._hits += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: float | None = None) -> None:
        """Store a value under key, updating LRU order and evicting if needed."""
        effective_ttl = self._default_ttl if ttl is None else ttl
        if effective_ttl is not None and effective_ttl < 0:
            raise ValueError("ttl must be non-negative or None")

        with self._lock:
            now = monotonic()
            self._entries[key] = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                accessed_at=now,
                ttl=effective_ttl,
            )
            self._entries.move_to_end(key)

            while len(self._entries) > self._max_size:
                self._entries.popitem(last=False)
                self._evictions += 1

    def delete(self, key: str) -> bool:
        """Remove an entry and return whether it existed."""
        with self._lock:
            if key not in self._entries:
                return False

            del self._entries[key]
            return True

    def clear(self) -> None:
        """Remove all cache entries while preserving statistics."""
        with self._lock:
            self._entries.clear()

    def size(self) -> int:
        """Return the current number of stored entries."""
        with self._lock:
            return len(self._entries)

    def get_stats(self) -> dict[str, int]:
        """Return cache hit, miss, eviction, and size counters."""
        with self._lock:
            return {
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "size": len(self._entries),
            }
