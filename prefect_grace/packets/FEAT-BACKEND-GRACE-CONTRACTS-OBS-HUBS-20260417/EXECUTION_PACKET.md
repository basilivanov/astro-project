# Execution Packet: Backend GRACE Contracts And Observability Hubs

## Objective
Bring the current backend hub slice to stable strict-GRACE addressability and reviewer-readable development observability without changing product business semantics.

## Slice
- slice_id: `SLICE-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`
- slice_slug: `backend-grace-contracts-observability-hubs-20260417`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417`

## Source Of Truth
- `/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/feature-brief.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/wave-plan.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/architect_manifest.json`
- `/opt/astro-project/backend/app/main.py`
- `/opt/astro-project/backend/app/logging_utils.py`
- `/opt/astro-project/backend/app/middleware/correlation.py`
- `/opt/astro-project/backend/app/services/day_brief.py`
- `/opt/astro-project/backend/app/services/day_brief_validators.py`
- `/opt/astro-project/backend/app/services/scheduler.py`
- `/opt/astro-project/backend/app/services/analytics.py`
- `/opt/astro-project/tools/post_test_review.py`

## Impacted Modules
- `M-API-GATEWAY`
- `M-TRACE-LOGGING`
- `M-DAY-BRIEF-SERVICE`
- `M-WEEK-BRIEF-SERVICE`
- `M-ANALYTICS-EVENTS`
- `M-OPS-AUTOMATION`

## Allowed Write Scope
- `/opt/astro-project/backend/app/main.py`
- `/opt/astro-project/backend/app/logging_utils.py`
- `/opt/astro-project/backend/app/middleware/correlation.py`
- `/opt/astro-project/backend/app/services/day_brief.py`
- `/opt/astro-project/backend/app/services/day_brief_validators.py`
- `/opt/astro-project/backend/app/services/scheduler.py`
- `/opt/astro-project/backend/app/services/analytics.py`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/tools/log_watch/common.py`
- `/opt/astro-project/tools/log_watch/scheduler_watch.py`
- `/opt/astro-project/tests/test_day_brief.py`
- `/opt/astro-project/tests/test_day_brief_schema.py`
- `/opt/astro-project/tests/test_week_brief_api.py`
- `/opt/astro-project/tests/test_logging_utils_grace.py`
- `/opt/astro-project/tests/test_catalog_logging.py`
- `/opt/astro-project/tests/test_billing_scheduler.py`
- `/opt/astro-project/tests/test_post_test_review.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CONTRACTS-OBS-HUBS-20260417/**`

## Frozen Scope
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/backend/app/services/report_workflow.py`
- `/opt/astro-project/backend/app/services/feed_service.py`
- `/opt/astro-project/backend/app/services/personalized_daily.py`
- `/opt/astro-project/backend/app/services/access_control.py`
- `/opt/astro-project/backend/app/services/billing.py`
- `/opt/astro-project/backend/app/services/referral_service.py`
- `/opt/astro-project/backend/app/models.py`
- `/opt/astro-project/backend/app/db.py`
- `/opt/astro-project/backend/app/catalog_logging.py`
- `/opt/astro-project/backend/app/diagnostics.py`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`

## Business Invariants
- No DayBrief, WeekBrief, report-read, scheduler, analytics, auth, billing, or scoring business semantics change in this slice.
- Existing GRACE logging envelope, correlation model, and transport remain the only allowed observability backbone.
- Packet-local evidence in W01 and W02 cannot close the feature; W03 owns the final canonical `today-week` verdict.
- Scheduler or analytics non-emission must be called out explicitly instead of being silently treated as clean coverage.

## Verification
- `docker exec astro-project-backend-1 python3 scripts/pipeline.py`
- `docker exec astro-project-backend-1 python3 -m pytest -q tests/test_day_brief.py tests/test_day_brief_schema.py tests/test_week_brief_api.py tests/test_logging_utils_grace.py tests/test_catalog_logging.py tests/test_billing_scheduler.py tests/test_post_test_review.py`
- `python3 tools/post_test_review.py --profile read-only --since 30m --report-format md`
- `python3 tools/post_test_review.py --profile today-week --since 30m --report-format md`

## Observability Policy
W01 and W02 own packet-local/read-only evidence only. W03 owns the canonical `today-week` closeout and accepts only `clean` or `degraded-but-expected`; `unexpected-degradation` and `no-evidence-blocker` block the feature.

## Worker Deliverables
1. Code or test deltas for the active packet only.
2. Fresh targeted verification evidence.
3. Explicit observability verdict for the owned evidence lane.
4. Reviewer-facing note with scope, risks, and whether the next packet is unblocked.
