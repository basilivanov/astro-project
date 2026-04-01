# Frontend Structural Audit — strict GRACE

Date: 2026-04-01
Scope: `frontend` surfaces for Today, Week, Create/Billing, Profile/Onboarding, Start/Home.
Rules applied: strict GRACE, `<=1000` lines per file, `<=4000` tokens per function.

## Method
- Reviewed `AGENTS.md` and `GRACE.md`.
- Inspected target route surfaces and shared modules.
- Checked for `START_MODULE_CONTRACT`, `START_MODULE_MAP`, function contracts, and semantic `START_BLOCK`/`END_BLOCK` coverage.
- Measured file line counts and approximate function token counts from TS/TSX AST.

## Surface verdicts

### 1. Today / Home
- `frontend/app/page.tsx`: partially compliant.
- Strengths: has module contract; home telemetry flow is explicit.
- Gaps: no module map; large monolithic page component `FeedPage` (`418` lines file, main function ~`1565` tokens); semantic blocks are sparse relative to surface complexity; helper contracts are mostly absent.
- `frontend/components/today/daybrief-sections.tsx`: structurally weak under strict GRACE.
- Strengths: componentized UI.
- Gaps: no module contract, no module map, no function contracts, no semantic blocks; file is large (`595` lines) and serves as mixed domain+presentation registry.
- `frontend/lib/day-brief.ts`: structurally weak under strict GRACE.
- Strengths: function sizes are acceptable.
- Gaps: no module contract/map, no function contracts, no semantic blocks; central Today normalization logic is unannotated.

### 2. Week
- `frontend/app/week/page.tsx`: materially under-annotated.
- Strengths: file size acceptable (`328` lines); child panels already split.
- Gaps: no module contract, no module map, no function contracts, effectively no semantic blocks; main function `WeekPageContent` is ~`1634` tokens and owns too many concerns (fetching, state, telemetry, rendering).
- `frontend/lib/week-brief.ts`: moderate hotspot.
- Strengths: under file/function hard limits.
- Gaps: no contract/map/block coverage; main mapper `mapWeekReportToWeekBrief` is ~`1495` tokens and is a likely drift point.
- `frontend/components/week/*.tsx`: good direction on file size, but missing uniform module contracts and block-level semantic coordinates.

### 3. Create / Billing
- `frontend/app/create/create-page-client.tsx`: critical structural hotspot.
- Strengths: best current GRACE instrumentation in target scope; has module contract/map and multiple semantic blocks.
- Hard limit breach: file is `1435` lines (`>1000`), main function `CreatePageContent` is ~`8828` tokens (`>4000`).
- Additional hotspots: `handleCheckout` ~`1073` tokens, `renderProductInputPanel` ~`1004` tokens, `handleCreateReport` ~`587` tokens.
- Structural issue: one mega-component still owns orchestration, state machine, side effects, checkout resumption, and rendering.
- `frontend/app/create/create-page-logic.ts`: healthy base module, but lacks strict-GRACE annotations.
- `frontend/components/catalog/catalog-checkout-resume.tsx`: high but not over limit; `445` lines, main component ~`3012` tokens.
- Gaps: no visible module contract/map in audited slice output; should be treated as near-threshold reusable flow module.
- `frontend/app/billing/complete/billing-complete-page-client.tsx`: under hard limits, but no module contract/map/function contracts; main component ~`1571` tokens still mixes resume orchestration with UI.
- `frontend/components/catalog/create-shared.ts`: manageable size, but missing full annotation coverage for a shared domain contract module.
- `frontend/components/catalog/catalog-analytics.ts`: strong example; has module contract/map and function contracts.
- `frontend/lib/product-billing.ts`: small, but lacks module contract/map; suitable quick-win annotation target.

### 4. Profile / Onboarding
- `frontend/app/profile/page.tsx`: relatively mature.
- Strengths: has module contract/map and some semantic blocks.
- Gaps: function contracts are still uneven; file size (`373` lines) is acceptable.
- `frontend/app/onboarding/profile/page.tsx`: high-priority annotation gap.
- Strengths: file size okay (`267` lines).
- Gaps: no module contract, no module map, almost no block contracts; main function `OnboardingPage` ~`2773` tokens and couples step UX, form submission, validation wiring, and routing.

### 5. Start / Gateway
- `frontend/app/start/page.tsx`: best-in-class strict-GRACE surface in this audit.
- Strengths: has explicit module contract/map, named block registry, function contracts, trace-oriented semantics.
- Remaining gap: some helper lambdas remain anonymous; could be normalized later, but not priority.

### 6. Read / Home-adjacent relevant surface
- `frontend/app/read/[id]/page.tsx`: critical hotspot adjacent to Create/Billing and report consumption.
- Strengths: has module contract/map and multiple function contracts/blocks.
- Hard risk: file is `967` lines, very close to `1000` cap; main function `ReadReportPageContent` is ~`6126` tokens (`>4000`).
- Verdict: not immediately in the named surface list, but relevant enough to include because it is tightly coupled to Create/Billing and content consumption flows.

## Hotspots vs hard limits

### File size hotspots
1. `frontend/app/create/create-page-client.tsx` — `1435` lines — **BREACH**
2. `frontend/app/read/[id]/page.tsx` — `967` lines — **NEAR LIMIT**
3. `frontend/components/today/daybrief-sections.tsx` — `595` lines — **WATCH**
4. `frontend/components/catalog/catalog-checkout-resume.tsx` — `537` lines — **WATCH**
5. `frontend/lib/week-brief.ts` — `501` lines — **WATCH**

### Function size hotspots
1. `frontend/app/create/create-page-client.tsx:137` `CreatePageContent` — ~`8828` tokens — **BREACH**
2. `frontend/app/read/[id]/page.tsx:133` `ReadReportPageContent` — ~`6126` tokens — **BREACH**
3. `frontend/components/catalog/catalog-checkout-resume.tsx:93` `CatalogCheckoutResumeBanner` — ~`3012` tokens — **HIGH**
4. `frontend/app/onboarding/profile/page.tsx:16` `OnboardingPage` — ~`2773` tokens — **HIGH**
5. `frontend/app/week/page.tsx:73` `WeekPageContent` — ~`1634` tokens — **MEDIUM**
6. `frontend/app/billing/complete/billing-complete-page-client.tsx:21` `BillingCompletePageClient` — ~`1571` tokens — **MEDIUM**
7. `frontend/app/page.tsx:179` `FeedPage` — ~`1565` tokens — **MEDIUM**
8. `frontend/lib/week-brief.ts:222` `mapWeekReportToWeekBrief` — ~`1495` tokens — **MEDIUM**

## Missing strict-GRACE artifacts

### Missing or incomplete module contracts / maps
- Missing module contract + module map:
  - `frontend/app/week/page.tsx`
  - `frontend/app/onboarding/profile/page.tsx`
  - `frontend/app/billing/complete/billing-complete-page-client.tsx`
  - `frontend/components/today/daybrief-sections.tsx`
  - `frontend/lib/week-brief.ts`
  - `frontend/lib/day-brief.ts`
  - `frontend/lib/product-billing.ts`
- Has module contract but missing module map:
  - `frontend/app/page.tsx`
- Likely needs contract review despite partial maturity:
  - `frontend/components/catalog/catalog-checkout-resume.tsx`
  - `frontend/components/catalog/create-shared.ts`

### Missing function contracts on critical logic
- `frontend/app/page.tsx`: `normalizeProfile`, `normalizeMockProfile`, `resolveMockToday`, `fetchJson`, `FeedPage`, CTA handlers.
- `frontend/app/week/page.tsx`: `WeekPageContent` and fetch/interaction callbacks.
- `frontend/app/onboarding/profile/page.tsx`: `OnboardingPage`, `submitForm`, `handleNext`.
- `frontend/app/billing/complete/billing-complete-page-client.tsx`: `BillingCompletePageClient`, `resumeCheckout`.
- `frontend/lib/day-brief.ts`: payload normalizers and legacy adapter functions.
- `frontend/lib/week-brief.ts`: mapper/repair helpers.
- `frontend/lib/product-billing.ts`: all exported helpers.

### Missing semantic START_BLOCK / END_BLOCK coverage
- Major absence in:
  - `frontend/app/week/page.tsx`
  - `frontend/app/onboarding/profile/page.tsx`
  - `frontend/app/billing/complete/billing-complete-page-client.tsx`
  - `frontend/components/today/daybrief-sections.tsx`
  - `frontend/lib/day-brief.ts`
  - `frontend/lib/week-brief.ts`
- Partial/inconsistent block semantics in:
  - `frontend/app/page.tsx`
  - `frontend/components/catalog/catalog-checkout-resume.tsx`

## Prioritized remediation plan

### Priority 0 — split first, before more annotation
1. Split `frontend/app/create/create-page-client.tsx`.
   - Extract orchestration hook/module: checkout session sync, report creation, draft restore, token/bootstrap.
   - Extract render surfaces: product input panel, checkout state panel, result/error panel.
   - Keep page entrypoint thin with module map pointing to submodules.
2. Split `frontend/app/read/[id]/page.tsx`.
   - Extract read-report controller hook, share/resume action helpers, failure-state panel composition.
   - Reduce page file well below `900` lines and main function below `4000` tokens.

### Priority 1 — annotate and bound route controllers
3. Add full module contract + module map + function contracts + semantic blocks to:
   - `frontend/app/week/page.tsx`
   - `frontend/app/onboarding/profile/page.tsx`
   - `frontend/app/billing/complete/billing-complete-page-client.tsx`
   - `frontend/app/page.tsx` (add missing module map and function contracts)
4. Introduce explicit `M-*` IDs for Today/Week/Profile-Onboarding/Billing modules and stable block IDs for fetch, fallback, CTA, and redirect flows.

### Priority 2 — annotate domain adapters before business drift
5. Add module contracts/maps and function contracts to:
   - `frontend/lib/day-brief.ts`
   - `frontend/lib/week-brief.ts`
   - `frontend/lib/product-billing.ts`
   - `frontend/components/catalog/create-shared.ts`
6. In `frontend/lib/week-brief.ts`, split `mapWeekReportToWeekBrief` into smaller normalization stages with named contracts.
7. In `frontend/components/today/daybrief-sections.tsx`, separate pure content builders from presentational cards and annotate each exported section component.

### Priority 3 — harden near-threshold reusable surfaces
8. Refactor `frontend/components/catalog/catalog-checkout-resume.tsx` before it crosses hard complexity limits.
   - Split polling/sync state from visual banner rendering.
   - Add module contract/map if absent and semantic blocks for restore, resume, cancel.
9. Normalize `frontend/components/week/*.tsx` and Today child components with lightweight module contracts where they participate in active write scope.

## Suggested execution waves
- Wave A: `create-page-client` split.
- Wave B: `read/[id]/page.tsx` split.
- Wave C: route annotation pass for `page.tsx`, `week/page.tsx`, `onboarding/profile/page.tsx`, `billing-complete-page-client.tsx`.
- Wave D: domain adapter annotation/refactor for `day-brief.ts`, `week-brief.ts`, `product-billing.ts`.
- Wave E: reusable UI module cleanup for `daybrief-sections.tsx`, `catalog-checkout-resume.tsx`, `components/week/*`.

## Audit conclusion
- The frontend already contains pockets of strict-GRACE discipline (`start/page.tsx`, `catalog-analytics.ts`, parts of `create-page-client.tsx`, `read/[id]/page.tsx`, `profile/page.tsx`).
- The main structural risk is not just missing comments/contracts; it is concentration of orchestration inside a few mega-functions and under-annotated domain adapters.
- First remediation should target the two token-limit breaches, then add contract/map/block coverage to route controllers and normalization modules.
