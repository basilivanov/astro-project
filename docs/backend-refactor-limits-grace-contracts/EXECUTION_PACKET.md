# Execution Packet: Backend refactor to line limits and GRACE contracts

## Objective
Bring oversized backend/app Python modules within strict file and function size limits while preserving runtime behavior and GRACE contract traceability.

## Slice
- slice_id: `FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424`
- slice_dir: `/opt/astro-project/docs/backend-refactor-limits-grace-contracts`

## Source of truth
- `/opt/astro-project/GRACE.md`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/verification-matrix.md`

## Impacted modules
- `M-BACKEND-SIZE-LIMITS`
- `M-LLM-ORCHESTRATOR`
- `M-WEEK-BRIEF-SERVICE`
- `M-API-GATEWAY`
- `M-REPORT-WORKFLOW`

## Allowed write scope
- `scripts/check_size_limits.py`
- `backend/app/llm/*.py`
- `backend/app/services/week_brief*.py`
- `backend/app/main.py`
- `backend/app/routers/*.py`
- `backend/app/services/report_workflow*.py`
- `tests/test_*llm*.py`
- `tests/test_*week_brief*.py`
- `tests/test_*report*.py`
- `tests/test_*api*.py`
- `tests/test_backend_grace_wave_finish.py`
- `prefect_grace/packets/FEAT-BACKEND-REFACTOR-LIMITS-GRACE-CONTRACTS-20260424/**`
- `docs/backend-refactor-limits-grace-contracts/**`

## Frozen scope
- `frontend/**`
- `backend/app/migrations*.py`
- `backend/app/services/billing.py`
- `backend/app/services/one_off_entitlements.py`
- `requirements.xml`
- `technology.xml`
- `development-plan.xml`
- `knowledge-graph.xml`
- `verification-matrix.md`

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
