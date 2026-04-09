# Frontend Functional Reliability Verification Matrix

## Intent
This slice defines a reliability-first frontend gate. The primary question is not "did coverage go up?" but "does the page load, can the user interact, and does the business path complete correctly?"

## Canonical runner
- `./scripts/run_e2e.sh`
- Wrapper responsibilities already built into the repo:
  - validates backend `/health`
  - validates backend `/api/health` with DB connected
  - validates frontend container health
  - validates frontend `/api/health` proxy
  - runs Playwright inside the dedicated Docker E2E container

## Verification ladder

### 1. Fast rerun gate
Use when the fix corresponds to an already failing cached Playwright case.

- Command: `./scripts/run_e2e.sh --last-failed`
- Proves: quick confirmation that the previously failing frontend slice is back to green
- Not sufficient when: there is no cached failure, the touched area is broader, or the failing test did not cover the business path you changed

### 2. Shared frontend smoke gate
Use before handing off meaningful frontend reliability work that affects shared shell/navigation/create/admin basics.

- Command: `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts e2e/core-ux.spec.ts e2e/report-create.spec.ts e2e/quality.spec.ts`
- Proves:
  - admin smoke routes load
  - core UX/navigation shell still works
  - report create path still works at smoke level
  - baseline quality guards remain intact
- This is the canonical shared reliability bundle already referenced by `verification-matrix.md`.

### 3. Targeted route and interaction gate
Use for the smallest reliable proof after a route-specific or interaction-specific change.

| Reliability target | Preferred command examples | What it proves |
| --- | --- | --- |
| Landing/start/core shell | `./scripts/run_e2e.sh e2e/core-ux.spec.ts` | Guest/public landing and start auth gate remain operational; this is not authenticated consumer proof |
| Landing marketing surface | `./scripts/run_e2e.sh e2e/landing.spec.ts` | Entry page loads and primary entry interactions still work |
| History CTA and continuation | `./scripts/run_e2e.sh e2e/history-cta.spec.ts` | History route loads and CTA/open behavior remains valid |
| Profile/edit helper interactions | `./scripts/run_e2e.sh e2e/profile-edit.spec.ts` | Mock/helper profile form regression stays actionable, but this is not canonical signed-auth acceptance |
| Today interaction/read semantics | `./scripts/run_e2e.sh e2e/today-daybrief.spec.ts` | Canonical Today screen opens disclosures and preserves read semantics when `day_brief_v1` is present |
| Today compatibility fallback | `./scripts/run_e2e.sh e2e/today-degraded.spec.ts` | Non-canonical Today payload is rendered as explicit degraded state instead of synthetic premium reconstruction |
| Week fallback/live semantics | `./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts e2e/week-fallback.regression.spec.ts` | Week route handles compatibility fallback without crash and keeps fallback explicitly marked |
| Week refresh/live regressions | `./scripts/run_e2e.sh e2e/week-home-refresh.regression.spec.ts e2e/week-live.spec.ts` | Week interaction/load regressions stay fixed |
| Console/runtime hygiene | `./scripts/run_e2e.sh e2e/route-console.spec.ts` | Hidden JS/runtime errors do not slip through behind a loaded page |
| Failure-state guard | `./scripts/run_e2e.sh e2e/report-failure.spec.ts` | Controlled failure UI works instead of uncontrolled crash |

### 4. Targeted business-path gate
Use whenever the changed slice affects real product semantics such as create/read, storefront bridging, billing return, or entitlement-based access.

| Business path | Preferred command examples | What it proves |
| --- | --- | --- |
| Report create baseline | `./scripts/run_e2e.sh e2e/report-create.spec.ts` | User can still submit the core create flow |
| Broader report workflow | `./scripts/run_e2e.sh e2e/report-workflow.spec.ts` | Multi-step create/read workflow behavior remains valid |
| Billing mock bridge | `./scripts/run_e2e.sh e2e/billing-mock.spec.ts` | Checkout-to-complete-to-read bridge still works in the mocked runtime |
| Billing catalog alignment | `./scripts/run_e2e.sh e2e/billing-catalog-alignment.spec.ts` | Storefront/catalog semantics remain aligned with checkout paths |
| Month forecast storefront bridge | `./scripts/run_e2e.sh e2e/month-forecast-bridge-storefront.spec.ts` | Month forecast storefront path reaches expected continuation |
| Year forecast storefront bridge | `./scripts/run_e2e.sh e2e/year-forecast-bridge-storefront.spec.ts` | Year forecast storefront path reaches expected continuation |
| Solar return storefront bridge | `./scripts/run_e2e.sh e2e/solar-return-bridge-storefront.spec.ts` | Solar return storefront path reaches expected continuation |
| Synastry storefront bridge | `./scripts/run_e2e.sh e2e/synastry-bridge-storefront.spec.ts` | Synastry storefront path reaches expected continuation |
| Read surfaces | `./scripts/run_e2e.sh e2e/year-forecast-read.spec.ts e2e/ten-year-forecast-read.spec.ts` | Report read pages open into semantically correct read states |
| Signed Telegram authenticated lane | `./scripts/run_e2e.sh e2e/telegram-signed-auth.spec.ts` | Canonical authenticated consumer path is `signed Telegram initData -> canonical day_brief_v1/week_brief_v1 -> shared detail-layer renderer`; the suite proves Today, Week, Profile, `Profile/edit`, and onboarding/profile without mock runtime, and the command must fail fast if `TELEGRAM_BOT_TOKEN` is absent |

### 5. Targeted admin reliability gate
Use when the change affects operator workflows or admin-only screens.

| Admin area | Preferred command examples | What it proves |
| --- | --- | --- |
| Core admin smoke | `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts` | Admin critical routes load and basic operations stay reachable |
| Users | `./scripts/run_e2e.sh e2e/admin.users.spec.ts` | User management UI remains functional |
| Clients | `./scripts/run_e2e.sh e2e/admin.clients.spec.ts` | Client/admin lookup flows remain functional |
| Entitlements | `./scripts/run_e2e.sh e2e/admin.entitlements.spec.ts` | Entitlement/operator actions remain functional |
| Operations | `./scripts/run_e2e.sh e2e/admin.operations.spec.ts` | Admin operational surface remains healthy |
| Diagnostics | `./scripts/run_e2e.sh e2e/admin.diagnostics.spec.ts` | Diagnostic/admin health UI still behaves correctly |
| RBAC | `./scripts/run_e2e.sh e2e/admin.rbac.spec.ts` | Access control paths remain intact |

## Selection rules
- Start with `--last-failed` only if it is relevant to the active regression.
- Run the smallest targeted spec that proves the exact touched route or business path.
- Escalate to the shared smoke bundle when:
  - the change touches shared layout/navigation
  - the change touches create flow infrastructure
  - the change touches common client-side utilities with broad blast radius
  - the change touches admin shell/common operator affordances
- Include `e2e/route-console.spec.ts` when a change could produce runtime errors while leaving the page visually present.
- Use business-path suites, not only smoke, when the route depends on billing, entitlement, create/read, fallback, or continuation semantics.
- For auth-sensitive consumer routes, run a signed-lane proof; mock-lane-only evidence is invalid.
- Fallback specs prove degraded-state safety only; they do not prove canonical authenticated behavior.
- Canonical frontend MVP proof for Today/Week is only valid when the page is fed `day_brief_v1` / `week_brief_v1`; compatibility fallback proof must be attached separately.

## Local adaptation: authoring guidance
- Keep this guidance controller-owned and lightweight: it supports verification clarity, not a new mandatory test style layer.
- For Playwright, prefer scenario-oriented test names, stable semantic IDs/selectors, and evidence-driven failure output.
- Key assertions must prove product semantics: the user/operator reached the intended state and saw the contractually correct content or status, not just that a control existed or a disclosure opened.
- Fallback copy is valid evidence only when the scenario contract explicitly calls for fallback; it is invalid when the product should show real data, real completion state, or real entitlement/admin content.
- Use VM mapping in Playwright when it helps explain state, route, or business-path failures; treat it as optional diagnostic structure.
- For Jest, organize tests around module and behavior contracts so failures map back to the owned contract surface.
- Use semantic blocks only in larger helpers or fixtures when they materially improve readability; they are optional, not required in every test.

## Pass criteria
A frontend slice is green only when all applicable statements are true:

- The route under change loads without crash, blank fatal shell, or visible 500 state.
- The primary user action on that route succeeds.
- The expected business outcome is reached for the touched flow.
- The asserted content/state is semantically correct for the product contract; placeholder or fallback text does not count unless that fallback is the correct contracted result.
- No required signal-hygiene guard for that slice is failing.
- If the bug was a crash/500/regression, a reproduction test exists and passes.
- If the touched route is an authenticated consumer route, the asserted success state is proven in the signed Telegram lane.

## Required escalation for severe regressions
If the changed route produces a 500, render crash, broken hydration/runtime path, or blocked critical interaction:

- add or update a targeted Playwright reproduction
- fix the defect
- rerun the smallest proving spec
- rerun the shared smoke bundle if the blast radius is not obviously isolated

## Relationship to coverage
- Coverage growth remains useful and should continue.
- Coverage is not the acceptance gate for this slice.
- A route with better coverage but broken load/interaction/business behavior is still red.
- A route with modest coverage but proven functional reliability on the scoped critical path can be accepted for this slice.
