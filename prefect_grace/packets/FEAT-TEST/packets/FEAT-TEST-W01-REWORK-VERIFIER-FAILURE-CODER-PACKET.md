# Packet: FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET

## Title
Rework Verifier Failure Coder Packet

## GRACE IDs
- feature_ref: `feature:FEAT-TEST`
- wave_ref: `feature:FEAT-TEST:wave:W01`
- packet_ref: `feature:FEAT-TEST:wave:W01:packet:FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET`

## Packet Type
rework

## Summary
Fix verifier/test issues from REVIEWER-1: insufficient write scope allowed for this feature

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`CODER-1`

## Review Target
-

## Write Scope
- Only the files required to fix verifier failures from `REVIEWER-1`.

## Inputs
- Failed verifier packet `REVIEWER-1`.
- Verifier failure details.

## Acceptance Criteria
- Verifier issues and test failures are resolved.
- No unrelated scope expansion.
- Updated verification evidence is ready.

## Verification Profile
- backend: rerun the minimally sufficient backend profile if backend code changed
- frontend: rerun targeted Playwright if UI changed
- observability: repeat post-test evidence review for the affected flow

## Execution Hints
- verifier_rework_attempt: 1
- verifier_rework_max_attempts: 3

## Reviewer Gate
- All verifier/test failure reasons are resolved.

## Dependencies
- REVIEWER-1

## Notes
- Auto-recovery attempt 1 of 3.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-TEST-W01-REWORK-VERIFIER-FAILURE-CODER-PACKET",
  "feature_id": "FEAT-TEST",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Rework Verifier Failure Coder Packet",
  "summary": "Fix verifier/test issues from REVIEWER-1: insufficient write scope allowed for this feature",
  "write_scope": [
    "Only the files required to fix verifier failures from `REVIEWER-1`."
  ],
  "inputs": [
    "Failed verifier packet `REVIEWER-1`.",
    "Verifier failure details."
  ],
  "acceptance_criteria": [
    "Verifier issues and test failures are resolved.",
    "No unrelated scope expansion.",
    "Updated verification evidence is ready."
  ],
  "verification_profile": {
    "backend": "rerun the minimally sufficient backend profile if backend code changed",
    "frontend": "rerun targeted Playwright if UI changed",
    "observability": "repeat post-test evidence review for the affected flow"
  },
  "execution_hints": {
    "verifier_rework_attempt": 1,
    "verifier_rework_max_attempts": 3
  },
  "reviewer_gate": [
    "All verifier/test failure reasons are resolved."
  ],
  "dependencies": [
    "REVIEWER-1"
  ],
  "notes": [
    "Auto-recovery attempt 1 of 3."
  ],
  "parent_packet_id": "CODER-1",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
