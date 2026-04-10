# Day/Week review evidence

- Date: 2026-04-10
- Commit baseline: d479771
- Current committed base: 70cf145
- Day canon packet: PKT-DAY-CANON-NO-FALLBACK-2026-04-10
- App build: local dev bundle from current worktree for `DAY-PUBLICATION-PARITY-01`
- Viewport: 390x844 (Telegram WebApp representative mobile viewport)
- Primary capture lane: mock-helper for deterministic visual review
- Signed canonical runtime is verified separately by `./scripts/run_e2e.sh e2e/telegram-signed-auth.spec.ts`
- Signed Day proof lane is the primary product proof path; `frontend/e2e/day-canon-visual-evidence.spec.ts` remains mock-helper visual harness only.
- Current signed Day closeout status in this branch snapshot: `blocked in this shell unless TELEGRAM_BOT_TOKEN is provided`; fail-fast behavior is intentional and is part of the primary proof contract.
- Observability closeout status: `FAIL_OBSERVABILITY_GATE` in the currently published branch-visible `post-test-review.md`; Today is no longer labeled clean when the same analysis window still carries auth-fallback or fallback-contaminated evidence, and Week remains blocked separately.
- If a device screenshot shows `объяснение недоступно` on canonical Today while these captures do not, treat it as deploy/cache/bundle parity drift first.

## Files

| File | Lane | Notes |
| --- | --- | --- |
| today-canonical-top.png | mock-helper | strict canonical Day top: hero + 4 domains only |
| today-canonical-domain-energy-expanded.png | mock-helper | canonical Today, Тонус expanded |
| today-canonical-domain-money-expanded.png | mock-helper | canonical Today, Работа и деньги expanded |
| today-canonical-domain-love-expanded.png | mock-helper | canonical Today, Чувства expanded |
| today-canonical-domain-focus-expanded.png | mock-helper | canonical Today, focus card expanded |
| today-no-data.png | mock-helper | explicit canonical no-data state without fallback prose |
| today-error.png | mock-helper | explicit canonical error state without fallback substitution |
| today-domain-failed.png | mock-helper | per-domain failed state rendered honestly inside the four-card shell |
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
| week-canonical-bottom.png | mock-helper | optional extra Week lower fold |
| week-monday-sunday-order-proof.png | mock-helper | weekday ordering proof |

## Notes

- `signed` lane screenshots are not included here because deterministic repository-safe capture is done through mock-helper. Runtime correctness for signed Telegram lane is covered by Playwright signed-auth specs.
- Day publication proof now lists only current strict Day artifacts; stale Day windows/risks/bottom/degraded references are removed.
- Compatibility screenshots are intentionally lighter than canonical ones and must not be used as premium-reference images.
- What changed in this wave:
  - Day domain titles are locked to `Тонус / Работа и деньги / Чувства / Фокус`;
  - adapter now accepts only `day_brief_canon_v1` and rejects bridge `day_brief_v2`;
  - partial-ready semantics remain intentionally allowed only when at least one complete domain exists; otherwise the route collapses to `no_data`;
  - explicit no-data, error, and domain-failed states were re-captured after the label lock.
- Forbidden-token and fallback-copy pass completed for visible Day surfaces:
  - checked canonical, no-data, and domain-failed captures for internal/fallback leakage;
  - checked that Day UI no longer renders windows, best-use, risks, factor cards, or signal badges.
- Observability note:
  - branch-visible closeout now uses strict clean semantics for Today: if the analyzed window still contains auth-fallback, fallback, or validator-fallback signals, the Today block is published as non-clean rather than clean-with-alerts.
  - current published state is intentionally non-clean because the same 30m window still contains fallback-contaminated canonical evidence for Today and no canonical Week evidence.
