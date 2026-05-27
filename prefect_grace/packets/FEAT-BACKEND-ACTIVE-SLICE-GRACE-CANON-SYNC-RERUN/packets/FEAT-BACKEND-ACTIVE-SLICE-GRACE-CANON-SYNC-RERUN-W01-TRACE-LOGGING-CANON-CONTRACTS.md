# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-TRACE-LOGGING-CANON-CONTRACTS

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-TRACE-LOGGING-CANON-CONTRACTS`

## Summary
Align strict-GRACE contracts, module maps, and semantic execution blocks for logging_utils plus correlation glue without changing correlation or structured logging behavior.

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
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-ARCHITECT-FORMALIZATION
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync-rerun/ARCHITECT_HANDOFF.md
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/architect_manifest.json
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/development-plan.slice.backend-active-slice-grace-canon-sync.xml

## Acceptance Criteria
- logging_utils.py and correlation.py expose strict-GRACE module contracts, module maps, and stable semantic START/END blocks aligned to the existing backend style.
- Function contracts are added only where the local strict-GRACE style requires exported or orchestration entrypoints.
- Correlation identifier behavior, middleware behavior, and structured log payload semantics remain unchanged.
- Only the declared trace/logging files are modified.
- The targeted trace/logging tests and backend quick profile pass.

## Verification Profile
- backend: Run backend quick plus the smallest targeted backend tests covering the trace/logging slice.
- frontend: Not applicable; frontend/UI is frozen and untouched.
- observability: Formal observability ownership is deferred to the W01 packet-local verifier; this packet only needs stable names and explicit note-taking for any obvious evidence gap.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_logging_utils_grace.py tests/test_catalog_logging.py
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
- Reject if the diff touches catalog_logging.py, frontend paths, or any frozen backend path.
- Reject if the change rewrites log transport, correlation semantics, or payload fields instead of marker/contract alignment.
- Accept only if the packet leaves stable module/function/block names visible in code and tests or records a concrete gap.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING

## Notes
- Reuse the current backend-active-slice module boundaries from /opt/astro-project/docs/backend-active-slice-grace-canon-sync/* per architect formalization; the rerun changes evidence ownership, not scope.
- This packet is sequenced first because downstream packets depend on stable trace/logging names.
