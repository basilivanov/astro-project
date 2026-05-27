# Packet: FEAT-PLAN-HINTS-W01-VERIFIER-EVIDENCE

## Title
Verifier Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-PLAN-HINTS`
- wave_ref: `feature:FEAT-PLAN-HINTS:wave:W01`
- packet_ref: `feature:FEAT-PLAN-HINTS:wave:W01:packet:FEAT-PLAN-HINTS-W01-VERIFIER-EVIDENCE`

## Packet Type
execution

## Summary
Verify backend change

## Wave
W01

## Role
verifier

## Reasoning
high

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
- frontend: Run `corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx` and `./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts`
- observability: Run `python3 tools/post_test_review.py --profile today-week --since 30m --report-format md`
- execution:
  - observability_scope: wave_final
  - canonical_flow_commands:
    - python3 scripts/verify_api_responses.py
    - python3 tests/verify_week_forecast.py
  - frontend_commands:
    - corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx
    - ./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts
  - observability_commands:
    - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
  - touches_frontend: True
  - requires_frontend_visual: True
  - artifact_globs:
    - frontend/test-results/**/*

## Execution Hints
- runner: codex
- frontend_commands:
  - corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx
  - ./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts
- observability_commands:
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- canonical_flow_commands:
  - python3 scripts/verify_api_responses.py
  - python3 tests/verify_week_forecast.py
- observability_scope: wave_final
- touches_frontend: True
- requires_frontend_visual: True
- artifact_globs:
  - frontend/test-results/**/*
- backend_profile: backend_quick
- include_day_live_canary: False

## Reviewer Gate
-

## Dependencies
- FEAT-PLAN-HINTS-W01-BACKEND-PACKET

## Notes
-

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-PLAN-HINTS-W01-VERIFIER-EVIDENCE",
  "feature_id": "FEAT-PLAN-HINTS",
  "wave_id": "W01",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Verifier Evidence",
  "summary": "Verify backend change",
  "write_scope": [],
  "inputs": [],
  "acceptance_criteria": [],
  "verification_profile": {
    "backend": "not required",
    "frontend": "Run `corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx` and `./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts`",
    "observability": "Run `python3 tools/post_test_review.py --profile today-week --since 30m --report-format md`",
    "execution": {
      "observability_scope": "wave_final",
      "canonical_flow_commands": [
        "python3 scripts/verify_api_responses.py",
        "python3 tests/verify_week_forecast.py"
      ],
      "frontend_commands": [
        "corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx",
        "./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts"
      ],
      "observability_commands": [
        "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
      ],
      "touches_frontend": true,
      "requires_frontend_visual": true,
      "artifact_globs": [
        "frontend/test-results/**/*"
      ]
    }
  },
  "execution_hints": {
    "runner": "codex",
    "frontend_commands": [
      "corepack pnpm --dir frontend exec jest --runInBand test/app/home-page.test.tsx",
      "./scripts/run_e2e.sh e2e/day-dev-indicator.spec.ts"
    ],
    "observability_commands": [
      "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
    ],
    "canonical_flow_commands": [
      "python3 scripts/verify_api_responses.py",
      "python3 tests/verify_week_forecast.py"
    ],
    "observability_scope": "wave_final",
    "touches_frontend": true,
    "requires_frontend_visual": true,
    "artifact_globs": [
      "frontend/test-results/**/*"
    ],
    "backend_profile": "backend_quick",
    "include_day_live_canary": false
  },
  "reviewer_gate": [],
  "dependencies": [
    "FEAT-PLAN-HINTS-W01-BACKEND-PACKET"
  ],
  "notes": [],
  "parent_packet_id": null,
  "review_target_packet_id": null,
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
