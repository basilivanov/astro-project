# Evidence — FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY — Attempt 0001

packet_id: FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY-W01-APPROVED-DEPLOYMENT-APPLY
attempt: 0001
status: ready_for_review
submitted_at: 2026-05-28

## Summary

All implementation requirements completed. The managed packet runner Prefect
deployment apply path is real, gated, and auditable. All approval gates are
enforced. Zero Prefect flow runs created in all modes. Zero live agents started.
No persistent workers left running.

## Implementation Completed

1. ✅ Real apply-mode CLI switch (`--apply`) and tests
2. ✅ Apply helper validates entrypoint before applying
3. ✅ Injected tests proving approved apply is reachable
4. ✅ Regression tests for missing approval, dry-run, invalid entrypoint, apply failure
5. ✅ Real live Prefect apply kept out of automated verification

## Acceptance Criteria

- ✅ Dry-run binding reports deployment plan without mutation
- ✅ Approved injected apply returns `deployment_mutation=applied` only when helper actually applies
- ✅ Missing gates block before any Prefect mutation
- ✅ Live worker-container dry-run reaches Prefect and creates zero flow runs
- ✅ Manual `scripts/grace_worker_smoke.sh` remains green and leaves no persistent worker

## Verification Results

### Targeted pytest output
- File: `pytest_output.txt`
- Result: 58 passed in 13.14s
- Platform tests: 20 passed
- CLI tests: 7 passed
- Contract tests: 31 passed

### Compile output
- File: `compile_output.txt`
- Result: PASSED (no output = success)

### Targeted lint output
- File: `lint_output.txt`
- Result: All modules comply with GRACE Canon Script Discipline
- Checked: prefect_worker_binding.py, runtime_adapter.py, CLI handler, parser

### Strict packet validation
- File: `packet_validation.json`
- Result: ok=true, no warnings, no errors

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
  - All approval gates enforced

## Key Implementation Details

### Approval Gates
Real deployment apply requires ALL of:
1. `--apply` flag (enables non-dry-run mode)
2. `--apply-deployment` flag (requests deployment mutation)
3. `--i-understand-prefect-mutation` flag (acknowledgement)
4. `GRACE_PREFECT_BINDING_APPROVED=deployment` env var (operator approval)

Missing any gate results in `ok=False` and `deployment_mutation="none"`.

### Deployment Contract
- Deployment name: `prefect-grace-managed-packet-runner/live-managed-packet-runner`
- Entrypoint: `prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow`
- Work pool: `astro-process` (type: `process`)
- Work queue: `grace-live`
- Working directory: from runtime_config

### Test Coverage
- Platform-level injected tests with mocked Prefect client
- CLI arg propagation tests
- Dry-run planning tests
- Approval gate enforcement tests (including valid deployment case)
- Apply success with deployment re-read tests
- Apply failure tests
- Entrypoint validation tests

## No Escalation Triggers

- ✅ Deployment apply does NOT create packet flow runs
- ✅ Apply is NOT reachable without all approval gates
- ✅ Deployment points to correct entrypoint, pool, queue, working dir
- ✅ Output contains no secrets or unbounded logs

## Artifacts

All evidence artifacts are in this directory:
- evidence_manifest.json
- pytest_output.txt
- compile_output.txt
- lint_output.txt
- packet_validation.json
- worker_dry_run.json
- worker_smoke.txt
- zero_mutations_proof.txt
- EVIDENCE.md (this file)

## Ready for Review

This packet is ready for Architect review. All requirements met, all tests
passing, all approval gates enforced, zero mutations in all modes.
