# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-WAVE-VERIFICATION

## Title
Report Workflow Wave Verification

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-WAVE-VERIFICATION`

## Packet Type
execution

## Summary
Verify W03 report workflow split with architect-authorized targeted tests, strict size evidence, and wave-final Report/Week observability.

## Wave
W03

## Role
verifier

## Reasoning
high

## Parent Packet
-

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION`

## Write Scope
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**

## Inputs
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W00-PLANNER-SLICING
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W00-ARCHITECT-FORMALIZATION
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION

## Acceptance Criteria
- W03 targeted report workflow, context, contract, fallback, and natal section tests pass.
- Strict backend/app size check passes with no allow-known-oversized files.
- Architect-authorized canonical flow commands emit fresh Report/Week evidence.
- today-week post-test review reports a clean verdict with no unexpected degradation.

## Verification Profile
- backend: W03 targeted pytest plus strict size checker with no known oversized allowlist.
- frontend: Not required; frontend is frozen and untouched.
- observability: Wave-final Report/Week post-test review with clean verdict required.
- execution:
  - backend_commands:
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_report_workflow_regression.py tests/test_report_context.py tests/test_report_contract.py tests/test_validation_template_fallback.py tests/test_natal_section_context.py
    - docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict
  - frontend_commands:
  - observability_scope: wave_final
  - canonical_flow_commands:
    - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_report_workflow_regression.py
  - observability_commands:
    - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
  - touches_frontend: False
  - requires_frontend_visual: False
  - artifact_globs:
    - logs/**/*.log
    - test-results/**/*
    - prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_commands:
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_report_workflow_regression.py tests/test_report_context.py tests/test_report_contract.py tests/test_validation_template_fallback.py tests/test_natal_section_context.py
  - docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict
- observability_commands:
  - python3 tools/post_test_review.py --profile today-week --since 30m --report-format md
- canonical_flow_commands:
  - docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_report_workflow_regression.py
- observability_scope: wave_final
- touches_frontend: False
- requires_frontend_visual: False
- artifact_globs:
  - logs/**/*.log
  - test-results/**/*
  - prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**
- include_day_live_canary: False

## Reviewer Gate
- Fresh canonical evidence follows the canonical_flow_commands, not stale logs.
- Observability verdict is clean; unexpected degradation blocks W04 final verification.
- Evidence identifies latest trace_id, report_id, or request_id where available.

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION

## Notes
- Use only architect-authorized W03 canonical flow commands.
- Do not run frontend E2E because frontend is frozen and untouched.

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-WAVE-VERIFICATION",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W03",
  "packet_type": "execution",
  "role": "verifier",
  "reasoning": "high",
  "title": "Report Workflow Wave Verification",
  "summary": "Verify W03 report workflow split with architect-authorized targeted tests, strict size evidence, and wave-final Report/Week observability.",
  "write_scope": [
    "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**"
  ],
  "inputs": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W00-PLANNER-SLICING",
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W00-ARCHITECT-FORMALIZATION",
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION"
  ],
  "acceptance_criteria": [
    "W03 targeted report workflow, context, contract, fallback, and natal section tests pass.",
    "Strict backend/app size check passes with no allow-known-oversized files.",
    "Architect-authorized canonical flow commands emit fresh Report/Week evidence.",
    "today-week post-test review reports a clean verdict with no unexpected degradation."
  ],
  "verification_profile": {
    "backend": "W03 targeted pytest plus strict size checker with no known oversized allowlist.",
    "frontend": "Not required; frontend is frozen and untouched.",
    "observability": "Wave-final Report/Week post-test review with clean verdict required.",
    "execution": {
      "backend_commands": [
        "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_report_workflow_regression.py tests/test_report_context.py tests/test_report_contract.py tests/test_validation_template_fallback.py tests/test_natal_section_context.py",
        "docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict"
      ],
      "frontend_commands": [],
      "observability_scope": "wave_final",
      "canonical_flow_commands": [
        "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_report_workflow_regression.py"
      ],
      "observability_commands": [
        "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
      ],
      "touches_frontend": false,
      "requires_frontend_visual": false,
      "artifact_globs": [
        "logs/**/*.log",
        "test-results/**/*",
        "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**"
      ]
    }
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "runner": "codex",
    "backend_commands": [
      "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_report_workflow_regression.py tests/test_report_context.py tests/test_report_contract.py tests/test_validation_template_fallback.py tests/test_natal_section_context.py",
      "docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict"
    ],
    "observability_commands": [
      "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md"
    ],
    "canonical_flow_commands": [
      "docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_report_workflow_regression.py"
    ],
    "observability_scope": "wave_final",
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "artifact_globs": [
      "logs/**/*.log",
      "test-results/**/*",
      "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**"
    ],
    "include_day_live_canary": false
  },
  "reviewer_gate": [
    "Fresh canonical evidence follows the canonical_flow_commands, not stale logs.",
    "Observability verdict is clean; unexpected degradation blocks W04 final verification.",
    "Evidence identifies latest trace_id, report_id, or request_id where available."
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION"
  ],
  "notes": [
    "Use only architect-authorized W03 canonical flow commands.",
    "Do not run frontend E2E because frontend is frozen and untouched."
  ],
  "parent_packet_id": null,
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-REPORT-WORKFLOW-RUNTIME-GENERATION-EXTRACTION",
  "route_classification": null,
  "requested_rework_mode": null,
  "rework_mode": null
}
END_FINAL_PACKET_CONTRACT_JSON
