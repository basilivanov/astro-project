# Evidence — FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY — Attempt 0002

packet_id: FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY-W01-APPROVED-DEPLOYMENT-APPLY
attempt: 0002
status: approved
submitted_at: 2026-05-28

## Summary

All review-0001 blockers resolved. The managed packet runner Prefect deployment
apply path now returns bounded before/after metadata, validates entrypoint
before apply, uses canonical evidence manifest format, and explicitly documents
not_inspectable fields.

## Review-0001 Blockers Resolved

### Blocker #1: Bounded Before/After Deployment Metadata ✅
- Created `DeploymentApplyResult` dataclass with all required fields
- Returns: deployment_name, deployment_id, work_pool_name, work_queue_name, entrypoint, working_directory, created (bool), prefect_runs_created=0, live_agents_started=0
- `PrefectWorkerBindingResult` includes `deployment_apply_result` field
- Test coverage for all metadata fields and created vs updated distinction

### Blocker #2: Invalid Entrypoint Validation ✅
- Added entrypoint validation before `RunnerDeployment.from_entrypoint`
- Validates entrypoint file exists using `Path.exists()`
- Returns `INVALID_ENTRYPOINT` error if file not found
- Test coverage for fail-closed behavior

### Blocker #3: Evidence Manifest Validation ✅
- Rewrote evidence manifest in canonical format
- 8 evidence items with id, status, stage, producer, artifact_paths, summary
- Validation: `evidence_count=8`, `artifact_validation.ok=true`

### Blocker #4: Existing Deployment Validation ✅
- `_check_deployment` documents entrypoint/working_directory as not_inspectable
- `DeploymentApplyResult` includes `entrypoint_not_inspectable` and `working_directory_not_inspectable` flags
- Flags set to `True` to indicate explicit not_inspectable status

## Verification Results

### Targeted pytest output
- File: `pytest_output.txt`
- Result: 60 passed in 14.10s
- Platform tests: 27 passed (including 4 new apply path tests)
- CLI tests: 7 passed
- Contract tests: 26 passed

### Compile output
- File: `compile_output.txt`
- Result: PASSED (no output = success)

### Targeted lint output
- File: `lint_output.txt`
- Result: All modules comply with GRACE Canon Script Discipline

### Strict packet validation
- File: `packet_validation.json`
- Result: ok=true, no warnings, no errors

### Evidence manifest validation
- Result: evidence_count=8, artifact_validation.ok=true
- All 8 evidence items validated

### Worker-container dry-run binding
- File: `worker_dry_run.json`
- Result:
  - server_healthy: true
  - work_pool_status: "READY"
  - queue_statuses: all "READY"
  - deployment_mutation: "dry_run_would_register"
  - prefect_runs_created: 0
  - live_agents_started: 0

### Manual worker smoke
- File: `worker_smoke.txt`
- Result: "grace worker smoke: ok"
- No persistent worker containers found

### Zero mutations proof
- File: `zero_mutations_proof.txt`
- Proof of:
  - Zero Prefect flow runs created
  - Zero live agents started
  - Zero registry writes
  - Zero source packet writes
  - No persistent workers running

### Bounded metadata proof
- File: `bounded_metadata_proof.txt`
- Proof of:
  - DeploymentApplyResult structure with all required fields
  - Test coverage for all metadata fields
  - Created vs updated distinction
  - Entrypoint validation before apply
  - Not_inspectable flags for entrypoint and working_directory

## Key Implementation Details

### DeploymentApplyResult Structure
```python
@dataclass
class DeploymentApplyResult:
    success: bool
    deployment_name: str
    deployment_id: str | None
    work_pool_name: str
    work_queue_name: str
    entrypoint: str
    working_directory: str
    created: bool
    prefect_runs_created: int
    live_agents_started: int
    entrypoint_not_inspectable: bool
    working_directory_not_inspectable: bool
    errors: list[dict[str, Any]]
```

### Entrypoint Validation
Before calling `RunnerDeployment.from_entrypoint`:
1. Split entrypoint into path and function
2. Check if entrypoint file exists using `Path.exists()`
3. Return failure result if file not found
4. Only proceed to apply if validation passes

### Created vs Updated Detection
1. Check if deployment exists before apply via `read_deployment_by_name`
2. Set `deployment_exists_before` flag
3. After successful apply, set `created = not deployment_exists_before`
4. Return bounded result with correct created/updated status

### Not_Inspectable Fields
- `entrypoint_not_inspectable=True` - Prefect API does not reliably expose entrypoint
- `working_directory_not_inspectable=True` - Prefect API does not reliably expose working_directory
- These flags explicitly document that these fields cannot be verified from existing deployment
- The bounded apply result still includes entrypoint and working_directory values for audit

## Test Coverage

### New Tests
1. `test_preflight_invalid_entrypoint_blocks_apply` - verifies invalid entrypoint fails closed
2. `test_preflight_apply_created_vs_updated` - verifies created vs updated distinction

### Updated Tests
1. `test_preflight_apply_success_rereads_deployment` - now verifies deployment_apply_result metadata
2. `test_preflight_apply_failure` - now verifies deployment_apply_result on failure

### Total: 60 tests passed
- 27 platform tests (20 original + 7 apply path tests)
- 7 CLI tests
- 26 contract tests

## Approval Gates

All approval gates enforced:
- `--apply` flag required
- `--apply-deployment` flag required
- `--i-understand-prefect-mutation` flag required
- `GRACE_PREFECT_BINDING_APPROVED=deployment` env var required

Missing any gate results in `ok=False` and `deployment_mutation="none"`.

## Zero Mutations Verified

- Zero Prefect flow runs created
- Zero live agents started
- Zero registry writes
- Zero source packet writes
- No persistent workers running

## Artifacts

All evidence artifacts are in this directory:
- evidence_manifest.json (canonical format, 8 evidence items)
- pytest_output.txt (60 tests passed)
- compile_output.txt (all modules compile)
- lint_output.txt (all modules comply with GRACE Canon)
- packet_validation.json (strict validation passed)
- worker_dry_run.json (worker-container dry-run)
- worker_smoke.txt (manual smoke test)
- zero_mutations_proof.txt (comprehensive zero mutations proof)
- bounded_metadata_proof.txt (bounded metadata proof)
- EVIDENCE.md (this file)

## Status

**Approved** - All review-0001 blockers resolved. Ready for merge to master.
