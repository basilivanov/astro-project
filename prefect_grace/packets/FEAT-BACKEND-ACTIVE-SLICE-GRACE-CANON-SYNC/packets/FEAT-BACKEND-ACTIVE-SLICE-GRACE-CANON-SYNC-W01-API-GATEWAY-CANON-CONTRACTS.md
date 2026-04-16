# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-API-GATEWAY-CANON-CONTRACTS

## Summary
Align strict-GRACE contracts and semantic blocks for main.py route, startup, request correlation, and active-slice orchestration markers without changing API behavior.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/backend/app/main.py
- /opt/astro-project/tests/test_week_brief_api.py

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-DAY-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-WEEK-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-SCHEDULER-ANALYTICS-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/ARCHITECT_HANDOFF.md

## Acceptance Criteria
- main.py exposes strict-GRACE module contract, module map, required function contracts, and semantic START/END blocks for route, startup, and orchestration markers.
- Request correlation binding remains behaviorally unchanged unless a safe marker-only consolidation is made within architect boundaries.
- Day, Week, report readout, workflow entrypoint, scheduler, analytics, and correlation/logging references are addressable by stable names where main.py orchestrates them.
- API route behavior, response semantics, and startup semantics remain unchanged.
- No frontend files and no frozen-scope backend files are modified.

## Verification Profile
- backend: Run API-adjacent WeekBrief test and backend quick after this packet or as part of combined W01 verification.
- frontend: Not applicable; frontend is frozen and must not be touched.
- observability: Post-test evidence must show API gateway route/startup/correlation markers can be attributed by module/function/block names when emitted.
- execution: {'backend_commands': ['docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_api.py', 'docker exec astro-project-backend-1 python3 scripts/pipeline.py'], 'frontend_commands': [], 'observability_commands': ['python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'], 'touches_frontend': False, 'requires_frontend_visual': False, 'artifact_globs': ['/opt/astro-project/test-results/**/*', '/opt/astro-project/logs/**/*', '/opt/astro-project/backend/logs/**/*']}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Diff is limited to main.py and declared API-adjacent test file.
- Reviewer can identify stable module/function/block names for route, startup, orchestration, and correlation binding markers.
- No API behavior, route semantics, startup behavior, or response schema changes are introduced.
- No frozen-scope service is modified.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-DAY-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-WEEK-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-SCHEDULER-ANALYTICS-CONTRACTS

## Notes
- This packet is sequenced after service packets so main.py markers can reference stabilized names.
- Do not refactor report_workflow.py.
