# Packet: FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-FINAL-CANONICAL-BACKEND-CLOSEOUT

## Title
Final Canonical Backend Closeout

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417`
- wave_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417:wave:W03:packet:FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-FINAL-CANONICAL-BACKEND-CLOSEOUT`

## Packet Type
execution

## Summary
Run backend quick, the architect-authorized canonical emitter command, read-only hub review, and today-week canonical review.

## Wave
W03

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
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-ARCHITECT-GATE-SCHEDULER-ANALYTICS-HUBS

## Acceptance Criteria
- backend:quick passes.
- Canonical emitter command passes.
- today-week verdict is clean or degraded-but-expected.
- read-only hub review is explicit.

## Verification Profile
- backend: docker exec astro-project-backend-1 python3 scripts/pipeline.py; docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py
- frontend: not applicable
- observability: python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 scripts/pipeline.py
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py
  - frontend_commands:
  - observability_commands:
    - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
    - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
  - observability_profile: today-week
  - observability_scope: wave_final
  - canonical_flow_commands:
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py
  - touches_frontend: False
  - requires_frontend_visual: False

## Execution Hints
- workdir: /opt/astro-project
- runner: codex
- backend_commands:
  - docker exec astro-project-backend-1 python3 scripts/pipeline.py
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- canonical_flow_commands:
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py
- observability_scope: wave_final
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
- Reject missing canonical today-week evidence.
- Reject unexpected-degradation or no-evidence-blocker.
- Reject missing read-only hub interpretation.

## Dependencies
- FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-ARCHITECT-GATE-SCHEDULER-ANALYTICS-HUBS

## Notes
- This is the only packet that owns wave_final today-week closeout.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W03-FINAL-CANONICAL-BACKEND-CLOSEOUT",
  "feature_id": "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417",
  "wave_id": "W03",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Final Canonical Backend Closeout",
  "summary": "Run backend quick, the architect-authorized canonical emitter command, read-only hub review, and today-week canonical review.",
  "write_scope": [
    "/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-WAVE-FINISH-20260417/evidence/**"
  ],
  "inputs": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-ARCHITECT-GATE-SCHEDULER-ANALYTICS-HUBS"
  ],
  "acceptance_criteria": [
    "backend:quick passes.",
    "Canonical emitter command passes.",
    "today-week verdict is clean or degraded-but-expected.",
    "read-only hub review is explicit."
  ],
  "verification_profile": {
    "backend": "docker exec astro-project-backend-1 python3 scripts/pipeline.py; docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py",
    "frontend": "not applicable",
    "observability": "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md; python3 tools/post_test_review.py --profile today-week --since 30m --report-format md",
    "execution": {
      "backend_commands": [
        "docker exec astro-project-backend-1 python3 scripts/pipeline.py",
        "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py"
      ],
      "frontend_commands": [],
      "observability_commands": [
        "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md",
        "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
      ],
      "observability_profile": "today-week",
      "observability_scope": "wave_final",
      "canonical_flow_commands": [
        "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py"
      ],
      "touches_frontend": false,
      "requires_frontend_visual": false
    }
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "runner": "codex",
    "backend_commands": [
      "docker exec astro-project-backend-1 python3 scripts/pipeline.py",
      "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py"
    ],
    "observability_commands": [
      "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md",
      "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
    ],
    "canonical_flow_commands": [
      "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py"
    ],
    "observability_scope": "wave_final",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Reject missing canonical today-week evidence.",
    "Reject unexpected-degradation or no-evidence-blocker.",
    "Reject missing read-only hub interpretation."
  ],
  "dependencies": [
    "FEAT-BACKEND-GRACE-WAVE-FINISH-20260417-W02-ARCHITECT-GATE-SCHEDULER-ANALYTICS-HUBS"
  ],
  "notes": [
    "This is the only packet that owns wave_final today-week closeout."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
