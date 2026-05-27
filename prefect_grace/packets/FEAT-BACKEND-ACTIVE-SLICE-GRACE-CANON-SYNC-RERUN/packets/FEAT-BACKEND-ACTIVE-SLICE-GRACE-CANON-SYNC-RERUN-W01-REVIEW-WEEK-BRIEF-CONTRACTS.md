# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-WEEK-BRIEF-CONTRACTS

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-WEEK-BRIEF-CONTRACTS`

## Summary
Accept or reject the Week service packet against scope containment, behavior preservation, and contract readability.

## Wave
W01

## Role
reviewer

## Reasoning
high

## Write Scope
- Review verdict for the WeekBrief contract packet

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-WEEK-BRIEF-CANON-CONTRACTS

## Acceptance Criteria
- The verdict explicitly accepts or rejects coder_week_brief_contracts.
- The review confirms the diff is limited to the declared Week service write scope.
- The review confirms Week semantics remain unchanged.
- Any rejection names the smallest required rework scope.

## Verification Profile
- backend: Review the targeted Week service test and backend quick outcome from the coder packet.
- frontend: Not applicable; frontend/UI is frozen and untouched.
- observability: Confirm Week service markers are readable enough for the packet-local verifier or that the exact gap is named.
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
- Reject if Week behavior changed or if tests were weakened.
- Reject if the review cannot tie its verdict to concrete diff or test evidence.
- Accept only if downstream integration can rely on stabilized Week service naming.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-WEEK-BRIEF-CANON-CONTRACTS

## Notes
-
