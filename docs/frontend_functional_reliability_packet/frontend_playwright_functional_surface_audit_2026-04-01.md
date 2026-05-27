# Frontend Playwright Functional Surface Audit

Date: 2026-04-01  
Project root: `/opt/astro-project`  
Scope: frontend functional reliability audit only; docs/read-only mapping for Playwright execution planning.

## 1. Purpose

This document converts the current frontend into an execution-ready Playwright reliability map.

Target intent:
- guard the important user-facing routes against load/runtime failure;
- prove that primary taps/clicks/navigation/submit flows still work;
- prove that high-value business paths still reach the intended outcome;
- add touch/swipe coverage where the UI explicitly depends on mobile gesture semantics;
- use screenshots where they add strong signal without making the suite brittle;
- make it operationally realistic to target roughly **95% functional reliability of important surfaces**, not 95% DOM coverage.

This is a companion audit to the existing packet files in `docs/frontend_functional_reliability_packet/`.

## 2. Inputs reviewed

Reviewed sources:
- `/opt/astro-project/AGENTS.md`
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/docs/frontend_functional_reliability_packet/FRONTEND_FUNCTIONAL_RELIABILITY_EXECUTION_PACKET.md`
- `/opt/astro-project/docs/frontend_functional_reliability_packet/requirements.slice.frontend-functional-reliability.xml`
- `/opt/astro-project/docs/frontend_functional_reliability_packet/development-plan.slice.frontend-functional-reliability.xml`
- `/opt/astro-project/docs/frontend_functional_reliability_packet/verification-matrix.slice.frontend-functional-reliability.md`
- `/opt/astro-project/frontend/playwright.config.cjs`
- current Playwright inventory under `frontend/e2e/**`
- frontend route inventory under `frontend/app/**`
- relevant interactive components under `frontend/components/**`

## 3. Executive assessment

The project already has a meaningful Playwright estate with good coverage in these areas:
- core shell and route-console hygiene;
- report create and several business-path storefront bridges;
- admin smoke and several admin workflows;
- week and read-path regressions;
- visual baselines for a small set of core screens.

However, the current suite does **not yet look like a full frontend surface map**. It is stronger on selected flows than on systematic route-by-route guarding. The main reliability gaps are:
- some user-facing routes exist but are not clearly guarded by route-load/navigation tests;
- several interactive surfaces are component-rich but only partially checked for tap/click behavior;
- mobile-only gesture semantics exist in code but are sparsely represented in Playwright;
- console/pageerror/request-failure guards are present in some specs, but not yet consistently enforced across all critical routes;
- visual assertions exist, but the strategy is still too narrow to catch layout regressions on several high-value screens.

Conclusion: the repo is **well past zero**, but still needs a structured second-wave Playwright program to reach a credible ~95% functional reliability target for important user-facing behavior.

## 4. Route inventory mapped into functional surfaces

### 4.1 Consumer / public / authenticated user routes

| Route | Functional surface | Importance | Interaction type | Current state (approx) | Notes |
| --- | --- | --- | --- | --- | --- |
| `/` | Home / today feed | P0 | load, CTA tap, score/detail expansion, nav | partially covered | `core-ux`, `today-daybrief`, `traffic-lights`, `visual`; should remain a top smoke route |
| `/start` | startup / boot routing gateway | P0 | load, redirect, continuation routing | covered | `start-gateway.spec.ts`; needs ongoing guard because redirects are business-critical |
| `/landing` | marketing landing | P1 | load, CTA tap, legal links | covered | `landing.spec.ts`; visual/layout also relevant |
| `/create` | report create / paywall / purchase entry | P0 | form fill, product selection, submit, paywall branch | covered but fragmented | multiple create/storefront specs exist; still needs canonical surface matrix |
| `/billing/complete` | payment completion / resume / back path | P0 | load, auto-continue, back tap, swipe-back | partially covered | `billing-yoomoney-return.spec.ts`; explicit swipe/back semantics need stronger dedicated coverage |
| `/profile` | profile overview | P1 | load, referral/copy, navigation to edit | partially covered | `profile.referral`, `profile-vasily-toggle`, visual; should include route-level console guard |
| `/profile/edit` | profile edit form | P0 | fill/edit/save/back | covered | `profile-edit.spec.ts`; still should include explicit failure/validation variant |
| `/onboarding/profile` | first-run profile onboarding | P0 | fill, next, redirect | likely undercovered | no clearly named dedicated spec in inventory |
| `/reports` | storefront/catalog | P0 | card taps, product routing, bridge semantics | covered | many bridge specs rely on it; visual and route-console still important |
| `/reports/history` | user history | P1 | load, CTA/open existing report | covered | `history-cta.spec.ts` |
| `/read/[id]` | canonical read surface | P0 | load, section expand, content read, no runtime crash | covered for some report types | strong but should be made type-matrix explicit |
| `/reports/[id]` | direct report detail / legacy route | P1 | load and action availability | partially covered | appears used by natal master UI specs; must clarify ownership with `/read/[id]` |
| `/week` | weekly guidance interactive page | P0 | load, day tap, CTA tap, fallback, deep sections | strongly covered | week suite is one of the strongest areas |
| `/prices` | pricing info | P2 | load, links/CTA | not clearly covered | cheap route smoke candidate |
| `/share` | share surface | P2 | load, share/copy/deeplink | not clearly covered | route exists but no obvious dedicated spec |
| `/support` | support form | P1 | back nav, topic select, textarea, submit | undercovered | route has form behavior; should get dedicated interaction test |
| `/partner` | partner page | P2 | load, CTA/link | not clearly covered | cheap route smoke candidate |
| `/legal/privacy` | static legal page | P3 | load/scroll only | indirectly covered at best | include in route sweep, not deep interaction |
| `/legal/terms` | static legal page | P3 | load/scroll only | indirectly covered at best | include in route sweep, not deep interaction |

### 4.2 Admin / operator routes

| Route | Functional surface | Importance | Interaction type | Current state (approx) | Notes |
| --- | --- | --- | --- | --- | --- |
| `/admin` | redirect root | P1 | redirect to dashboard | implicitly covered | should be included in admin smoke |
| `/admin/dashboard` | admin overview | P0 | load, stats/cards, navigation links | covered | part of admin smoke / visual candidate |
| `/admin/clients` | client list/manage | P0 | search/create/open detail | covered | `admin.clients.spec.ts` |
| `/admin/clients/[id]` | client detail | P1 | detail actions/navigation | partially covered | likely covered transitively, but direct route proof desirable |
| `/admin/users` | user list/manage | P0 | search/open user/quick actions | covered | `admin.users.spec.ts`, `admin.entitlements.spec.ts` |
| `/admin/users/[id]` | user detail / entitlements actions | P0 | grant/add-days/add-balance/action modal | covered | important operator flow |
| `/admin/reports` | report queue/list | P0 | search/open detail/regenerate entry | covered | strong operational importance |
| `/admin/reports/[id]` | report operations detail | P0 | regenerate/export/telemetry/progress | strongly covered | one of the most mature admin surfaces |
| `/admin/health` | diagnostics / health page | P0 | diagnostics runner, result evidence | covered | `admin.diagnostics.spec.ts` |
| `/admin/audit` | audit log | P1 | load/filter/verify event presence | partially covered | validated in entitlements scenario but still worth direct load guard |
| `/admin/broadcast` | mass broadcast form | P1 | fill form, submit, result state | undercovered | route is operationally risky; deserves dedicated spec |
| `/admin/tickets` | support tickets | P1 | load list, external reply link presence | undercovered | route exists with visible operator utility but no obvious dedicated spec |

## 5. Critical functional surfaces that MUST be covered by Playwright regression

These are the surfaces that should be treated as mandatory for a 95%-reliability program.

## Product-first assertion policy

- Controller-owned rule: key route and business-path tests must assert meaningful product outcomes and semantic correctness, not only existence/visibility/open state.
- Accept fallback copy only when fallback is the contractually correct product result for that scenario.
- Do not mark a surface green on fallback/placeholder copy when the route should render real user, report, billing, entitlement, or admin data.

### 5.1 P0 consumer surfaces

1. **App bootstrap / routing gateway**
   - `/start`
   - Must prove startup decisions do not strand the user on a blank/loop/bad redirect state.

2. **Home / today feed**
   - `/`
   - Must prove: page loads, no fatal shell error, important cards/sections render, at least one primary action responds, navigation works.

3. **Create / purchase entry**
   - `/create`
   - Must prove: report type selection, required fields, paywall path, submit path, branch continuity.

4. **Billing completion / resume path**
   - `/billing/complete`
   - Must prove: completion page loads, success state is visible, fallback/back path works, mobile swipe-back or tap-back semantics work where explicitly implemented.

5. **Read surfaces**
   - `/read/[id]` and any still-user-facing `/reports/[id]`
   - Must prove: report opens, key sections expand, content renders, no pageerror/console-fatal path, type-specific layouts do not crash.

6. **Week page**
   - `/week`
   - Must prove: hero renders, day cards react, CTA works, fallback path works, deeper panels render safely.

7. **Profile edit / onboarding**
   - `/profile/edit`
   - `/onboarding/profile`
   - Must prove: core fields can be edited, toggles work, save/continue works, next navigation works.

8. **Storefront / catalog**
   - `/reports`
   - Must prove: cards are visible, route transitions are correct, entitlement/paywall bridge semantics remain valid for key products.

### 5.2 P0 admin/operator surfaces

1. **Admin dashboard**
   - `/admin/dashboard`
   - Must prove: dashboard loads, main nav reachable, data cards render without breaking shell.

2. **User and client management**
   - `/admin/users`
   - `/admin/users/[id]`
   - `/admin/clients`
   - Must prove: search/open/detail/action flows still work.

3. **Report operations**
   - `/admin/reports`
   - `/admin/reports/[id]`
   - Must prove: list opens, detail opens, regenerate/export actions respond, telemetry/evidence state remains present.

4. **Diagnostics**
   - `/admin/health`
   - Must prove: diagnostics can run and evidence/result status renders.

### 5.3 Cross-cutting reliability guards that MUST exist

Across all P0/P1 routes, Playwright should explicitly guard:
- page does not render a visible 500/fatal shell/error boundary unexpectedly;
- no uncaught `pageerror` events;
- no high-severity console errors on load or on primary interaction;
- critical API failures do not silently degrade into unusable UI;
- route transitions complete instead of hanging;
- tap targets are actually actionable on mobile viewport;
- when mobile gesture handlers exist in code, at least one success-path gesture test exists.

## 6. Recommended Playwright test layers

The suite should be organized as layered reliability proof, not one undifferentiated pile of E2E files.

### 6.1 Layer A — Smoke

Purpose:
- fastest broad confidence signal for pages opening and core affordances responding.

Include:
- `/start`
- `/`
- `/week`
- `/reports`
- `/profile`
- `/admin/dashboard`
- `/admin/users`
- `/admin/reports`
- `/admin/health`

Assertions:
- route loads;
- one primary control is visible and clickable;
- no fatal shell / blank page / visible 500;
- no console/pageerror for guarded routes.

Operational goal:
- this is the bundle that runs before handoff for broad frontend changes.

### 6.2 Layer B — Route integrity

Purpose:
- systematic route-by-route “page exists and is operational” guard.

Include dedicated route tests for all user-facing routes, including lower-interaction pages:
- `/landing`
- `/prices`
- `/partner`
- `/share`
- `/support`
- `/legal/privacy`
- `/legal/terms`
- `/reports/history`
- `/onboarding/profile`
- `/admin/broadcast`
- `/admin/tickets`
- `/admin/audit`
- direct dynamic route smoke for representative IDs (`/read/[id]`, `/reports/[id]`, `/admin/users/[id]`, `/admin/clients/[id]`)

Assertions:
- route resolves;
- key heading/testid exists;
- no fatal runtime errors;
- if route contains links/buttons, at least the primary one responds.

### 6.3 Layer C — Interaction

Purpose:
- prove tap/click/input mechanics continue to work.

Targets:
- bottom navigation;
- home CTA and score/detail interactions;
- profile referral copy and edit navigation;
- support form input + submit;
- create form toggles, date/time/place selection, report type selection;
- read page accordion/section toggles;
- week day-card tap and CTA;
- admin filters/search/buttons;
- diagnostics runner button;
- broadcast form submission.

Assertions:
- input changes persist in UI;
- buttons actually trigger state/navigation/result;
- hidden interaction regressions are caught even when route still loads.

### 6.4 Layer D — Business-path

Purpose:
- guard flows where “loads fine” is not enough.

Mandatory business-path groups:
- startup routing continuation;
- create → paywall/checkout → billing complete → read continuation;
- catalog/storefront bridge for core products;
- history → open report;
- read flows for key report classes;
- admin entitlements/regeneration/diagnostics.

This is the layer that carries most of the “95% reliability” weight.

### 6.5 Layer E — Visual

Purpose:
- catch obvious layout regressions on stable, high-value screens.

Use visual assertions only on stable surfaces where a screenshot is strong signal and the data can be controlled.

Best candidates:
- home shell (stable mock state);
- reports/catalog storefront;
- profile overview;
- week hero and main panel stack;
- admin dashboard;
- a canonical read page for one or two major report types.

Avoid using visual-only checks as a substitute for interaction or business proof.

## 7. Where console / network / 500 guards are required

### 7.1 Console + pageerror guards should be mandatory on
- `/`
- `/start`
- `/create`
- `/billing/complete`
- `/profile`
- `/profile/edit`
- `/onboarding/profile`
- `/reports`
- `/reports/history`
- `/read/[id]`
- `/reports/[id]`
- `/week`
- `/support`
- `/admin/dashboard`
- `/admin/users`
- `/admin/users/[id]`
- `/admin/clients`
- `/admin/reports`
- `/admin/reports/[id]`
- `/admin/health`
- `/admin/broadcast`

Reason:
these routes are interactive, stateful, or operationally critical enough that hidden JS/runtime failures matter even if some markup still appears.

### 7.2 Explicit network/request guards are high value on
- `/start` because routing often depends on bootstrap requests;
- `/create` because product/access/checkout state can silently drift;
- `/billing/complete` because completion flows are network-sensitive;
- `/read/[id]` and `/week` because content hydration/parsing failures can be masked by partial UI;
- admin routes with action buttons (`/admin/users/[id]`, `/admin/reports/[id]`, `/admin/health`, `/admin/broadcast`).

Guard pattern recommendation:
- fail on unexpected 5xx for page-critical requests;
- allow known mocked/optional requests only when explicitly documented;
- attach trace/screenshot on failure.

### 7.3 Visible 500/fatal-state guards should exist on
- all P0 routes;
- all operator routes that gate business operations.

The suite should explicitly reject:
- generic Next error shell;
- blank page with missing hero/root content;
- visible “500”, “Application error”, or local fatal fallback where the route is expected to work.

## 8. Where swipe / touch behavior must be checked

The codebase already contains explicit mobile touch handlers, so swipe/touch is not optional here.

### 8.1 Must-check gesture surfaces

1. **`/billing/complete`**
   - file signal: `frontend/app/billing/complete/billing-complete-page-client.tsx`
   - code includes `touchstart` / `touchend` handling and swipe-back hint/action.
   - Playwright should test:
     - tap back control works;
     - swipe gesture triggers the intended back/fallback behavior;
     - gesture does not accidentally break primary completion continuation.

2. **Checkout resume / catalog continuation**
   - file signal: `frontend/components/catalog/catalog-checkout-resume.tsx`
   - code includes touch handlers for resume/cancel/back semantics.
   - Playwright should test:
     - resume CTA works;
     - cancel works;
     - swipe/back gesture works if the component is user-visible in a route flow.

3. **Week day-card tapping on mobile**
   - file signal: `frontend/components/week/week-day-grid.tsx`
   - tap semantics already partially covered, but should stay in the mobile viewport path.

4. **Bottom navigation mobile taps**
   - file signal: `frontend/components/BottomNav.tsx`
   - should be covered as actual bottom-nav taps across home/week/reports/profile.

### 8.2 Swipe/touch coverage currently appears weak

Current inventory suggests stronger click/tap coverage than gesture coverage. For a mobile-first consumer UI, that is a gap. A 95%-reliability target should include at least a small but explicit gesture layer, not only desktop-like clicking.

## 9. Screenshot / snapshot guidance: high value vs brittle

### 9.1 High-value visual assertions

Use screenshots on stable mock-controlled states with strong layout risk and limited data churn.

Recommended:
- home page in deterministic mock state;
- week page in deterministic mock state;
- reports/catalog listing with deterministic product cards;
- profile overview with deterministic mock profile;
- admin dashboard with mocked/stable stats;
- one read page per major rendering class:
  - canonical narrative read surface,
  - accordion-heavy read surface,
  - chart/card-heavy read surface if applicable.

Best screenshot scope:
- component or main-content region screenshots first;
- full-page screenshots only where shell layout itself is the subject.

### 9.2 Brittle visual assertions

Avoid or minimize screenshots for:
- highly dynamic dates/timestamps/counters;
- pages with unstable backend-fed lists unless mocked tightly;
- diagnostic/audit/operator tables that reorder or vary often;
- animation/transient toast states unless intentionally frozen;
- payment completion states with timing-based redirects unless redirect timing is disabled in test mode.

### 9.3 Snapshot recommendation

Prefer semantic text/assertion snapshots over pixel snapshots when the goal is structural content rendering, especially for read pages and fallback states. Use pixel screenshots only for layout-sensitive surfaces.

## 10. Current coverage gaps

The following gaps look material from the current inventory.

### 10.1 Missing or weak route-level coverage
- `/onboarding/profile`
- `/support`
- `/prices`
- `/share`
- `/partner`
- `/legal/privacy`
- `/legal/terms`
- `/admin/broadcast`
- `/admin/tickets`
- `/admin/audit` as a direct surface, not only incidental assertion inside another flow
- likely `/admin/clients/[id]` direct route proof
- likely `/admin/users/[id]` direct route smoke separate from business actions

### 10.2 Missing or weak interaction coverage
- bottom-nav end-to-end traversal as an explicit consumer-shell guard;
- support form submit result/failure states;
- profile overview primary controls and referral-copy behavior as first-class route behavior;
- onboarding happy path and field validation behavior;
- billing completion back controls and swipe-back behavior;
- checkout resume/cancel gesture semantics;
- admin broadcast form success/failure behavior;
- ticket page actionable link presence and empty/non-empty states.

### 10.3 Missing or inconsistent signal-hygiene coverage
- some specs collect console/pageerror evidence, but there is not yet an obvious systematic route guard matrix;
- request-failure/5xx guard semantics are not clearly standardized across all P0 routes;
- lower-interaction routes can still regress to framework/runtime error states without a dedicated sentinel test.

### 10.4 Visual coverage gaps
- only a subset of core pages currently has stored snapshots;
- no clear dedicated visual baselines for onboarding, support, billing complete, or admin health;
- visual strategy is not yet expressed as a stable-vs-brittle policy in the packet.

## 11. Recommended prioritization waves

### Wave 1 — Close the route-integrity holes (highest ROI)

Goal:
- every important route has at least one Playwright proof that it loads and does not crash.

Add/strengthen:
- `/onboarding/profile`
- `/support`
- `/prices`
- `/share`
- `/partner`
- `/legal/privacy`
- `/legal/terms`
- `/admin/broadcast`
- `/admin/tickets`
- `/admin/audit`
- representative direct-route dynamic smoke for detail routes

Acceptance:
- route-level smoke + console/pageerror + visible fatal/500 guard.

### Wave 2 — Normalize interaction proof on P0/P1 routes

Goal:
- primary control on each key route is not merely visible; it works.

Add/strengthen:
- bottom nav route traversal;
- home CTA/detail tap flows;
- support submit;
- onboarding continue flow;
- billing complete back/tap path;
- profile overview to edit and referral copy;
- admin broadcast submit;
- admin tickets surface state assertions.

Acceptance:
- each P0/P1 route has at least one meaningful interaction assertion.

### Wave 3 — Mobile touch/gesture reliability

Goal:
- explicit mobile-only behavior is no longer assumed.

Add/strengthen:
- billing complete swipe-back;
- checkout-resume swipe/back semantics;
- week/mobile day-card and CTA path under mobile viewport;
- bottom-nav mobile tap regression bundle.

Acceptance:
- at least one dedicated gesture spec exists for each code-backed gesture surface.

### Wave 4 — Visual stabilization on deterministic states

Goal:
- catch major layout regressions cheaply.

Add/strengthen:
- targeted screenshot baselines for home, week, catalog, profile, admin dashboard, key read surfaces.

Acceptance:
- screenshots are limited to stable mock states and maintained deliberately.

### Wave 5 — Business-path hardening / type matrix completion

Goal:
- the highest-value revenue and content paths are explicitly proven across representative product/report types.

Add/strengthen:
- create → billing → read for the main monetized routes;
- read-path matrix for key report classes not yet explicitly covered;
- admin/operator critical flows with failure variants.

Acceptance:
- top business journeys are explicitly green, not inferred from nearby tests.

## 12. Operational meaning of “~95% functional reliability with Playwright”

This target should be interpreted operationally, not mathematically.

It means:
1. **Nearly all important user-facing routes have route-load guards.**
   - A regression that causes blank page, 500, hydration crash, or broken shell on a meaningful route is likely to be caught before release.

2. **Every P0 route has at least one meaningful interaction proof.**
   - Not just “page opened,” but “the primary user action still works.”

3. **Every top business path has end-to-end proof.**
   - Especially create, paywall/checkout continuation, billing completion, read continuation, week/home consumption, and operator report actions.

4. **Mobile-specific behaviors are covered where code depends on them.**
   - Swipe/touch is part of the product contract, not an untested implementation detail.

5. **Signal hygiene is systematic.**
   - Console/pageerror/critical request failures are treated as test failures on important routes.

6. **Visual checks catch the most damaging layout regressions.**
   - Without turning the suite into brittle screenshot churn.

7. **The remaining 5% is acknowledged residual risk.**
   - Edge copy changes, rare timing races, low-value static pages, non-critical cosmetic drift, and deep permutations outside the selected product/report matrix.

A practical definition for this repo:
- **P0 surfaces:** near-complete route + interaction + business coverage;
- **P1 surfaces:** route + one primary interaction + signal hygiene guard;
- **P2/P3 surfaces:** route integrity only unless they become business-critical.

## 13. Recommended execution model for future workers

When implementing the next wave of Playwright work, use this order:
1. route-integrity holes first;
2. signal-hygiene normalization second;
3. interaction gaps third;
4. gesture coverage fourth;
5. visual stabilization fifth;
6. broader product/read-path matrix expansion last.

Reason:
- load/runtime regressions and broken primary controls usually produce the largest real-user damage for the least implementation cost.

## 14. Suggested spec organization improvements

Without forcing immediate renames, future work will be easier if specs are mentally grouped as:
- `smoke.*`
- `routes.*`
- `interactions.*`
- `business-path.*`
- `visual.*`
- `admin.*`
- `mobile-gesture.*`
- `quality.*`

Even if existing files stay in place, the packet should treat the suite through those layers.

## 15. Concrete next additions recommended

Highest-value next docs-to-execution candidates:
1. `support.spec.ts`
2. `onboarding-profile.spec.ts`
3. `route-integrity.spec.ts` for low-interaction consumer pages
4. `admin.broadcast.spec.ts`
5. `admin.tickets.spec.ts`
6. `billing-complete-gesture.spec.ts`
7. `bottom-nav-mobile.spec.ts`
8. `profile-home.spec.ts` or stronger `profile.spec.ts`
9. `route-signal-hygiene.spec.ts` matrix for P0/P1 pages
10. expanded `visual.spec.ts` with deterministic mock states only

## 16. Final assessment

To target ~95% frontend functional reliability with Playwright in this repo, the project does **not** need exhaustive click coverage of every element. It **does** need:
- full important-route mapping;
- explicit route-load and signal-hygiene guards;
- meaningful interaction proof on all P0/P1 surfaces;
- business-path proof for revenue/content/admin-critical journeys;
- dedicated mobile gesture coverage where code implements gesture semantics;
- stable screenshot evidence on selected high-value layouts.

The existing suite provides a strong base. The remaining work is mainly **systematization and gap closure**, not a greenfield test program.
