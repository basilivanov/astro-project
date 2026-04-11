# Today Screen Review Verification Slice

Snapshot boundary: $(git -C /opt/astro-project rev-parse HEAD)
Parent matrix: `/opt/astro-project/verification-matrix.md`
Slice id: `SLICE-TODAY-SCREEN-REVIEW`

## VM IDs

| VM ID | Covers | Deterministic checks | Pass signal |
| --- | --- | --- | --- |
| `VM-TODAY-HERO-CLEAN` | `SCN-TODAY-HERO-CLEAN`, `SCN-TODAY-MOON-DEDUPE` | `docker exec astro-project-backend-1 python3 scripts/pipeline.py`; targeted frontend assertions around Today hero rendering | Hero shows one verdict path only; moon context remains compact and non-duplicative. |
| `VM-TODAY-RAW-TAGS` | `SCN-TODAY-NO-RAW-TAGS`, `SCN-TODAY-NO-FALSE-BIRTHTIME` | `./scripts/run_e2e.sh --last-failed`; targeted `quality` or `today` spec | No raw service tags or misleading birth-time warning visible on Today UI. |
| `VM-TODAY-DETAIL-LAYER` | `SCN-TODAY-SCORES-DETAIL` | targeted backend tests for canonical DTO shape; targeted e2e/spec for domain explanation blocks | Each canonical Day domain exposes one bounded explanation path and no extra windows/risks layers. |

| `VM-TODAY-CANON-LANE` | canonical Telegram-authenticated Day | `./scripts/run_e2e.sh e2e/telegram-signed-auth.spec.ts -g "Today"`; targeted adapter tests | Signed Telegram lane proves `ready`, `no_data`, `error`, and partial-ready/domain-failed without legacy Day surface sections. |
| `VM-TODAY-LIVE-CANARY` | live Telegram canary Day acceptance | `TELEGRAM_LIVE_CANARY_INIT_DATA=... TELEGRAM_LIVE_CANARY_USER_ID=... ./scripts/run_e2e.sh e2e/telegram-live-canary.spec.ts`; post-review `python3 tools/post_test_review.py --profile today-week --include-day-live-canary --report-format md` | `no_data`, failed, malformed/non-canonical payload, non-200 `/api/users/me` or `/api/feed/today`, and missing request/trace capture are deploy blockers. Artifacts are saved under `artifacts/day_live_canary/<timestamp>/`. |

## Evidence rules

- Worker MUST attach the exact commands executed and PASS/FAIL result.
- Worker MUST include file-level diff summary grouped by frontend/backend/tests.
- If a spec is missing for a reproduced defect, worker MUST add or update a deterministic reproduction test before claiming green.
- If `--last-failed` is empty/non-informative, worker MUST run a targeted Today/quality spec instead of stopping at a no-op.
