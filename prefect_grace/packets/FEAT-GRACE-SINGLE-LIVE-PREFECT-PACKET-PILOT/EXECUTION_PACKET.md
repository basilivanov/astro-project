# Execution Packet: FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT-W01-MANAGED-PREFECT-SCRATCH-RUN

## Objective

Run one operator-approved synthetic scratch packet through the real Prefect
managed packet runner deployment and GRACE worker, with no product-code scope.

This is the first real Prefect-managed packet execution after deployment
binding. It must prove that Prefect creates exactly one managed packet flow run,
the worker consumes it, the managed runner uses an isolated worktree, and scope
evidence remains confined to scratch-only paths. It must not run a real Astro
product packet yet.

## Slice

- slice_id: `SLICE-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT`
- slice_slug: `grace-single-live-prefect-packet-pilot`
- feature_id: `FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT`
- packet_id: `FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT-W01-MANAGED-PREFECT-SCRATCH-RUN`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY-W01-APPROVED-DEPLOYMENT-APPLY, FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE, FEAT-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET-W01-LIVE-OPT-IN-SINGLE-SCRATCH`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/prefect_worker_binding.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/live_opt_in_single_scratch_packet.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_execution.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_submission.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`

## Impacted Modules

- `M-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-MANAGED-PACKET-RUNNER`
- `M-GRACE-LIVE-OPT-IN`
- `M-GRACE-SCOPE-GUARD`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/single_live_prefect_packet_pilot.py`
- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_execution.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_submission.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_single_live_prefect_packet_pilot.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_single_live_prefect_packet_pilot.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-SINGLE-LIVE-PREFECT-PACKET-PILOT/**`
- `/tmp/grace-single-live-prefect-packet-pilot/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/** outside current packet`
- `/opt/astro-project/.worktrees/**`

## Must Preserve

- Exactly one synthetic scratch packet is selected.
- Dry-run default creates zero Prefect flow runs and starts zero agents.
- Real execution requires explicit CLI opt-in and an environment token.
- Scratch packet allowed scope is only `scratch/grace-single-live-prefect/**`
  inside the isolated worktree.
- Backend, frontend, platform code, source packets, registry state, Docker
  compose files, `.env`, and product services are frozen.
- Git commit, push, and merge are disabled for this packet.
- CLI JSON envelope keeps `result == data`.

## Required Design Decisions

### 1. Prefect Is The Execution Path

The real path must submit the managed packet runner deployment through Prefect.
Local direct runner calls are allowed only as injected unit-test seams.

### 2. Single Scratch Packet

The command must synthesize or consume exactly one scratch packet under a
temporary packet root. It must fail closed if more than one packet is runnable
or if the selected packet comes from the real source corpus.

### 3. Bounded Polling

If the command waits for the flow run, polling must have a timeout, bounded
events, and a final status summary. It must not stream full logs.

## Implementation Requirements

1. Add a pilot module and CLI command, or extend the existing single-live pilot
   with a `prefect-managed-scratch` mode.
2. Support injected submitter/status-reader tests.
3. Cover dry-run, missing opt-in, missing deployment, one flow run submitted,
   worker timeout, domain accepted, scope blocked, and no product writes.
4. Preserve the worktree for inspection by default.
5. Do not run a real live agent in automated tests; use injected execution for
   tests and one manually approved live proof only when requested.

## Acceptance Criteria

- Dry-run shows exactly one scratch packet candidate and zero side effects.
- Missing opt-in blocks before Prefect submission.
- Approved injected live path creates exactly one Prefect run and one agent
  launch.
- Scope evidence shows no writes outside scratch/temp roots.
- No Git mutations or product service changes occur.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_single_live_prefect_packet_pilot.py \
  tests/test_prefect_grace_cli_single_live_prefect_packet_pilot.py \
  tests/test_prefect_grace_single_live_packet_pilot.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile, targeted lint, strict packet validation, worker-container dry-run
binding proof, and injected live proof. Do not run real live agent without
Architect approval.

## Expected Evidence

- Strict validation output.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Dry-run CLI proof.
- Missing opt-in blocked proof.
- Injected one-run proof with `prefect_runs_created=1`.
- Scope proof with only scratch/temp writes.
- Post-test observability verdict.

## Escalation Triggers

- More than one packet can run.
- A real source packet is selected.
- Product code or source packet files are modified.
- Git mutation is reachable.
- Output includes unbounded logs or secrets.
