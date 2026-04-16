# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS

## Summary
Align strict-GRACE contracts, semantic blocks, and packet-local observability attribution for WeekBrief payload and envelope handling without changing WeekBrief semantics.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/backend/app/services/week_brief_service.py
- /opt/astro-project/tests/test_week_brief_service.py
- /opt/astro-project/tests/test_week_brief_api.py

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/requirements.slice.backend-active-slice-grace-canon-sync.xml
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/development-plan.slice.backend-active-slice-grace-canon-sync.xml

## Acceptance Criteria
- week_brief_service.py exposes strict-GRACE module contract, module map, required function contracts, and semantic START/END blocks.
- WeekBrief payload and envelope semantics remain unchanged.
- WeekBrief public entrypoints remain stable.
- WeekBrief emitted evidence includes packet-local lane/scope plus request, trace, correlation, module, function, and block attribution.
- Tests cover updated contract/addressability expectations where appropriate without loosening existing business assertions.
- No frontend files and no frozen-scope backend files are modified.

## Verification Profile
- backend: Run targeted WeekBrief tests and backend quick after this packet or as part of combined W01 verification.
- frontend: Not applicable; frontend is frozen and must not be touched.
- observability: Post-test evidence for WeekBrief paths must be attributable by module/function/block names and packet-local lane/scope; W01 does not claim canonical today-week closeout.
- execution: {'backend_commands': ['docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py tests/test_week_brief_api.py', 'docker exec astro-project-backend-1 python3 scripts/pipeline.py'], 'frontend_commands': [], 'observability_commands': ['python3 tools/post_test_review.py --profile read-only --since 30m --report-format md'], 'touches_frontend': False, 'requires_frontend_visual': False, 'artifact_globs': ['/opt/astro-project/test-results/**/*', '/opt/astro-project/logs/**/*', '/opt/astro-project/backend/logs/**/*']}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Diff is limited to WeekBrief service and declared WeekBrief tests.
- Reviewer can identify stable module/function/block names for WeekBrief payload and envelope handling.
- No WeekBrief business semantic change is introduced.
- Targeted tests are green or a precise blocker is documented.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS

## Notes
- Do not widen into frontend visual proof work.
- Do not change WeekBrief response semantics.
