# Day/Week review evidence

- Date: 2026-04-10
- Commit baseline: d479771
- Current committed base: 2491165
- App build: local dev bundle from current worktree for `VISUAL-FINAL-FINISH-DAY-WEEK-02`
- Viewport: 390x844 (Telegram WebApp representative mobile viewport)
- Primary capture lane: mock-helper for deterministic visual review
- Signed canonical runtime is verified separately by `./scripts/run_e2e.sh e2e/telegram-signed-auth.spec.ts`
- If a device screenshot shows `объяснение недоступно` on canonical Today while these captures do not, treat it as deploy/cache/bundle parity drift first.

## Files

| File | Lane | Notes |
| --- | --- | --- |
| today-canonical-top.png | mock-helper | canonical `day_brief_v1` top of Today |
| today-canonical-domain-energy-expanded.png | mock-helper | canonical Today, energy card expanded |
| today-canonical-domain-money-expanded.png | mock-helper | canonical Today, work/money card expanded |
| today-canonical-domain-love-expanded.png | mock-helper | canonical Today, love card expanded |
| today-canonical-domain-focus-expanded.png | mock-helper | canonical Today, focus card expanded |
| today-canonical-windows.png | mock-helper | canonical Today windows after merge/dedupe |
| today-canonical-risks.png | mock-helper | canonical Today risks after dedupe/cap |
| today-compatibility-degraded.png | mock-helper | degraded Today compatibility state from legacy payload |
| week-canonical-overview-top.png | mock-helper | canonical Week first fold |
| week-canonical-domains.png | mock-helper | weekly domains as primary product |
| week-canonical-domain-work-expanded.png | mock-helper | work/money weekly domain disclosure |
| week-canonical-domain-focus-expanded.png | mock-helper | focus weekly domain disclosure |
| week-canonical-rhythm-strip.png | mock-helper | compact Monday→Sunday rhythm strip |
| week-canonical-day-drawer.png | mock-helper | canonical day drill-down drawer |
| week-canonical-actions-risks.png | mock-helper | compact weekly actions and risks |
| week-canonical-explainability.png | mock-helper | supporting explainability block |
| week-canonical-deep-sections.png | mock-helper | deep reading below secondary boundary |
| week-compatibility-overview.png | mock-helper | honest compatibility overview |
| week-compatibility-day-drawer.png | mock-helper | compatibility day drawer, intentionally lighter |
| week-empty.png | mock-helper | explicit no-report empty state |
| week-in-progress.png | mock-helper | explicit in-progress state |
| today-canonical-bottom.png | mock-helper | optional extra Today lower fold |
| week-canonical-bottom.png | mock-helper | optional extra Week lower fold |
| week-monday-sunday-order-proof.png | mock-helper | weekday ordering proof |

## Notes

- `signed` lane screenshots are not included here because deterministic repository-safe capture is done through mock-helper. Runtime correctness for signed Telegram lane is covered by Playwright signed-auth specs.
- Compatibility screenshots are intentionally lighter than canonical ones and must not be used as premium-reference images.
- What changed in this wave:
  - degraded Today hero no longer surfaces raw payload headlines and stays in product-language copy;
  - compatibility/in-progress Week hero and meta chips are sanitized away from internal or placeholder-like wording;
  - mobile `Ритм недели` is lighter and visually secondary to the domain cards;
  - deep sections now prefer quiet prose rendering over visible fallback-scaffolding treatment.
- Forbidden-token pass completed for visible degraded/compatibility surfaces:
  - checked against `legacy`, `fallback`, `week_map`, `weekbrief`, `headline`, `markdown`, `weekly report`, `compatibility`;
  - guardrails are covered by refreshed component/app/e2e assertions for Today degraded, Week compatibility, Week in-progress, and deep-section fallback paths.
