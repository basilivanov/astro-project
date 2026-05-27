# Packet: FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER

## Title
Fix Missing LLM Parse Semantic Block End Marker

## GRACE IDs
- feature_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- wave_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01`
- packet_ref: `feature:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424:wave:W01:packet:FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER`

## Packet Type
rework

## Summary
Add the missing paired END_BLOCK for START_BLOCK: LLM_PARSE_VALIDATE in backend/app/llm/orchestrator_parse.py, then refresh W01 verifier evidence for GRACE marker pairing and targeted W01 checks.

## Wave
W01

## Role
verifier

## Reasoning
medium

## Parent Packet
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS`

## Review Target
`FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS`

## Write Scope
- backend/app/llm/orchestrator_parse.py
- prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**

## Inputs
- Verifier blocker: backend/app/llm/orchestrator_parse.py:51 has START_BLOCK: LLM_PARSE_VALIDATE without matching END_BLOCK
- Reviewer verdict: rework_required, route self_resolvable_rework, mode light_resume
- W01 verifier packet FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS

## Acceptance Criteria
- backend/app/llm/orchestrator_parse.py has a correctly paired END_BLOCK for LLM_PARSE_VALIDATE
- No unrelated code behavior, public imports, parsing semantics, LLM fallback semantics, or WeekBrief code is changed
- GRACE marker check shows matched START_BLOCK/END_BLOCK markers for orchestrator_parse.py
- W01-owned file sizes remain <=1000 lines
- W01 targeted tests still pass or verifier records why a narrower marker-only refresh is sufficient for this localized metadata fix

## Verification Profile
- backend: Run at minimum grep/marker pairing check for backend/app/llm/orchestrator_parse.py plus W01 size scan. Prefer rerun W01 targeted pytest if available: docker exec astro-project-backend-1 python3 -m pytest -q tests/test_llm_cli_parsing.py tests/test_llm_fallback_chain.py tests/test_llm_model_routing.py tests/test_week_brief_service.py tests/test_week_brief_api.py
- frontend: not required
- observability: packet_local evidence refresh only; degraded-but-expected remains acceptable because W01 does not own canonical Today/Week closeout

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
- requested_rework_mode: light_resume
- light_resume_downgrade_reason: light_resume is only allowed for coder packets

## Reviewer Gate
- Confirm the rework is limited to the missing semantic block marker and evidence artifacts
- Confirm no product behavior, API behavior, LLM validation behavior, or WeekBrief behavior changed
- Confirm refreshed evidence resolves the exact verifier blocker

## Dependencies
- FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS

## Notes
- Do not request planner; packet topology is unchanged
- Do not escalate to user; this is a local GRACE marker defect
- Do not broaden into W02/W03 oversized files

## Contract JSON
FINAL_PACKET_CONTRACT_JSON
{
  "packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-FIX-MISSING-LLM-PARSE-SEMANTIC-BLOCK-END-MARKER",
  "feature_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424",
  "wave_id": "W01",
  "packet_type": "rework",
  "role": "verifier",
  "reasoning": "medium",
  "title": "Fix Missing LLM Parse Semantic Block End Marker",
  "summary": "Add the missing paired END_BLOCK for START_BLOCK: LLM_PARSE_VALIDATE in backend/app/llm/orchestrator_parse.py, then refresh W01 verifier evidence for GRACE marker pairing and targeted W01 checks.",
  "write_scope": [
    "backend/app/llm/orchestrator_parse.py",
    "prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**"
  ],
  "inputs": [
    "Verifier blocker: backend/app/llm/orchestrator_parse.py:51 has START_BLOCK: LLM_PARSE_VALIDATE without matching END_BLOCK",
    "Reviewer verdict: rework_required, route self_resolvable_rework, mode light_resume",
    "W01 verifier packet FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS"
  ],
  "acceptance_criteria": [
    "backend/app/llm/orchestrator_parse.py has a correctly paired END_BLOCK for LLM_PARSE_VALIDATE",
    "No unrelated code behavior, public imports, parsing semantics, LLM fallback semantics, or WeekBrief code is changed",
    "GRACE marker check shows matched START_BLOCK/END_BLOCK markers for orchestrator_parse.py",
    "W01-owned file sizes remain <=1000 lines",
    "W01 targeted tests still pass or verifier records why a narrower marker-only refresh is sufficient for this localized metadata fix"
  ],
  "verification_profile": {
    "backend": "Run at minimum grep/marker pairing check for backend/app/llm/orchestrator_parse.py plus W01 size scan. Prefer rerun W01 targeted pytest if available: docker exec astro-project-backend-1 python3 -m pytest -q tests/test_llm_cli_parsing.py tests/test_llm_fallback_chain.py tests/test_llm_model_routing.py tests/test_week_brief_service.py tests/test_week_brief_api.py",
    "frontend": "not required",
    "observability": "packet_local evidence refresh only; degraded-but-expected remains acceptable because W01 does not own canonical Today/Week closeout"
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
    "rework_mode": "bounded_fresh",
    "requested_rework_mode": "light_resume",
    "light_resume_downgrade_reason": "light_resume is only allowed for coder packets"
  },
  "reviewer_gate": [
    "Confirm the rework is limited to the missing semantic block marker and evidence artifacts",
    "Confirm no product behavior, API behavior, LLM validation behavior, or WeekBrief behavior changed",
    "Confirm refreshed evidence resolves the exact verifier blocker"
  ],
  "dependencies": [
    "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS"
  ],
  "notes": [
    "Do not request planner; packet topology is unchanged",
    "Do not escalate to user; this is a local GRACE marker defect",
    "Do not broaden into W02/W03 oversized files"
  ],
  "parent_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS",
  "review_target_packet_id": "FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424-W01-VERIFY-W01-SIZE-GUARD-AND-SMALL-SERVICE-SPLITS",
  "route_classification": "self_resolvable_rework",
  "requested_rework_mode": "light_resume",
  "rework_mode": "bounded_fresh"
}
END_FINAL_PACKET_CONTRACT_JSON
