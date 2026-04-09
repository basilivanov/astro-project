
- 2026-04-09: Task Auth/Week lane divergence — tightened MVP auth/test lane policy across docs: signed Telegram initData is the canonical authenticated path; mock lane remains test-only; guest lane remains public-entry-only. Verification target: docs-only packet, no runtime code changed.

- 2026-03-27: Task F2 — migrated `/week` top layer to `WeekBrief` map (`frontend/app/week/page.tsx`, `frontend/components/week/*`, `frontend/lib/week-brief.ts`), preserved deep markdown/resume banner, refreshed `frontend/e2e/week-home-refresh.regression.spec.ts`, verification target: `./scripts/run_e2e.sh e2e/week-home-refresh.regression.spec.ts`.

- 2026-03-27: Task F3 — audited root `.gitignore` and expanded ignore rules for sensitive/local noise (`tmp/`, `telegram_files/`, `output_to_user/`, local env/keys, Python caches/coverage, Playwright artifacts, IDE folders, docker compose overrides, `.ductor*`, `frontend/tsconfig.tsbuildinfo`). Verification target: `git status --short` should not surface newly ignored local artifacts.

- 2026-04-09: Final sink-freshness slice restored Today canonical evidence freshness via writable sink fallback and post-test review fallback awareness; verified targeted logging/post-review tests, backend pipeline, API verify, curl, and today-week post-test evidence (Today clean, records_checked 20; Week remained no-evidence-blocker/out-of-scope).
