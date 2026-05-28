# Review 0001 — FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING

status: rework_required
reviewer: codex
source_hash: sha256:415028c5458ea4395a3d5dfb7cff4528cbc60891763b5637b01268378e096358
attempt: attempt-0001
reviewed_at: 2026-05-28

## Verdict

Rework required.

The rework improved the read-only path when the command is executed inside the
GRACE worker image: it reaches the live Prefect server, validates
`astro-process`, sees `grace-live` / `grace-monitoring`, and reports the missing
managed packet runner deployment without creating flow runs. That is useful.

The packet is still not acceptable because approved deployment apply is wired
to a nonexistent flow entrypoint, and the worker smoke flag does not run the
bounded worker runtime smoke required by the packet.

## Blockers

### 1. Deployment apply uses a nonexistent managed runner entrypoint

`prefect_grace/platform/runtime_adapter.py:557-564` builds the deployment from:

```text
prefect_grace/flows/managed_packet_runner.py:managed_packet_runner
```

That file/function does not exist. The actual accepted managed packet runner
flow is:

```text
prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow
```

This means the explicit deployment apply path is not a valid implementation of
the packet contract. It will either fail at apply time or register the wrong
artifact if a similarly named module appears later.

Required fix:

- point deployment apply at the real `managed_packet_runner_flow.py:managed_packet_runner_flow`
  entrypoint;
- add a regression test that verifies the exact entrypoint string;
- run an approved apply proof only after explicit operator approval, or keep it
  blocked but do not claim apply readiness.

### 2. `--run-worker-smoke` does not run the worker runtime smoke

`prefect_grace/platform/prefect_worker_binding.py:227-249` now checks that the
work pool and queue can be read through the Prefect client. That is a useful
read-only API check, but it is not the worker runtime smoke described in the
execution packet.

The packet requires a bounded summary for the worker container path:

- image built or present;
- Prefect version inside worker;
- API health;
- work pool found;
- required queues found;
- CLI import ok;
- Docker socket ok;
- persistent worker containers left running count.

The existing `scripts/grace_worker_smoke.sh` already proves most of this. The
binding command should either invoke it through a bounded adapter and summarize
the result, or reject `--run-worker-smoke` as unsupported. Returning
`worker_runtime_smoke={"smoke_ran": true, "ok": true}` after only API reads is
too weak for this gate.

Required fix:

- implement a bounded adapter around `scripts/grace_worker_smoke.sh` or an
  equivalent one-shot container smoke;
- include persistent worker count and no-flow-run/no-live-agent counters;
- add tests that prove the summary is bounded and that no persistent worker was
  left running.

### 3. Host CLI proof still cannot validate the live stack

`python3 -m prefect_grace.cli prefect-worker-binding --project prefect_grace/project.yaml --dry-run --json`
still returns `PREFECT_CLIENT_REQUIRED` on the host because Prefect is not
installed in the host Python environment.

The worker-container invocation does work:

```bash
docker compose -f docker-compose.yml -f docker-compose.grace-worker.yml \
  --profile grace-worker run --rm --no-deps grace_worker \
  python3 -m prefect_grace.cli prefect-worker-binding \
  --project prefect_grace/project.yaml \
  --dry-run \
  --json
```

That may be an acceptable operational decision, but then the packet and CLI help
need to make the execution environment explicit. The current packet text says
the local Prefect stack is available and gives the host command as the real
read-only proof.

Required fix:

- either make the host command perform the read-only proof without requiring a
  host Prefect install, or document/encode the worker-container command as the
  canonical operator path;
- keep fail-closed behavior for environments where neither path is available.

## Non-Blocking Notes

- `create_prefect_sync_client()` enters a Prefect client context with
  `__enter__()` and never closes it. For short CLI processes this is not
  immediately dangerous, but it is still a poor lifecycle contract. Prefer a
  context manager wrapper or close hook.
- The CLI JSON envelope flattens top-level `errors` to strings while
  `result.errors` keeps structured dicts. Most GRACE JSON commands preserve
  structured errors.
- `submit-packets` still defaults to `--runner e2e`, while this binding checks
  the managed packet runner deployment. This is not necessarily a blocker for
  this packet, but the next live path must explicitly select `--runner managed`
  or change the default.

## Verification Reviewed

- `pytest -q tests/test_prefect_grace_prefect_worker_binding.py tests/test_prefect_grace_cli_prefect_worker_binding.py tests/test_prefect_grace_cli_contracts.py`: `50 passed`.
- `python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands`: passed.
- Targeted GRACE lint for `prefect_worker_binding.py`, CLI handler, `runtime_adapter.py`, and parser: passed.
- `python3 -m prefect_grace.cli validate-packet prefect_grace/packets/FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING/EXECUTION_PACKET.md --strict --json`: `ok=true`.
- Host CLI dry-run: `ok=false`, `PREFECT_CLIENT_REQUIRED`, zero flow runs, zero live agents.
- Worker-container CLI dry-run: reaches live Prefect API, `server_healthy=true`,
  `work_pool_status=READY`, both queues `READY`, deployment missing,
  `deployment_mutation=dry_run_would_register`, zero flow runs, zero live
  agents.
- Worker-container CLI with `--run-worker-smoke`: reports `smoke_ran=true`,
  `ok=true`, but only because the client can read pool/queue; it does not run
  the one-shot worker runtime smoke.

## Required Rework

1. Fix the managed packet runner deployment entrypoint.
2. Implement a true bounded worker runtime smoke or fail closed when
   `--run-worker-smoke` is requested.
3. Clarify or implement the canonical real operator path: host CLI vs worker
   container CLI.
4. Add regression tests for deployment entrypoint, smoke summary, and client
   lifecycle/close behavior.
5. Re-run targeted tests, strict validation, compile, targeted lint, real
   worker-container CLI proof, and optional full `./scripts/grace_worker_smoke.sh`.

## Acceptance Criteria For Next Review

- Approved deployment apply cannot target a nonexistent module/function.
- `--run-worker-smoke` proves the worker runtime path, not only Prefect API
  readability.
- Operator documentation and CLI proof use the same environment where Prefect is
  actually installed.
- Dry-run still creates zero Prefect flow runs, starts zero live agents, starts
  no persistent worker, and mutates no registry/source packet state.
