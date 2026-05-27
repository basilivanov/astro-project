# Packet: FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W01-REVIEWER-VERDICT

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
- FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W01-LIVE-IMPLEMENTATION-PACKET
- FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W01-VERIFIER-EVIDENCE

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

## Reviewer Gate
- Do not invent new scope.
- Do not accept missing evidence.

## Dependencies
- FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W01-LIVE-IMPLEMENTATION-PACKET
- FEAT-WEEK-RUNTIME-INDICATOR-RETRY-W01-VERIFIER-EVIDENCE

## Notes
- Escalate to architect when the blocker changes decomposition or business semantics.
