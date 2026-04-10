# Today/Week Detail-Layer Controlled Refactor Plan

## Goal
Bring `Today` and `Week` to one reusable, premium-looking detail-layer model without a blind rewrite. The refactor should preserve current surface behavior, reduce contract asymmetry, and allow staged rollout with minimal regression risk.

## 2026-04-10 Status
- Shared frontend detail contract is now implemented in `frontend/lib/detail-layer.ts` and reused by `Today` plus `Week` domain/action/risk disclosures.
- `frontend/lib/detail-layer.ts` now uses repo-local imports only; machine-specific filesystem paths are removed from runtime/test code.
- `Today` canonical happy-path is now limited to `day_brief_v1`; legacy payloads are rendered as explicit compatibility fallback instead of premium reconstruction.
- `Today` scored cards no longer allow score-without-explanation: if scoped evidence is thin, the renderer derives a bounded domain-safe explanation path instead of falling back to `объяснение недоступно`.
- `Today` timing windows now pass through a post-normalization step that merges adjacent identical windows and collapses labels into a finite product taxonomy instead of generator-looking duplicates.
- `Today` diagnostics now expose canonical / compatibility / degraded render-path markers in non-production builds, so screenshots from stale device bundles can be separated from real DTO/render regressions.
- `Week` now has split mappers in `frontend/lib/week-brief.ts`: canonical `week_brief` and compatibility `week_map/chunks` are no longer merged in one happy-path adapter.
- `/week` controller now mirrors `Today` more strictly: canonical screen requires `week_brief`, compatibility screen requires explicit legacy payload, and missing history without payload resolves to empty/create semantics instead of synthesized compatibility.
- `Week` day strip is intentionally compact-only; canonical mode stays brief, while compatibility mode is explicitly marked as fallback without pseudo-depth.
- `Week` main information architecture is now domain-led: hero -> weekly domains -> compact rhythm strip -> compact actions/risks -> optional supporting explainability -> optional deep reading.
- `Week` visible calendar shell is now hard Monday→Sunday. Canonical and compatibility modes share the same stable calendar order; if fewer than seven explicit day payloads exist, the strip keeps an honest empty skeleton instead of fabricating depth.

## Current State Summary

### Today
- `Today` already has item-level detail disclosure for scores, windows, and risks.
- Main contract lives in `frontend/lib/day-brief.ts` and supports:
  - `details.why_title`
  - `details.why_text`
  - `details.supporting_factors[]`
- UI implementation is concentrated in `frontend/components/today/daybrief-sections.tsx`.
- `Today` also has a second explainability lane via `explainability.selected_factors` and personalized factors.
- Scored domains must always surface one explanation path: scoped factors, scoped `why_text`, domain-matched explainability support, or a bounded domain-safe generic explanation.
- Window cards should feel productized, not generator-like: adjacent same-signal windows merge, repeated disclosure copy is capped, and labels stay inside a controlled vocabulary.

### Week
- `Week` uses several separate detail concepts instead of one unified detail-layer:
  - `domains[].why_text + supporting_factors[]`
  - `best_uses[]` / `risks[]` with `why_text + supporting_factors[]`
  - `major_factors[]` in explainability panel
  - `deep_sections[]` for long-form report rendering
- Main contract lives in `frontend/lib/week-brief.ts` and is flatter / less normalized than `DayBriefDto`.
- UI is split across:
  - `frontend/components/week/week-domain-panel.tsx`
  - `frontend/components/week/week-actions-panel.tsx`
  - `frontend/components/week/week-explainability-panel.tsx`
  - `frontend/components/week/week-deep-sections.tsx`
- Product priority is now explicit:
  - weekly domains are the default summary layer
  - Monday→Sunday strip is secondary drill-down
  - actions/risks stay compact support
  - deep sections remain optional long-form reading, not a competing main screen
  - compatibility fallback must stay visually lighter than canonical week and must never reuse giant day-feed semantics as the premium main surface

## Target Architecture

### 1. Unified Detail-Layer Concept
Use one common presentation model across `Today` and `Week`:
- **summary layer**: always-visible short verdict/action card
- **detail layer**: expandable explanation packet for the same card
- **deep layer**: optional long-form markdown/report content for report-grade reading

This means:
- `Today` keeps its current disclosure UX but moves onto a reusable renderer contract.
- `Week` stops inventing separate detail presentations for domains/actions/risks/explainability and instead maps them into the same detail packet shape.
- `deep_sections` remain a separate long-form layer, but visually and conceptually become “deep layer”, not a parallel explanation system.

### 2. Shared Frontend Contract
Introduce a frontend-only normalized contract that both pages map into before rendering:

```ts
export type DetailSupportingFactor = {
  id?: string | null;
  label: string;
  explanation_human: string;
  explanation_astro?: string | null;
  value?: string | null;
  impact?: "high" | "medium" | "low" | null;
  domain?: string | null;
  family?: string | null;
};

export type DetailLayer = {
  title?: string | null;
  summary?: string | null;
  why_text: string;
  supporting_factors: DetailSupportingFactor[];
  evidence_badges?: Array<{
    label: string;
    tone?: "neutral" | "good" | "warn";
  }>;
  cta_label?: string | null;
};
```

Recommended normalization rule:
- `why_text` = canonical body copy for disclosure content.
- `title` = optional UI headline (`why_title` in Today maps here).
- `summary` = optional one-line compact lead if the design needs a preview line.
- `supporting_factors[]` = one canonical shape for item-level evidence.
- `evidence_badges[]` = optional compact metadata chips (confidence, precision, source, timeframe).

### 3. Shared Reusable Component Shape
Build one small reusable UI primitive family instead of per-screen ad hoc disclosure blocks:
- `DetailDisclosureCard`
- `DetailFactorsList`
- `DetailEvidenceChips`

Recommended props shape:

```ts
type DetailDisclosureCardProps = {
  testId?: string;
  title: string;
  subtitle?: string | null;
  detail: DetailLayer | null;
  fallbackClosedLabel?: string;
  tone?: "default" | "positive" | "caution";
};
```

Render rules:
- If `detail` is absent, render only summary shell.
- If `detail.why_text` exists or factors exist, render one common disclosure trigger.
- Deduplicate semantically repeated factor text before render.
- Keep long-form markdown out of this component.

### 4. Day/Week Responsibility Split
- **Surface mappers** build normalized cards.
- **Reusable detail components** render them.
- **Deep sections renderer** stays separate for markdown/report blocks.

That gives a stable layering:
1. transport DTO (`day_brief`, `week_brief`)
2. page-level mapper (`TodayViewModel`, `WeekSurfaceModel`)
3. normalized detail-layer adapter
4. reusable disclosure components
5. page composition

For weekly composition, prefer:
1. `WeekHeroMap`
2. weekly domain cards
3. compact Monday→Sunday strip
4. compact actions / risks
5. optional supporting explainability
6. optional deep sections behind a lower-priority boundary

## Contract Strategy

### Frontend-only, no backend change needed
Can be done immediately by adapter/mapping only:
- Normalize Today `details` into `DetailLayer`
- Normalize Week `domains`, `best_uses`, `risks` into `DetailLayer`
- Move Week explainability cards onto same visual disclosure primitives
- Reuse semantic-deduping rules from `Today`
- Align tone/copy/layout between `Today` and `Week`

### Needs backend contract or mapping upgrade
Recommended, but not required for wave 1-2:
- Add explicit `details` object to `WeekBrief.domains[]`
- Add explicit `details` object to `WeekBrief.best_uses[]` and `WeekBrief.risks[]`
- Optionally add `details` / `supporting_factors` to `major_factors[]`
- Optionally expose a concise explainability support packet in `WeekBrief.explainability` parallel to `DayBrief.explainability.selected_factors_support`

Best long-term backend direction:
- converge `WeekBrief` item detail fields toward the same nested `details` shape already used by `DayBrief`
- keep `deep_sections` as long-form only
- avoid encoding UI-only labels in backend

## Recommended Waves

### Wave 1 — Frontend normalization seam
**Risk:** low
**Goal:** introduce shared detail-layer types and adapters without changing visible behavior much.

Changes:
- Add shared detail-layer types + mapping helpers.
- Adapt `Today` and `Week` data into the same normalized detail shape.
- Keep existing page layout/components mostly intact.

Deliverables:
- `frontend/lib/detail-layer.ts` (new)
- lightweight adapter helpers for Today and Week
- tests for normalization and dedupe behavior

Why first:
- creates one seam for refactor
- no backend dependency
- minimal UX risk

### Wave 2 — Reusable disclosure components
**Risk:** low-medium
**Goal:** replace bespoke item detail rendering with shared components.

Changes:
- Extract reusable `DetailDisclosureCard` / factors list / evidence chips.
- Migrate Today score/window/risk detail blocks first.
- Then migrate Week domains/actions/risks to the same primitive.

Deliverables:
- unified disclosure UX across Today/Week
- lower duplication in `daybrief-sections.tsx`
- smaller Week panel components

Why second:
- Today already has the richer behavior and is the right reference implementation.
- Week can adopt the proven renderer instead of inventing another path.

### Wave 3 — Explainability alignment
**Risk:** medium
**Goal:** bring `WeekExplainabilityPanel` into the same detail-layer system and separate “detail” from “deep report”.

Changes:
- Convert explainability factor cards to the same detail card primitive.
- Add optional evidence chips from `confidence`, `birth_time_used`, `top_signal_source`, `timing_precision`.
- Clarify UI hierarchy: summary explanation panel vs deep report sections.

Deliverables:
- one consistent detail language across Today and Week
- explainability panel looks like the same product family as item detail disclosures

Why third:
- this changes information architecture more visibly
- better done after the core disclosure renderer is stable

### Wave 4 — Backend contract convergence (optional but recommended)
**Risk:** medium-high
**Goal:** reduce adapter complexity by aligning `WeekBrief` item contracts to Day-style nested `details` packets.

Changes:
- update backend week brief model/builders/validators
- preserve backward compatibility at frontend mapper layer during rollout
- update API contract tests and docs

Deliverables:
- less asymmetric DTO design
- easier future reuse across Admin/Report surfaces

Why fourth:
- requires wider blast radius and stronger regression coverage
- not needed to unlock UI refactor

## Recommended Execution Order
1. Define `DetailLayer` contract and adapter utilities.
2. Add mapper tests for Today + Week normalized detail packets.
3. Extract reusable disclosure primitives from Today implementation.
4. Migrate Today to primitives with snapshot/interaction parity.
5. Migrate Week domains/actions/risks to primitives.
6. Align Week explainability panel to same family.
7. Re-evaluate if backend `WeekBrief` contract convergence still pays off.
8. Only then, if worth it, do backend nested `details` upgrade.

## Exact Write Scopes

### Wave 1 likely write scopes
- `frontend/lib/detail-layer.ts` (new)
- `frontend/lib/day-brief.ts`
- `frontend/lib/week-brief.ts`
- `frontend/test/lib/day-brief.test.ts`
- `frontend/test/lib/week-brief.test.ts`

### Wave 2 likely write scopes
- `frontend/components/detail/detail-disclosure-card.tsx` (new)
- `frontend/components/detail/detail-factors-list.tsx` (new)
- `frontend/components/detail/detail-evidence-chips.tsx` (new)
- `frontend/components/today/daybrief-sections.tsx`
- `frontend/components/week/week-actions-panel.tsx`
- `frontend/components/week/week-domain-panel.tsx`
- `frontend/test/components/today/daybrief-sections.test.tsx`
- new focused component tests under `frontend/test/components/detail/`

### Wave 3 likely write scopes
- `frontend/components/week/week-explainability-panel.tsx`
- `frontend/components/week/week-deep-sections.tsx` (only if hierarchy/copy needs tightening)
- `frontend/test/components/week-explainability-panel.test.tsx`
- `frontend/test/app/week-page.test.tsx`

### Wave 4 likely write scopes
- `backend/app/services/week_brief_types.py`
- `backend/app/services/week_brief.py` or corresponding builder source
- `backend/app/services/week_brief_validators.py`
- `tests/test_week_brief_service.py`
- `tests/test_week_brief_api.py`
- `docs/WEEKMAP_FACTORS.md`
- optionally `docs/TODAY_BLOCKS.md` if shared contract docs move there

## Concrete Contract Recommendation

### Canonical item-level contract going forward
For both `Today` and `Week`, prefer:

```ts
item: {
  id: string;
  title: string;
  summary?: string | null;
  advice?: string | null;
  detail?: DetailLayer | null;
}
```

Mapping examples:
- `Today score.details` → `detail`
- `Today window.details` → `detail`
- `Today risk.why_text + supporting_factors` → synthetic `detail`
- `Week domain.why_text + supporting_factors` → synthetic `detail`
- `Week best_use/risk why_text + supporting_factors` → synthetic `detail`
- `Week explainability factor` → synthetic `detail`

### Deep-layer contract remains separate
Keep report-grade markdown as:

```ts
type DeepSection = {
  id: string;
  slug: string;
  title: string;
  summary?: string | null;
  body_markdown: string;
  is_primary?: boolean;
  order?: number | null;
};
```

This avoids polluting item-level detail disclosure with long-form content.

## Risk Notes
- Biggest risk is mixing explainability, supporting factors, and report markdown into one overloaded component. Avoid that.
- `Today` already contains semantic dedupe logic; this should be extracted and reused, not reimplemented separately for `Week`.
- `WeekDeepSections` should remain opt-in long-form reading and not become the default explanation path for summary cards.
- Backend convergence should be contract-additive first, not destructive.

## Verification Profile Per Wave
- Wave 1-2 frontend changes:
  - targeted frontend tests for `Today` and `Week` detail interactions
  - `./scripts/run_e2e.sh --last-failed` or targeted `today-daybrief` / `week` specs
- Any backend WeekBrief change:
  - `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
  - targeted `tests/test_week_brief_service.py` and `tests/test_week_brief_api.py`
- After each substantial run, inspect observability evidence for Today/Week flows and record verdict (`clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`).

## Recommended Starting Point
Start with **Wave 1 + first half of Wave 2**:
- create `frontend/lib/detail-layer.ts`
- normalize Today/Week item detail packets
- extract one shared disclosure primitive
- migrate Today first
- only after Today parity, migrate Week domains/actions/risks

This gives maximum leverage with minimal blast radius and does not require backend changes.
