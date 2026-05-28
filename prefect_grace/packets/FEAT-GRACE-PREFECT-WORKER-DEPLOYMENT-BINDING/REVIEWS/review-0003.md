# Review 0003 — FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING

status: rework_required
reviewer: codex
source_hash: sha256:415028c5458ea4395a3d5dfb7cff4528cbc60891763b5637b01268378e096358
reviewed_commit: 97d5ed5
attempt: attempt-0003
reviewed_at: 2026-05-28

## Verdict

Rework required.

The CLI now has an explicit `--apply` flag, so the specific review-0002 issue
that made non-dry-run mode unreachable is partially fixed. However, the approved
first deployment registration path is still not operational end-to-end, and one
dry-run planning contract from review-0002 was regressed.

I did not run real deployment apply against the live Prefect server.

## Blockers

### 1. First deployment apply returns `applied` while still blocked by stale missing-deployment evidence

`prefect_grace/platform/prefect_worker_binding.py:466-492` checks the deployment
before apply, appends `DEPLOYMENT_NOT_FOUND`, then applies the deployment. After a
successful apply it only sets:

```text
deployment_mutation = "applied"
```

It does not re-read the deployment, clear the stale `DEPLOYMENT_NOT_FOUND`, or
update `deployment_exists` / `deployment_parameters_valid`. Then
`prefect_grace/platform/prefect_worker_binding.py:503-510` computes `ok` from the
pre-apply values:

```text
and (deployment_exists and parameters_valid)
```

Injected proof, with no live Prefect mutation:

```text
{'ok': False,
 'deployment_exists': False,
 'deployment_parameters_valid': False,
 'deployment_mutation': 'applied',
 'errors': [{'type': 'DEPLOYMENT_NOT_FOUND', ...}],
 'warnings': ['Deployment applied: dep-123'],
 'prefect_runs_created': 0,
 'live_agents_started': 0}
```

This means the first real deployment registration can report both
`deployment_mutation=applied` and `ok=false` with `DEPLOYMENT_NOT_FOUND`. That is
not an operator-safe apply result.

Required fix:

- after successful apply, re-read the managed deployment and recompute routing
  validity from after-state;
- remove or replace stale pre-apply missing-deployment errors when apply succeeds;
- return bounded before/after deployment metadata;
- add an injected platform regression where deployment is missing, apply helper
  succeeds, and the final result is internally consistent.

### 2. Plain `--apply-deployment` no longer produces a dry-run plan

Review-0002 required:

```text
keep plain --apply-deployment as dry-run planning unless that explicit mutation
flag is present
```

The rework instead blocks before preflight:

`prefect_grace/cli_commands/prefect_worker_binding.py:39-42`

```text
if args.apply_deployment and not args.apply:
    ERROR: --apply-deployment requires --apply flag
```

Safe worker-container proof with approval env and acknowledgement exits with code
2 before producing the `dry_run_would_apply` plan:

```bash
docker compose -f docker-compose.yml -f docker-compose.grace-worker.yml \
  --profile grace-worker run --rm --no-deps \
  -e GRACE_PREFECT_BINDING_APPROVED=deployment \
  grace_worker \
  python3 -m prefect_grace.cli prefect-worker-binding \
    --project prefect_grace/project.yaml \
    --apply-deployment \
    --i-understand-prefect-mutation \
    --json
```

Observed:

```text
ERROR: --apply-deployment requires --apply flag
```

Required behavior: without `--apply`, the command should stay read-only and
return a bounded dry-run apply plan. With `--apply`, it may enter real mutation
mode only when every approval gate is present.

### 3. New CLI apply test mocks below the behavior it claims to prove

`tests/test_prefect_grace_cli_prefect_worker_binding.py:270` patches
`run_prefect_worker_binding_preflight` and returns a fabricated
`deployment_mutation="applied"` result. That proves the CLI passes args to a mock;
it does not prove that the injected apply helper is called, that deployment
after-state is validated, or that zero flow runs are created by the real platform
path.

Required fix:

- keep a CLI arg propagation test;
- add platform-level injected tests around
  `run_prefect_worker_binding_preflight(...)` and `_apply_managed_packet_deployment`;
- cover missing deployment -> apply success -> re-read ready, apply failure, and
  dry-run would-apply.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_worker_binding.py tests/test_prefect_grace_cli_prefect_worker_binding.py tests/test_prefect_grace_cli_contracts.py`: `53 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `prefect_worker_binding.py`, `runtime_adapter.py`, CLI
  handler, and parser: passed.
- Strict packet validation: `ok=true`.
- Host CLI dry-run: fail-closed with `PREFECT_CLIENT_REQUIRED`, zero flow runs,
  zero live agents.
- Worker-container CLI dry-run: live Prefect API reached; `astro-process`,
  `grace-live`, and `grace-monitoring` ready; deployment missing;
  `deployment_mutation=dry_run_would_register`; zero flow runs and zero live
  agents.
- Worker-container plain `--apply-deployment` with approval env and acknowledgement
  exits code 2 before preflight.
- Injected apply proof demonstrates stale after-apply result; no live Prefect
  mutation was performed.

## Required Rework

1. Preserve dry-run planning for plain `--apply-deployment`.
2. Make approved apply re-read deployment after-state and return a consistent
   result.
3. Add injected platform tests that exercise the real preflight apply branch.
4. Re-run targeted tests, compile, lint, strict validation, safe worker dry-run,
   and safe dry-run apply-plan proof.
