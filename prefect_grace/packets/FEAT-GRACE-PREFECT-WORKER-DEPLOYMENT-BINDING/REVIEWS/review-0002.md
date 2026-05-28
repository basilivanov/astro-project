# Review 0002 — FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING

status: rework_required
reviewer: codex
source_hash: sha256:415028c5458ea4395a3d5dfb7cff4528cbc60891763b5637b01268378e096358
attempt: attempt-0002
reviewed_at: 2026-05-28

## Verdict

Rework required.

The rework fixes the incorrect managed packet runner entrypoint and removes the
false-positive worker smoke. The worker-container read-only preflight still
correctly reaches the live Prefect server and validates the pool/queues.

However, the approved deployment apply path is still not operational through
the CLI: `--apply-deployment` cannot enter non-dry-run mode because the parser
has no `--no-dry-run` or equivalent apply flag. With all approval gates present,
the command only reports `deployment_mutation=dry_run_would_apply`.

## Blockers

### 1. Approved deployment apply is unreachable from the CLI

`prefect_grace/cli_commands/parser.py:683-692` defines:

```text
--dry-run action=store_true default=True
--apply-deployment
--i-understand-prefect-mutation
```

There is no flag that sets `args.dry_run` to `False`. Therefore
`prefect_grace/platform/prefect_worker_binding.py:479-487` always takes the
dry-run branch for CLI calls, even when `--apply-deployment`,
`--i-understand-prefect-mutation`, and
`GRACE_PREFECT_BINDING_APPROVED=deployment` are present.

Verified command:

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

Observed result:

```json
{
  "dry_run": true,
  "deployment_mutation": "dry_run_would_apply",
  "prefect_runs_created": 0,
  "live_agents_started": 0
}
```

Required fix:

- add an explicit mutation flag that makes real deployment apply reachable only
  with all approval gates present, for example `--apply` or `--no-dry-run`;
- keep plain `--apply-deployment` as dry-run planning unless that explicit
  mutation flag is present;
- add CLI contract tests proving approved apply can call the injected apply
  helper, while missing approval and dry-run still create zero mutations;
- do not run real apply against the live server until the Architect explicitly
  approves that mutation.

## Non-Blocking Notes

- The entrypoint is now corrected to
  `prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow`.
- The current `--run-worker-smoke` fail-closed behavior is acceptable as a
  temporary contract if the command clearly points operators to
  `scripts/grace_worker_smoke.sh`.
- `create_prefect_sync_client()` still enters a client context without a close
  path. This is not blocking for short-lived CLI processes, but should be
  cleaned up before long-lived orchestration loops.
- Top-level CLI envelope errors are still flattened to strings while
  `result.errors` preserves structured dicts.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_worker_binding.py tests/test_prefect_grace_cli_prefect_worker_binding.py tests/test_prefect_grace_cli_contracts.py`: `51 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `prefect_worker_binding.py`, CLI handler,
  `runtime_adapter.py`, and parser: passed.
- Strict packet validation: `ok=true`.
- Host CLI dry-run: `PREFECT_CLIENT_REQUIRED`, fail-closed, zero flow runs.
- Worker-container CLI dry-run: live Prefect API reached; `astro-process`,
  `grace-live`, and `grace-monitoring` ready; managed deployment missing;
  zero flow runs and zero live agents.
- Worker-container `--run-worker-smoke`: fail-closed with
  `WORKER_SMOKE_FAILED` and pointer to `scripts/grace_worker_smoke.sh`.
- Manual `./scripts/grace_worker_smoke.sh`: passed; no persistent `grace_worker`
  container left running.

## Required Rework

1. Add a real, explicit apply-mode switch for deployment mutation.
2. Cover approved real apply with injected tests without touching live Prefect.
3. Re-run targeted tests, compile, lint, strict validation, worker-container
   dry-run proof, approved-apply dry-run proof, and manual worker smoke.

## Acceptance Criteria For Next Review

- CLI has a clear dry-run/apply separation for deployment mutation.
- Approved apply path is reachable in tests and cannot be reached without all
  gates.
- Dry-run and smoke-fail-closed paths still create zero Prefect flow runs and
  start zero live agents.
