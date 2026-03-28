# Testing Guide

## DayBrief tests: when you need mocks vs `psycopg2`

### Short answer
- `DayBrief` unit tests are intended to run with stubs/mocks and do **not** require a real PostgreSQL connection.
- If a test imports `backend.app.main`, it pulls in a much wider application graph than the DayBrief service itself, including optional runtime dependencies such as `stellium_engine` and, in some environments, database-related packages.
- For pure DayBrief coverage, prefer testing the DayBrief service layer and patching dependencies instead of booting the full app unless you specifically need an API integration test.

### Why the import error is misleading
If you see an error while collecting `tests/test_day_brief.py`, for example:

```text
ImportError while importing test module '/app/tests/test_day_brief.py'
...
from backend.app.main import app
...
from stellium_engine import EqualHouses, PlacidusHouses, WholeSignHouses
ImportError: cannot import name 'EqualHouses' from 'stellium_engine'
```

that failure happens **before** any DayBrief logic needs PostgreSQL. In this case, the blocker is the app-level import chain (`backend.app.main` → `backend.app.engine_utils` → `stellium_engine`), not the DayBrief service itself.

## Recommended test strategy

### 1. DayBrief unit tests
Use stubs/mocks for:
- auth/user context
- feed/day brief builders
- cache/LLM adapters
- any app dependencies unrelated to the DayBrief contract

Recommended scope:
- `backend.app.services.day_brief`
- `backend.app.services.day_brief_types`
- narrowly scoped route tests with patched builders

Prefer running inside the backend container so Python/package versions match the app environment:

```bash
docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py
```

If the route test imports `backend.app.main`, stub heavy imports first or move the test lower in the stack so it exercises DayBrief behavior without loading unrelated engine modules.

### 2. Backend quick verification
After a meaningful backend change, run the required quick profile:

```bash
docker exec astro-project-backend-1 python3 scripts/pipeline.py
```

This is the canonical backend verification command for this repo.

### 3. Integration tests
You need real DB-related dependencies such as `psycopg2` only when the test actually exercises:
- real SQLAlchemy/Postgres wiring
- startup paths that initialize DB access
- integration flows that depend on the live backend container environment

In those cases, do **not** install random packages into the host Python first. Prefer the backend container / project-managed dependency flow.

## When `psycopg2` is required

`psycopg2` is required for tests or runtime flows that use the PostgreSQL driver, typically via `DATABASE_URL=postgresql+psycopg2://...`.

Typical cases:
- integration tests against the real app stack
- DB session / model tests that connect to Postgres
- backend startup or code paths that import DB-backed modules without mocking them out

It is usually **not** required for isolated DayBrief unit tests if you mock the DB-facing pieces correctly.

## How to install `psycopg2` correctly

### Preferred: use the backend container
First check whether the backend container already has the dependency set expected by the app:

```bash
docker exec astro-project-backend-1 python3 -c "import psycopg2; print('psycopg2 ok')"
```

If your tests are meant to run in the app environment, run them there instead of on the host:

```bash
docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py
```

### If the project manages dependencies with Poetry
Install from the backend environment, not ad hoc from the host:

```bash
docker exec astro-project-backend-1 poetry add psycopg2-binary
```

or, if it is already declared and just needs syncing:

```bash
docker exec astro-project-backend-1 poetry install
```

### If the project uses `requirements*.txt`
Add the dependency to the appropriate requirements file and rebuild/sync the backend environment, for example:

```bash
docker exec astro-project-backend-1 pip install psycopg2-binary
```

Use this only as a short-lived local fix unless the dependency is also recorded in the project dependency manifest.

## Mocking guidance for DayBrief tests

Prefer mocking at the seam closest to the behavior you care about:
- patch `build_day_brief_payload` / `build_day_brief_fallback` for route tests
- patch LLM/cache helpers in `feed_service` when verifying API shape
- avoid importing the whole FastAPI app if a service-level test is enough

Good fit for mocking:
- DTO/schema validation
- fallback behavior
- premium-state mapping
- explainability payload shaping
- cache hit/miss behavior at the service boundary

Bad fit for full-app imports:
- tests that only assert DayBrief JSON shape
- tests that do not need router registration/startup behavior

## Practical answer to the original question
- For `DayBrief` unit tests: **mock DB-related dependencies differently; do not treat `psycopg2` as required by default.**
- For integration tests that intentionally boot real backend wiring: **install/use `psycopg2` in the backend container via the project dependency manager.**
- If the immediate failure is the `stellium_engine` import chain, fix the test boundary first; installing `psycopg2` will not solve that specific collection error.
