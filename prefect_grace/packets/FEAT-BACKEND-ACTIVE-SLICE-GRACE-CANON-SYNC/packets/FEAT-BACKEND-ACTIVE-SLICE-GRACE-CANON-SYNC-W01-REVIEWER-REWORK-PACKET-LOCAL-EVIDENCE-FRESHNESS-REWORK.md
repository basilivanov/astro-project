# Packet: FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-REWORK-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK

## Title
Reviewer Rework Packet-Local Evidence Freshness Rework

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- wave_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC:wave:W01:packet:FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-REWORK-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK`

## Packet Type
gate_decision

## Summary
Review whether the architect-bounded direct rework for `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET` addressed the reviewer blockers.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
`FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET`

## Review Target
`FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK`

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK

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

## Reviewer Gate
- Assess only the original blocker scope.
- Escalate only if blockers imply decomposition or business changes.

## Dependencies
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK
- FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK

## Notes
- This reviewer packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-REVIEWER-REWORK-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK",
  "feature_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer Rework Packet-Local Evidence Freshness Rework",
  "summary": "Review whether the architect-bounded direct rework for `FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET` addressed the reviewer blockers.",
  "write_scope": [
    "Review verdict and blocker notes only."
  ],
  "inputs": [
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK",
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK"
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
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "Assess only the original blocker scope.",
    "Escalate only if blockers imply decomposition or business changes."
  ],
  "dependencies": [
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK",
    "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-VERIFIER-REWORK-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK"
  ],
  "notes": [
    "This reviewer packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-LIVE-IMPLEMENTATION-PACKET",
  "review_target_packet_id": "FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC-W01-PACKET-LOCAL-EVIDENCE-FRESHNESS-REWORK",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
