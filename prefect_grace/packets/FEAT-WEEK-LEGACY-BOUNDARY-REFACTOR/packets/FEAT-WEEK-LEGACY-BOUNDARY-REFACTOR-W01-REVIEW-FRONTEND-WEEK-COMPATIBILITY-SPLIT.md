# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-FRONTEND-WEEK-COMPATIBILITY-SPLIT

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEW-FRONTEND-WEEK-COMPATIBILITY-SPLIT`

## Summary
Review the frontend helper split for canonical-only /week behavior, compatibility isolation, scope control, and targeted test adequacy.

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
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-FRONTEND-WEEK-COMPATIBILITY-SPLIT

## Acceptance Criteria
- Frontend compatibility split is accepted, rejected with concrete rework items, or blocked with a specific missing-evidence reason.
- Reviewer confirms no visible Week UI files were touched.
- Reviewer confirms frontend acceptance criteria are backed by executed command results.

## Verification Profile
- backend: Not required for this frontend-helper review.
- frontend: Inspect coder evidence and rerun only if evidence is missing, stale, or inconsistent with the diff.
- observability: Do not require canonical Today/Week evidence for this reviewer packet; packet-local verification is deferred to the verifier packet.
- execution:
  - backend_commands:
  - frontend_commands:
  - observability_scope: none
  - canonical_flow_commands:
  - observability_commands:
  - touches_frontend: True
  - requires_frontend_visual: False
  - artifact_globs:

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Accept only if frontend/lib/week-brief.ts remains canonical-only and fail-closed for non-canonical inputs.
- Accept only if frontend/lib/week-brief-compat.ts owns legacy reconstruction logic and remains outside the canonical /week path.
- Reject if frontend/app/week/page.tsx, frontend/components/week/**, or frontend/app/read/** changed without architect escalation.
- Reject if targeted frontend tests are absent, failing, or not attributable to the helper split.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-FRONTEND-WEEK-COMPATIBILITY-SPLIT

## Notes
- Visual evidence is not mandatory here because the slice forbids visible Week UI changes; any UI-touching change must be escalated before acceptance.
