# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-ARCHITECT-REWORK-LIVE-IMPLEMENTATION-PACKET

## Title
Architect Rework Live Implementation Packet

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-ARCHITECT-REWORK-LIVE-IMPLEMENTATION-PACKET`

## Packet Type
rework

## Summary
Review reviewer blockers for FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Backend quick and targeted pytest passed; W01 packet-local scope does not require canonical today-week closeout; Verifier reported no-evidence-blocker for packet-local observability; Read-only evidence was stale and lacked current-run trace_id/request_id/report_id attribution

## Wave
W01

## Role
architect

## Reasoning
xhigh

## Parent Packet
`FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET`

## Review Target
`FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET`

## Write Scope
- Architect routing decision and direct rework specification only.

## Inputs
- Target coder packet `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET`.
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
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT

## Notes
- Return FINAL_DIRECT_REWORK_PACKET_JSON.
- Use route_classification=self_resolvable_rework when the next step is a bounded coder packet.
- Use rework_mode=light_resume only for small packet-local fixes that can safely reuse coder context.
- Use rework_mode=bounded_fresh for bounded fixes that still need a fresh coder packet.
- Use rework_mode=decision_required when the blocker should not resume coder work directly.
- Use requires_user_decision only for true business/product/user decisions.
- Use requires_planner only when packet graph or decomposition must change.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-ARCHITECT-REWORK-LIVE-IMPLEMENTATION-PACKET",
  "feature_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "architect",
  "reasoning": "xhigh",
  "title": "Architect Rework Live Implementation Packet",
  "summary": "Review reviewer blockers for FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Backend quick and targeted pytest passed; W01 packet-local scope does not require canonical today-week closeout; Verifier reported no-evidence-blocker for packet-local observability; Read-only evidence was stale and lacked current-run trace_id/request_id/report_id attribution",
  "write_scope": [
    "Architect routing decision and direct rework specification only."
  ],
  "inputs": [
    "Target coder packet `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET`.",
    "Reviewer packet `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT`.",
    "Reviewer blocker notes and latest verifier evidence."
  ],
  "acceptance_criteria": [
    "Architect classifies the blocker as self-resolvable, requires_user_decision, or requires_planner.",
    "If self-resolvable, architect returns a bounded direct rework packet for coder.",
    "If escalation is required, architect states the narrowest blocking reason."
  ],
  "verification_profile": {
    "backend": "not required",
    "frontend": "not required",
    "observability": "artifact review only"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "Do not widen scope beyond the reviewer blockers.",
    "Prefer bounded coder rework over user escalation when the blocker is self-resolvable."
  ],
  "dependencies": [
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET",
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-VERDICT"
  ],
  "notes": [
    "Return FINAL_DIRECT_REWORK_PACKET_JSON.",
    "Use route_classification=self_resolvable_rework when the next step is a bounded coder packet.",
    "Use rework_mode=light_resume only for small packet-local fixes that can safely reuse coder context.",
    "Use rework_mode=bounded_fresh for bounded fixes that still need a fresh coder packet.",
    "Use rework_mode=decision_required when the blocker should not resume coder work directly.",
    "Use requires_user_decision only for true business/product/user decisions.",
    "Use requires_planner only when packet graph or decomposition must change."
  ],
  "parent_packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET",
  "review_target_packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
