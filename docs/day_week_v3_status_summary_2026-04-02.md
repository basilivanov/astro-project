# Day/Week v3 status summary (2026-04-02)

## Scope

Synthesis of current `Today` / `Week` v3 state after the already landed product, contract, QA, and rendered-gate waves.

Primary inputs:
- `docs/day_week_v3_audit_execution_plan_2026-04-02.md`
- `docs/day_week_v2_closure_review_2026-04-02.md`
- `docs/day_week_contract_audit_v2_2026-04-02.md`
- `docs/PRODUCT_SURFACE_BRIEF.md`
- `docs/POST_TEST_OBSERVABILITY_REVIEW_2026-04-01.md`
- `/home/astro/.ductor/workspace/telegram_files/2026-04-01/day_week_review_and_fix_tz_v3.md`

## What is already closed enough

### Product / surface baseline
- `Today` top layer is already DTO-native and no longer depends on legacy top-level business assembly.
- `Week` top layer already runs through `WeekBrief`-first mapping instead of mixed legacy assembly.
- Shared day/week detail normalization already exists via `frontend/lib/detail-layer.ts`.
- Major packet/docs/governance work is in place: execution packets, regression map, observability gate memo, targeted acceptance profiles.

### Contract / architecture baseline
- `DayBrief` and `WeekBrief` are established as the canonical top-layer contracts.
- The repo already documents the real remaining contract gap: weekly day cards are not yet true first-class detail DTO items.
- The current state is compatible with bounded frontend-only correctness cleanup before any deeper backend extension.

### QA / governance baseline
- Canonical quick/smoke profiles and the post-test observability gate are already defined and integrated into repo guidance.
- Rendered-gate work has already started to formalize evidence review beyond green tests.

## What is still open

### Open v3 correctness cleanup
- Today disclosure-building is still too permissive about using broad/global factor pools instead of score-scoped evidence.
- `frontend/lib/day-brief.ts` still allows placeholder/generic factor material that violates v3 honesty rules.
- Shared detail-layer sanitation is not yet strict enough to fully reject raw colon-style keys, raw enum/status chips, and duplicate/noisy evidence rows.
- Weekly domain/action panels still allow arbitrary week-level fallback behavior that v3 explicitly wants removed.

### Open weekly product-model cleanup
- `Week` still centers a `dayCards` model instead of the requested split where a compact day strip is secondary and domain insights remain the primary detail system.
- Weekly day cards still lack true day-like disclosure DTO parity (`id`, `details.why_text`, `details.supporting_factors`, optional relation ids).

### Open gate tightening
- Tests and rendered/pass-gate expectations are not yet fully rewritten to reject bad output patterns such as raw keys, raw enum chips, and arbitrary fallback factors.
- Observability policy exists, but the v3 invariants are not yet locked as explicit cross-surface anti-regression assertions.

## Recommended status by wave

- **Product baseline:** mostly closed.
- **Contract baseline:** mostly closed, with one explicit residual weekly day-card DTO gap.
- **QA/governance baseline:** mostly closed.
- **v3 correctness cleanup:** open.
- **v3 weekly model simplification:** open.
- **v3 gate hardening:** open.

## Highest-value next bounded wave

Best next packet after current runs: **one correctness wave covering A+B+C from the v3 execution plan**.

### Why this wave first
- It closes the highest-value user-visible honesty issues without requiring a large UI refactor.
- It is mostly frontend-bounded and does not depend on the larger weekly DTO extension.
- It creates the clean invariant base needed before tightening tests/gates or doing the bigger `dayStrip` refactor.

### Included slice
- central sanitation hardening in `frontend/lib/detail-layer.ts`
- Today score disclosure source narrowing
- weekly domain/action fallback cleanup
- targeted test rewrites that reject the now-forbidden outputs for these surfaces

### Explicitly not included
- full weekly `dayStrip` product-model split
- backend DTO extension for weekly day-card detail parity
- broader rendered-gate expansion beyond the minimal invariant updates needed for this correctness slice

## Recommended follow-up order

1. **Correctness wave (A+B+C)** — close raw/noisy/fake evidence paths.
2. **Gate tightening wave (E partial/final)** — lock those invariants in tests and rendered/pass expectations.
3. **Weekly model wave (D + DTO extension if approved)** — `dayStrip` split and real weekly day-card detail parity.

## Reviewer verdict

v3 should currently be treated as **partially complete but not closed**.

The repo is already in a good state for a narrow next packet, but the cleanest statement is:

> product/contract/QA foundations are in place; the remaining highest-value work is a bounded correctness cleanup wave, followed by gate tightening, with weekly product-model simplification kept as a separate follow-up.
