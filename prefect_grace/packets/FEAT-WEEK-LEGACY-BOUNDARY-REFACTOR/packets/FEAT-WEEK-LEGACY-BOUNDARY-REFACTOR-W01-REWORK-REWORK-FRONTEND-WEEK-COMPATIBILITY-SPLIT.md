# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REWORK-REWORK-FRONTEND-WEEK-COMPATIBILITY-SPLIT

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REWORK-REWORK-FRONTEND-WEEK-COMPATIBILITY-SPLIT`

## Summary
Address reviewer blockers from FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REWORK-FRONTEND-WEEK-COMPATIBILITY-SPLIT: Tracked frontend/app/week/page.tsx diff was cleared, but an untracked visible Week component remains under frozen frontend/components/week scope; Original frozen visible Week UI scope blocker is not fully resolved

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- Only the files required to address blockers from `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REWORK-FRONTEND-WEEK-COMPATIBILITY-SPLIT`.

## Inputs
- Parent packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REWORK-FRONTEND-WEEK-COMPATIBILITY-SPLIT`.
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
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REWORK-FRONTEND-WEEK-COMPATIBILITY-SPLIT

## Notes
- This is a localized rework packet created from reviewer blockers.
