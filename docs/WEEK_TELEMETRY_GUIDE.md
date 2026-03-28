# WeekBrief Telemetry Guide

## Purpose

This guide systematizes WeekBrief telemetry across generation and UX layers so week telemetry can be correlated with catalog, resume, and quality events using the same identifiers.

## Canonical sources

### Backend generation
- `backend/app/services/week_brief_service.py`
- Responsible for deterministic WeekBrief assembly, fallback handling, validation, and quality/log emission.
- Canonical source for generation-phase payload shape, fallback mode, and correlation/flow propagation from backend logging helpers.

### Frontend week surface
- `frontend/app/week/page.tsx`
- Orchestrates week screen telemetry for surface view and interactive UX events.
- Defines the week page telemetry context (`surface`, `flow_id`) and passes click handlers into week UI blocks.

### Frontend week blocks
- `frontend/components/week/week-hero-map.tsx`
- `frontend/components/week/week-day-grid.tsx`
- `frontend/components/week/week-domain-panel.tsx`
- `frontend/components/week/week-actions-panel.tsx`
- `frontend/components/week/week-explainability-panel.tsx`
- `frontend/components/week/week-deep-sections.tsx`
- These files define the visual block boundaries and stable UI anchors (`data-testid`, block semantics) that telemetry should map to.

## Telemetry model

WeekBrief telemetry should be read in three layers:
- **generation** — backend built/validated/fell back while preparing the WeekBrief payload.
- **surface view** — frontend opened/rendered the `/week` surface.
- **interaction UX** — frontend user actions inside week blocks.

Use these canonical dimensions for all WeekBrief events:
- `flow_id` — ties WeekBrief interactions to the commercial/reading flow.
- `surface` — identifies the product surface where the event happened.
- `block_id` — identifies the concrete UI block or generation stage.
- `correlation_id` / request correlation — ties backend generation and frontend UX into one trace when available.

## Canonical identifiers

### `flow_id`
Recommended canonical value for WeekBrief telemetry:
- `flow_id=week_brief`

When WeekBrief is opened from a broader commercial bridge or storefront flow, preserve the upstream flow where appropriate and keep `week_brief` as the local reading flow marker. If the existing frontend constant uses a broader forecast/catalog flow, WeekBrief docs should still describe the local semantic flow as `week_brief` and note the bridge relationship explicitly.

### `surface`
Recommended WeekBrief surface values:
- `surface=week_view` — main `/week` screen render.
- `surface=week_generation` — backend generation/validation/fallback stage.
- `surface=week_resume_banner` — resume/return entrypoint shown on week surface.

### `block_id`
Recommended stable block identifiers:
- `week_generation`
- `week_hero`
- `week_day_grid`
- `week_day_card`
- `week_domain_panel`
- `week_domain_card`
- `week_primary_cta`
- `week_actions_panel`
- `week_risks_panel`
- `week_explainability_panel`
- `week_deep_sections`
- `week_resume_banner`

## Event inventory

### Generation events
Backend generation telemetry originates in `backend/app/services/week_brief_service.py` through logging/quality helpers.

Recommended event family:
- `week_brief.generation_started`
- `week_brief.generation_succeeded`
- `week_brief.generation_fallback`
- `week_brief.generation_failed`
- `quality.schema_failure` / sibling quality events when validation fails

Expected dimensions:
- `flow_id=week_brief`
- `surface=week_generation`
- `block_id=week_generation`
- `week_start`, `week_end`
- `fallback_mode`
- `prompt_version=week_brief_prompt_v2`
- correlation identifiers from `get_correlation_ids()` when present

Interpretation:
- generation success/fallback/failure is the backend source of truth;
- frontend should not invent generation status independently;
- quality telemetry is the canonical way to diagnose schema/contract degradation.

### UX events
Frontend UX telemetry is centered in `frontend/app/week/page.tsx` and mapped to week blocks in `frontend/components/week/*`.

Recommended event family:
- `week_brief.view`
- `week_brief.day_card_open`
- `week_brief.domain_open`
- `week_brief.cta_click`
- `week_brief.resume_banner_impression`
- `week_brief.resume_banner_click`

#### `week_brief.view`
Meaning:
- first stable render/open of the week page.

Dimensions:
- `flow_id=week_brief`
- `surface=week_view`
- `block_id=week_hero` for the landing hero context, or `week_view` as a page-level block if page-scope telemetry is separated
- `fallback_mode`
- optional summary dimensions such as `week_type`, `traffic_light`, `domain_count`, `day_count`

Source anchors:
- `frontend/app/week/page.tsx`
- `frontend/components/week/week-hero-map.tsx`

#### `week_brief.day_card_open`
Meaning:
- user opens/selects a day card from the week grid.

Dimensions:
- `flow_id=week_brief`
- `surface=week_view`
- `block_id=week_day_card`
- `day`
- `weekday`
- `mode`
- `index`

Source anchors:
- `frontend/app/week/page.tsx`
- `frontend/components/week/week-day-grid.tsx`

#### `week_brief.domain_open`
Meaning:
- user expands/navigates into a domain detail from the domain panel.

Dimensions:
- `flow_id=week_brief`
- `surface=week_view`
- `block_id=week_domain_card`
- `domain_key`
- `domain_title`
- `domain_value`
- `index`

Source anchors:
- `frontend/components/week/week-domain-panel.tsx`

Note:
- if current UI is read-only and no click exists yet, keep this event documented as the intended semantic event bound to a future expand/open affordance instead of overloading impressions.

#### `week_brief.cta_click`
Meaning:
- primary monetization/continuation action from the week hero.

Dimensions:
- `flow_id=week_brief`
- `surface=week_view`
- `block_id=week_primary_cta`
- `cta_kind=primary`
- `target_surface` or `target_flow` when known

Source anchors:
- `frontend/app/week/page.tsx`
- `frontend/components/week/week-hero-map.tsx`

#### `week_brief.resume_banner_impression` and `week_brief.resume_banner_click`
Meaning:
- user sees or clicks resume/return banner connected to unfinished catalog/checkouts/read flows.

Dimensions:
- `flow_id=week_brief` plus upstream resume/catalog flow when present
- `surface=week_resume_banner`
- `block_id=week_resume_banner`
- `resume_kind`
- `target_product`
- `resume_state`

Source anchors:
- week entry surface and shared resume/banner integrations
- relationship documented against `docs/CATALOG_CHECKOUT_RESUME_BANNER.md`

## Block mapping

Stable telemetry-to-UI mapping:
- `week_hero` → `frontend/components/week/week-hero-map.tsx`
- `week_day_grid` / `week_day_card` → `frontend/components/week/week-day-grid.tsx`
- `week_domain_panel` / `week_domain_card` → `frontend/components/week/week-domain-panel.tsx`
- `week_actions_panel` → `frontend/components/week/week-actions-panel.tsx`
- `week_risks_panel` → `frontend/components/week/week-actions-panel.tsx`
- `week_explainability_panel` → `frontend/components/week/week-explainability-panel.tsx`
- `week_deep_sections` → `frontend/components/week/week-deep-sections.tsx`
- `week_primary_cta` → `frontend/components/week/week-hero-map.tsx`

## Relationship to catalog and resume telemetry

WeekBrief telemetry should align with storefront/catalog telemetry rather than creating a separate incompatible taxonomy.

Shared principles:
- keep `correlation_id` stable across catalog entry → checkout/resume → read/week surface;
- preserve upstream commercial `flow_id` when WeekBrief is reached from catalog/storefront funnels;
- add local `surface=week_view` or `surface=week_resume_banner` so week behavior is still queryable independently;
- treat CTA clicks as handoff points between read telemetry and catalog telemetry.

Practical linkage with `docs/CATALOG_CHECKOUT_RESUME_BANNER.md`:
- resume banner impressions/clicks on week should use the same resume semantics as catalog/read surfaces;
- if the banner returns the user to an unfinished purchase or a previously unlocked reading, keep the same resume token/state dimensions;
- if week primary CTA opens a storefront/catalog destination, emit both the local week CTA event and the downstream catalog event with a shared correlation/flow chain.

## Relationship to quality telemetry

WeekBrief quality telemetry belongs to the same operational family documented in `docs/QUALITY_TELEMETRY_RUNBOOK.md`.

Key rules:
- validation/schema regressions should emit `quality.*` events from backend generation code;
- fallback activation is operationally meaningful and should be queryable both as week generation telemetry and as a quality signal;
- UX telemetry must not hide backend degradation: a successful `week_brief.view` can coexist with `week_brief.generation_fallback` or `quality.schema_failure`.

Recommended joins:
- join `week_brief.view` with backend `week_brief.generation_*` by correlation/request identifiers;
- join `quality.schema_failure` with `week_brief.generation_fallback` to measure how often users saw safe-mode week pages;
- join week CTA/resume events with quality events to detect whether degraded generation impacts monetization or continuation.

## Operational reading flow

Canonical WeekBrief journey:
1. backend starts WeekBrief generation;
2. backend validates payload and emits success/fallback/quality events;
3. frontend opens `week_view` and emits page-view telemetry;
4. user interacts with day cards, domains, CTA, or resume banner;
5. downstream catalog/resume/read flows continue with shared correlation context.

## Commands

Documentation-only task, but WeekBrief telemetry touches backend generation semantics. For task acceptance and neighboring regression safety, mention these canonical commands:
- `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- `./scripts/run_e2e.sh --last-failed`

If/when week-specific UI telemetry wiring changes beyond docs, add targeted Playwright coverage, for example:
- `./scripts/run_e2e.sh e2e/quality.spec.ts -g "week"`

## Acceptance checklist

- `docs/WEEK_TELEMETRY_GUIDE.md` exists and documents generation + UX events.
- Canonical sources are listed: backend WeekBrief service, week page, and week UI components.
- `flow_id`, `surface`, and `block_id` are standardized for WeekBrief.
- WeekBrief linkage to catalog/resume telemetry is documented.
- WeekBrief linkage to quality telemetry is documented.
- Task record in `docs/TASK.md` mentions the added documentation and canonical verification commands.
