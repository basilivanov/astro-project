# Execution Packet: FEAT-ASTRO-DATE-FORMATTER-TEST-W01-ISO-DATE-UTILS

## Objective

Add a simple ISO date formatting utility to the backend for consistent date handling.
This is a test packet to validate the GRACE orchestrator end-to-end with real code changes.

## Slice

- slice_id: `SLICE-ASTRO-DATE-FORMATTER-TEST`
- slice_slug: `astro-date-formatter-test`
- feature_id: `FEAT-ASTRO-DATE-FORMATTER-TEST`
- packet_id: `FEAT-ASTRO-DATE-FORMATTER-TEST-W01-ISO-DATE-UTILS`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-ASTRO-UTILS-MVP`
- depends_on: ``
- feature_dir: `prefect_grace/packets/FEAT-ASTRO-DATE-FORMATTER-TEST`

## Source Of Truth

- `backend/app/utils/date_utils.py` (will be created)
- `backend/tests/test_date_utils.py` (will be created)

## Impacted Modules

- `M-ASTRO-BACKEND-UTILS`
- `M-ASTRO-BACKEND-TESTS`

## Allowed Write Scope

- `backend/app/utils/date_utils.py`
- `backend/tests/test_date_utils.py`
- `prefect_grace/packets/FEAT-ASTRO-DATE-FORMATTER-TEST/**`

## Frozen Scope

- `frontend/**`
- `scripts/pipeline.py`
- `prefect_grace/platform/**`
- `prefect_grace/flows/**`
- `prefect_grace/tasks/**`

## Must Preserve

- No breaking changes to existing code
- All tests must pass
- Code follows Python best practices
- No external dependencies added

## Recommended Role Assignment

- coder: `Codex medium`; simple utility function
- verifier: `Codex low`; unit tests only
- reviewer: `Codex medium`; code quality check
- rework policy: light resume for style issues

## Required Design Decisions

### 1. Date Utility Functions

Add the following functions to `backend/app/utils/date_utils.py`:

- `format_iso_date(dt: datetime) -> str`: Format datetime to ISO 8601 string
- `parse_iso_date(date_str: str) -> datetime`: Parse ISO 8601 string to datetime
- `get_current_utc() -> datetime`: Get current UTC datetime

### 2. Test Coverage

Add unit tests in `backend/tests/test_date_utils.py`:

- Test format_iso_date with various datetime objects
- Test parse_iso_date with valid and invalid strings
- Test get_current_utc returns UTC timezone

## Implementation Requirements

1. Create `backend/app/utils/date_utils.py` with the three functions
2. Create `backend/tests/test_date_utils.py` with comprehensive tests
3. Ensure all tests pass
4. Follow PEP 8 style guidelines

## Acceptance Criteria

- All three utility functions implemented
- All unit tests pass
- No external dependencies added
- Code is clean and well-documented

## Verification

Run unit tests:

```bash
cd /opt/astro-project/backend
python -m pytest tests/test_date_utils.py -v
```

Run linting:

```bash
cd /opt/astro-project/backend
python -m pylint app/utils/date_utils.py
```

## Expected Evidence

- Unit test output showing all tests passed
- Linting output showing no errors
- Confirmation that no external dependencies were added

## Escalation Triggers

- Tests fail
- Linting shows critical errors
- External dependencies required
