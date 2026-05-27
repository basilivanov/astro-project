# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-SCHEDULER-CANON-CONTRACTS

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-SCHEDULER-CANON-CONTRACTS`

## Summary
Align strict-GRACE contracts and semantic blocks for scheduler job entrypoints without changing automation or billing-adjacent behavior.

## Wave
W01

## Role
coder

## Reasoning
medium

## Write Scope
- /opt/astro-project/backend/app/services/scheduler.py
- /opt/astro-project/tests/test_billing_scheduler.py

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/architect_manifest.json

## Acceptance Criteria
- scheduler.py exposes strict-GRACE module contracts, module maps, required function contracts, and stable semantic START/END blocks for job entrypoints.
- Scheduler job semantics remain unchanged.
- Only the declared scheduler files are modified.
- The targeted scheduler test and backend quick profile pass.
- The packet does not touch billing.py, models.py, db.py, frontend paths, or other frozen surfaces.

## Verification Profile
- backend: Run backend quick plus the smallest targeted backend tests covering scheduler behavior.
- frontend: Not applicable; frontend/UI is frozen and untouched.
- observability: Formal observability ownership is deferred to the W01 packet-local verifier; this packet only needs stable names and explicit note-taking for any obvious evidence gap.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_billing_scheduler.py
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
- Reject if billing-adjacent semantics, job scheduling behavior, or frozen files change.
- Reject if the packet widens into observability redesign.
- Accept only if scheduler names are concrete enough for later packet-local and canonical evidence review.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS

## Notes
-
