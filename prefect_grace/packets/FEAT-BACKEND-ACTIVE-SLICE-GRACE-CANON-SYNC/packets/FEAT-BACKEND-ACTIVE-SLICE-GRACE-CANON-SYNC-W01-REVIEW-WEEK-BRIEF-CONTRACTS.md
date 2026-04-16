# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-WEEK-BRIEF-CONTRACTS

## Summary
Accept or reject WeekBrief canon-sync against addressability, behavior preservation, and evidence readability.

## Wave
W01

## Role
reviewer

## Reasoning
medium

## Write Scope
-

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-PLANNER-SLICING
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS

## Acceptance Criteria
- WeekBrief packet modifies only its declared write scope.
- WeekBrief service contracts are readable and aligned to local strict-GRACE style.
- No WeekBrief payload, envelope, or API semantic change is present.
- Tests remain meaningful and are not weakened.

## Verification Profile
- backend: Review targeted WeekBrief test evidence and backend quick evidence when available.
- frontend: Not applicable; frontend must remain untouched.
- observability: Confirm WeekBrief evidence can be attributed by module/function/block names or that a clear blocker exists.
- execution: {'backend_commands': [], 'frontend_commands': [], 'observability_commands': [], 'touches_frontend': False, 'requires_frontend_visual': False, 'artifact_globs': []}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Accept only if WeekBrief behavior preservation is concrete from diff and tests.
- Reject if contracts are decorative but do not make entrypoints and blocks addressable.
- Reject if frozen scope is touched.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-WEEK-BRIEF-CANON-CONTRACTS

## Notes
-
