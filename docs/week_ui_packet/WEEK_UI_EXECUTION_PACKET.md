# Week UI Execution Packet

Packet id: `SLICE-WEEK-UI-EXECUTION`
Parent docs: `requirements.xml`, `development-plan.xml`, `verification-matrix.md`
Reference packet: `docs/today_screen_packet`

## Purpose

This packet prepares the next Week/UI execution slice for coder workers.
It does not introduce new product features.
It freezes the Week top-layer contract so workers can refine or stabilize `/week` without drifting into backend business-logic invention or deep-report redesign.

## Source-of-truth summary

- Canonical top-layer DTO is `WeekBrief` / `WeekBriefEnvelope`.
- Backend owns week calculations, day scoring, domain aggregation, report linkage, and factor assembly.
- Frontend owns adaptation and presentation via `frontend/lib/week-brief.ts` and `frontend/app/week/page.tsx`.
- Legacy `week_map` is fallback input, not a license to reintroduce frontend business logic.
- Deep markdown report content remains secondary in `/read/[id]`, not the primary Week screen layer.

## Execution intent

Implementers should treat `/week` as a strict layered surface:

1. state boundary,
2. top hero/theme,
3. week day-map,
4. domain/practical guidance,
5. factor-backed explainability,
6. CTA/report or premium path,
7. compact fallback transparency.

Do not add new sections unless they clearly map to existing DTO semantics.
Do not move week logic into the frontend.
Do not turn top layer into a markdown summary of the full report.

## Semantic coordinates

### `COORD-WEEK-HERO`

- Purpose: one semantic center for the week.
- Primary DTO fields:
  - `summary`
  - `status`
  - `explainability.confidence`
  - `reportId` / `cta.primary`
- UI expectation:
  - one hero/theme block,
  - concise framing,
  - no duplicate deep-report prose,
  - no competing second headline.

### `COORD-WEEK-DAY-MAP`

- Purpose: show the structure of the week as ordered day cards.
- Primary DTO field:
  - `day_cards[]`
- Each card should remain semantically stable:
  - `date`
  - `weekday`
  - `score`
  - `mode`
  - `headline`
  - `best_for[]`
  - `avoid[]`
- UI expectation:
  - cards are ordered by week chronology,
  - each card reads as a practical day snapshot,
  - frontend does not recompute score logic.

### `COORD-WEEK-DOMAINS`

- Purpose: convert week guidance into actionable domains.
- Primary DTO fields:
  - `domains[]`
  - optional `best_uses[]`
  - optional `risks[]`
- UI expectation:
  - compact domain cards,
  - polished user-facing wording,
  - no raw category/service labels leaking through.

### `COORD-WEEK-FACTORS`

- Purpose: explain why the week gets its framing.
- Primary DTO fields:
  - `major_factors[]`
  - `explainability.confidence`
  - `explainability.birth_time_used`
- UI expectation:
  - bounded explainability blocks,
  - visible rationale through labels/explanations/impact,
  - trust context stays compact and non-technical.

### `COORD-WEEK-CTA`

- Purpose: give the user a clear next action.
- Primary DTO fields:
  - `cta.primary`
  - `reportId`
  - `status`
  - optional `premium`
- UI expectation:
  - if `reportId` exists, CTA defaults to opening full report,
  - otherwise CTA routes to premium/create flow,
  - telemetry event names remain stable.

### `COORD-WEEK-FALLBACK`

- Purpose: degrade safely when strict WeekBrief data is partial or absent.
- Primary inputs:
  - `week_brief_envelope.data`
  - `week_brief`
  - fallback adapter from `week_map`
  - mock/default payloads used for local/dev path
- UI expectation:
  - compact fallback note via `week-fallback-note`,
  - usable screen remains visible,
  - no raw JSON/debug fields,
  - no silent semantic confusion about whether data is ready.

## DTO → UI mapping

## Backend inputs

- `backend/app/main.py`
  - report lookup and `/api/reports/:id` payload handoff
  - `week_brief_envelope`, `week_brief`, `week_map`
- `backend/app/services/week_brief_service.py`
  - deterministic WeekBrief assembly
- `backend/app/services/week_map.py`
  - fallback-compatible week map and legacy normalization source

## Frontend adapter boundary

- `frontend/lib/week-brief.ts`
  - canonical frontend normalization layer
  - maps `week_brief` first,
  - may adapt `week_map` as bounded fallback,
  - must not invent new score/domain logic

## Frontend surface boundary

- `frontend/app/week/page.tsx`
  - owns fetch/init state,
  - chooses loading/error/ready path,
  - resolves CTA,
  - triggers analytics,
  - renders fallback note when adapter enters fallback mode.

## Frozen mapping rules

- `week_brief_envelope.data` wins over plain `week_brief` when present.
- Envelope/report `status` must remain visible in state logic even if UI text is compact.
- `week_map` fallback is allowed only through adapter normalization.
- `reportId` presence controls open-report path more strongly than copy heuristics.
- `explainability` supports trust/explanation and telemetry; it is not a dumping ground for raw backend diagnostics.

## Acceptance criteria

- `/week` remains a WeekBrief-driven surface, not a mixed legacy assembly.
- State boundaries are explicit: loading, error, ready, in-progress, fallback, report/premium CTA.
- Hero/theme remains single-center and concise.
- Day cards remain chronologically stable and sourced from DTO data.
- Domain/factor/CTA blocks are clearly mapped to DTO ownership.
- Fallback mode remains visible, compact, and safe.
- Verification profile is deterministic and Week-targeted.

## Write scope

Allowed write scope for coder workers in this slice:

- `frontend/app/week/page.tsx`
- `frontend/components/week/*`
- `frontend/lib/week-brief.ts`
- `frontend/e2e/week-live.spec.ts`
- `frontend/e2e/week-page-fallback.spec.ts`
- `frontend/e2e/week-fallback.regression.spec.ts`
- `frontend/e2e/week-home-refresh.regression.spec.ts`
- `backend/app/services/week_brief_service.py`
- `backend/app/services/week_map.py`
- `backend/app/main.py`
- `tests/*week*`

## Frozen scope

Do not expand into these areas for this slice:

- `frontend/app/page.tsx`
- `frontend/components/today/*`
- `frontend/app/read/*`
- `frontend/app/history/*`
- `frontend/app/profile/*`
- `backend/app/services/day_brief*`
- `billing/*`
- `infra/*`

## Verification

Minimum required profile for substantial Week/UI change:

- `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- `./scripts/run_e2e.sh e2e/week-home-refresh.regression.spec.ts`
- `./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts`

Add when touched area requires it:

- `./scripts/run_e2e.sh e2e/week-fallback.regression.spec.ts`
- `./scripts/run_e2e.sh e2e/week-live.spec.ts`

Evidence expectations:

- exact commands,
- PASS/FAIL result,
- files changed,
- VM IDs closed,
- note on fallback-path impact when relevant.

## Execution waves

### `WAVE-WEEK-STATE-AND-STRUCTURE-FIRST`

Start here.

Goal:
- stabilize top-layer state handling and visible structure before copy polish.

Worker focus:
- loading/error/in-progress/ready handling,
- report lookup to adapter handoff,
- fallback note behavior,
- CTA resolution,
- non-duplicative hero/day-map structure.

Done when:
- Week screen cannot silently mix conflicting states,
- fallback path is safe,
- target verification profile is green.

### `WAVE-WEEK-EXPLAINABILITY-AND-POLISH-NEXT`

Only after first wave is green.

Goal:
- refine factor/explainability/domain presentation without changing product scope.

Worker focus:
- major factors readability,
- confidence/birth-time trust context,
- domain card polish,
- preserving strict DTO ownership.

Done when:
- visible explainability is clearer,
- no raw technical leakage appears,
- deep report remains separate from top layer.

## Notes for coder workers

- If a needed field is missing, prefer documenting or extending DTO shape at the service/adapter boundary rather than recreating logic inside components.
- If page behavior depends on `week_brief` vs `week_map`, make that distinction explicit in code and verification.
- If a change touches fallback behavior, update or add the narrowest Week spec that reproduces the issue.
- Do not code unrelated product improvements under this packet.
