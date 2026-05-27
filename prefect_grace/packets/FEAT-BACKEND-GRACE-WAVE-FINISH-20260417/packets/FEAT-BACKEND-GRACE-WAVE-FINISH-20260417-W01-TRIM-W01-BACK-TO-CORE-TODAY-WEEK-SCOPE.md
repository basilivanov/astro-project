# Packet: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-TRIM-W01-BACK-TO-CORE-TODAY-WEEK-SCOPE

## Title
Trim W01 Back To Core Today Week Scope

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-TRIM-W01-BACK-TO-CORE-TODAY-WEEK-SCOPE`

## Packet Type
rework

## Summary
Remove W02-owned scheduler and analytics hub observability changes from the W01 slice, preserve the already-verified core Today/Week attribution work, and rerun the existing W01 verification lane.

## Wave
W01

## Role
coder

## Reasoning
high

## Parent Packet
`FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE`

## Review Target
`FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE`

## Write Scope
- /opt/astro-project/backend/app/logging_utils.py
- /opt/astro-project/tests/test_logging_utils_grace.py
- /opt/astro-project/tools/post_test_review.py

## Inputs
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-REVIEW-CORE-TODAY-WEEK-EVIDENCE reviewer blockers
- Latest W01 verifier evidence confirming current-run Today/Week attribution is already sufficient

## Acceptance Criteria
- W01 no longer carries scheduler or analytics hub routing, hub-specific tests, or hub digest expansion owned by W02.
- Verified W01 core Today/Week evidence changes remain intact, including stable DayBrief attribution behavior and targeted current-run evidence coverage.
- No business behavior changes are introduced outside scope correction.
- The existing W01 verifier lane is rerun and remains packet-local only, with no claim of final canonical closeout.

## Verification Profile
- backend: Rerun `docker exec astro-project-backend-1 python3 scripts/pipeline.py` and the existing W01 targeted core-evidence pytest lane.
- frontend: not applicable
- observability: Rerun the W01 read-only packet-local review; acceptable verdict is `clean` or `degraded-but-expected` only for unexercised W02 hubs.

## Execution Hints
- workdir: /opt/astro-project
- rework_mode: bounded_fresh

## Reviewer Gate
- Reject any remaining scheduler or analytics hub work in W01-owned files.
- Reject regressions in current-run Today/Week attribution evidence.
- Reject any W01 claim of final canonical today-week closeout.

## Dependencies
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE

## Notes
- Keep the accepted DayBrief block-naming fix and targeted core evidence test coverage.
- Do not widen rework into scheduler.py, analytics.py, frontend, WeekBrief service, or packet topology changes.
- If hub-specific observability support is still needed, defer it to the existing W02 slice rather than retaining it in W01.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-TRIM-W01-BACK-TO-CORE-TODAY-WEEK-SCOPE",
  "feature_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "coder",
  "reasoning": "high",
  "title": "Trim W01 Back To Core Today Week Scope",
  "summary": "Remove W02-owned scheduler and analytics hub observability changes from the W01 slice, preserve the already-verified core Today/Week attribution work, and rerun the existing W01 verification lane.",
  "write_scope": [
    "/opt/astro-project/backend/app/logging_utils.py",
    "/opt/astro-project/tests/test_logging_utils_grace.py",
    "/opt/astro-project/tools/post_test_review.py"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE",
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-REVIEW-CORE-TODAY-WEEK-EVIDENCE reviewer blockers",
    "Latest W01 verifier evidence confirming current-run Today/Week attribution is already sufficient"
  ],
  "acceptance_criteria": [
    "W01 no longer carries scheduler or analytics hub routing, hub-specific tests, or hub digest expansion owned by W02.",
    "Verified W01 core Today/Week evidence changes remain intact, including stable DayBrief attribution behavior and targeted current-run evidence coverage.",
    "No business behavior changes are introduced outside scope correction.",
    "The existing W01 verifier lane is rerun and remains packet-local only, with no claim of final canonical closeout."
  ],
  "verification_profile": {
    "backend": "Rerun `docker exec astro-project-backend-1 python3 scripts/pipeline.py` and the existing W01 targeted core-evidence pytest lane.",
    "frontend": "not applicable",
    "observability": "Rerun the W01 read-only packet-local review; acceptable verdict is `clean` or `degraded-but-expected` only for unexercised W02 hubs."
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "Reject any remaining scheduler or analytics hub work in W01-owned files.",
    "Reject regressions in current-run Today/Week attribution evidence.",
    "Reject any W01 claim of final canonical today-week closeout."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE"
  ],
  "notes": [
    "Keep the accepted DayBrief block-naming fix and targeted core evidence test coverage.",
    "Do not widen rework into scheduler.py, analytics.py, frontend, WeekBrief service, or packet topology changes.",
    "If hub-specific observability support is still needed, defer it to the existing W02 slice rather than retaining it in W01."
  ],
  "parent_packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE",
  "review_target_packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
