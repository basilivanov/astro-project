# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-ARCHITECT-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE

## Title
Architect Rework Rework Week Boundary Route Gate And Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-ARCHITECT-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`

## Packet Type
rework

## Summary
Review reviewer blockers for FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Verifier rerun still lacks fresh attributable visual proof for both canonical and fail-closed Week states.; Existing visual artifacts come from earlier runs and do not satisfy the direct rework evidence gate.; This is the same evidence blocker after a localized rework, so it must now be treated as pipeline repair rather than another product rework.

## Wave
W01

## Role
architect

## Reasoning
xhigh

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`

## Write Scope
- Architect routing decision and direct rework specification only.

## Inputs
- Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`.
- Reviewer packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REVIEWER-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`.
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
- rework_mode: bounded_fresh

## Reviewer Gate
- Do not widen scope beyond the reviewer blockers.
- Prefer bounded coder rework over user escalation when the blocker is self-resolvable.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REVIEWER-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE

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
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-ARCHITECT-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "architect",
  "reasoning": "xhigh",
  "title": "Architect Rework Rework Week Boundary Route Gate And Evidence",
  "summary": "Review reviewer blockers for FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Verifier rerun still lacks fresh attributable visual proof for both canonical and fail-closed Week states.; Existing visual artifacts come from earlier runs and do not satisfy the direct rework evidence gate.; This is the same evidence blocker after a localized rework, so it must now be treated as pipeline repair rather than another product rework.",
  "write_scope": [
    "Architect routing decision and direct rework specification only."
  ],
  "inputs": [
    "Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`.",
    "Reviewer packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REVIEWER-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE`.",
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
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "Do not widen scope beyond the reviewer blockers.",
    "Prefer bounded coder rework over user escalation when the blocker is self-resolvable."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REVIEWER-REWORK-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE"
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
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE",
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-RERUN-20260417-W01-REWORK-WEEK-BOUNDARY-ROUTE-GATE-AND-EVIDENCE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
