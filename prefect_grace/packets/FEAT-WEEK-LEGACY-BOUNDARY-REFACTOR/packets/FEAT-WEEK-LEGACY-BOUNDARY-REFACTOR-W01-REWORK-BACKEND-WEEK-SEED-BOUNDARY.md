# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REWORK-BACKEND-WEEK-SEED-BOUNDARY

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REWORK-BACKEND-WEEK-SEED-BOUNDARY`

## Summary
Address reviewer blockers from FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-BACKEND-WEEK-SEED-BOUNDARY: Frontend helper packet remains rework_required because frozen visible Week UI scope was touched without architect approval; Verifier command executions passed, but the wave still fails acceptance because frozen Week UI files changed and the verifier packet reported that scope blocker

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- Only the files required to address blockers from `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-BACKEND-WEEK-SEED-BOUNDARY`.

## Inputs
- Parent packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-BACKEND-WEEK-SEED-BOUNDARY`.
- Reviewer blocker notes.

## Acceptance Criteria
- Reviewer blockers are addressed directly.
- No unrelated scope expansion.
- Updated verification evidence is ready for re-review.

## Verification Profile
- backend: rerun the minimally sufficient backend profile if backend code changed
- frontend: rerun targeted Playwright if UI changed
- observability: repeat post-test evidence review for the affected flow

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- All blocker reasons are addressed.
- No new regressions are introduced in the scoped flow.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-BACKEND-WEEK-SEED-BOUNDARY

## Notes
- This is a localized rework packet created from reviewer blockers.
