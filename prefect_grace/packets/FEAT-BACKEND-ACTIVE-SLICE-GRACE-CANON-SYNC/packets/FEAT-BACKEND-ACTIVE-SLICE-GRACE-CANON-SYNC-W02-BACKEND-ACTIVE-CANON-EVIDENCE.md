# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W02-BACKEND-ACTIVE-CANON-EVIDENCE

## Summary
Run the slice verification lanes and record deterministic backend and observability evidence for the completed W01 implementation.

## Wave
W02

## Role
verifier

## Reasoning
high

## Write Scope
-

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-DAY-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-WEEK-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-SCHEDULER-ANALYTICS-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-API-GATEWAY-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md

## Acceptance Criteria
- backend:quick command passes or failure is attached with exact failing test and traceback summary.
- Targeted pytest command for Day, Week, logging, catalog logging, and scheduler coverage passes or failure is attached with exact failing test and traceback summary.
- Post-test observability command completes and yields a verdict of clean or degraded-but-expected.
- If observability evidence is absent, fragmented, or unexpectedly degraded, verifier returns no-evidence-blocker or unexpected-degradation and blocks acceptance.
- No frontend commands are run because frontend is frozen and untouched.

## Verification Profile
- backend: Execute backend quick and targeted pytest for VM-BACKEND-ACTIVE-CANON-STRUCTURE and VM-BACKEND-ACTIVE-CANON-PIPELINE.
- frontend: Not applicable; frontend is frozen and must remain untouched.
- observability: Execute today-week post-test review and classify the observability verdict as clean, degraded-but-expected, unexpected-degradation, or no-evidence-blocker.
- execution: {'backend_commands': ['docker exec astro-project-backend-1 python3 scripts/pipeline.py', 'docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py'], 'frontend_commands': [], 'observability_commands': ['python3 tools/post_test_review.py --profile today-week --since 30m --report-format md'], 'touches_frontend': False, 'requires_frontend_visual': False, 'artifact_globs': ['/opt/astro-project/test-results/**/*', '/opt/astro-project/logs/**/*', '/opt/astro-project/backend/logs/**/*', '/opt/astro-project/reports/**/*', '/opt/astro-project/artifacts/**/*']}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_commands:
  - docker exec astro-project-backend-1 python3 scripts/pipeline.py
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py
- observability_commands:
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- touches_frontend: False
- requires_frontend_visual: False
- artifact_globs:
  - /opt/astro-project/test-results/**/*
  - /opt/astro-project/logs/**/*
  - /opt/astro-project/backend/logs/**/*
  - /opt/astro-project/reports/**/*
  - /opt/astro-project/artifacts/**/*
- include_day_live_canary: False

## Reviewer Gate
- Verifier must report exact commands, PASS/FAIL result, and observability verdict.
- Verifier must not treat green tests alone as acceptance without post-test evidence review.
- Verifier must identify any scheduler or analytics evidence gap explicitly.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-DAY-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-WEEK-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-SCHEDULER-ANALYTICS-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-API-GATEWAY-CONTRACTS

## Notes
- This packet has no write scope; it records verification evidence only.
- Frontend visual evidence is not required because frontend is frozen and not touched.
