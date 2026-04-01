# Rendered Gate Read surface wave-1 plan (bounded)

## Goal

Define the first bounded rendered-gate rollout wave for `FLOW-READ-SURFACE` so the repo can extend beyond Today/Week without overreaching the current artifact/review model.

This note is intentionally short and execution-oriented.

## Why Read goes next

`Read` is the closest adjacent surface to the current Today/Week pilot:
- it is primarily a read-only rendered surface rather than a mutation-heavy workflow;
- it already has route-level functional coverage on `/read/[id]` and adjacent report-read scenarios;
- it naturally links rendered evidence to `report_id` / `trace_id` / replay evidence;
- it exercises fallback handling, which is already a first-class concern in `VM-READ-QUALITY`.

## Wave-1 scope

Bounded target:
- one canonical `site_web` rendered scenario on `/read/[id]`;
- one canonical fallback/continuity rendered scenario on `/read/[id]`;
- optional parity preparation for Telegram harness, but not required for initial green gate.

Not in wave 1:
- full report-type matrix;
- billing/resume unlock branching as primary rendered gate;
- admin/report-ops readouts;
- broad `/reports/[id]` legacy-route parity.

## Minimal first scenarios

Take these first, in this order:

1. `read_rendered_wave1_site_web_primary`
   - route: `/read/[id]?mock=1`
   - report type: one stable completed report with visible structured sections
   - purpose: prove canonical read shell, section rendering, safe interaction, no runtime crash

2. `read_rendered_wave1_site_web_fallback`
   - route: `/read/[id]?mock=1`
   - report payload: completed report with malformed/raw chunk content that must still render readable fallback text
   - purpose: prove fallback is visible, intentional, and non-crashing

3. `read_rendered_wave1_site_web_continuity`
   - route: `/read/[id]?mock=1`
   - payload: known-time / whole-sign / continuity evidence case
   - purpose: prove continuity evidence survives rendering and does not regress into silent degradation

If the first wave must be cut further, keep only scenarios 1 and 2.

## Highest-value rendered invariants

Prefer invariants that are both user-meaningful and stable across fixture churn.

### Tier A — must-have
- `read.hero_present`
  - page hero and report title render
- `read.content_blocks_present`
  - at least one semantic content block or rendered section is visible
- `read.no_runtime_crash`
  - no `pageerror`, no fatal shell, no visible error boundary on success path
- `read.no_console_error`
  - no console `error` on load/primary interaction
- `read.fallback_text_visible_when_expected`
  - malformed/raw chunk content remains visible as readable fallback text

### Tier B — high-value, still stable
- `read.section_expand_safe`
  - accordion/section expansion works without breaking layout or content
- `read.chart_or_visual_safe`
  - if chart/SVG is present, it renders without crash
- `read.continuity_evidence_visible`
  - known-time / safe-mode / fixture continuity evidence remains visible when scenario expects it

### Avoid in first wave
- copy-fragile long text assertions;
- large report-type-specific semantic matrices;
- exact ordering assertions across all sections;
- visual-diff style invariants.

## Pass-mode policy for wave 1

Recommended approach: **phased**, not full `both` immediately.

Phase 1A:
- required: `site_web`
- optional: none
- gate meaning: prove Read can emit stable rendered artifacts on the same artifact/review stack as Today/Week

Phase 1B:
- add: `telegram_webapp` for the same primary scenario once harness parity is stable
- still optional: `both`

Phase 1C:
- add: `both` only after site and telegram have demonstrated the same compact invariant set on Read

Reasoning:
- current Today/Week pilot already proves `site_web` + `telegram_webapp` + `both` vocabulary and digest handling;
- Read has stronger dependence on route params, report payload shape, and continuity/fallback panels;
- forcing `both` in the first Read wave increases false negatives before stable cross-surface invariant groups are frozen.

## Likely touch files

Most likely first-wave write scope:
- `frontend/e2e/rendered-gate-wave1.spec.ts`
- `frontend/e2e/utils.ts`
- `tests/test_post_test_review.py`
- `tests/test_rendered_artifacts.py`
- `docs/RENDERED_GATE_PASS_MATRIX_SYNC.md`
- `docs/rendered_gate_read_surface_wave1_plan_2026-04-02.md`

Possible adjacent read-only context files to inspect, but not necessarily change:
- `frontend/app/read/[id]/page.tsx`
- `frontend/app/read/[id]/page-helpers.ts`
- `frontend/e2e/quality.spec.ts`
- `frontend/e2e/read-whole-sign-edge.spec.ts`
- `frontend/e2e/year-forecast-read.spec.ts`
- `frontend/e2e/ten-year-forecast-read.spec.ts`
- `tools/rendered_artifacts.py`
- `tools/post_test_review.py`

## Honest green verification package

For a truthful wave-1 green on Read, require all of the following:

1. Targeted rendered Playwright run
   - `./scripts/run_e2e.sh frontend/e2e/rendered-gate-wave1.spec.ts -g "Read|read"`
   - or exact targeted case names once added

2. Existing adjacent read functional proof
   - at minimum one of:
     - `./scripts/run_e2e.sh frontend/e2e/quality.spec.ts -g "report render|chart render|invalid report blocks|empty completed report"`
     - `./scripts/run_e2e.sh frontend/e2e/read-whole-sign-edge.spec.ts`
   - if fallback is part of the change, include the fallback-specific targeted read case as well

3. Backend quick profile
   - `docker exec astro-project-backend-1 python3 scripts/pipeline.py`

4. Post-test observability review
   - review rendered artifact JSON for Read
   - run `tools/post_test_review.py` on the latest relevant artifacts/logs
   - confirm `report_id` / `trace_id` / `request_id` linkage where available
   - explicit verdict must be one of:
     - `clean`
     - `degraded-but-expected`
     - `unexpected-degradation`
     - `no-evidence-blocker`

Wave-1 green is not honest if Playwright passes but rendered artifact linkage or post-test evidence is missing.

## Read-specific risks vs Today/Week

Read is easier than mutation-heavy surfaces, but riskier than Today/Week in a few specific ways:

1. Payload heterogeneity
   - `/read/[id]` must tolerate many report shapes, mixed chunk structures, raw text, and optional chart payloads.
   - Today/Week are already more normalized around dedicated view-models.

2. Fallback breadth
   - Read is explicitly responsible for safe rendering of malformed/legacy content.
   - This broadens acceptable output space and makes strict rendered assertions easier to overfit.

3. Route ownership ambiguity
   - public read behavior is split between `/read/[id]` and some lingering `/reports/[id]` semantics.
   - Today/Week have clearer canonical surfaces.

4. Entitlement/resume adjacency
   - Read can sit near checkout/resume/share flows and access-source metadata.
   - That creates more degradation paths than pure Today/Week readout pages.

5. Report-type matrix pressure
   - once Read enters rendered-gate rollout, stakeholders may try to treat one green scenario as proof for all report types.
   - the wave must stay bounded to one or two canonical scenarios first.

## Recommended execution order

1. Freeze Read wave-1 scenario list and invariant groups in docs.
2. Add `site_web` rendered artifact emission for one canonical Read success path.
3. Add `site_web` rendered artifact emission for one canonical Read fallback/continuity path.
4. Extend digest/review expectations for `FLOW-READ-SURFACE`.
5. Run targeted Playwright + backend quick.
6. Review rendered artifacts and observability evidence.
7. Only then decide whether Telegram parity is ready for phase 1B.
