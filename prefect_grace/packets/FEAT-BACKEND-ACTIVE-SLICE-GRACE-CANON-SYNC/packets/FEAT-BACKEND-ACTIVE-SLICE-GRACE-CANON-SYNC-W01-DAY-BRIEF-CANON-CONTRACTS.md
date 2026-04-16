# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-DAY-BRIEF-CANON-CONTRACTS

## Summary
Align strict-GRACE contracts and semantic blocks for DayBrief assembly and validation without changing DayBrief payload semantics.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/backend/app/services/day_brief.py
- /opt/astro-project/backend/app/services/day_brief_validators.py
- /opt/astro-project/tests/test_day_brief.py
- /opt/astro-project/tests/test_day_brief_schema.py

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/requirements.slice.backend-active-slice-grace-canon-sync.xml
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/development-plan.slice.backend-active-slice-grace-canon-sync.xml

## Acceptance Criteria
- day_brief.py exposes strict-GRACE module contract, module map, required function contracts, and semantic START/END blocks.
- day_brief_validators.py exposes strict-GRACE module contract, module map, required function contracts, and semantic START/END blocks.
- DayBrief payload semantics, scoring behavior, validation behavior, and public entrypoints remain unchanged.
- Tests cover the updated contract/addressability expectations where appropriate without loosening existing business assertions.
- No frontend files and no frozen-scope backend files are modified.

## Verification Profile
- backend: Run targeted DayBrief tests and backend quick after this packet or as part of combined W01 verification.
- frontend: Not applicable; frontend is frozen and must not be touched.
- observability: Post-test evidence for Today/DayBrief paths must be attributable by module/function/block names.
- execution: {'backend_commands': ['docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py', 'docker exec astro-project-backend-1 python3 scripts/pipeline.py'], 'frontend_commands': [], 'observability_commands': ['python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'], 'touches_frontend': False, 'requires_frontend_visual': False, 'artifact_globs': ['/opt/astro-project/test-results/**/*', '/opt/astro-project/logs/**/*', '/opt/astro-project/backend/logs/**/*']}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Diff is limited to DayBrief service, validator, and declared DayBrief tests.
- Reviewer can identify stable module/function/block names for DayBrief assembly and validation.
- No scoring, schema, or payload semantic change is introduced.
- Targeted tests are green or a precise blocker is documented.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS

## Notes
- Treat existing well-marked backend modules as the style reference.
- If a function contract creates semantic risk, keep behavior unchanged and document the remaining canon gap.
