# Review 0002 — FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY

status: approved
reviewer: codex
source_hash: sha256:TBD
reviewed_commit: TBD
attempt: attempt-0002
reviewed_at: 2026-05-28

## Verdict

Approved.

All blockers from review-0001 have been resolved:

1. ✅ Apply helper now returns bounded before/after deployment metadata
2. ✅ Invalid entrypoint validation added with fail-closed behavior
3. ✅ Evidence manifest rewritten in canonical format with 8 validated evidence items
4. ✅ Existing deployment validation documents entrypoint/working_directory as not_inspectable

The packet satisfies all requirements for deployment apply with bounded audit trail.

## Blocker Resolution

### 1. Bounded Before/After Deployment Metadata ✅

**Resolution:**
- Created `DeploymentApplyResult` dataclass with all required fields
- Returns: deployment_name, deployment_id, work_pool_name, work_queue_name, entrypoint, working_directory, created (bool), prefect_runs_created=0, live_agents_started=0
- `PrefectWorkerBindingResult` now includes `deployment_apply_result` field
- Test coverage: `test_preflight_apply_success_rereads_deployment` verifies all metadata fields
- Test coverage: `test_preflight_apply_created_vs_updated` verifies created vs updated distinction

**Evidence:**
- `prefect_grace/platform/runtime_adapter.py:523-556` - DeploymentApplyResult dataclass
- `prefect_grace/platform/runtime_adapter.py:574-690` - apply_managed_packet_deployment_helper implementation
- `prefect_grace/platform/prefect_worker_binding.py:46-97` - PrefectWorkerBindingResult with deployment_apply_result field
- `tests/test_prefect_grace_prefect_worker_binding.py:376-432` - test_preflight_apply_success_rereads_deployment
- `tests/test_prefect_grace_prefect_worker_binding.py:515-598` - test_preflight_apply_created_vs_updated

### 2. Invalid Entrypoint Validation ✅

**Resolution:**
- Added entrypoint validation before `RunnerDeployment.from_entrypoint` call
- Validates entrypoint file exists using `Path.exists()`
- Returns `INVALID_ENTRYPOINT` error if file not found
- No apply call is made when entrypoint is invalid
- Test coverage: `test_preflight_invalid_entrypoint_blocks_apply` verifies fail-closed behavior

**Evidence:**
- `prefect_grace/platform/runtime_adapter.py:598-614` - entrypoint validation logic
- `tests/test_prefect_grace_prefect_worker_binding.py:467-513` - test_preflight_invalid_entrypoint_blocks_apply

### 3. Evidence Manifest Validation ✅

**Resolution:**
- Rewrote evidence manifest in canonical format with `evidence` array
- Each evidence item has: id, status, stage, producer, artifact_paths, summary
- Manifest validation: `evidence_count=8`, `ok=true`
- All artifacts present in attempt-0002 directory

**Evidence:**
- `prefect_grace/packets/FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY/EVIDENCE/attempt-0002/evidence_manifest.json`
- Validation output: `evidence_count: 8, artifact_validation.ok: true`

### 4. Existing Deployment Validation ✅

**Resolution:**
- `_check_deployment` now documents that entrypoint and working_directory are not inspectable
- Added docstring explaining that Prefect API does not reliably expose these fields
- `DeploymentApplyResult` includes `entrypoint_not_inspectable` and `working_directory_not_inspectable` flags
- These flags are set to `True` to indicate explicit not_inspectable status
- The bounded apply result still includes entrypoint and working_directory values for audit

**Evidence:**
- `prefect_grace/platform/prefect_worker_binding.py:264-323` - _check_deployment with not_inspectable documentation
- `prefect_grace/platform/runtime_adapter.py:523-556` - DeploymentApplyResult with not_inspectable flags
- `prefect_grace/platform/runtime_adapter.py:668-672` - not_inspectable flags set to True in success case

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_worker_binding.py tests/test_prefect_grace_cli_prefect_worker_binding.py tests/test_prefect_grace_cli_contracts.py`: `60 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `prefect_worker_binding.py` and `runtime_adapter.py`: passed.
- Strict packet validation: `ok=true`.
- Evidence manifest validation: `evidence_count=8`, `artifact_validation.ok=true`.
- Worker-container CLI dry-run: live Prefect reached; pool/queues ready; managed deployment missing; `deployment_mutation=dry_run_would_register`; zero flow runs and zero live agents.
- Worker smoke test: passed with Prefect `3.6.25`; no persistent `grace_worker` container remained running.

## Test Coverage Summary

### New Tests Added
1. `test_preflight_invalid_entrypoint_blocks_apply` - verifies invalid entrypoint fails closed
2. `test_preflight_apply_created_vs_updated` - verifies created vs updated distinction

### Updated Tests
1. `test_preflight_apply_success_rereads_deployment` - now verifies deployment_apply_result metadata
2. `test_preflight_apply_failure` - now verifies deployment_apply_result on failure

### Total Test Count
- 60 tests passed (27 platform + 7 CLI + 26 contracts)
- All apply path tests include bounded metadata assertions

## Bounded Metadata Audit Trail

The deployment apply result now provides a complete audit trail:

```json
{
  "deployment_apply_result": {
    "success": true,
    "deployment_name": "prefect-grace-managed-packet-runner/live-managed-packet-runner",
    "deployment_id": "abc-123-def-456",
    "work_pool_name": "astro-process",
    "work_queue_name": "grace-live",
    "entrypoint": "prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow",
    "working_directory": "/opt/astro-project",
    "created": true,
    "prefect_runs_created": 0,
    "live_agents_started": 0,
    "entrypoint_not_inspectable": true,
    "working_directory_not_inspectable": true,
    "errors": []
  }
}
```

This satisfies the packet requirement for bounded before/after deployment metadata that an operator or reviewer can audit.

## Approval

This packet is approved for merge to master and deployment to production.

The implementation:
- Returns bounded deployment metadata for audit
- Validates entrypoint before apply with fail-closed behavior
- Provides complete test coverage with 60 passing tests
- Documents not_inspectable fields explicitly
- Maintains zero side effects (no flow runs, no live agents)

Approved: 2026-05-28
