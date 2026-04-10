# Day/Week review evidence

- Date: 2026-04-10
- Commit baseline: d479771
- Refresh source: worktree above `e9adea5` with `VISUAL-FINISH-DAY-WEEK-01` applied
- App build: local dev bundle from current worktree above the recorded baseline commit
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
- This refresh specifically proves four visual changes for this wave:
  - canonical Today keeps calm daily wording and never falls back to apology-style explanation copy;
  - canonical Week is still domain-led, while the day rhythm stays compact and secondary;
  - day drawer copy varies by selected day and no longer leaks internal drill-down wording;
  - compatibility and deep layers use product-language labels instead of internal implementation terms.
