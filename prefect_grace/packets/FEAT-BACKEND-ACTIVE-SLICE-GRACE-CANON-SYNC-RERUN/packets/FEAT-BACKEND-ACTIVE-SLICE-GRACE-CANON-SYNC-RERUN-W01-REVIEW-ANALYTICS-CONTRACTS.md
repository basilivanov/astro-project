# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-ANALYTICS-CONTRACTS

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-REVIEW-ANALYTICS-CONTRACTS`

## Summary
Accept or reject the analytics packet against scope containment, behavior preservation, and explicit handling of any evidence gap.

## Wave
W01

## Role
reviewer

## Reasoning
medium

## Write Scope
- Review verdict for the analytics contract packet

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-ANALYTICS-CANON-CONTRACTS

## Acceptance Criteria
- The verdict explicitly accepts or rejects coder_analytics_contracts.
- The review confirms the diff is limited to analytics.py.
- The review confirms analytics behavior remains unchanged.
- Any rejection names the smallest required rework scope.

## Verification Profile
- backend: Review the backend quick outcome from the coder packet.
- frontend: Not applicable; frontend/UI is frozen and untouched.
- observability: Confirm the packet either improves analytics marker readability or names the exact evidence gap that later verifiers must handle.
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
- Reject if analytics semantics changed or scope widened.
- Reject if the packet hides the lack of direct analytics evidence.
- Accept only if downstream packets can rely on stabilized analytics naming and explicit gap handling.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-RERUN-W01-ANALYTICS-CANON-CONTRACTS

## Notes
-
