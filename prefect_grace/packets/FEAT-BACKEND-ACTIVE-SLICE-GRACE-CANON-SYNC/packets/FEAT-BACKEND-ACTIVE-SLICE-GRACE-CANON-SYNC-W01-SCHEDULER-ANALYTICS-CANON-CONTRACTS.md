# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-SCHEDULER-ANALYTICS-CANON-CONTRACTS

## Summary
Align strict-GRACE contracts and semantic blocks for scheduler jobs and analytics event persistence without changing job or analytics semantics.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/backend/app/services/scheduler.py
- /opt/astro-project/backend/app/services/analytics.py
- /opt/astro-project/tests/test_billing_scheduler.py

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/knowledge-graph.slice.backend-active-slice-grace-canon-sync.xml
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md

## Acceptance Criteria
- scheduler.py exposes strict-GRACE module contract, module map, required function contracts, and semantic START/END blocks for job markers.
- analytics.py exposes strict-GRACE module contract, module map, required function contracts, and semantic START/END blocks for analytics event markers.
- Scheduler job semantics and analytics writes remain unchanged.
- Any scheduler or analytics evidence gap not naturally emitted by W01 verification is explicitly documented for verifier handling.
- No frontend files and no frozen-scope backend files are modified.

## Verification Profile
- backend: Run targeted scheduler test and backend quick after this packet or as part of combined W01 verification.
- frontend: Not applicable; frontend is frozen and must not be touched.
- observability: Post-test evidence must either include scheduler/analytics attribution or explicitly record why the targeted run did not emit those paths.
- execution: {'backend_commands': ['docker exec astro-project-backend-1 python3 -m pytest -q tests/test_billing_scheduler.py', 'docker exec astro-project-backend-1 python3 scripts/pipeline.py'], 'frontend_commands': [], 'observability_commands': ['python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'], 'touches_frontend': False, 'requires_frontend_visual': False, 'artifact_globs': ['/opt/astro-project/test-results/**/*', '/opt/astro-project/logs/**/*', '/opt/astro-project/backend/logs/**/*']}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Diff is limited to scheduler, analytics, and declared scheduler test file.
- Reviewer can identify stable module/function/block names for scheduler and analytics paths.
- No billing, access control, database model, or analytics write semantic change is introduced.
- Scheduler or analytics observability gaps are explicitly documented if evidence is not emitted by tests.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS

## Notes
- billing.py, models.py, and db.py are frozen and must not be touched.
- Do not widen into an observability redesign.
