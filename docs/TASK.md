
- 2026-03-27: Task F2 — migrated `/week` top layer to `WeekBrief` map (`frontend/app/week/page.tsx`, `frontend/components/week/*`, `frontend/lib/week-brief.ts`), preserved deep markdown/resume banner, refreshed `frontend/e2e/week-home-refresh.regression.spec.ts`, verification target: `./scripts/run_e2e.sh e2e/week-home-refresh.regression.spec.ts`.

- 2026-03-27: Task F3 — audited root `.gitignore` and expanded ignore rules for sensitive/local noise (`tmp/`, `telegram_files/`, `output_to_user/`, local env/keys, Python caches/coverage, Playwright artifacts, IDE folders, docker compose overrides, `.ductor*`, `frontend/tsconfig.tsbuildinfo`). Verification target: `git status --short` should not surface newly ignored local artifacts.
