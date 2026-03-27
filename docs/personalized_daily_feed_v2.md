# Personalized Daily Feed v2

## Goal
Replace the MVP-like Moscow/generic `/api/feed/today` logic with a narrow, facts-first personalization layer that stays backward compatible for existing clients.

## Current Implementation Slice
- Endpoint remains `GET /api/feed/today`.
- Response shape remains the same: `date`, `moon_sign`, `moon_phase`, `moon_emoji`, `aspects_count`, `general_vibe`, `traffic_lights`.
- Personalization is activated when `X-Telegram-Auth` is present and resolves to a valid user profile.
- Anonymous or invalid-auth requests fall back to a safe general path instead of failing.

## Module Boundaries

### 1. `backend/app/services/personalized_daily.py`
- Responsibility: build facts-first daily context.
- Inputs:
  - `now_utc`
  - optional `User`
- Outputs:
  - local date/timezone/location
  - Moon sign / phase / emoji
  - `aspect_summary`
  - `traffic_lights`
  - optional fast transit-to-natal hits
  - optional week/month/year horizon facts
  - `cache_scope` for LLM memoization
- Internal rules:
  - timezone priority: `current_timezone` -> `birth_timezone` -> `UTC`
  - location priority for transits: current coords -> birth coords -> current location -> birth place -> `Moscow`
  - full personalization requires `birth_date` and `birth_place`
  - partial profile still gets local timezone/location + Moon/day context

### 2. `backend/app/services/feed_service.py`
- Responsibility: convert facts into short vibe text.
- Changes in v2:
  - exposes `build_personalized_feed()` as the public GRACE facade for assembling the final feed copy from deterministic astro facts and semantic personalization blocks
  - exposes `enqueue_regeneration()` as an explicit current-day cache invalidation hook so the next read rebuilds the feed for the same `moon_sign` + `cache_scope`
  - accepts optional `personalization_context`
  - cache key includes `cache_scope`
  - fallback text can include factual emphasis when LLM is unavailable
  - prompt explicitly forbids inventing aspects/events outside supplied facts
  - uses explicit prompt registry entry `personalized_daily_v2` inside `backend/app/services/feed_service.py`

### Feed service public entrypoints

#### `build_personalized_feed()`
- Async facade over `get_daily_vibe_llm()`.
- Input contract:
  - required deterministic day facts: `moon_sign`, `moon_phase`, `aspects_summary`
  - optional `personalization_context` with fact-first semantic payload from `personalized_daily.py`
  - optional `cache_scope` for per-profile memoization
  - optional `correlation_id` for GRACE trace continuity
- Behavior:
  - opens a dedicated `BUILD_PERSONALIZED_FEED` trace block
  - delegates actual prompt/fallback execution to `get_daily_vibe_llm()`
  - preserves the same normalization and hallucination guardrails as the lower-level LLM path
- Output:
  - returns the final normalized `general_vibe` string, still constrained to the short two-sentence style contract

#### `enqueue_regeneration()`
- Sync invalidation hook for the in-memory daily feed cache.
- Input contract:
  - required `moon_sign`
  - optional `cache_scope`; defaults to shared cache space
  - optional `correlation_id`
- Behavior:
  - targets the current UTC day cache key: `(today, moon_sign, cache_scope)`
  - removes the cached entry if it exists
  - emits structured `feed.regeneration_enqueued` log with `cache_hit` so operators can see whether invalidation actually found cached data
- Output:
  - returns `True` when a cache entry was invalidated, otherwise `False`

### 3. `backend/app/main.py`
- Responsibility: API wiring.
- Changes in v2:
  - `/api/feed/today` accepts optional `X-Telegram-Auth`
  - auth failure is logged and ignored for this endpoint
  - endpoint calls `build_personalized_daily_facts()` first, then `get_daily_vibe_llm()`
  - hardcoded random traffic lights are removed

### 4. `frontend/app/page.tsx`
- Responsibility: activate personalized backend path.
- Change:
  - `X-Telegram-Auth` is now sent to `/api/feed/today`, same as `/api/users/me`

## Fact Sources

### Day context
- local date/time from user timezone
- transit chart at current local time and user location if available
- Moon sign and phase
- generic same-day transit backdrop if profile is incomplete

### Fast personalization
- tight transit-to-natal hits from `Sun`, `Mercury`, `Venus`, `Mars`
- filtered to natal personal points: `Sun`, `Moon`, `Mercury`, `Venus`, `Mars`, `ASC`, `MC`

### Horizon context
- week: `calculate_forecast_week_data()`
- month: `calculate_forecast_month_data()`
- year: `calculate_forecast_year_data()`
- failures in any one horizon layer degrade to partial facts, not full endpoint failure

## Traffic Lights v2
- No randomness.
- Base score comes from current week/day traffic context.
- Adjustments come from:
  - fast hits relevant to health / money / love
  - month status
  - current month status inside year data
  - void-of-course style Moon penalty from weekly moon context

## Rollout Notes

### Safe now
- `GET /api/feed/today` keeps anonymous mode intact and adds deterministic personalization when `X-Telegram-Auth` resolves.
- Traffic lights are facts-based and stable for the same `cache_scope`; random fallback has been removed.
- Partial profiles work in `profile_light`: local timezone, local date and Moon context still render without natal fast hits.
- Prompt contract is pinned via `personalized_daily_v2` registry entry, so feed copy cannot invent extra aspects or non-factual events.
- Internal QA can inspect `meta` via `?debug=true` or `X-Feed-Debug: 1`; anonymous callers do not receive this block, and production frontend no longer requests debug by default.

### Log-driven contour
- Structured events for `FEED-PERSONALIZED-DAILY` now use `feed.entry`, `feed.debug`, and `feed.error`.
- Minimal contour coverage:
  - request start in `backend/app/main.py`
  - auth fallback in `backend/app/main.py`
  - facts builder start/cache hit/build result in `backend/app/services/personalized_daily.py`
  - public feed facade block `BUILD_PERSONALIZED_FEED` in `backend/app/services/feed_service.py`
  - regeneration invalidation event `feed.regeneration_enqueued` in `backend/app/services/feed_service.py`
  - LLM prompt path in `backend/app/main.py`
  - endpoint fallback path in `backend/app/main.py`
- Safe fields only: `path`, `auth_mode`, `personalization_level`, `cache_scope`, `timezone`, `location`, `prompt_path`, `fallback_reason`, `has_fast_hits`. Raw `X-Telegram-Auth` / `initData` never enter logs.
- Replay helper: `python3 tools/feed_logs/replay_last.py <jsonl-log-file>` prints the latest feed flow summary with auth mode, personalization level, prompt path, cache hit, and fallback outcome.

### Rollout checklist
1. Monitor `feed.entry`, `feed.debug`, and `feed.error` INFO/ERROR logs for `cache_scope`, `personalization_level`, prompt path, and fallback reasons.
2. If profile data changes during the day, clear in-memory daily cache on profile update or wait until next local date boundary.
3. Frontend consumes `moon`, `fast_hits`, `traffic_lights`, and optional `meta` without page reload.
4. Example internal request: `curl -H "X-Telegram-Auth: <token>" "http://localhost:8000/api/feed/today?debug=true"`.
5. Example anonymous request: `curl "http://localhost:8000/api/feed/today"` returns stable non-random fallback facts without `meta`.

## Verification
- `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_daily_feed_robustness.py tests/test_personalized_daily_service.py`
- `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- `./scripts/run_e2e.sh e2e/core-ux.spec.ts`

## Known Residual Risk
- Current targeted `core-ux` run passes live mock-auth feed load, profile page, and week page, but the three mock-only fallback/empty/error assertions are drifting and need separate frontend cleanup.

## Gate Evidence — FLOW-DAILY-FEED (2026-03-20)

- Flow verdict: `FLOW-DAILY-FEED` ✅ PASS on 2026-03-20 14:39 UTC after rerunning the personalized daily regression bundle end-to-end.
- Backend targeted suite: `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_personalized_daily_service.py tests/test_daily_feed_robustness.py tests/verify_daily_feed.py` → exit code `0`, `8 passed` in `3.06s` (warnings limited to known Pydantic/FastAPI deprecations).
- Frontend coverage: `FRONTEND_HEALTH_CONTAINER=astro-project-frontend-1 E2E_BASE_URL=http://astro-project-frontend-1:3000 ./scripts/run_e2e.sh e2e/core-ux.spec.ts` → exit code `0`, `7 passed` in `13.1s` after all health probes (`backend`, `db`, `frontend`, `proxy`) succeeded.
- Evidence for this Gate lives in the terminal logs for the commands above; no additional artifacts were generated beyond the standard Playwright output inside `frontend/test-results/`.

## Gate Evidence — FLOW-DAILY-FEED

- Flow ID: `FLOW-DAILY-FEED`. Targeted regression executed `2026-03-20 14:40-14:41 UTC`.
- Backend targeted pytest: `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_daily_feed_robustness.py tests/test_personalized_daily_service.py` → `8 passed, 7 warnings, exit 0`.
- Backend quick: `docker exec astro-project-backend-1 python3 scripts/pipeline.py` completed with all bundled hooks PASS to keep shared surfaces green.
- Frontend/E2E: `FRONTEND_HEALTH_CONTAINER=astro-project-frontend-1 E2E_BASE_URL=http://astro-project-frontend-1:3000 ./scripts/run_e2e.sh e2e/core-ux.spec.ts` → `7 passed` covering personalized daily happy path, safe fallback, retry/error states, and profile/week views.
- Log contour snapshot: `2026-03-20 14:41:21 feed.endpoint.success auth=True cache_scope=c1c0f0aac14a36b3 debug=True path=/api/feed/today` confirms personalized_v2 cache scope, auth-enabled run, and debug meta path immediately after the regression bundle.
