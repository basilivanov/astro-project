# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-ARCHITECT-REWORK-BACKEND-ACTIVE-SLICE-CANON-SYNC

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-ARCHITECT-REWORK-BACKEND-ACTIVE-SLICE-CANON-SYNC`

## Summary
Review reviewer blockers for FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Backend quick and targeted pytest passed; W01 does not need canonical today-week closeout; Verifier reported stale read-only observability evidence; No fresh packet-local trace_id/request_id/report_id evidence was attributable to the current verifier run

## Wave
W01

## Role
architect

## Reasoning
xhigh

## Write Scope
- Architect routing decision and direct rework specification only.

## Inputs
- Target coder packet `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC`.
- Reviewer packet `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT`.
- Reviewer blocker notes and latest verifier evidence.

## Acceptance Criteria
- Architect classifies the blocker as self-resolvable, requires_user_decision, or requires_planner.
- If self-resolvable, architect returns a bounded direct rework packet for coder.
- If escalation is required, architect states the narrowest blocking reason.

## Verification Profile
- backend: not required
- frontend: not required
- observability: artifact review only

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- Do not widen scope beyond the reviewer blockers.
- Prefer bounded coder rework over user escalation when the blocker is self-resolvable.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-BACKEND-ACTIVE-SLICE-CANON-SYNC
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT

## Notes
- Return FINAL_DIRECT_REWORK_PACKET_JSON.
- Use route_classification=self_resolvable_rework when the next step is a bounded coder packet.
- Use rework_mode=light_resume only for small packet-local fixes that can safely reuse coder context.
- Use rework_mode=bounded_fresh for bounded fixes that still need a fresh coder packet.
- Use rework_mode=decision_required when the blocker should not resume coder work directly.
- Use requires_user_decision only for true business/product/user decisions.
- Use requires_planner only when packet graph or decomposition must change.
