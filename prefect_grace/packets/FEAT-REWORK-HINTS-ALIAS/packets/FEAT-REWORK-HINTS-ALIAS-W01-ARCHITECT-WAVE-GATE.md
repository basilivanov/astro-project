# Packet: FEAT-REWORK-HINTS-ALIAS-W01-ARCHITECT-WAVE-GATE

## Title
Architect Wave Gate

## GRACE IDs
- feature_ref: `feature:FEAT-REWORK-HINTS-ALIAS`
- wave_ref: `feature:FEAT-REWORK-HINTS-ALIAS:wave:W01`
- packet_ref: `feature:FEAT-REWORK-HINTS-ALIAS:wave:W01:packet:FEAT-REWORK-HINTS-ALIAS-W01-ARCHITECT-WAVE-GATE`

## Packet Type
gate_decision

## Summary
Accept or reject the completed wave based on business fit, UX, visual proof, and overall feature intent.

## Wave
W01

## Role
architect

## Reasoning
xhigh

## Parent Packet
-

## Review Target
-

## Write Scope
- Wave acceptance note only.
- No direct implementation changes in this gate packet.

## Inputs
- FEAT-REWORK-HINTS-ALIAS-W01-REVIEWER-VERDICT
- FEAT-REWORK-HINTS-ALIAS-W01-VERIFIER-EVIDENCE
- FEAT-REWORK-HINTS-ALIAS-W01-IMPLEMENTATION
- wave plan

## Acceptance Criteria
- Wave result matches business intent.
- Frontend visual proof is sufficient when UI is touched.
- Technical acceptance is backed by verifier and reviewer evidence.

## Verification Profile
- backend: consume verifier evidence
- frontend: review screenshots, Playwright evidence, and expected UI states if UI is touched
- observability: review verifier observability verdict for the wave

## Execution Hints
- sandbox: danger-full-access

## Reviewer Gate
- Architect confirms wave acceptance or rejects it with explicit reasons.

## Dependencies
- FEAT-REWORK-HINTS-ALIAS-W01-REVIEWER-VERDICT

## Notes
- This is the wave-level acceptance gate.
- Frontend visual review belongs here when the wave touches UI.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-REWORK-HINTS-ALIAS-W01-ARCHITECT-WAVE-GATE",
  "feature_id": "FEAT-REWORK-HINTS-ALIAS",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "architect",
  "reasoning": "xhigh",
  "title": "Architect Wave Gate",
  "summary": "Accept or reject the completed wave based on business fit, UX, visual proof, and overall feature intent.",
  "write_scope": [
    "Wave acceptance note only.",
    "No direct implementation changes in this gate packet."
  ],
  "inputs": [
    "FEAT-REWORK-HINTS-ALIAS-W01-REVIEWER-VERDICT",
    "FEAT-REWORK-HINTS-ALIAS-W01-VERIFIER-EVIDENCE",
    "FEAT-REWORK-HINTS-ALIAS-W01-IMPLEMENTATION",
    "wave plan"
  ],
  "acceptance_criteria": [
    "Wave result matches business intent.",
    "Frontend visual proof is sufficient when UI is touched.",
    "Technical acceptance is backed by verifier and reviewer evidence."
  ],
  "verification_profile": {
    "backend": "consume verifier evidence",
    "frontend": "review screenshots, Playwright evidence, and expected UI states if UI is touched",
    "observability": "review verifier observability verdict for the wave"
  },
  "execution_hints": {
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "Architect confirms wave acceptance or rejects it with explicit reasons."
  ],
  "dependencies": [
    "FEAT-REWORK-HINTS-ALIAS-W01-REVIEWER-VERDICT"
  ],
  "notes": [
    "This is the wave-level acceptance gate.",
    "Frontend visual review belongs here when the wave touches UI."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
