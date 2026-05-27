# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-WAVE-VERIFICATION

## Title
API Gateway Wave Verification

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-WAVE-VERIFICATION`

## Packet Type
execution

## Summary
Verify W02 API gateway split with architect-authorized targeted tests, route evidence, strict size evidence, and wave-final Today/Week/Admin/Catalog observability.

## Wave
W02

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION`

## Write Scope
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W00-PLANNER-SLICING
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION

## Acceptance Criteria
- W02 targeted API/Admin/Access/Feed/Catalog tests pass.
- main.py is at or below 1000 physical lines while report_workflow.py may remain a known W03 oversized file.
- Architect-authorized canonical flow commands emit fresh Today/Week/Admin/Catalog evidence.
- today-week post-test review reports a clean verdict with no unexpected degradation.

## Verification Profile
- backend: W02 targeted pytest plus strict size checker with report_workflow.py as the only transitional known oversized file.
- frontend: Not required; frontend is frozen and untouched.
- observability: Wave-final Today/Week/Admin/Catalog post-test review with clean verdict required.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_api_contract_wave1.py tests/test_admin_api.py tests/test_access_control_integration.py tests/test_daily_feed_robustness.py tests/test_catalog_logging.py
    - docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict --allow-known-oversized backend/app/services/report_workflow.py
  - frontend_commands:
  - observability_scope: wave_final
  - canonical_flow_commands:
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_catalog_logging.py
  - observability_commands:
    - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
  - touches_frontend: False
  - requires_frontend_visual: False
  - artifact_globs:
    - logs/**/*.log
    - test-results/**/*
    - playwright-report/**/*
    - prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_commands:
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_api_contract_wave1.py tests/test_admin_api.py tests/test_access_control_integration.py tests/test_daily_feed_robustness.py tests/test_catalog_logging.py
  - docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict --allow-known-oversized backend/app/services/report_workflow.py
- observability_commands:
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- canonical_flow_commands:
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_catalog_logging.py
- observability_scope: wave_final
- touches_frontend: False
- requires_frontend_visual: False
- artifact_globs:
  - logs/**/*.log
  - test-results/**/*
  - playwright-report/**/*
  - prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**
- include_day_live_canary: False

## Reviewer Gate
- Fresh canonical evidence follows the canonical_flow_commands, not stale logs.
- Observability verdict is clean; unexpected degradation blocks W03.
- Evidence identifies latest trace_id, report_id, or request_id where available.

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION

## Notes
- Use only architect-authorized W02 canonical flow commands.
- Do not run frontend E2E because frontend is frozen and untouched.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-WAVE-VERIFICATION",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W02",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "API Gateway Wave Verification",
  "summary": "Verify W02 API gateway split with architect-authorized targeted tests, route evidence, strict size evidence, and wave-final Today/Week/Admin/Catalog observability.",
  "write_scope": [
    "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W00-PLANNER-SLICING",
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W00-ARCHITECT-FORMALIZATION",
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION"
  ],
  "acceptance_criteria": [
    "W02 targeted API/Admin/Access/Feed/Catalog tests pass.",
    "main.py is at or below 1000 physical lines while report_workflow.py may remain a known W03 oversized file.",
    "Architect-authorized canonical flow commands emit fresh Today/Week/Admin/Catalog evidence.",
    "today-week post-test review reports a clean verdict with no unexpected degradation."
  ],
  "verification_profile": {
    "backend": "W02 targeted pytest plus strict size checker with report_workflow.py as the only transitional known oversized file.",
    "frontend": "Not required; frontend is frozen and untouched.",
    "observability": "Wave-final Today/Week/Admin/Catalog post-test review with clean verdict required.",
    "execution": {
      "backend_commands": [
        "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_api_contract_wave1.py tests/test_admin_api.py tests/test_access_control_integration.py tests/test_daily_feed_robustness.py tests/test_catalog_logging.py",
        "docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict --allow-known-oversized backend/app/services/report_workflow.py"
      ],
      "frontend_commands": [],
      "observability_scope": "wave_final",
      "canonical_flow_commands": [
        "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_catalog_logging.py"
      ],
      "observability_commands": [
        "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
      ],
      "touches_frontend": false,
      "requires_frontend_visual": false,
      "artifact_globs": [
        "logs/**/*.log",
        "test-results/**/*",
        "playwright-report/**/*",
        "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**"
      ]
    }
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "runner": "codex",
    "backend_commands": [
      "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_api_contract_wave1.py tests/test_admin_api.py tests/test_access_control_integration.py tests/test_daily_feed_robustness.py tests/test_catalog_logging.py",
      "docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict --allow-known-oversized backend/app/services/report_workflow.py"
    ],
    "observability_commands": [
      "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
    ],
    "canonical_flow_commands": [
      "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_catalog_logging.py"
    ],
    "observability_scope": "wave_final",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "artifact_globs": [
      "logs/**/*.log",
      "test-results/**/*",
      "playwright-report/**/*",
      "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**"
    ],
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Fresh canonical evidence follows the canonical_flow_commands, not stale logs.",
    "Observability verdict is clean; unexpected degradation blocks W03.",
    "Evidence identifies latest trace_id, report_id, or request_id where available."
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION"
  ],
  "notes": [
    "Use only architect-authorized W02 canonical flow commands.",
    "Do not run frontend E2E because frontend is frozen and untouched."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-API-GATEWAY-ROUTER-EXTRACTION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
