# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS

## Title
Fix W03 Report Workflow Extraction Regressions

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W03:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS`

## Packet Type
rework

## Summary
Fix the bounded W03 report workflow behavior regressions: restore the missing _join_sentence_parts dependency in the month forecast fallback path and preserve scene_seeds in the executive section prompt contract, then rerun targeted W03 report tests and refresh verifier evidence.

## Wave
W03

## Role
verifier

## Reasoning
high

## Parent Packet
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT`

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT`

## Write Scope
- backend/app/services/report_workflow.py
- backend/app/services/report_workflow*.py
- tests/test_report_context.py only if reproduction assertion needs alignment with preserved behavior
- tests/test_natal_section_context.py only if reproduction assertion needs alignment with preserved behavior
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**

## Inputs
- Verifier blocker: tests/test_report_context.py::test_month_forecast_fallback_uses_weekly_campaign_structure failed with NameError: _join_sentence_parts is not defined
- Verifier blocker: tests/test_natal_section_context.py::TestNatalSectionContext::test_facts_first_prompt_contract_and_validation failed because executive_spec.prompt is missing scene_seeds
- Reviewer verdict: rework_required, route self_resolvable_rework, mode bounded_fresh
- W03 verifier evidence shows strict size check passed, canonical W03 pytest passed, backend quick passed, and observability was clean

## Acceptance Criteria
- Month forecast fallback path can call or import _join_sentence_parts without NameError
- executive_spec.prompt preserves the required scene_seeds prompt contract token
- No report workflow lifecycle, persistence, notification, chart calculation, API, auth, billing, or frontend behavior is changed
- report_workflow.py and extracted report_workflow*.py modules remain <=1000 lines
- Targeted W03 report pytest passes for tests/test_report_workflow_regression.py tests/test_report_context.py tests/test_report_contract.py tests/test_validation_template_fallback.py tests/test_natal_section_context.py
- If backend code changes are made, rerun the canonical W03 tests and record updated evidence
- Wave-final observability remains clean or any new blocker is narrowed to a concrete W03 cause

## Verification Profile
- backend: Run targeted W03 report tests: docker exec astro-project-backend-1 python3 -m pytest -q tests/test_report_workflow_regression.py tests/test_report_context.py tests/test_report_contract.py tests/test_validation_template_fallback.py tests/test_natal_section_context.py. Also rerun docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict and canonical W03 pytest if code changed: docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_report_workflow_regression.py.
- frontend: not required
- observability: wave_final evidence refresh required; rerun python3 tools/post_test_review.py --profile read-only --since 30m --report-format md after backend verification

## Execution Hints
- workdir: /opt/astro-project
- sandbox: danger-full-access
- runner: codex
- backend_profile: backend_quick
- observability_profile: read-only
- observability_commands:
  - python3 tools/post_test_review.py --profile read-only --since 30m --report-format md
- artifact_globs:
  - logs/*.jsonl
  - test-results/**/*.json
  - test-results/**/*.md
  - prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/**
- touches_frontend: False
- requires_frontend_visual: False
- include_day_live_canary: False
- rework_mode: bounded_fresh

## Reviewer Gate
- Confirm rework is limited to the two W03 report workflow extraction regressions and evidence refresh
- Confirm failed targeted tests now pass
- Confirm size limit remains satisfied for report_workflow.py and extracted modules
- Confirm no product behavior or report workflow lifecycle drift
- Confirm observability remains clean

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT

## Notes
- Do not request planner; packet topology is unchanged
- Do not escalate to user; blockers are local extraction compatibility defects
- Do not broaden into W04 final verification work
- Do not edit frontend; no visual proof is required

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-FIX-W03-REPORT-WORKFLOW-EXTRACTION-REGRESSIONS",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W03",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "high",
  "title": "Fix W03 Report Workflow Extraction Regressions",
  "summary": "Fix the bounded W03 report workflow behavior regressions: restore the missing _join_sentence_parts dependency in the month forecast fallback path and preserve scene_seeds in the executive section prompt contract, then rerun targeted W03 report tests and refresh verifier evidence.",
  "write_scope": [
    "backend/app/services/report_workflow.py",
    "backend/app/services/report_workflow*.py",
    "tests/test_report_context.py only if reproduction assertion needs alignment with preserved behavior",
    "tests/test_natal_section_context.py only if reproduction assertion needs alignment with preserved behavior",
    "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**"
  ],
  "inputs": [
    "Verifier blocker: tests/test_report_context.py::test_month_forecast_fallback_uses_weekly_campaign_structure failed with NameError: _join_sentence_parts is not defined",
    "Verifier blocker: tests/test_natal_section_context.py::TestNatalSectionContext::test_facts_first_prompt_contract_and_validation failed because executive_spec.prompt is missing scene_seeds",
    "Reviewer verdict: rework_required, route self_resolvable_rework, mode bounded_fresh",
    "W03 verifier evidence shows strict size check passed, canonical W03 pytest passed, backend quick passed, and observability was clean"
  ],
  "acceptance_criteria": [
    "Month forecast fallback path can call or import _join_sentence_parts without NameError",
    "executive_spec.prompt preserves the required scene_seeds prompt contract token",
    "No report workflow lifecycle, persistence, notification, chart calculation, API, auth, billing, or frontend behavior is changed",
    "report_workflow.py and extracted report_workflow*.py modules remain <=1000 lines",
    "Targeted W03 report pytest passes for tests/test_report_workflow_regression.py tests/test_report_context.py tests/test_report_contract.py tests/test_validation_template_fallback.py tests/test_natal_section_context.py",
    "If backend code changes are made, rerun the canonical W03 tests and record updated evidence",
    "Wave-final observability remains clean or any new blocker is narrowed to a concrete W03 cause"
  ],
  "verification_profile": {
    "backend": "Run targeted W03 report tests: docker exec astro-project-backend-1 python3 -m pytest -q tests/test_report_workflow_regression.py tests/test_report_context.py tests/test_report_contract.py tests/test_validation_template_fallback.py tests/test_natal_section_context.py. Also rerun docker exec astro-project-backend-1 python3 scripts/check_size_limits.py --root backend/app --strict and canonical W03 pytest if code changed: docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_report_workflow_regression.py.",
    "frontend": "not required",
    "observability": "wave_final evidence refresh required; rerun python3 tools/post_test_review.py --profile read-only --since 30m --report-format md after backend verification"
  },
  "execution_hints": {
    "workdir": "/opt/astro-project",
    "sandbox": "danger-full-access",
    "runner": "codex",
    "backend_profile": "backend_quick",
    "observability_profile": "read-only",
    "observability_commands": [
      "python3 tools/post_test_review.py --profile read-only --since 30m --report-format md"
    ],
    "artifact_globs": [
      "logs/*.jsonl",
      "test-results/**/*.json",
      "test-results/**/*.md",
      "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/evidence/**"
    ],
    "touches_frontend": false,
    "requires_frontend_visual": false,
    "include_day_live_canary": false,
    "rework_mode": "bounded_fresh"
  },
  "reviewer_gate": [
    "Confirm rework is limited to the two W03 report workflow extraction regressions and evidence refresh",
    "Confirm failed targeted tests now pass",
    "Confirm size limit remains satisfied for report_workflow.py and extracted modules",
    "Confirm no product behavior or report workflow lifecycle drift",
    "Confirm observability remains clean"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT"
  ],
  "notes": [
    "Do not request planner; packet topology is unchanged",
    "Do not escalate to user; blockers are local extraction compatibility defects",
    "Do not broaden into W04 final verification work",
    "Do not edit frontend; no visual proof is required"
  ],
  "parent_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT",
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W03-VERIFY-W03-REPORT-WORKFLOW-SPLIT",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
