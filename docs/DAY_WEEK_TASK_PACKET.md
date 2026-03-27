
# Day/Week DTO & UI Controller Packet (Strict GRACE)

## Overview
- **Phase sequence:** `PHASE-DAY-BRIEF` → `PHASE-WEEK-BRIEF` → `PHASE-FRONTEND-TODAY` → `PHASE-FRONTEND-WEEK` → follow-up hardening.
- **Pilot slice:** consumer Today + Week surfaces in Telegram mini-app.
- **Modules touched:** M-DAY-BRIEF-SERVICE, M-WEEK-BRIEF-SERVICE, M-FACTS-CALC, M-API-GATEWAY, M-FRONTEND-TODAY, M-FRONTEND-WEEK, M-LLM-ORCHESTRATION, M-OPS-AUTOMATION.
- **Frozen surfaces:** App Router shell / ConsumerPageShell, BottomNav wiring, admin routes, catalog/store, billing flows, bot delivery.
- **Fixture policy:** deterministic mock payloads for Playwright specs; backend relies on local fixtures + fallback (no live LLM calls during tests).
- **Evidence expectation:** test logs, schema validation notes, telemetry samples; update TASK.md + relevant docs for each task.

## Wave 1 — Backend DTOs

### Task B1: DayBrief backend DTO
- **Provider / profile suggestion:** codex-codex2/gpt-5.4 (thinking: high)
- **Write scope:** backend/app/services/day_brief*.py, backend/app/feed_service.py, backend/app/main.py, tests/test_day_brief*.py, telemetry config, docs/TASK.md.
- **Must-preserve invariants:** legacy `/api/feed/today` fields; entitlement gating; feed cache behavior.
- **Scope:**
  - Implement `backend/app/services/day_brief_service.py` (types + validators) per `tmp/day_week_models.py` & `day_brief.schema.json`.
  - Integrate DayBrief build + fallback into `feed_service.py` and surface `day_brief` field in `/api/feed/today` (`backend/app/main.py`).
  - Add telemetry fields (`trace_id`, `generation_mode`, `birth_time_used`, `confidence_bucket`, `factor_count`) and log builder/fallback events.
  - Expand unit tests (`tests/test_day_brief.py` + new files if needed) to validate DTO construction, fallback, schema compliance.
- **Verification commands:**
  - `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
  - Schema validation snippet (`python3 - <<'PY' ... DayBrief.model_validate(...)` or dedicated test)
- **Evidence:** pipeline log excerpt, schema validation note, telemetry sample.
- **Gate condition:** `/api/feed/today` returns `day_brief` matching schema; fallback path works; legacy fields untouched.

### Task B2: WeekBrief backend DTO
- **Provider:** codex-codex3/gpt-5.4 (thinking: high)
- **Write scope:** backend/app/services/week_brief*.py, backend/app/services/report_workflow.py, backend/app/main.py, tests/test_week_brief*.py, tests/test_report_workflow_regression.py, docs/TASK.md.
- **Must-preserve:** report chunk lifecycle, `/api/reports/{id}` structure, deep read sections, polling cadence.
- **Scope:**
  - Create `backend/app/services/week_brief_service.py` (DTO assembly, envelope support) using `tmp/week_brief*.json` & `day_week_models.py`.
  - Extend `report_workflow.py` to export slow background layers (progressions, solar arc, profection/time lord, solar return, long transits) plus `week_data` seeds.
  - Attach `week_brief` (and optional `week_brief_envelope`) to `/api/reports/{id}` for `report_type="week_forecast"` while preserving `chunks[]`.
  - Add strict validators/tests (new `tests/test_week_brief_service.py` + updates to `tests/test_report_workflow_regression.py`).
- **Verification:** backend pipeline command above + targeted pytest for new suite.
- **Evidence:** pipeline log, pytest log, schema validation note, telemetry sample (`week_brief_built`).
- **Gate condition:** Completed week detail includes valid `week_brief`; telemetry emitted; deep sections unchanged.

## Wave 2 — Frontend surfaces

### Task F1: Today screen → DayBrief
- **Provider:** codex-codex6/gpt-5.4 (thinking: medium)
- **Write scope:** frontend/app/page.tsx, frontend/components/today/*, frontend/lib/day-brief*.ts, telemetry wiring, new Playwright spec + fixtures, docs/TASK.md.
- **Must-preserve:** ConsumerPageShell layout, BottomNav visibility rules, temporary legacy adapter fallback.
- **Scope:**
  - Add shared types/adapter (`frontend/lib/day-brief.ts`) to map API payload (with temporary legacy adapter fallback).
  - Rewrite `frontend/app/page.tsx` + today components to render exclusively from DTO (verdict, domain scores, windows, actions, risks, explainability, CTA, premium state).
  - Remove hero meta / legacy copy, ensure telemetry uses new events (`today.brief_view`, `today.score_tap`, etc.).
  - Create/update Playwright spec `frontend/e2e/today-daybrief.spec.ts` for deterministic mock payload.
- **Verification:** `npx tsc --noEmit`; `./scripts/run_e2e.sh e2e/today-daybrief.spec.ts`.
- **Evidence:** e2e log, screenshot (optional), lint/tsc output.
- **Gate condition:** Today page shows 5 required blocks from DTO; fallback path handles legacy.

### Task F2: Week screen → WeekBrief map
- **Provider:** codex-codex7/gpt-5.4 (thinking: medium)
- **Write scope:** frontend/app/week/page.tsx, frontend/components/week/*, frontend/lib/week-brief.ts, Playwright regression + fixtures, docs/TASK.md.
- **Must-preserve:** deep sections/markdown experience, polling/resume banner behavior.
- **Scope:**
  - Add types/adapter (`frontend/lib/week-brief.ts`), new components for hero (thesis/theme/week type), day grid, domain gauges, actions/risks list, explainability chips, CTA block.
  - Keep deep sections below as secondary layer with existing chunk renderer.
  - Update telemetry (`week.brief_view`, `week.day_card_click`, etc.).
  - Refresh Playwright regression `frontend/e2e/week-home-refresh.regression.spec.ts` with deterministic WeekBrief fixture.
- **Verification:** `./scripts/run_e2e.sh e2e/week-home-refresh.regression.spec.ts` + lint if needed.
- **Evidence:** e2e log, screenshot, adapter unit tests if added.
- **Gate condition:** Week map renders from DTO even if chunks degrade; deep sections remain available.

## Wave 3 — LLM & telemetry hardening (after Waves 1–2)

### Task L1: DayBrief/WeekBrief polish prompts & fallback templates
- **Provider:** codex-codex8/gpt-5.4 (thinking: medium)
- **Write scope:** backend/app/llm/*, fallback templates, telemetry docs.
- **Scope:** update prompts to JSON-only seeds, add deterministic fallback templates, ensure logging of prompt usage + failures.
- **Verification:** targeted unit/dry-run tests for prompt/fallback; pipeline if code touched.
- **Evidence:** prompt test log, fallback sample, doc update.

### Task L2: Analytics & adapters cleanup
- **Provider:** codex-codex9/gpt-5.4 (thinking: low)
- **Write scope:** removal of legacy builders (frontend/backend), analytics docs.
- **Scope:** remove `resolveDayMode`, `buildTimelineWindows`, etc. once DTO flows are live; update `docs/GRACE_ARTIFACTS.md`, `TASK.md`.
- **Verification:** lint/tsc + targeted tests for touched surfaces.
- **Evidence:** diffs, doc references.

## Controller notes
- Execute Wave 1 before Wave 2 (frontend depends on DTOs).
- Each worker must update `TASK.md`, relevant docs, and provide evidence (test logs, schema validation notes, telemetry samples).
- Use `tmp/day_week_models.py` & schema files as source of truth; no manual schema drift.
- If a specific `codex-codexN/gpt-5.4` profile is unavailable, reroute to another `codex-codexM/gpt-5.4` profile before switching providers.
