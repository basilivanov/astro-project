# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-DAY-BRIEF-CANON-CONTRACTS

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-DAY-BRIEF-CANON-CONTRACTS`

## Summary
Align strict-GRACE contracts and semantic blocks for DayBrief assembly plus validation without changing Day payload or scoring semantics.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- /opt/astro-project/backend/app/services/day_brief.py
- /opt/astro-project/backend/app/services/day_brief_validators.py
- /opt/astro-project/tests/test_day_brief.py
- /opt/astro-project/tests/test_day_brief_schema.py

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS
- /opt/astro-project/docs/backend-active-slice-grace-canon-sync/architect_manifest.json

## Acceptance Criteria
- day_brief.py and day_brief_validators.py expose strict-GRACE module contracts, module maps, required function contracts, and stable semantic START/END blocks.
- Day payload semantics, scoring behavior, and validation semantics remain unchanged.
- Only the declared Day files are modified.
- The targeted Day tests and backend quick profile pass.
- The packet does not touch frontend, report_workflow.py, or other frozen surfaces.

## Verification Profile
- backend: Run backend quick plus the smallest targeted backend tests covering DayBrief assembly and validation.
- frontend: Not applicable; frontend/UI is frozen and untouched.
- observability: Formal observability ownership is deferred to the W01 packet-local verifier; this packet only needs stable names and explicit note-taking for any obvious evidence gap.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py
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
- Reject if the diff changes Day payload shape, scoring, or validation semantics.
- Reject if the packet touches personalized_daily.py, feed_service.py, frontend paths, or other frozen files.
- Accept only if module/function/block names become concrete enough for packet-local evidence review.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-TRACE-LOGGING-CONTRACTS

## Notes
- Use existing well-marked backend modules as the local style reference.
