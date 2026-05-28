# Review 0001 — FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY

status: rework_required
reviewer: codex
source_hash: sha256:0ad3753fa62edcc89abc5d7c228bd1500080e41797ba989f929acbaa4395d6f0
reviewed_commit: 0033b97
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

Rework required.

The inherited worker-binding guardrails are in good shape: dry-run is default,
plain `--apply-deployment` remains a read-only plan, missing apply gates fail
closed, and worker-container read-only checks reach the live Prefect server.

However, this packet has stricter requirements than the accepted worker-binding
packet. The packet-specific apply audit contract and evidence manifest are not
yet satisfied.

No real deployment apply was run against the live Prefect server during review.

## Blockers

### 1. Apply helper still does not return bounded before/after deployment metadata

The packet requires `apply_managed_packet_deployment_helper(...)` to return
bounded before/after deployment metadata: deployment name, deployment id, work
pool, work queue, entrypoint, working directory, created vs updated, and zero
side-effect counters.

Current implementation in `prefect_grace/platform/runtime_adapter.py:537-590`
still returns only:

```text
(success: bool, deployment_id: str | None, errors: list)
```

`prefect_grace/platform/prefect_worker_binding.py` then exposes only
`deployment_mutation="applied"` and a warning with the id. There is no structured
before/after metadata for an operator or reviewer to audit, and no created-vs-
updated distinction.

Required fix:

- return a structured apply result, or add a structured field to the binding
  result, containing bounded before/after deployment metadata;
- include at least deployment name/id, work pool, work queue, entrypoint,
  working directory, created vs updated, `prefect_runs_created=0`, and
  `live_agents_started=0`;
- cover it with injected tests for missing deployment -> created and existing
  deployment -> updated.

### 2. Invalid entrypoint is not validated before apply and has no regression

The packet requires the helper to validate the entrypoint before applying and to
cover invalid entrypoint failure. Current code hard-codes:

```text
prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow
```

inside `RunnerDeployment.from_entrypoint(...)`, but there is no explicit
pre-apply validation helper and no injected invalid-entrypoint test. The existing
test only proves the current file/function exists; it does not prove the apply
path fails closed before mutation if the entrypoint becomes invalid or the API
shape changes.

Required fix:

- add explicit entrypoint validation before `RunnerDeployment.from_entrypoint`
  or make the helper testably validate the flow file/function before apply;
- add a regression that forces invalid entrypoint and proves no apply call is
  made, `ok=false`, and `deployment_mutation` is not `applied`.

### 3. Evidence manifest is not actually validating the claimed artifacts

`prefect_grace/packets/FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY/EVIDENCE/attempt-0001/evidence_manifest.json`
uses `evidence_items` with `path` fields. The current validator parses canonical
`evidence` items with `artifact_paths`.

Observed validation:

```text
evidence_count: 0
validated_artifacts: []
missing_artifacts: []
ok: true
```

So the manifest passes while validating none of the listed artifacts. This makes
the evidence weaker than the packet claims.

Required fix:

- rewrite the manifest to canonical `evidence` entries with `id`, `status`,
  `stage`, `producer`, `artifact_paths`, and `summary`;
- use manifest-local artifact paths, for example `pytest_output.txt`;
- rerun `validate-evidence-manifest` and require `evidence_count > 0` plus
  non-empty `validated_artifacts`.

### 4. Existing deployment validation does not inspect entrypoint or working directory

The packet escalation triggers include wrong entrypoint, pool, queue, or working
directory. `_check_deployment(...)` currently verifies only work pool and work
queue. It does not inspect deployment entrypoint/pull steps/working directory, so
an existing deployment with correct routing but wrong working directory could be
reported ready.

Required fix:

- when the deployment object exposes this data, validate entrypoint and working
  directory;
- if Prefect's API cannot expose them reliably, return explicit
  `not_inspectable` metadata in the bounded result instead of silently claiming
  the deployment contract is fully verified.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_worker_binding.py tests/test_prefect_grace_cli_prefect_worker_binding.py tests/test_prefect_grace_cli_contracts.py`: `58 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `prefect_worker_binding.py`, `runtime_adapter.py`, CLI
  handler, and parser: passed.
- Strict packet validation for this packet: `ok=true`.
- `validate-evidence-manifest`: `ok=true`, but `evidence_count=0` and
  `validated_artifacts=[]`, which is a blocker above.
- Worker-container CLI dry-run: live Prefect reached; pool/queues ready; managed
  deployment missing; `deployment_mutation=dry_run_would_register`; zero flow
  runs and zero live agents.
- Worker-container plain `--apply-deployment` with approval env and
  acknowledgement: `deployment_mutation=dry_run_would_apply`; zero flow runs and
  zero live agents.
- `./scripts/grace_worker_smoke.sh`: passed with Prefect `3.6.25`; no persistent
  `grace_worker` container remained running.

## Required Rework

1. Implement and expose bounded before/after deployment apply metadata.
2. Add invalid-entrypoint fail-closed validation and regression coverage.
3. Validate existing deployment entrypoint/working directory, or report them as
   explicitly not inspectable.
4. Rewrite and revalidate the evidence manifest so the artifacts are actually
   checked.
5. Re-run targeted tests, compile, lint, strict packet validation, evidence
   manifest validation, safe worker dry-run, safe worker apply-plan, and worker
   smoke.
