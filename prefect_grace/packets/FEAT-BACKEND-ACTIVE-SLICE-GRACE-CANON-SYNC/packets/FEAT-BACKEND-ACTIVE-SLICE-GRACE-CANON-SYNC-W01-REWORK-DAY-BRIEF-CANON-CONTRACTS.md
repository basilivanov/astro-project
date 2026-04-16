# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REWORK-DAY-BRIEF-CANON-CONTRACTS

## Summary
Address reviewer blockers from FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-DAY-BRIEF-CANON-CONTRACTS: DayBrief diff is limited to declared packet scope; DayBrief service and validator GRACE contracts and blocks are readable; Targeted DayBrief tests and backend quick are reported green; Post-test Today/DayBrief observability evidence is missing with FAIL_NO_EVIDENCE/no-evidence-blocker

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- Only the files required to address blockers from `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-DAY-BRIEF-CANON-CONTRACTS`.

## Inputs
- Parent packet `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-DAY-BRIEF-CANON-CONTRACTS`.
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
-

## Reviewer Gate
- All blocker reasons are addressed.
- No new regressions are introduced in the scoped flow.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-DAY-BRIEF-CANON-CONTRACTS

## Notes
- This is a localized rework packet created from reviewer blockers.
