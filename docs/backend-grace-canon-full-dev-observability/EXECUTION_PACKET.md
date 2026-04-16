# Execution Packet: Backend GRACE Canon Sync and Full Dev Observability

## Objective
Upgrade the existing backend active slice from partial GRACE structure to dense, trace-first development observability without changing business semantics.

## Slice
- slice_id: `SLICE-FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS`
- slice_dir: `/opt/astro-project/docs/backend-grace-canon-full-dev-observability`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/backend-grace-canon-full-dev-observability/requirements.slice.backend-grace-canon-full-dev-observability.xml`
- `/opt/astro-project/docs/backend-grace-canon-full-dev-observability/development-plan.slice.backend-grace-canon-full-dev-observability.xml`
- `/opt/astro-project/docs/backend-grace-canon-full-dev-observability/verification-matrix.slice.backend-grace-canon-full-dev-observability.md`
- `/opt/astro-project/docs/backend-grace-canon-full-dev-observability/knowledge-graph.slice.backend-grace-canon-full-dev-observability.xml`

## Impacted modules
- `M-API-GATEWAY`
- `M-TRACE-LOGGING`
- `M-DAY-BRIEF-SERVICE`
- `M-WEEK-BRIEF-SERVICE`
- `M-ANALYTICS-EVENTS`
- `M-OPS-AUTOMATION`

## Allowed write scope
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS/wave-plan.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-BACKEND-GRACE-CANON-FULL-DEV-OBS/packets`
- `/opt/astro-project/docs/backend-grace-canon-full-dev-observability`
- `/opt/astro-project/backend/app/main.py`
- `/opt/astro-project/backend/app/logging_utils.py`
- `/opt/astro-project/backend/app/middleware/correlation.py`
- `/opt/astro-project/backend/app/services/day_brief.py`
- `/opt/astro-project/backend/app/services/day_brief_validators.py`
- `/opt/astro-project/backend/app/services/week_brief_service.py`
- `/opt/astro-project/backend/app/services/scheduler.py`
- `/opt/astro-project/backend/app/services/analytics.py`
- `/opt/astro-project/tests/test_day_brief.py`
- `/opt/astro-project/tests/test_day_brief_schema.py`
- `/opt/astro-project/tests/test_week_brief_service.py`
- `/opt/astro-project/tests/test_week_brief_api.py`
- `/opt/astro-project/tests/test_logging_utils_grace.py`
- `/opt/astro-project/tests/test_catalog_logging.py`
- `/opt/astro-project/tests/test_billing_scheduler.py`

## Frozen scope
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

## Execution policy
- Respect the slice requirements and write scope exactly.
- Do not widen scope without architect approval.
- If a crash or 500 appears, add or update a reproduction test before claiming green.
- Verification must include post-test observability review when the slice touches a required surface.

## Worker deliverables
1. Code changes for the active packet only.
2. Updated or added tests for the affected slice.
3. Verification evidence and observability verdict.
4. Short reviewer-facing note: risks, open questions, and whether the next packet is unblocked.
