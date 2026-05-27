# Packet: FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-REVIEW-EVIDENCE-COMMAND

## Title
Review Evidence Command

## GRACE IDs
- feature_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424`
- wave_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424:wave:W01`
- packet_ref: `feature:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424:wave:W01:packet:FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-REVIEW-EVIDENCE-COMMAND`

## Packet Type
execution

## Summary
Review W01 implementation and verifier evidence for strict canonical evidence correctness.

## Wave
W01

## Role
reviewer

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND`

## Write Scope
- feature-local review artifacts only

## Inputs
- FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND
- FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND

## Acceptance Criteria
- Implementation stays within allowed scope.
- Generation path exercises owned producers.
- Watcher/reviewer strictness remains intact.
- Verifier evidence proves freshness and identifiers.

## Verification Profile
- backend: evidence review only
- frontend: not required
- observability: evidence review only

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access

## Reviewer Gate
- No unrelated backend refactor.
- No fabricated evidence.
- No missing evidence flow.

## Dependencies
- FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND

## Notes
- Escalate only if command cannot be deterministic without live dependencies.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-REVIEW-EVIDENCE-COMMAND",
  "feature_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "reviewer",
  "reasoning": "high",
  "title": "Review Evidence Command",
  "summary": "Review W01 implementation and verifier evidence for strict canonical evidence correctness.",
  "write_scope": [
    "feature-local review artifacts only"
  ],
  "inputs": [
    "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND",
    "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND"
  ],
  "acceptance_criteria": [
    "Implementation stays within allowed scope.",
    "Generation path exercises owned producers.",
    "Watcher/reviewer strictness remains intact.",
    "Verifier evidence proves freshness and identifiers."
  ],
  "verification_profile": {
    "backend": "evidence review only",
    "frontend": "not required",
    "observability": "evidence review only"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access"
  },
  "reviewer_gate": [
    "No unrelated backend refactor.",
    "No fabricated evidence.",
    "No missing evidence flow."
  ],
  "dependencies": [
    "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-VERIFY-EVIDENCE-COMMAND"
  ],
  "notes": [
    "Escalate only if command cannot be deterministic without live dependencies."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424-W01-CANONICAL-EVIDENCE-COMMAND",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
