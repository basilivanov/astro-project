# Execution Packet: Backend Active Slice GRACE Canon Sync

## Objective
Make the current backend active slice formally addressable through strict-GRACE module contracts, module maps, function contracts, and semantic START/END blocks before deeper backend refactor and maximal observability work.

## Slice
- slice_id: `SLICE-FEAT-BACKEND-ACTIVE-SLICE-GRACE-CANON-SYNC`
- slice_dir: `/opt/astro-project/docs/backend-active-slice-grace-canon-sync`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/docs/backend-active-slice-grace-canon-sync/requirements.slice.backend-active-slice-grace-canon-sync.xml`
- `/opt/astro-project/docs/backend-active-slice-grace-canon-sync/development-plan.slice.backend-active-slice-grace-canon-sync.xml`
- `/opt/astro-project/docs/backend-active-slice-grace-canon-sync/verification-matrix.slice.backend-active-slice-grace-canon-sync.md`
- `/opt/astro-project/docs/backend-active-slice-grace-canon-sync/knowledge-graph.slice.backend-active-slice-grace-canon-sync.xml`

## Impacted modules
- `M-API-GATEWAY`
- `M-TRACE-LOGGING`
- `M-DAY-BRIEF-SERVICE`
- `M-WEEK-BRIEF-SERVICE`
- `M-ANALYTICS-EVENTS`
- `M-OPS-AUTOMATION`

## Allowed write scope
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
- `/opt/astro-project/frontend`
- `/opt/astro-project/backend/app/services/report_workflow.py`
- `/opt/astro-project/backend/app/services/feed_service.py`
- `/opt/astro-project/backend/app/services/personalized_daily.py`
- `/opt/astro-project/backend/app/services/access_control.py`
- `/opt/astro-project/backend/app/services/billing.py`
- `/opt/astro-project/backend/app/services/referral_service.py`
- `/opt/astro-project/backend/app/models.py`
- `/opt/astro-project/backend/app/db.py`

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
