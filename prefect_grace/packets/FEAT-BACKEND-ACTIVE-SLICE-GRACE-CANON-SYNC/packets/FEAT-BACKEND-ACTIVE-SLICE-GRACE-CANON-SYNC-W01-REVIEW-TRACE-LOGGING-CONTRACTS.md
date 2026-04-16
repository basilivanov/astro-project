# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEW-TRACE-LOGGING-CONTRACTS

## Summary
Accept or reject the trace/logging canon-sync packet against frozen scope, behavior preservation, and evidence readability.

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
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-TRACE-LOGGING-CANON-CONTRACTS

## Acceptance Criteria
- Trace/logging packet modifies only its declared write scope.
- GRACE contracts and block markers are stable and locally consistent.
- Runtime behavior for correlation IDs and structured logging payloads is not changed except for marker/readability metadata.
- Verification results or documented pending combined verification are sufficient to proceed to dependent packets.

## Verification Profile
- backend: Review targeted test output supplied by coder or verifier; request rework if missing.
- frontend: Not applicable; frontend must remain untouched.
- observability: Confirm evidence attribution is readable or gap is explicitly tracked.
- execution: {'backend_commands': [], 'frontend_commands': [], 'observability_commands': [], 'touches_frontend': False, 'requires_frontend_visual': False, 'artifact_globs': []}

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Accept only if the implementation is marker/contract alignment, not a logging rewrite.
- Reject if frozen scope is touched.
- Reject if evidence names remain ambiguous without a documented reason.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-TRACE-LOGGING-CANON-CONTRACTS

## Notes
- This early review reduces rework risk for downstream Day, Week, scheduler, analytics, and API packets that depend on trace/logging naming.
