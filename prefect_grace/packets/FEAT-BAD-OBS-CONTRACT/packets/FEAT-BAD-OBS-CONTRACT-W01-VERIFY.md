# Packet: FEAT-BAD-OBS-CONTRACT-W01-VERIFY

## Title
Verify

## GRACE IDs
- feature_ref: `feature:FEAT-BAD-OBS-CONTRACT`
- wave_ref: `feature:FEAT-BAD-OBS-CONTRACT:wave:W01`
- packet_ref: `feature:FEAT-BAD-OBS-CONTRACT:wave:W01:packet:FEAT-BAD-OBS-CONTRACT-W01-VERIFY`

## Packet Type
execution

## Summary
Verify

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
-

## Inputs
-

## Acceptance Criteria
-

## Verification Profile
- backend: not required
- frontend: not required
- observability: artifact review only
- execution:
  - observability_commands:
    - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md

## Execution Hints
- runner: codex
- observability_commands:
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- backend_profile: backend_quick
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False

## Reviewer Gate
-

## Dependencies
- FEAT-BAD-OBS-CONTRACT-W01-MAIN

## Notes
-

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BAD-OBS-CONTRACT-W01-VERIFY",
  "feature_id": "FEAT-BAD-OBS-CONTRACT",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Verify",
  "summary": "Verify",
  "write_scope": [],
  "inputs": [],
  "acceptance_criteria": [],
  "verification_profile": {
    "execution": {
      "observability_commands": [
        "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
      ]
    }
  },
  "execution_hints": {
    "runner": "codex",
    "observability_commands": [
      "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
    ],
    "backend_profile": "backend_quick",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false
  },
  "reviewer_gate": [],
  "dependencies": [
    "FEAT-BAD-OBS-CONTRACT-W01-MAIN"
  ],
  "notes": [],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
