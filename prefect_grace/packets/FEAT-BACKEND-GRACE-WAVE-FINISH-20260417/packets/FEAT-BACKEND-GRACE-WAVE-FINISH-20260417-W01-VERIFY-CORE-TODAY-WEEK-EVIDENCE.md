# Packet: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFY-CORE-TODAY-WEEK-EVIDENCE

## Title
Verify Core Today Week Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W01:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFY-CORE-TODAY-WEEK-EVIDENCE`

## Packet Type
execution

## Summary
Run W01 backend and read-only evidence checks and record current-run ids.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
-

## Review Target
-

## Write Scope
- /opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-WAVE-FINISH-20260417/evidence/**

## Inputs
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE

## Acceptance Criteria
- backend:quick passes.
- Targeted core evidence pytest passes.
- read-only verdict is clean or degraded-but-expected with explicit reason.

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
- Reject stale or missing current-run core evidence.
- Reject no-evidence-blocker for an intentionally exercised core path.

## Dependencies
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE

## Notes
- W01 is packet_local only.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-VERIFY-CORE-TODAY-WEEK-EVIDENCE",
  "feature_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verify Core Today Week Evidence",
  "summary": "Run W01 backend and read-only evidence checks and record current-run ids.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-WAVE-FINISH-20260417/evidence/**"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE"
  ],
  "acceptance_criteria": [
    "backend:quick passes.",
    "Targeted core evidence pytest passes.",
    "read-only verdict is clean or degraded-but-expected with explicit reason."
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
    "Reject stale or missing current-run core evidence.",
    "Reject no-evidence-blocker for an intentionally exercised core path."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W01-CORE-TODAY-WEEK-EVIDENCE-SLICE"
  ],
  "notes": [
    "W01 is packet_local only."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
