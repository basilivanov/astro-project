# Packet: FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-REWORK-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-REWORK-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE`

## Summary
Address reviewer blockers from FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE: Frontend scope and visual acceptance are sufficiently evidenced, including dev-collapsed, dev-expanded, prod-unchanged, and local non-banner containment.; Wave-final observability evidence is not acceptable: FLOW-TODAY-WEEK-WEEK returned no-evidence-blocker.; Verifier showed no fresh canonical Week records were produced for the required verification window, so the packet cannot be accepted yet.

## Wave
W01

## Role
coder

## Reasoning
high

## Write Scope
- Only the files required to address blockers from `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE`.

## Inputs
- Parent packet `FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE`.
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
- FEAT-WEEK-RUNTIME-INDICATOR-RERUN-2-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE

## Notes
- This is a localized rework packet created from reviewer blockers.
