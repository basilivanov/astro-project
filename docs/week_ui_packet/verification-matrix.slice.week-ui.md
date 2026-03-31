# Week UI Execution Verification Slice

Snapshot boundary: `$(git -C /opt/astro-project rev-parse HEAD)`
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-WEEK-UI-EXECUTION`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-WEEK-STATE-BOUNDARY` | `SCN-WEEK-ENVELOPE-READY`, `SCN-WEEK-STATUS-STATES`, `SCN-WEEK-CTA-CLEAR` | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`; `./scripts/run_e2e.sh e2e/week-home-refresh.regression.spec.ts` | `/week` preserves loading/error/ready/in-progress semantics, and CTA path is correct for report vs premium/create. |
| `VM-WEEK-FALLBACK-SAFETY` | `SCN-WEEK-LEGACY-FALLBACK`, `SCN-WEEK-FALLBACK-TRANSPARENCY` | `./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts`; `./scripts/run_e2e.sh e2e/week-fallback.regression.spec.ts` | Fallback note is compact and visible when expected; page remains usable and does not leak raw payload/debug fields. |
| `VM-WEEK-UI-MAPPING` | `SCN-WEEK-HERO-SINGLE-SEMANTIC-CENTER`, `SCN-WEEK-DAY-CARDS-MAP`, `SCN-WEEK-DOMAINS-AND-GUIDANCE` | targeted frontend assertions in `e2e/week-live.spec.ts` or refresh regression spec; optional targeted backend tests for DTO mapping | Hero/theme, day cards, domain guidance, and CTA resolve from documented WeekBrief fields without frontend business-logic drift. |
| `VM-WEEK-EXPLAINABILITY` | `SCN-WEEK-MAJOR-FACTORS-VISIBLE`, `SCN-WEEK-CONFIDENCE-AND-BIRTHTIME` | backend quick pipeline; targeted week spec covering factor/explainability rendering | Major factors are rendered as bounded explainability artifacts; confidence/birth-time semantics remain stable and non-misleading. |

## Evidence rules

- Worker MUST attach exact commands executed and PASS/FAIL result.
- Worker MUST group evidence by `backend`, `frontend`, and `docs/packet alignment`.
- If a spec is updated or added, worker MUST state which VM ID it closes.
- If fallback behavior changes, worker MUST include before/after note for `week_brief` vs `week_map` path.
- If verification is blocked by environment, worker MUST record exact blocker and stop short of claiming completion.

## Minimum execution profile

- `backend:quick`
  - `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- `frontend:week-targeted`
  - `./scripts/run_e2e.sh e2e/week-home-refresh.regression.spec.ts`
  - `./scripts/run_e2e.sh e2e/week-page-fallback.spec.ts`
- Add one of the following when the touched area requires it:
  - `./scripts/run_e2e.sh e2e/week-fallback.regression.spec.ts`
  - `./scripts/run_e2e.sh e2e/week-live.spec.ts`

## Semantic coordinates to verify

- `COORD-WEEK-HERO`
  - Source DTO: `summary`, `status`, `explainability`, optional `premium`/`report_ref`
  - UI contract: one theme-centered hero/verdict area; not a markdown mirror
- `COORD-WEEK-DAY-MAP`
  - Source DTO: `day_cards[]`
  - UI contract: ordered day cards with stable `date`, `weekday`, `score`, `mode`, `headline`, `best_for`, `avoid`
- `COORD-WEEK-DOMAINS`
  - Source DTO: `domains[]`, optional `best_uses[]`, `risks[]`
  - UI contract: practical guidance cards; no raw service labels
- `COORD-WEEK-FACTORS`
  - Source DTO: `major_factors[]`, `explainability.confidence`, `explainability.birth_time_used`
  - UI contract: bounded explainability support, compact trust context
- `COORD-WEEK-CTA`
  - Source DTO: `cta.primary`, `report_ref`, `premium`, `status`
  - UI contract: open report when available; otherwise premium/create path
- `COORD-WEEK-FALLBACK`
  - Source DTO: adapter fallback from `week_map` or mock/default payload
  - UI contract: compact fallback note via `week-fallback-note`; screen still useful

## Non-goals for verification

- No requirement to validate deep `/read/[id]` markdown rendering here.
- No requirement to validate unrelated Today/Profile/Admin surfaces.
- No full Playwright regression unless the change spills beyond Week slice or architect requests release-level confidence.
