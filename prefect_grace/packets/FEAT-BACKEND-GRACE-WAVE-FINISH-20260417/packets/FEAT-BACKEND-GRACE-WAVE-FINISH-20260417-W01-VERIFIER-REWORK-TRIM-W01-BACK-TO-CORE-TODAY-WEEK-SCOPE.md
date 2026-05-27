# Packet: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFIER-REWORK-TRIM-W01-BACK-TO-CORE-TODAY-WEEK-SCOPE

## Title
Verifier Rework Trim W01 Back To Core Today Week Scope

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFIER-REWORK-TRIM-W01-BACK-TO-CORE-TODAY-WEEK-SCOPE`

## Packet Type
rework

## Summary
Validate the architect-bounded direct rework for `FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE` and capture fresh evidence.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE`

## Review Target
-

## Write Scope
- Verification notes and evidence references only.

## Inputs
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-TRIM-W01-BACK-TO-CORE-TODAY-WEEK-SCOPE
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-REVIEW-CORE-TODAY-WEEK-EVIDENCE

## Acceptance Criteria
- Commands run are recorded for the direct rework packet.
- Evidence paths are refreshed for the reworked scope.
- Observability verdict is explicit for the direct rework.

## Verification Profile
- backend: docker exec astro-project-backend-1 python3 scripts/pipeline.py; docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k "today or week or core"
- frontend: not applicable
- observability: python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 scripts/pipeline.py
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k "today or week or core"
  - frontend_commands:
  - observability_commands:
    - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
  - observability_profile: read-only
  - observability_scope: packet_local
  - canonical_flow_commands:
  - touches_frontend: False
  - requires_frontend_visual: False

## Execution Hints
- workdir: /opt/astro-project
- rework_mode: bounded_fresh
- runner: codex
- backend_commands:
  - docker exec astro-project-backend-1 python3 scripts/pipeline.py
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k "today or week or core"
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- observability_scope: packet_local
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Evidence must correspond to the direct rework packet, not the original attempt.
- Missing visual proof remains a blocker for UI work.

## Dependencies
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-TRIM-W01-BACK-TO-CORE-TODAY-WEEK-SCOPE

## Notes
- This verifier packet was created for architect-bounded direct rework.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFIER-REWORK-TRIM-W01-BACK-TO-CORE-TODAY-WEEK-SCOPE",
  "feature_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verifier Rework Trim W01 Back To Core Today Week Scope",
  "summary": "Validate the architect-bounded direct rework for `FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE` and capture fresh evidence.",
  "write_scope": [
    "Verification notes and evidence references only."
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-TRIM-W01-BACK-TO-CORE-TODAY-WEEK-SCOPE",
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-REVIEW-CORE-TODAY-WEEK-EVIDENCE"
  ],
  "acceptance_criteria": [
    "Commands run are recorded for the direct rework packet.",
    "Evidence paths are refreshed for the reworked scope.",
    "Observability verdict is explicit for the direct rework."
  ],
  "verification_profile": {
    "backend": "docker exec astro-project-backend-1 python3 scripts/pipeline.py; docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k \"today or week or core\"",
    "frontend": "not applicable",
    "observability": "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md",
    "execution": {
      "backend_commands": [
        "docker exec astro-project-backend-1 python3 scripts/pipeline.py",
        "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k \"today or week or core\""
      ],
      "frontend_commands": [],
      "observability_commands": [
        "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md"
      ],
      "observability_profile": "read-only",
      "observability_scope": "packet_local",
      "canonical_flow_commands": [],
      "touches_frontend": false,
      "requires_frontend_visual": false
    }
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "rework_mode": "bounded_fresh",
    "runner": "codex",
    "backend_commands": [
      "docker exec astro-project-backend-1 python3 scripts/pipeline.py",
      "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k \"today or week or core\""
    ],
    "observability_commands": [
      "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md"
    ],
    "observability_scope": "packet_local",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Evidence must correspond to the direct rework packet, not the original attempt.",
    "Missing visual proof remains a blocker for UI work."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-TRIM-W01-BACK-TO-CORE-TODAY-WEEK-SCOPE"
  ],
  "notes": [
    "This verifier packet was created for architect-bounded direct rework."
  ],
  "parent_packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE",
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
