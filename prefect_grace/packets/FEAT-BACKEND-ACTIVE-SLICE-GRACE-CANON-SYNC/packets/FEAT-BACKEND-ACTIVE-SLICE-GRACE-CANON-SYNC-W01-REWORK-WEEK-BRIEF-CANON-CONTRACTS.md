# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REWORK-WEEK-BRIEF-CANON-CONTRACTS

## Summary
Address reviewer blockers from FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS: WeekBrief diff is limited to declared packet scope; WeekBrief GRACE contracts and telemetry attribution are readable; Targeted WeekBrief tests and backend quick are reported green; Required host-side post-test review still returned FAIL_NO_EVIDENCE

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- Only the files required to address blockers from `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS`.

## Inputs
- Parent packet `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS`.
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
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS

## Notes
- This is a localized rework packet created from reviewer blockers.
