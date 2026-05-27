# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-ARCHITECT-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE

## Title
Architect Rework Capture Fresh Week Frontend Visual Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-ARCHITECT-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`

## Packet Type
rework

## Summary
Review reviewer blockers for FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Fresh visual artifacts now exist, but they show canonical Week regressions instead of satisfying requires_frontend_visual=true; The remaining blocker is a bounded implementation fix in the original execution packet, not an architect decision or pipeline repair

## Wave
W01

## Role
architect

## Reasoning
xhigh

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`

## Write Scope
- Architect routing decision and direct rework specification only.

## Inputs
- Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`.
- Reviewer packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`.
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
- rework_mode: bounded_fresh
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is limited to narrow packet-local write scope

## Reviewer Gate
- Do not widen scope beyond the reviewer blockers.
- Prefer bounded coder rework over user escalation when the blocker is self-resolvable.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE

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
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-ARCHITECT-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "architect",
  "reasoning": "xhigh",
  "title": "Architect Rework Capture Fresh Week Frontend Visual Evidence",
  "summary": "Review reviewer blockers for FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE and decide whether to issue a bounded direct coder rework, escalate to the user, or request planner decomposition: Fresh visual artifacts now exist, but they show canonical Week regressions instead of satisfying requires_frontend_visual=true; The remaining blocker is a bounded implementation fix in the original execution packet, not an architect decision or pipeline repair",
  "write_scope": [
    "Architect routing decision and direct rework specification only."
  ],
  "inputs": [
    "Target coder packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`.",
    "Reviewer packet `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`.",
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
    "sandbox": "danger-full-access",
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is limited to narrow packet-local write scope"
  },
  "reviewer_gate": [
    "Do not widen scope beyond the reviewer blockers.",
    "Prefer bounded coder rework over user escalation when the blocker is self-resolvable."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE"
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
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
