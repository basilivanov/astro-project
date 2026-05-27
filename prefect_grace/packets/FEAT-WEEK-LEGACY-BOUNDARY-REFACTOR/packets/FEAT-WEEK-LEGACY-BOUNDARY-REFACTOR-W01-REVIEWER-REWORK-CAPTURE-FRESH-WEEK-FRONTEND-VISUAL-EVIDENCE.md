# Packet: FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE

## Title
Reviewer Rework Capture Fresh Week Frontend Visual Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR`
- wave_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01`
- packet_ref: `feature:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR:wave:W01:packet:FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`

## Packet Type
gate_decision

## Summary
Review whether the architect-bounded direct rework for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR` addressed the reviewer blockers.

## Wave
W01

## Role
reviewer

## Reasoning
xhigh

## Parent Packet
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR`

## Review Target
`FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE`

## Write Scope
- Review verdict and blocker notes only.

## Inputs
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE

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
- light_resume_downgrade_reason: light_resume is limited to narrow packet-local write scope

## Reviewer Gate
- Assess only the original blocker scope.
- Escalate only if blockers imply decomposition or business changes.

## Dependencies
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE
- FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE

## Notes
- This reviewer packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-REVIEWER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
  "feature_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR",
  "wave_id": "W01",
  "packet_type": "gate_decision",
  "role": "reviewer",
  "reasoning": "xhigh",
  "title": "Reviewer Rework Capture Fresh Week Frontend Visual Evidence",
  "summary": "Review whether the architect-bounded direct rework for `FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR` addressed the reviewer blockers.",
  "write_scope": [
    "Review verdict and blocker notes only."
  ],
  "inputs": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE"
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
    "light_resume_downgrade_reason": "light_resume is limited to narrow packet-local write scope"
  },
  "reviewer_gate": [
    "Assess only the original blocker scope.",
    "Escalate only if blockers imply decomposition or business changes."
  ],
  "dependencies": [
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
    "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-VERIFIER-REWORK-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE"
  ],
  "notes": [
    "This reviewer packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-WEEK-LEGACY-BOUNDARY-REFACTOR",
  "review_target_packet_id": "FEAT-WEEK-LEGACY-BOUNDARY-REFACTOR-W01-CAPTURE-FRESH-WEEK-FRONTEND-VISUAL-EVIDENCE",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
