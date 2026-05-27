# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-WEEK-BRIEF-CANON-CONTRACTS

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-WEEK-BRIEF-CANON-CONTRACTS`

## Summary
Align strict-GRACE contracts and semantic blocks for WeekBrief service logic without changing Week response semantics.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/backend/app/services/week_brief_service.py
- /opt/astro-project/tests/test_week_brief_service.py

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/architect_manifest.json

## Acceptance Criteria
- week_brief_service.py exposes strict-GRACE module contracts, module maps, required function contracts, and stable semantic START/END blocks.
- Week payload and envelope semantics remain unchanged.
- Only the declared Week service files are modified.
- The targeted Week service test and backend quick profile pass.
- The packet does not touch frontend, report_workflow.py, or other frozen surfaces.

## Verification Profile
- backend: Run backend quick plus the smallest targeted backend tests covering the Week service slice.
- frontend: Not applicable; frontend/UI is frozen and untouched.
- observability: Formal observability ownership is deferred to the W01 packet-local verifier; this packet only needs stable names and explicit note-taking for any obvious evidence gap.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_service.py
    - docker exec astro-project-backend-1 python3 scripts/pipeline.py
  - frontend_commands:
  - observability_scope: none
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: False
  - requires_frontend_visual: False
  - artifact_globs:
    - /opt/astro-project/test-results/**/*
    - /opt/astro-project/logs/**/*
    - /opt/astro-project/backend/logs/**/*
    - /opt/astro-project/artifacts/**/*

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Reject if Week payload or envelope behavior changes.
- Reject if the packet widens into API-layer, frontend, or report_workflow changes.
- Accept only if service-level names are concrete enough for later main.py integration and verifier review.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS

## Notes
-
