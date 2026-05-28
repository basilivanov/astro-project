"""Cache entry model with TTL expiration support."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any


@dataclass(slots=True)
class CacheEntry:
    """Single cache value plus timestamps used by the LRU cache."""

    key: str
    value: Any
    created_at: float
    accessed_at: float
    ttl: float | None

    def is_expired(self) -> bool:
        """Return True when the entry has exceeded its configured TTL."""
        if self.ttl is None:
            return False

        return monotonic() - self.created_at >= self.ttl
