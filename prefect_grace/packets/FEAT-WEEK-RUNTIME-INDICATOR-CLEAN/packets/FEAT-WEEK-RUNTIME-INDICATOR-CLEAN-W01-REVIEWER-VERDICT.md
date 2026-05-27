# Packet: FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-REVIEWER-VERDICT

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN`
- wave_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN:wave:W01`
- packet_ref: `feature:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN:wave:W01:packet:FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-REVIEWER-VERDICT`

## Summary
Judge the packet outcome and decide accepted, rework_required, blocked, or escalate_to_architect.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-VERIFIER-EVIDENCE

## Acceptance Criteria
- Exactly one verdict is returned.
- Blockers are actionable.
- Follow-up action is explicit.

## Verification Profile
- backend: not required
- frontend: not required
- observability: consume verifier evidence and notes

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Do not invent new scope.
- Do not accept missing evidence.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-WEEK-DEV-INDICATOR-DIAGNOSTICS-DISCLOSURE
- FEAT-WEEK-RUNTIME-INDICATOR-CLEAN-W01-VERIFIER-EVIDENCE

## Notes
- Escalate to architect when the blocker changes decomposition or business semantics.
