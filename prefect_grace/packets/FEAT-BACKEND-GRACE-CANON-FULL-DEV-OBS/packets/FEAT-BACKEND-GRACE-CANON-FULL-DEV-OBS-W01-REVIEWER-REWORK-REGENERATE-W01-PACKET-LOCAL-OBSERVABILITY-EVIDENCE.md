# Packet: FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REVIEWER-REWORK-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE

## Title
Reviewer Rework Regenerate W01 Packet-Local Observability Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS`
- wave_ref: `feature:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS:wave:W01:packet:FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REVIEWER-REWORK-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE`

## Packet Type
gate_decision

## Summary
Review whether the architect-bounded direct rework for `FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET` addressed the reviewer blockers.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
`FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET`

## Review Target
`FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE`

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE
- FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-VERIFIER-REWORK-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE

## Acceptance Criteria
- Exactly one verdict is returned.
- The original blockers are either resolved or explicitly remain.
- No unrelated scope expansion is accepted.

## Verification Profile
- backend: consume verifier evidence
- frontend: consume verifier evidence
- observability: consume verifier evidence

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- rework_mode: bounded_fresh
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is limited to at most two small blocker reasons

## Reviewer Gate
- Assess only the original blocker scope.
- Escalate only if blockers imply decomposition or business changes.

## Dependencies
- FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE
- FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-VERIFIER-REWORK-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE

## Notes
- This reviewer packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REVIEWER-REWORK-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE",
  "feature_id": "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer Rework Regenerate W01 Packet-Local Observability Evidence",
  "summary": "Review whether the architect-bounded direct rework for `FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET` addressed the reviewer blockers.",
  "write_scope": [
    "Review verdict and blocker notes only."
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE",
    "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-VERIFIER-REWORK-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE"
  ],
  "acceptance_criteria": [
    "Exactly one verdict is returned.",
    "The original blockers are either resolved or explicitly remain.",
    "No unrelated scope expansion is accepted."
  ],
  "verification_profile": {
    "backend": "consume verifier evidence",
    "frontend": "consume verifier evidence",
    "observability": "consume verifier evidence"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is limited to at most two small blocker reasons"
  },
  "reviewer_gate": [
    "Assess only the original blocker scope.",
    "Escalate only if blockers imply decomposition or business changes."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE",
    "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-VERIFIER-REWORK-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE"
  ],
  "notes": [
    "This reviewer packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-LIVE-IMPLEMENTATION-PACKET",
  "review_target_packet_id": "FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS-W01-REGENERATE-W01-PACKET-LOCAL-OBSERVABILITY-EVIDENCE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
