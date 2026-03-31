# NATAL_DAILY_BACKEND_EXECUTION_PACKET

## Mission
This packet defines the execution-ready GRACE handoff for the backend slice covering:
- natal generation reliability;
- day-brief / daily report generation quality and reliability;
- personalized daily feed contract safety relevant to the daily generation path.

This packet is documentation-only and intentionally excludes product feature work.

## Slice Coordinates
- Slice: `SL-NATAL-DAILY-BACKEND`
- Modules:
  - `M-NATAL-CONTEXT-ENGINE`
  - `M-NATAL-PROMPT-CONTRACT`
  - `M-NATAL-SUMMARY-LAYER`
  - `M-DAY-BRIEF-SERVICE`
  - `M-DAY-BRIEF-VALIDATORS`
  - `M-DAILY-FEED-PERSONALIZATION`

## Canonical Truth Paths

### 1. Natal generation truth path
- `backend/app/services/report_workflow.py` is the canonical truth source for natal section context, report context, section ordering, forecast windows, and deterministic fallback wiring.
- `section_context.insight_pack` is the priority deterministic substrate for premium natal sections, especially `executive_summary` and `final_synthesis`.
- `birth_time_known=false` is a hard gate: house-derived sections must be filtered upstream, not patched downstream.
- Summary-layer sections are high-risk because they can appear superficially “good” while drifting into generic content or repair leakage.

### 2. Prompt/runtime truth path
- `backend/app/llm/orchestrator.py` is the runtime prompt contract and bounded repair/fallback layer.
- `backend/app/reporting/section_templates.py` may be touched only if the slice requires contract text correction; prompt-only mitigation is not the preferred first move.
- Deterministic chart facts must remain primary. Prompt language may clarify expression, but must not become the hidden source of truth.

### 3. Day-brief truth path
- `backend/app/services/day_brief.py` orchestrates generation flow.
- `backend/app/services/day_brief_validators.py` is the acceptance barrier for malformed or incomplete output.
- `backend/app/services/day_brief_types.py` defines the typed/schema contract that downstream consumers rely on.
- Repair/fallback must transform malformed generation into readable contract-safe output or explicit failure, never silent schema drift.

### 4. Daily feed truth path
- `backend/app/services/personalized_daily.py` provides facts-first daily personalization and safe prompt summary material.
- `/api/feed/today` remains backward compatible and deterministic for the same cache scope.
- `personalized_daily_v2` is the pinned prompt contract.
- Auth-safe logging is mandatory; raw auth payloads must never appear in logs.

## Risk Register

### `R-NATAL-SUMMARY-DRIFT`
Risk: `executive_summary` and `final_synthesis` can pass superficially while becoming generic, repetitive, or repair-leaky.

Required handling:
- prefer deterministic insight-pack grounding;
- preserve explicit coverage of life scene/resource/risk/relationships/money/growth;
- reject generic motto-style synthesis.

### `R-NATAL-FALLBACK-MASKING`
Risk: fallback path can hide contract failure behind empty or low-value content.

Required handling:
- fallback must stay visible, useful, and chart-specific;
- deterministic fallback is preferred over soft-template filler.

### `R-DAY-BRIEF-SCHEMA-DRIFT`
Risk: repair logic can accidentally normalize malformed output into a payload that appears valid but breaks downstream assumptions.

Required handling:
- validators remain the acceptance gate;
- schema changes require explicit compatibility reasoning and regression updates.

### `R-DAILY-FEED-CONTRACT-DRIFT`
Risk: facts, prompt output, fallback payload, and logs drift apart, causing unstable feed behavior or auth leakage.

Required handling:
- facts builder remains first in flow;
- stable response shape and `traffic_lights` semantics are preserved;
- logs stay auth-safe.

## Allowed Write Scope
Only these paths are in scope for coder workers:
- `backend/app/services/report_workflow.py`
- `backend/app/llm/orchestrator.py`
- `backend/app/reporting/section_templates.py`
- `backend/app/services/day_brief.py`
- `backend/app/services/day_brief_validators.py`
- `backend/app/services/day_brief_types.py`
- `backend/app/services/personalized_daily.py`
- `tests/verify_natal_generation.py`
- `tests/test_day_brief.py`
- `tests/test_day_brief_schema.py`
- `tests/test_personalized_daily_service.py`
- `tests/test_daily_feed_robustness.py`

## Frozen Scope
Do not modify:
- `frontend/**`
- billing/checkout/catalog/product-rollout surfaces
- `bot/**`
- admin flows/surfaces
- horary/synastry/solar domain implementations beyond preserving current dependencies
- unrelated forecast/storefront slices

## Execution Waves

### Wave 1 — Natal truth-path audit
Goal:
- verify canonical ownership of section context, report context, and summary ordering.

Worker checklist:
- inspect `build_section_context`, `build_report_context`, `build_forecast_window`;
- confirm upstream `birth_time_known` gating;
- identify any hidden secondary truth sources.

Done when:
- no ambiguity remains about where natal facts originate;
- targeted natal truth-path tests pass.

### Wave 2 — Natal fallback/repair hardening
Goal:
- bound validator and fallback behavior for summary-layer failures.

Worker checklist:
- trace `generate_section_content` and fallback selectors;
- reproduce any repair leakage with a targeted test if missing;
- fix the root cause in the truth path or validator boundary before adjusting prompts.

Done when:
- summary-layer fallback is compact, chart-specific, and repair-safe;
- targeted natal validation/fallback tests pass.

### Wave 3 — Day-brief schema/validator hardening
Goal:
- preserve day-brief contract integrity under malformed or partial generation.

Worker checklist:
- map exact accepted schema in `day_brief_types` + `day_brief_validators`;
- add/update repro coverage for malformed outputs if needed;
- keep compatibility for existing consumers.

Done when:
- day-brief payloads are schema-valid and readable across success/repair/fallback paths.

### Wave 4 — Daily feed reliability hardening
Goal:
- keep the daily personalization path deterministic, auth-safe, and backward compatible.

Worker checklist:
- confirm `build_personalized_daily_facts()` remains first in flow;
- verify stable `traffic_lights` and prompt summary behavior;
- verify log safety and fallback shape.

Done when:
- targeted feed robustness bundle passes and contract drift is absent.

### Wave 5 — Handoff gate
Goal:
- ensure coder workers hand back exact PASS evidence and respect the frozen scope.

Worker checklist:
- run required commands;
- record any unresolved known gaps that remain outside this slice;
- do not claim broader product quality than the matrix proves.

## Required Verification
Run at minimum after each substantial backend change in this slice:
- `docker exec astro-project-backend-1 python3 scripts/pipeline.py`

Targeted bundles:
- `docker exec astro-project-backend-1 python3 -m pytest -q tests/verify_natal_generation.py tests/test_validation_relaxed.py tests/test_validation_template_fallback.py tests/test_report_contract.py`
- `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py`
- `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_daily_feed_robustness.py tests/test_personalized_daily_service.py tests/verify_daily_feed.py`
- optional contract probe: `python3 scripts/verify_api_responses.py`

## Known Out-of-Slice Gaps
These are known but intentionally not owned by this packet:
- frontend mock-only drift in some `core-ux` fallback/empty/error assertions;
- billing/runtime rollout behavior outside this backend slice;
- broader live editorial quality across all LLM/model permutations;
- non-natal/non-daily domains such as horary, synastry, solar, bot delivery, and admin surfaces.

## Worker Handoff Format
Any coder worker using this packet should hand back:
- exact files changed;
- exact commands run;
- PASS/FAIL result per verification bundle;
- unresolved risks, each explicitly tagged as in-slice or out-of-slice.
