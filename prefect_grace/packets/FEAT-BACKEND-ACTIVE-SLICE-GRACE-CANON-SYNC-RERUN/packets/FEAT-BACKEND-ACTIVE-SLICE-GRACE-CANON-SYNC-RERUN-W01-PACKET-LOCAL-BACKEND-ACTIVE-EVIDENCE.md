# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-PACKET-LOCAL-BACKEND-ACTIVE-EVIDENCE

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-PACKET-LOCAL-BACKEND-ACTIVE-EVIDENCE`

## Summary
Run the inherited packet-local verification lane for the completed W01 implementation and record read-only evidence without claiming canonical Today/Week closeout.

## Wave
W01

## Role
verifier

## Reasoning
high

## Write Scope
- Packet-local verification evidence for the completed W01 backend active-slice rerun

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-DAY-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-WEEK-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-SCHEDULER-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-ANALYTICS-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-API-GATEWAY-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md

## Acceptance Criteria
- The exact backend quick, targeted active-slice pytest, and packet-local observability commands are recorded with PASS or FAIL outcomes.
- The packet-local observability verdict is explicit and does not claim canonical Today/Week closeout.
- Packet-local evidence is attributable by module/function/block names for the touched active-slice paths, or the exact unreadable gap is recorded.
- Any scheduler or analytics evidence gap is explicit rather than hidden.
- No frontend commands are run.

## Verification Profile
- backend: Run backend quick and the full inherited active-slice targeted backend suite for packet-local verification.
- frontend: Not applicable; frontend/UI is frozen and untouched.
- observability: Review packet-local read-only evidence only and record a verdict without using canonical Today/Week ownership.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 scripts/pipeline.py
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_service.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py
  - frontend_commands:
  - observability_scope: packet_local
  - canonical_flow_commands:
  - observability_commands:
    - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
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
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- observability_scope: packet_local
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
- Block if green tests are reported without packet-local evidence review.
- Block if the verifier uses canonical Today/Week review instead of the packet-local lane.
- Block if evidence gaps are implicit, fragmented, or unlabeled.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-DAY-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-WEEK-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-SCHEDULER-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-ANALYTICS-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-API-GATEWAY-CONTRACTS

## Notes
- This packet owns the W01 evidence split promised by architect formalization: packet-local only, read-only only.
