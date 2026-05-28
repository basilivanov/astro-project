# Review 0003 — FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY

status: rework_required
reviewer: codex
source_hash: sha256:0ad3753fa62edcc89abc5d7c228bd1500080e41797ba989f929acbaa4395d6f0
reviewed_commit: 848b9af
attempt: attempt-0002
reviewed_at: 2026-05-28

## Verdict

Rework required.

The deployment apply result shape is improved, but the rework introduced a
larger safety regression outside packet scope, and the evidence/static gates are
not clean.

I did not run real Prefect deployment apply. During regression testing, a dry-run
E2E packet test started a real Codex verifier process; I killed only that pytest
process and its child Codex process.

## Blockers

### 1. Out-of-scope `e2e_packet_runner.py` change launches real agents in dry-run

`prefect_grace/platform/e2e_packet_runner.py` is not in this packet's allowed
write scope. Scope check against the changed files reports:

```text
outside_allowed:
  prefect_grace/platform/e2e_packet_runner.py
```

The change is also a safety regression. `run_e2e_packet(..., dry_run=True,
execute_agent=False, fake_verifier_output=None, fake_reviewer_output=None)` now
selects real verifier/reviewer launchers:

```text
if fake_verifier_output is None and fake_reviewer_output is None:
    verifier_launcher = _create_real_verifier_launcher(...)
    reviewer_launcher = _create_real_reviewer_launcher(...)
```

Those launchers call `_launch_codex_for_packet(..., dry_run=False)`.

Observed while running touched-file regression:

```text
pytest -q tests/test_prefect_grace_e2e_packet_runner.py tests/test_prefect_grace_e2e_packet_runner_flow.py
```

Process evidence showed:

```text
pytest ... test_prefect_grace_e2e_packet_runner.py ...
node /usr/local/bin/codex ... TEST-PACKET-W01-TEST-VERIFIER ...
```

This violates the E2E runner contract and this packet's no-live-agents safety
requirements.

Required fix:

- remove the `e2e_packet_runner.py` changes from this packet, or move them into
  a separate scoped packet;
- restore dry-run behavior so dry-run tests use fake launchers and never call
  `_launch_codex_for_packet`;
- add/restore regression coverage proving `dry_run=True` and
  `execute_agent=False` cannot start verifier/reviewer agents.

### 2. Targeted GRACE lint fails on the new `DeploymentApplyResult.to_dict`

Targeted lint output:

```text
[GRACE-LINT] Strict contract verification FAILED:
 - platform/runtime_adapter.py: Public function/method 'to_dict' on line 542 is missing a GRACE function contract.
```

Required fix:

- add the missing function contract before `DeploymentApplyResult.to_dict`;
- rerun targeted GRACE lint for all touched modules.

### 3. Evidence manifest still does not validate the listed artifacts

The attempt-0002 manifest has `evidence_count=8`, but all items use
`status: "passed"`. The artifact validator only validates `status="collected"`
items, so validation still checks zero artifact files:

```text
artifact_validation:
  ok: true
  validated_artifacts: []
  missing_artifacts: []
```

It also emits `unknown_evidence_id` warnings for every item.

Required fix:

- use canonical collected evidence items, for example `status: "collected"` and
  `stage: "packet_local"`;
- rerun validation and require non-empty `validated_artifacts`;
- either align IDs with the packet evidence contract, or explicitly document why
  the warnings are acceptable. Prefer contract-aligned IDs.

### 4. Invalid-entrypoint regression is mocked above the behavior it claims to prove

`test_preflight_invalid_entrypoint_blocks_apply` patches
`prefect_worker_binding._apply_managed_packet_deployment` and returns a fabricated
`INVALID_ENTRYPOINT` result. That proves preflight propagates an error from a
mock, but it does not prove `apply_managed_packet_deployment_helper(...)`
validates the entrypoint before `RunnerDeployment.from_entrypoint` or before
`deployment.apply(...)`.

Required fix:

- add a direct runtime_adapter-level test for
  `apply_managed_packet_deployment_helper(...)`;
- force an invalid entrypoint or missing entrypoint file and assert
  `RunnerDeployment.from_entrypoint` / `deployment.apply` are not called;
- keep the preflight propagation test as secondary coverage.

### 5. `review-0002.md` in the implementation commit is not a valid reviewer gate

The implementation commit added
`REVIEWS/review-0002.md` with `status: approved`, `reviewer: codex`,
`source_hash: sha256:TBD`, and `reviewed_commit: TBD`.

That is a self-approval artifact from the implementation commit, not an
independent review. It should not be used as the packet gate.

Required fix:

- remove or replace that artifact with a normal rework summary/evidence artifact;
- let the reviewer produce the next review artifact.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_worker_binding.py tests/test_prefect_grace_cli_prefect_worker_binding.py tests/test_prefect_grace_cli_contracts.py`: `60 passed`.
- `pytest -q tests/test_prefect_grace_e2e_packet_runner.py tests/test_prefect_grace_e2e_packet_runner_flow.py`: started a real Codex verifier process during dry-run; I terminated the run.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint: failed on missing contract in `runtime_adapter.py`.
- Strict packet validation: `ok=true`.
- Evidence manifest validation: `ok=true`, `evidence_count=8`, but
  `validated_artifacts=[]` and all evidence IDs are unknown to the contract.
- Scope check: failed because `prefect_grace/platform/e2e_packet_runner.py` is
  outside allowed write scope.

## Required Rework

1. Remove or rescope the `e2e_packet_runner.py` changes and restore dry-run
   no-live-agent behavior.
2. Fix GRACE lint for `DeploymentApplyResult.to_dict`.
3. Make the evidence manifest validate real artifact files.
4. Add direct runtime_adapter invalid-entrypoint coverage.
5. Remove the self-approved `review-0002.md` artifact from the implementation
   commit path and rerun the full packet/touched-file profile.
