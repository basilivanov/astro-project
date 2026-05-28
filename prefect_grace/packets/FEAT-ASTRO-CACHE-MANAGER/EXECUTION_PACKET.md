# Execution Packet: FEAT-ASTRO-CACHE-MANAGER-W01-LRU-CACHE

## Objective

Implement a thread-safe LRU (Least Recently Used) cache manager with TTL support.
This packet creates a production-ready caching system with expiration, size limits, and statistics.

## Slice

- slice_id: `SLICE-ASTRO-CACHE-MANAGER`
- slice_slug: `astro-cache-manager`
- feature_id: `FEAT-ASTRO-CACHE-MANAGER`
- packet_id: `FEAT-ASTRO-CACHE-MANAGER-W01-LRU-CACHE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-ASTRO-INFRASTRUCTURE-MVP`
- depends_on: ``
- feature_dir: `prefect_grace/packets/FEAT-ASTRO-CACHE-MANAGER`

## Source Of Truth

- `backend/app/cache/lru_cache.py` (will be created)
- `backend/app/cache/cache_entry.py` (will be created)
- `backend/tests/test_lru_cache.py` (will be created)

## Impacted Modules

- `M-ASTRO-BACKEND-CACHE`
- `M-ASTRO-BACKEND-TESTS`

## Allowed Write Scope

- `backend/app/cache/lru_cache.py`
- `backend/app/cache/cache_entry.py`
- `backend/app/cache/__init__.py`
- `backend/tests/test_lru_cache.py`
- `prefect_grace/packets/FEAT-ASTRO-CACHE-MANAGER/**`

## Frozen Scope

- `frontend/**`
- `scripts/pipeline.py`
- `prefect_grace/platform/**`
- `prefect_grace/flows/**`
- `prefect_grace/tasks/**`
- `backend/app/api/**`
- `backend/app/models/**`

## Must Preserve

- Thread-safety is critical
- No breaking changes to existing code
- All tests must pass
- Memory-efficient implementation
- No external dependencies beyond standard library

## Recommended Role Assignment

- coder: `Codex high`; complex threading and data structures
- verifier: `Codex high`; concurrency and edge case testing
- reviewer: `Codex high`; thread-safety and performance review
- rework policy: standard resume for concurrency issues

## Required Design Decisions

### 1. CacheEntry Model

Create `backend/app/cache/cache_entry.py`:

- `key: str` - cache key
- `value: Any` - cached value
- `created_at: float` - creation timestamp
- `accessed_at: float` - last access timestamp
- `ttl: float | None` - time-to-live in seconds (None = no expiration)
- `is_expired() -> bool` - check if entry has expired

### 2. LRUCache Implementation

Create `backend/app/cache/lru_cache.py` with LRUCache class:

- `__init__(max_size: int = 100, default_ttl: float | None = None)` - initialize cache
- `get(key: str) -> Any | None` - retrieve value, update access time, return None if expired/missing
- `set(key: str, value: Any, ttl: float | None = None)` - store value with optional TTL
- `delete(key: str) -> bool` - remove entry, return True if existed
- `clear()` - remove all entries
- `size() -> int` - current number of entries
- `get_stats() -> dict` - return hits, misses, evictions, size
- Thread-safe using threading.Lock
- Evict LRU entry when max_size reached
- Auto-remove expired entries on access

### 3. LRU Eviction Policy

- Use OrderedDict to track access order
- Move to end on access (get)
- Evict oldest (first) entry when size limit reached
- Track eviction count in statistics

### 4. Test Coverage

Create `backend/tests/test_lru_cache.py`:

- Test basic get/set operations
- Test LRU eviction when max_size reached
- Test TTL expiration
- Test delete and clear operations
- Test statistics tracking (hits, misses, evictions)
- Test thread-safety with concurrent access (10+ threads)
- Test edge cases (None values, empty cache, duplicate keys)
- Test memory efficiency with large datasets

## Implementation Requirements

1. Create CacheEntry dataclass with expiration logic
2. Implement thread-safe LRUCache with OrderedDict
3. Add comprehensive statistics tracking
4. Implement TTL expiration checking
5. Add unit tests with concurrency testing
6. Use Python type hints throughout
7. Follow PEP 8 style guidelines

## Acceptance Criteria

- LRUCache fully implemented with all methods
- Thread-safe implementation verified
- TTL expiration working correctly
- LRU eviction policy working
- All tests pass (minimum 12 test cases)
- Statistics tracking accurate
- No external dependencies added
- No memory leaks

## Verification

Run unit tests:

```bash
cd /opt/astro-project/backend
python -m pytest tests/test_lru_cache.py -v
```

Run concurrency stress test:

```bash
cd /opt/astro-project/backend
python -m pytest tests/test_lru_cache.py::test_thread_safety -v -s
```

Run linting:

```bash
cd /opt/astro-project/backend
python -m pylint app/cache/lru_cache.py app/cache/cache_entry.py
```

## Expected Evidence

- Test output showing all tests passed (minimum 12 tests)
- Concurrency test showing thread-safety
- Linting output showing no critical errors
- Performance metrics (cache hit rate, eviction rate)

## Escalation Triggers

- Thread-safety issues detected
- Memory leaks in cache
- Tests fail
- Performance degradation
- Linting shows critical errors
