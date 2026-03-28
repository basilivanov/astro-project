# Day/Week prompt bundles and fallbacks

This note documents the current Wave 5 prompt-hardening state for `DayBrief` and `WeekBrief`: prompt bundle versions, deterministic seeds, fallback-builder behavior, and where to inspect dry-run / telemetry evidence.

## Scope

- Day prompt bundle: `backend/app/services/day_brief.py`
- Week prompt bundle: `backend/app/services/week_brief_service.py`
- Seed assembly for week context: `backend/app/services/report_workflow.py`
- Regression coverage: `tests/test_day_week_prompts.py`

## Current prompt bundle versions

### DayBrief

- Constant: `DAY_BRIEF_PROMPT_VERSION = "day_brief_prompt_v2"`
- Builder: `build_day_brief_prompt_bundle(facts, general_vibe=...)`
- Output contract:
  - `version`: current registry version
  - `seed`: deterministic integer derived from facts
  - `model`: `deterministic_repo`
  - `prompt`: fully assembled prompt text for dry-run / inspection

The current prompt bundle intentionally keeps the prompt deterministic and narrow:

- uses only already prepared facts,
- bans inventing new entities / promises,
- fixes tone and output contract,
- injects semantic seeds such as `focus_key`, `headline`, `pacing`, and optional `general_vibe`.

### WeekBrief

- Constant: `WEEK_BRIEF_PROMPT_VERSION = "week_brief_prompt_v2"`
- Builder: `build_week_brief_prompt_bundle(seed)`
- Output contract:
  - `version`: current registry version
  - `seed`: deterministic integer derived from week inputs
  - `model`: `deterministic_repo`
  - `prompt`: fully assembled prompt text for dry-run / inspection

The week bundle is assembled from the normalized `week_brief_seed` context, including:

- week window / dates,
- summary traffic-light state,
- per-day statuses,
- semantic layer seeds,
- slow background context prepared in report workflow.

## Deterministic seeds

Both bundles use a stable integer seed so the prompt metadata and fallback copy remain reproducible in tests, diagnostics, and dry-runs.

### DayBrief seed

`backend/app/services/day_brief.py` uses `_stable_seed(*parts)` backed by SHA-256 and converts the first 8 hex chars to an integer.

Current DayBrief seed parts:

1. `local_dt.date().isoformat()`
2. `semantic.get("focus_key")`
3. `general_vibe`

In practical terms, the seed changes only when the local date, semantic focus, or explicitly supplied vibe changes.

### WeekBrief seed

`backend/app/services/week_brief_service.py` uses the same deterministic seed pattern, but the week seed is derived from week-level inputs.

The prompt test documents the active shape:

1. week window / day dates,
2. semantic `focus_key`,
3. summary or per-day traffic-light state.

The upstream context is assembled in `backend/app/services/report_workflow.py` by `_build_week_brief_seed_bundle(context)`, which prepares:

- `forecast_window`
- `summary`
- `days`
- `semantic_layer`
- `slow_background`

This split matters operationally: `report_workflow` decides the canonical seed payload, while `week_brief_service` turns it into deterministic prompt metadata and fallback output.

## Fallback builder behavior

Fallback mode is the guardrail path when LLM output is absent, invalid, or intentionally bypassed for deterministic inspection.

### DayBrief fallback

Main entrypoint: `build_day_brief_fallback(...)` in `backend/app/services/day_brief.py`.

Current behavior:

- always marks payload with `fallback_mode = True`,
- builds a valid summary/best-use/risk structure,
- uses deterministic semantic fallback copy instead of free-form generation,
- keeps headline / guide / actionable lines stable for the same seed inputs,
- overwrites the first `best_uses` and `risks` items with stable repo-owned text.

Important baseline copy currently comes from the constants:

- `DAY_FALLBACK_SUMMARY_HEADLINE`
- `DAY_FALLBACK_SUMMARY_GUIDE`
- `DAY_FALLBACK_BEST_USE`
- `DAY_FALLBACK_RISK`

This means fallback output is intentionally conservative, reviewable, and reproducible.

### WeekBrief fallback

Main entrypoint: `_build_week_brief_fallback(...)` in `backend/app/services/week_brief_service.py`.

Current behavior:

- returns a valid `WeekBrief`-shaped payload,
- always marks payload with `fallback_mode = True`,
- derives summary / best-use / risk text from deterministic week seed context,
- ties the copy to `week_brief_seed` semantic focus rather than ad-hoc model output,
- preserves telemetry metadata so operators can distinguish fallback from successful LLM assembly.

Operationally, week fallback depends on `context["week_brief_seed"]`. If that seed bundle is stable, fallback wording is stable too.

## Dry-run examples

The fastest reproducible examples live in `tests/test_day_week_prompts.py`.

### DayBrief dry-run

The test builds a prompt with:

- local datetime `2026-03-27T09:00:00+03:00`
- semantic focus `money_admin`
- headline seed `День любит аккуратный ход и ясную фиксацию.`
- pacing seed `Лучше идти короткими циклами.`
- `general_vibe="спокойный деловой фокус"`

Then it asserts:

- `version == DAY_BRIEF_PROMPT_VERSION`
- `model == "deterministic_repo"`
- `seed` is an integer
- prompt text contains the supplied `general_vibe`
- fallback payload has `fallback_mode is True`

Target reference: `tests/test_day_week_prompts.py:17`

### WeekBrief dry-run

The test builds a prompt from a deterministic seed bundle with:

- week starting `2026-03-30`
- all 7 days marked from the same normalized template
- summary traffic-light `YELLOW`
- semantic focus `launch`
- headline seed `Неделя просит собранного запуска.`

Then it asserts:

- `version == WEEK_BRIEF_PROMPT_VERSION`
- `model == "deterministic_repo"`
- `seed` is an integer
- prompt text contains the supplied semantic headline
- fallback payload has `fallback_mode is True`

Target reference: `tests/test_day_week_prompts.py:38`

## Telemetry and observability

### WeekBrief telemetry fields

`backend/app/services/week_brief_service.py` exposes prompt/fallback metadata through `_week_brief_log_fields(payload, prompt_meta=...)`.

Current logged fields include:

- `week_brief_confidence_bucket`
- `week_brief_confidence`
- `factor_count`
- `prompt_version`
- `prompt_seed`
- `week_brief_llm_model`

These fields are emitted into structured logs and mapped to quality events in the same module, including:

- `quality.schema_failure`
- `quality.fallback_activated`
- `quality.benchmark_linked`
- `quality.invalid_json`
- `quality.prompt_repair`
- `quality.repair_success`

This is the primary source of telemetry for answering:

- which prompt version produced the payload,
- which deterministic seed was used,
- whether fallback mode was activated,
- whether prompt repair / invalid JSON happened during assembly.

### DayBrief telemetry

DayBrief uses the same hardening philosophy: deterministic prompt metadata, fallback flagging, and structured logging from the service layer in `backend/app/services/day_brief.py`.

When documenting or debugging incidents, capture at minimum:

- prompt version,
- prompt seed,
- selected semantic focus,
- whether fallback mode activated,
- any validation failure that forced fallback.

## How to test

Primary regression target: `tests/test_day_week_prompts.py`

What it protects:

- current prompt bundle versions stay stable,
- deterministic repo model marker remains in place,
- seeds remain integers and reproducible,
- fallback builders continue returning non-empty deterministic payloads.

### Targeted pytest

Run the exact prompt/fallback regression with:

```bash
pytest tests/test_day_week_prompts.py
```

If needed, narrow to a single case:

```bash
pytest tests/test_day_week_prompts.py -k day
pytest tests/test_day_week_prompts.py -k week
```

### Backend acceptance command

Per repository protocol, the mandatory backend quick profile is:

```bash
docker exec astro-project-backend-1 python3 scripts/pipeline.py
```

Use this before handoff for any substantial backend/doc change that depends on backend behavior description.

### Recommended acceptance flow for this documentation task

1. `pytest tests/test_day_week_prompts.py`
2. `docker exec astro-project-backend-1 python3 scripts/pipeline.py`

## Acceptance checklist

- `docs/PROMPTS_AND_FALLBACKS.md` reflects current `v2` prompt bundle names.
- Deterministic seed sources are documented for day and week flows.
- Fallback behavior is described as deterministic and reviewable.
- Dry-run examples point to the canonical regression test.
- Telemetry section explains where `prompt_version`, `prompt_seed`, and fallback status come from.
- `docs/TASK.md` contains a task log entry for this documentation update.
