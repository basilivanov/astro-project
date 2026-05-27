# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-API-GATEWAY-CANON-CONTRACTS

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-API-GATEWAY-CANON-CONTRACTS`

## Summary
Align strict-GRACE contracts and semantic blocks for main.py startup, route orchestration, and correlation binding after the service-level names are stabilized.

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
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-DAY-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-WEEK-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-SCHEDULER-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-ANALYTICS-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/architect_manifest.json
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/ARCHITECT_HANDOFF.md

## Acceptance Criteria
- main.py exposes strict-GRACE module contracts, module maps, required function contracts, and stable semantic START/END blocks for startup, route orchestration, and correlation binding within the active slice.
- API response semantics, startup behavior, and request correlation behavior remain unchanged.
- Only main.py and test_week_brief_api.py are modified.
- The targeted API test and backend quick profile pass.
- The packet does not touch report_workflow.py, frontend paths, or other frozen surfaces.

## Verification Profile
- backend: Run backend quick plus the smallest targeted backend tests covering active-slice API integration.
- frontend: Not applicable; frontend/UI is frozen and untouched.
- observability: Formal observability ownership is deferred to the W01 packet-local verifier; this packet only needs stable names and explicit note-taking for any obvious evidence gap.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_week_brief_api.py
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
- Reject if route semantics, response semantics, startup behavior, or request correlation behavior change.
- Reject if the packet touches report_workflow.py, frontend paths, or any frozen backend path.
- Accept only if the packet provides the final integration names needed for W01 packet-local verification and W02 canonical closeout.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-DAY-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-WEEK-BRIEF-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-SCHEDULER-CONTRACTS
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-ANALYTICS-CONTRACTS

## Notes
- This is the final W01 integration coder packet and the reviewer/verifier anchor for combined slice acceptance.
