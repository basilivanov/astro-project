# Frontend Functional Reliability Execution Packet

## Objective
Deliver frontend work under a reliability-first gate: critical pages must load without errors, primary interactions must work, and business logic paths must complete correctly. Coverage growth continues, but it is not the primary acceptance signal for this packet.

## Source of truth
- `/opt/astro-project/AGENTS.md`
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/frontend/playwright.config.cjs`
- `/opt/astro-project/docs/frontend_functional_reliability_packet/requirements.slice.frontend-functional-reliability.xml`
- `/opt/astro-project/docs/frontend_functional_reliability_packet/development-plan.slice.frontend-functional-reliability.xml`
- `/opt/astro-project/docs/frontend_functional_reliability_packet/verification-matrix.slice.frontend-functional-reliability.md`

## Clarified intent
Use this packet when the main question is functional frontend confidence:
- does the page open cleanly?
- does the user/operator tap, click, open, submit, and navigate successfully?
- does the intended business path reach the correct outcome?

Do not treat rising coverage alone as success for this packet.

## Canonical execution policy
- Stay reliability-first.
- Stay product-first: key tests MUST assert meaningful product outcomes and semantic correctness, not only element existence, visibility, or open-state toggles.
- Use `./scripts/run_e2e.sh` as the canonical runner.
- Keep health checks in the execution path; do not bypass the wrapper unless the controller explicitly changes policy.
- After each significant frontend change, run the minimally sufficient targeted E2E profile until green.
- If the page crashes, returns 500, or breaks a critical interaction, add/update a reproduction Playwright test, fix, and rerun to green.
- Fallback copy may be asserted only when that fallback is product-contractually correct for the tested state; it is forbidden as a passing substitute when the product should show real user, report, billing, entitlement, or admin data.

## Execution ladder
1. `./scripts/run_e2e.sh --last-failed`
   - fastest rerun when cached failures already represent the active issue
2. `./scripts/run_e2e.sh e2e/admin.smoke.spec.ts e2e/core-ux.spec.ts e2e/report-create.spec.ts e2e/quality.spec.ts`
   - shared frontend smoke gate for broad shell/create/admin reliability
3. targeted route/interaction spec(s)
   - choose the smallest file or `-g` case proving the changed behavior
4. targeted business-path spec(s)
   - required for create/read, billing bridge, entitlement, fallback, and continuation semantics
5. targeted admin spec(s)
   - required when the touched slice is operator-facing

## Worker instructions
1. Map the touched surface to one of these categories:
   - core page load/navigation
   - primary interaction regression
   - business-path regression
   - admin/operator regression
   - fallback/failure-state regression
2. Select the minimal proving command from the verification matrix slice.
3. If the change has shared blast radius, rerun the shared smoke bundle before handoff.
4. Report back with:
   - files changed
   - exact commands run
   - which reliability dimension was proven
   - remaining risks or deferred follow-ups

## Local adaptation: test authoring
- This packet remains controller-owned: keep authoring guidance lightweight, practical, and subordinate to the reliability gate.
- Playwright tests should prefer scenario-oriented names, stable semantic IDs/selectors, and evidence-driven failure output.
- Assertions MUST prove semantic user-visible correctness: what product state was reached, what data meaning is shown, and what action outcome occurred.
- Do not accept tests that pass only because a panel opened, a node exists, or placeholder/fallback text rendered when the contractual outcome is live data or a real completed state.
- Add VM mapping in Playwright only when it sharpens diagnosis for a route, interaction, or business-path failure; it is useful, not mandatory.
- Jest tests should group around module contracts and observable behavior contracts, not incidental implementation fragments.
- Semantic blocks are optional for large helpers or fixtures where they improve readability; they are not mandatory in every test.
- Do not let local authoring conventions override canonical requirements such as targeted proof, reproduction for crash/500 regressions, and controller-selected verification scope.

## Minimum acceptable proof by change type
- Core page/shell change: load + navigation/tap proof
- Form/create change: load + submit + continuation proof
- Read surface change: load + open/disclosure/navigation proof
- Billing/storefront change: business-path bridge proof
- Admin change: admin smoke plus targeted operator flow proof
- Crash/500 fix: reproduction spec plus targeted green rerun
- For any key path above, proof is complete only when the asserted outcome is semantically correct for the product contract, including correct real-data rendering vs. intentionally valid fallback.

## Non-goals
- Do not widen this packet into a coverage-threshold program.
- Do not run full frontend regression after every small change unless blast radius justifies it.
- Do not substitute screenshot/visual checks for missing interaction or business-path proof.

## Deliverables from an execution worker
1. Code changes for the active reliability slice only.
2. New or updated Playwright reproduction when needed.
3. Passing targeted verification evidence.
4. Short handoff note stating whether broader smoke/admin/business suites are still recommended.
