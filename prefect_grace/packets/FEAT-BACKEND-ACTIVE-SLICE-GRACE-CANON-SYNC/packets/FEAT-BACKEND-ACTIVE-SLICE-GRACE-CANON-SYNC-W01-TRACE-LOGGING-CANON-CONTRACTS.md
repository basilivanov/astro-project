# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-TRACE-LOGGING-CANON-CONTRACTS

## Summary
Align strict-GRACE module contracts, module map, function contracts where required, and semantic block names for correlation and logging payload shaping only.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/backend/app/logging_utils.py
- /opt/astro-project/backend/app/middleware/correlation.py
- /opt/astro-project/tests/test_logging_utils_grace.py
- /opt/astro-project/tests/test_catalog_logging.py

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-ARCHITECT-FORMALIZATION
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/architect_manifest.json
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/EXECUTION_PACKET.md
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md

## Acceptance Criteria
- logging_utils.py exposes strict-GRACE module contract, module map, and stable semantic block markers aligned with local repository style.
- correlation.py exposes strict-GRACE module contract, module map, and stable semantic block markers aligned with local repository style.
- Function contracts are added only for exported, orchestration, or side-effect entrypoints required by the local strict-GRACE style.
- Correlation ID and structured logging payload behavior remain semantically unchanged.
- No frontend files and no frozen-scope backend files are modified.

## Verification Profile
- backend: Run targeted trace/logging tests and backend quick after this packet or as part of the combined W01 verification.
- frontend: Not applicable; frontend is frozen and must not be touched.
- observability: Evidence must show correlation/logging records can be attributed by module/function/block names, or a gap must be recorded for verifier/reviewer handling.
- execution: {'backend_commands': ['docker exec astro-project-backend-1 python3 -m pytest -q tests/test_logging_utils_grace.py tests/test_catalog_logging.py', 'docker exec astro-project-backend-1 python3 scripts/pipeline.py'], 'frontend_commands': [], 'observability_commands': ['python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'], 'touches_frontend': False, 'requires_frontend_visual': False, 'artifact_globs': ['/opt/astro-project/test-results/**/*', '/opt/astro-project/playwright-report/**/*', '/opt/astro-project/logs/**/*', '/opt/astro-project/backend/logs/**/*']}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Diff is limited to trace/logging write scope files listed in this packet.
- No logging transport redesign, middleware architecture rewrite, or catalog_logging.py rewrite is introduced.
- Tests or existing assertions cover the strict-GRACE trace/logging contract expectations.
- Any observability evidence gap is explicit and does not hide changed runtime behavior.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-PLANNER-SLICING

## Notes
- Architect open decision: keep current inline middleware unless consolidation onto CorrelationIdMiddleware is proven safe and remains marker-only.
- Do not widen into maximal logging rewrite.
