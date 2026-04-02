# Day/Week v3 audit + execution plan (2026-04-02)

## Scope
Audit against `/home/astro/.ductor/workspace/telegram_files/2026-04-01/day_week_review_and_fix_tz_v3.md`, mapped onto current repo state after v2 / v2.5 / vRendered-related work.

## Concise diagnosis

Current state is **partially aligned with v3 cleanup goals**, but the core v3 product cleanup is **not yet complete**.

### Already aligned / partially done
- `frontend/lib/detail-layer.ts` already suppresses some raw semantic keys and duplicate factor text.
- day/week mapping already has a shared normalized-detail path for several surfaces.
- closure/audit docs already capture the important contract diagnosis: day score details still risk generic/global evidence, and weekly day cards still do not have true detail DTO parity.

### Still open / materially blocking v3 closure
- `Today` still references `personalized_factors` / `selected_factors` in disclosure-building code paths, so the “no global fallback factors in day score disclosures” ask is **not fully closed**.
- `frontend/lib/day-brief.ts` still manufactures placeholder detail/factor content (`"Фактор дня"`, generic explanation, generic `why_text`), which conflicts with v3 honesty rules.
- weekly domain/action factor fallback still uses arbitrary week-level fallback selection (`slice(0, 2)` and broad fallback-to-week-factors behavior), which v3 explicitly forbids.
- weekly screen still structurally centers `dayCards`; the requested split into `dayStrip` + primary `domainInsights` model is **not implemented**.
- tests still contain fixtures/assertions around raw values like `money:green` and permissive factor/status behavior; they are not yet converted into anti-regression guards for v3 cleanup.

## Concrete asks extracted from v3

1. Remove global fallback factors from day score disclosures.
2. Remove colon-style raw keys from UI instead of humanizing them.
3. Remove raw enum/status values from detail chips.
4. Remove arbitrary weekly fallback like `week.factors.slice(0, 2)`.
5. Make weekly screen use one primary detail model, not two competing ones.
6. Demote weekly day cards into compact summary strip.
7. Keep weekly domain panel as primary detail system and sanitize it harder.
8. Unify/sanitize detail-layer rules across day/week.
9. Rewrite tests so they reject bad output instead of blessing it.
10. Update rendered/pass gates to reflect these invariants.

## Mapping to v2 / v2.5 / vRendered waves

### Closed or mostly closed in earlier waves
- Shared day/week detail normalization exists in `frontend/lib/detail-layer.ts`.
- Some raw semantic suppression already exists via `isLikelyRawSemanticKey(...)` in `frontend/lib/detail-layer.ts`.
- Existing audits in `docs/day_week_contract_audit_v2_2026-04-02.md` already identify the backend/frontend contract gap for weekly day-card explainability.

### Partially closed
- v2/v2.5 improved normalization and fallback resilience, but did **not** fully enforce v3 “no fake evidence” rules.
- vRendered likely improved render stability, but did **not** yet complete product-model simplification for weekly screen.

### Not closed
- Day score disclosure source narrowing.
- Placeholder factor suppression in `frontend/lib/day-brief.ts`.
- Weekly arbitrary factor fallback removal.
- Weekly `dayStrip` product split.
- Anti-bad-output test rewrite.
- Pass-matrix/rendered-gate tightening.

## Bounded independent tasks

### Task A — day disclosure source narrowing
**Goal:** stop score disclosures from using global factor pools.

**Files:**
- `frontend/components/today/daybrief-sections.tsx`
- `frontend/lib/day-brief.ts`
- `frontend/lib/detail-layer.ts`
- `frontend/test/components/today/daybrief-sections.test.tsx`
- `frontend/test/lib/day-brief.test.ts`
- `frontend/test/lib/detail-layer.test.ts`

**Scope:**
- replace current fallback chain with local-only / domain-scoped factor selection;
- add `selectScoreScopedFactors(...)` or equivalent;
- ensure empty factors means disclosure without factors or no disclosure.

**Depends on:** none.

### Task B — shared detail-layer sanitation hardening
**Goal:** enforce raw-key/raw-enum/duplicate suppression centrally.

**Files:**
- `frontend/lib/detail-layer.ts`
- `frontend/components/detail/detail-evidence-chips.tsx`
- `frontend/test/lib/detail-layer.test.ts`
- `frontend/test/components/detail/detail-primitives.test.tsx`

**Scope:**
- add/strengthen `sanitizeDetailLayer(...)`;
- drop colon keys, raw statuses, empty factor rows, duplicate lead/factor text;
- chip rendering should whitelist only meaningful display values.

**Depends on:** none; can run in parallel with Task A.

### Task C — weekly domain/action fallback cleanup
**Goal:** stop arbitrary weekly factor injection.

**Files:**
- `frontend/components/week/week-domain-panel.tsx`
- `frontend/components/week/week-actions-panel.tsx`
- `frontend/test/components/week/week-detail-panels.test.tsx`

**Scope:**
- remove `week.factors.slice(0, 2)` fallbacks;
- allow only direct item/domain factors or exact factor match;
- render disclosure only when meaningful content exists.

**Depends on:** Task B recommended first, but not strictly blocked.

### Task D — weekly product-model split (`dayStrip`)
**Goal:** make weekly day cards overview-only and keep domains as primary detail layer.

**Files:**
- `frontend/components/week/week-day-grid.tsx` or replacement
- `frontend/components/week/week-day-strip.tsx` (new)
- `frontend/lib/week-brief.ts`
- `frontend/app/week/page.tsx`
- `frontend/test/lib/week-brief.test.ts`
- `frontend/test/app/week-page.test.tsx`
- new `frontend/test/components/week/week-day-strip.test.tsx`

**Scope:**
- introduce `dayStrip` in surface model;
- keep compact summary card fields only;
- remove large-card explainability expectations from weekly day grid.

**Depends on:** none technically, but best after Task C to avoid reworking weekly semantics twice.

### Task E — rendered/pass gate tightening
**Goal:** align tests/evidence gates with v3 acceptance criteria.

**Files:**
- likely test files only, plus optional repo doc if gate policy is documented
- candidate docs: `docs/day_week_v3_audit_execution_plan_2026-04-02.md` or existing closure docs

**Scope:**
- remove assertions that accept `money:green`, raw enum chips, and arbitrary fallback factors;
- add cross-surface invariants suite.

**Depends on:** A/B/C minimum; D if weekly UI contract changes land.

## Recommended execution order

1. **Task B** — central sanitation rules first.
2. **Task A** — day score disclosure source narrowing.
3. **Task C** — weekly domain/action fallback cleanup.
4. **Task E (partial)** — lock new invariants in tests for A/B/C.
5. **Task D** — weekly product-model split into `dayStrip`.
6. **Task E (final)** — update weekly rendering tests and pass matrix.

Reasoning:
- B creates the shared reject/sanitize behavior used by A and C.
- A/C close the highest-priority v3 Wave 1 asks.
- D is a larger UI/model refactor and should not block correctness cleanup.

## Blockers / dependencies

### Hard blocker for full weekly day-like detail parity
Backend DTO still lacks true weekly day-card detail fields (`id`, `details.why_text`, `details.supporting_factors`). This is already identified in `docs/day_week_contract_audit_v2_2026-04-02.md`.

### Not a blocker for v3 Wave 1
Most of v3 Wave 1 can be completed frontend-only:
- raw key suppression;
- day disclosure source narrowing at render/mapping layer;
- weekly arbitrary fallback removal;
- test hardening.

### Soft blocker / coordination risk
If another wave is simultaneously changing weekly surface DTO names, Task D should wait for that contract to stabilize before renaming `dayCards` → `dayStrip` broadly.

## Verification profile for execution

For any implementation wave touching these files:
- frontend targeted tests for changed units/components;
- `./scripts/run_e2e.sh --last-failed` or targeted week/today specs;
- post-test evidence review for Today/Week flows per repo AGENTS requirements.

Suggested targeted specs:
- `frontend/e2e/today-daybrief.spec.ts`
- `frontend/e2e/week-page-fallback.spec.ts`
- `frontend/e2e/week-canonical-persona.spec.ts`

## Verdict

v3 is **not closed**. Best current classification:
- **Wave 1 correctness cleanup:** open
- **Wave 2 weekly model simplification:** open
- **Wave 3 gate hardening:** open

The repo is ready for bounded execution, but the cleanest next packet is **A+B+C as one correctness wave**, with **D** as a separate follow-up refactor packet.
