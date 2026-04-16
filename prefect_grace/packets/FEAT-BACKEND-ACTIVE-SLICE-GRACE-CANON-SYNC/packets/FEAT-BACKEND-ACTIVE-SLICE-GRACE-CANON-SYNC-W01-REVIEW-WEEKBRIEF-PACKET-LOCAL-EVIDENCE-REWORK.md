# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK`

## Summary
Review whether architect-issued direct rework `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK` resolves the W01 WeekBrief packet-local evidence blocker without claiming W02 canonical today-week evidence.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Write Scope
- Review verdict and blocker notes only. Do not edit implementation files.

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFY-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-WEEK-BRIEF-CONTRACTS

## Acceptance Criteria
- Exactly one verdict is returned: accepted, rework_required, blocked, or escalate_to_architect.
- Original WeekBrief W01 blocker is judged against packet-local read-only evidence only.
- Reviewer explicitly confirms W02 canonical today-week evidence remains separate and unclaimed by W01.

## Verification Profile
- backend: consume verifier targeted pytest and backend:quick evidence
- frontend: not applicable; frontend frozen and untouched
- observability: consume verifier read-only post-test review evidence only

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- observability_scope: packet_local
- touches_frontend: False
- requires_frontend_visual: False

## Reviewer Gate
- Accept only if WeekBrief rework stayed inside bounded write scope and backend/read-only evidence is clean or expected.
- Reject if the rework widens scope into canonical today-week ownership.
- If W01 is accepted, state that W02 canonical verifier/reviewer/architect must be rerun next.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFY-WEEKBRIEF-PACKET-LOCAL-EVIDENCE-REWORK

## Notes
- This reviewer packet is part of canonical feature-line continuation; no new business feature id or RERUN id is used.
