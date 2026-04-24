# Execution Packet: Canonical evidence generation orchestration for W03 closeout

## Objective
Provide a deterministic dev/test orchestration path that emits fresh canonical Today, Week, Admin, and Catalog evidence before strict post-test observability review.

## Slice
- slice_id: `FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424`
- slice_dir: `/opt/astro-project/docs/canonical-evidence-generation-orchestration`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`

## Impacted modules
- `M-DAY-BRIEF-SERVICE`
- `M-WEEK-BRIEF-SERVICE`
- `M-OPS-AUTOMATION`
- `M-API-GATEWAY`
- `FLOW-FORECAST-CATALOG`
- `FLOW-ADMIN-OPS`
- `VM-POST-TEST-OBSERVABILITY`

## Allowed write scope
- `scripts/generate_canonical_evidence.py`
- `tests/test_canonical_evidence_generation.py`
- `tests/test_post_test_review.py`
- `tests/test_log_watch_feed_admin.py`
- `tests/test_forecast_catalog_watch.py`
- `tools/post_test_review.py only for a minimal command adapter if strictly required`
- `tools/log_watch/*.py only for explicit generation hook support if strictly required`
- `prefect_grace/packets/FEAT-CANONICAL-EVIDENCE-GENERATION-ORCHESTRATION-20260424/**`

## Frozen scope
- `frontend/**`
- `backend report schema and billing semantics`
- `auth semantics and Telegram identity behavior`
- `watcher verdict strictness and FAIL_NO_EVIDENCE behavior`
- `root GRACE documents unless root_deltas are explicitly approved`

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
