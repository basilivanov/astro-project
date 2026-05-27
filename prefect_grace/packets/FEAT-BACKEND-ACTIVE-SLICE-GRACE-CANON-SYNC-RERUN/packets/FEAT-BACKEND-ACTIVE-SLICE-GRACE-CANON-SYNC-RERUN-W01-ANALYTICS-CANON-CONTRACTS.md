# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-ANALYTICS-CANON-CONTRACTS

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-ANALYTICS-CANON-CONTRACTS`

## Summary
Align strict-GRACE contracts and semantic blocks for analytics event validation and persistence without changing analytics semantics.

## Wave
W01

## Role
coder

## Reasoning
medium

## Write Scope
- /opt/astro-project/backend/app/services/analytics.py

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/architect_manifest.json

## Acceptance Criteria
- analytics.py exposes strict-GRACE module contracts, module maps, required function contracts where locally expected, and stable semantic START/END blocks.
- Allowed analytics event semantics and persistence behavior remain unchanged.
- Only analytics.py is modified.
- Backend quick remains green after the marker-only change.
- If the packet does not naturally emit direct analytics evidence, that gap is documented instead of widening scope.

## Verification Profile
- backend: Run backend quick for the analytics marker-only change; direct analytics coverage remains bounded to existing slice lanes.
- frontend: Not applicable; frontend/UI is frozen and untouched.
- observability: Formal observability ownership is deferred to the W01 packet-local verifier; this packet only needs stable names and explicit note-taking for any obvious evidence gap.
- execution:
  - backend_commands:
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
- Reject if analytics write semantics or frozen files change.
- Reject if the packet invents new analytics tests or scope beyond the inherited slice boundaries.
- Accept only if any remaining direct-analytics evidence gap is explicit and bounded.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS

## Notes
- The architect artifacts keep analytics inside the bounded active slice but do not authorize wider analytics refactor or new test surfaces.
