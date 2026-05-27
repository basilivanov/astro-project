# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE

## Title
Refresh W02 Canonical Observability Evidence

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W02:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE`

## Packet Type
rework

## Summary
Generate or repair fresh W02 wave-final Today, Week, Admin, and Catalog evidence, investigate the Week unexpected-degradation signals, rerun the W02 observability review, and record a clean verdict or a concrete localized cause if clean evidence cannot be produced.

## Wave
W02

## Role
verifier

## Reasoning
high

## Parent Packet
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT`

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT`

## Write Scope
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**
- logs/*.jsonl
- test-results/**/*.json
- test-results/**/*.md
- backend/app/routers/*.py only if investigation finds a W02 route/logging regression
- backend/app/main.py only if investigation finds a W02 route/logging regression
- tests/test_*api*.py only if a missing W02 evidence reproduction test is needed
- tests/test_admin_api.py only if a missing Admin evidence reproduction test is needed
- tests/test_catalog_logging.py only if a missing Catalog evidence reproduction test is needed
- tests/test_daily_feed_robustness.py only if a missing Today evidence reproduction test is needed
- tests/test_week_brief_api.py only if a missing Week evidence reproduction test is needed

## Inputs
- Verifier blocker: today-week observability review failed with FAIL_NO_EVIDENCE
- Verifier blocker: Today flow classified no-evidence-blocker despite fresh API log samples
- Verifier blocker: Week flow classified unexpected-degradation due chunk parse degradation/fallback samples
- Verifier blocker: Admin/Catalog log evidence is stale relative to W02 verification
- Reviewer verdict: rework_required, route self_resolvable_rework, mode bounded_fresh

## Acceptance Criteria
- Fresh W02 Today evidence has concrete trace_id/request_id/correlation_id and is no longer classified no-evidence-blocker
- Fresh W02 Week evidence is clean, or any degradation is traced to a concrete expected non-W02 cause and documented for reviewer decision
- Fresh Admin and Catalog evidence is newer than the rework verification run and includes relevant structured log samples
- python3 tools/post_test_review.py --profile today-week --since 30m --report-format md is rerun and the verdict is clean, or the remaining blocker is narrowed to a concrete product/pipeline cause
- W02 route/API behavior remains unchanged; rerun targeted W02 tests if any backend code changes are made
- backend/app/main.py remains <=1000 lines

## Verification Profile
- backend: If code changes are made, rerun W02 targeted tests: docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_catalog_logging.py && docker exec astro-project-backend-1 python3 -m pytest -q tests/test_api_contract_wave1.py tests/test_admin_api.py tests/test_access_control_integration.py tests/test_daily_feed_robustness.py tests/test_catalog_logging.py. Always confirm wc -l backend/app/main.py.
- frontend: not required
- observability: wave_final clean required for W02; rerun python3 tools/post_test_review.py --profile today-week --since 30m --report-format md plus inspect fresh logs/feed.jsonl, logs/report.jsonl, logs/admin.jsonl, and logs/catalog.jsonl

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
- Confirm rework is limited to W02 observability freshness/degradation blockers unless a direct W02 route/logging regression is found
- Confirm Today/Week/Admin/Catalog evidence is fresh relative to the rework run
- Confirm Week degradation is resolved or narrowed to a concrete expected non-W02 cause
- Confirm no API/auth/schema behavior drift

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT

## Notes
- Do not request planner; packet topology is unchanged
- Do not escalate to user unless the investigation proves a product/business decision is needed
- Do not broaden into W03 report_workflow refactor work
- No frontend visual proof is required because W02 did not touch UI

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-REFRESH-W02-CANONICAL-OBSERVABILITY-EVIDENCE",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W02",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "high",
  "title": "Refresh W02 Canonical Observability Evidence",
  "summary": "Generate or repair fresh W02 wave-final Today, Week, Admin, and Catalog evidence, investigate the Week unexpected-degradation signals, rerun the W02 observability review, and record a clean verdict or a concrete localized cause if clean evidence cannot be produced.",
  "write_scope": [
    "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**",
    "logs/*.jsonl",
    "test-results/**/*.json",
    "test-results/**/*.md",
    "backend/app/routers/*.py only if investigation finds a W02 route/logging regression",
    "backend/app/main.py only if investigation finds a W02 route/logging regression",
    "tests/test_*api*.py only if a missing W02 evidence reproduction test is needed",
    "tests/test_admin_api.py only if a missing Admin evidence reproduction test is needed",
    "tests/test_catalog_logging.py only if a missing Catalog evidence reproduction test is needed",
    "tests/test_daily_feed_robustness.py only if a missing Today evidence reproduction test is needed",
    "tests/test_week_brief_api.py only if a missing Week evidence reproduction test is needed"
  ],
  "inputs": [
    "Verifier blocker: today-week observability review failed with FAIL_NO_EVIDENCE",
    "Verifier blocker: Today flow classified no-evidence-blocker despite fresh API log samples",
    "Verifier blocker: Week flow classified unexpected-degradation due chunk parse degradation/fallback samples",
    "Verifier blocker: Admin/Catalog log evidence is stale relative to W02 verification",
    "Reviewer verdict: rework_required, route self_resolvable_rework, mode bounded_fresh"
  ],
  "acceptance_criteria": [
    "Fresh W02 Today evidence has concrete trace_id/request_id/correlation_id and is no longer classified no-evidence-blocker",
    "Fresh W02 Week evidence is clean, or any degradation is traced to a concrete expected non-W02 cause and documented for reviewer decision",
    "Fresh Admin and Catalog evidence is newer than the rework verification run and includes relevant structured log samples",
    "python3 tools/post_test_review.py --profile today-week --since 30m --report-format md is rerun and the verdict is clean, or the remaining blocker is narrowed to a concrete product/pipeline cause",
    "W02 route/API behavior remains unchanged; rerun targeted W02 tests if any backend code changes are made",
    "backend/app/main.py remains <=1000 lines"
  ],
  "verification_profile": {
    "backend": "If code changes are made, rerun W02 targeted tests: docker exec astro-project-backend-1 python3 -m pytest -q tests/test_backend_grace_wave_finish.py tests/test_catalog_logging.py && docker exec astro-project-backend-1 python3 -m pytest -q tests/test_api_contract_wave1.py tests/test_admin_api.py tests/test_access_control_integration.py tests/test_daily_feed_robustness.py tests/test_catalog_logging.py. Always confirm wc -l backend/app/main.py.",
    "frontend": "not required",
    "observability": "wave_final clean required for W02; rerun python3 tools/post_test_review.py --profile today-week --since 30m --report-format md plus inspect fresh logs/feed.jsonl, logs/report.jsonl, logs/admin.jsonl, and logs/catalog.jsonl"
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
    "Confirm rework is limited to W02 observability freshness/degradation blockers unless a direct W02 route/logging regression is found",
    "Confirm Today/Week/Admin/Catalog evidence is fresh relative to the rework run",
    "Confirm Week degradation is resolved or narrowed to a concrete expected non-W02 cause",
    "Confirm no API/auth/schema behavior drift"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT"
  ],
  "notes": [
    "Do not request planner; packet topology is unchanged",
    "Do not escalate to user unless the investigation proves a product/business decision is needed",
    "Do not broaden into W03 report_workflow refactor work",
    "No frontend visual proof is required because W02 did not touch UI"
  ],
  "parent_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT",
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W02-VERIFY-W02-API-GATEWAY-SPLIT",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "bounded_fresh",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
