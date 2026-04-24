# Execution Packet: Canonical observability evidence repair for Today Week Admin Catalog

## Objective
Repair canonical post-test observability evidence classification and freshness provenance so reviewers can distinguish clean evidence, real degradation, expected degradation, stale evidence, and true missing evidence.

## Slice
- slice_id: `SLICE-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424`
- slice_dir: `/opt/astro-project/docs/canonical-observability-evidence-repair`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`

## Impacted modules
- `M-OBSERVABILITY-POST-TEST-REVIEW`
- `M-OBSERVABILITY-LOG-WATCH`
- `M-CANONICAL-EVIDENCE-TESTS`

## Allowed write scope
- `prefect_grace/packets/FEAT-CANONICAL-OBSERVABILITY-EVIDENCE-REPAIR-20260424/**`
- `docs/canonical-observability-evidence-repair/**`
- `tools/post_test_review.py`
- `tools/log_watch/common.py`
- `tools/log_watch/feed_admin_watch.py`
- `tools/log_watch/forecast_catalog_watch.py`
- `tests/test_post_test_review.py`
- `tests/test_log_watch_feed_admin.py`
- `tests/test_forecast_catalog_watch.py`

## Frozen scope
- `frontend/**`
- `backend/app/** except logging-only producer fixes explicitly proven by W02/W03 evidence`
- `requirements.xml`
- `technology.xml`
- `development-plan.xml`
- `knowledge-graph.xml`
- `verification-matrix.md`
- `pricing, auth, billing, report schema, and DTO product behavior`

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
