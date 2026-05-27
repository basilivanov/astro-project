# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W02-WAVE-FINAL-BACKEND-ACTIVE-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W02:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W02-WAVE-FINAL-BACKEND-ACTIVE-EVIDENCE`

## Summary
Run the canonical W02 verification lane, emit fresh active-slice runtime evidence, and classify the final Today/Week observability verdict.

## Wave
W02

## Role
verifier

## Reasoning
high

## Write Scope
- Wave-final verification evidence for the backend active-slice rerun

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-PACKET-LOCAL-BACKEND-ACTIVE-EVIDENCE
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync-rerun/ARCHITECT_HANDOFF.md

## Acceptance Criteria
- The exact backend quick, targeted active-slice pytest, canonical flow, and canonical observability commands are recorded with PASS or FAIL outcomes.
- Fresh canonical flow commands run before canonical observability review.
- The final observability verdict is recorded as clean, degraded-but-expected, unexpected-degradation, or no-evidence-blocker.
- Latest relevant trace, report, or request identifiers are captured when present in the final evidence.
- Any scheduler or analytics evidence gap is explicit rather than hidden.
- No frontend commands are run.

## Verification Profile
- backend: Run backend quick and the inherited active-slice targeted backend suite again as the deterministic closeout lane.
- frontend: Not applicable; frontend/UI is frozen and untouched.
- observability: Own canonical Today/Week observability for the wave after fresh active-slice runtime emission and classify the verdict explicitly.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 scripts/pipeline.py
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py
  - frontend_commands:
  - observability_scope: wave_final
  - canonical_flow_commands:
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

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_commands:
  - docker exec astro-project-backend-1 python3 scripts/pipeline.py
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py
- observability_commands:
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- canonical_flow_commands:
  - docker exec astro-project-backend-1 python3 scripts/pipeline.py
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py
- observability_scope: wave_final
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
- Block if canonical flow commands were not executed before the Today/Week review.
- Block if the final verdict is unexpected-degradation or no-evidence-blocker.
- Block if green tests are reported without canonical observability review.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-PACKET-LOCAL-BACKEND-ACTIVE-EVIDENCE

## Notes
- This is the only packet that owns canonical Today/Week observability for the rerun slice.
