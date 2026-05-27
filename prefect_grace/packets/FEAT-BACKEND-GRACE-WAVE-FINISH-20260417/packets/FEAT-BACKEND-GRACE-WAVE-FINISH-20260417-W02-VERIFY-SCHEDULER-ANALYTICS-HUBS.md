# Packet: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-VERIFY-SCHEDULER-ANALYTICS-HUBS

## Title
Verify Scheduler Analytics Hubs

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W02:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-VERIFY-SCHEDULER-ANALYTICS-HUBS`

## Packet Type
execution

## Summary
Run W02 backend and read-only hub evidence checks and record explicit hub verdicts.

## Wave
W02

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
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE

## Acceptance Criteria
- backend:quick passes.
- Targeted hub evidence pytest passes.
- read-only hub verdict is clean or degraded-but-expected with explicit reason.

## Verification Profile
- backend: docker exec astro-project-backend-1 python3 scripts/pipeline.py; docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k "scheduler or analytics or hub"
- frontend: not applicable
- observability: python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 scripts/pipeline.py
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k "scheduler or analytics or hub"
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
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k "scheduler or analytics or hub"
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- observability_scope: packet_local
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Reject missing hub interpretation.
- Reject no-evidence-blocker for an intentionally exercised hub path.

## Dependencies
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE

## Notes
- W02 is packet_local only.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-VERIFY-SCHEDULER-ANALYTICS-HUBS",
  "feature_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verify Scheduler Analytics Hubs",
  "summary": "Run W02 backend and read-only hub evidence checks and record explicit hub verdicts.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-WAVE-FINISH-20260417/evidence/**"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE"
  ],
  "acceptance_criteria": [
    "backend:quick passes.",
    "Targeted hub evidence pytest passes.",
    "read-only hub verdict is clean or degraded-but-expected with explicit reason."
  ],
  "verification_profile": {
    "backend": "docker exec astro-project-backend-1 python3 scripts/pipeline.py; docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k \"scheduler or analytics or hub\"",
    "frontend": "not applicable",
    "observability": "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md",
    "execution": {
      "backend_commands": [
        "docker exec astro-project-backend-1 python3 scripts/pipeline.py",
        "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k \"scheduler or analytics or hub\""
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
      "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py -k \"scheduler or analytics or hub\""
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
    "Reject missing hub interpretation.",
    "Reject no-evidence-blocker for an intentionally exercised hub path."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-SCHEDULER-ANALYTICS-HUB-EVIDENCE-SLICE"
  ],
  "notes": [
    "W02 is packet_local only."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
