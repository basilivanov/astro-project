# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-BACKEND-WEEK-SEED-BOUNDARY

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-BACKEND-WEEK-SEED-BOUNDARY`

## Summary
Review the backend seed-boundary implementation for scope control, ownership correctness, stable fallback behavior, and test adequacy.

## Wave
W01

## Role
reviewer

## Reasoning
high

## Write Scope
-

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-PLANNER-SLICING
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W00-ARCHITECT-FORMALIZATION
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-BACKEND-WEEK-SEED-BOUNDARY

## Acceptance Criteria
- Backend seed-boundary implementation is accepted, rejected with concrete rework items, or blocked with a specific missing-evidence reason.
- Reviewer confirms the implementation did not widen frozen backend scope.
- Reviewer confirms backend acceptance criteria are backed by executed command results.

## Verification Profile
- backend: Inspect coder evidence and rerun only if evidence is missing, stale, or inconsistent with the diff.
- frontend: Not required for this backend-only review.
- observability: Do not require canonical Today/Week evidence for this reviewer packet; packet-local verification is deferred to the verifier packet.
- execution:
  - backend_commands:
  - frontend_commands:
  - observability_scope: none
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: False
  - requires_frontend_visual: False
  - artifact_globs:

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Accept only if week_brief_service.py no longer depends on report_workflow.py private Week seed helpers.
- Accept only if Week prompt-context wiring remains covered by tests or explicit code-path evidence.
- Reject if backend/app/main.py, backend/app/services/week_map.py, backend/app/services/day_brief*, or unrelated report_workflow decomposition changed.
- Reject if backend tests are absent, failing, or not attributable to the changed backend boundary.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-BACKEND-WEEK-SEED-BOUNDARY

## Notes
- This is an early rework gate so frontend work does not build on an unstable backend ownership boundary.
