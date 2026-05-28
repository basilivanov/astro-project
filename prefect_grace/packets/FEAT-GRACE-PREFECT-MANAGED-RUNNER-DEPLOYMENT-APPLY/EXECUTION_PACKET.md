# Execution Packet: FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY-W01-APPROVED-DEPLOYMENT-APPLY

## Objective

Make the managed packet runner Prefect deployment apply path real, gated, and
auditable.

This packet closes the remaining gap after `prefect-worker-binding`: the
operator can prove the live Prefect server, pool, queues, and worker runtime are
reachable, then explicitly create or refresh only the managed packet runner
deployment. It must not create packet flow runs, start workers, launch agents,
mutate registry state, commit, push, merge, or touch product services.

## Slice

- slice_id: `SLICE-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY`
- slice_slug: `grace-prefect-managed-runner-deployment-apply`
- feature_id: `FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY`
- packet_id: `FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY-W01-APPROVED-DEPLOYMENT-APPLY`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING-W01-PREFECT-WORKER-DEPLOYMENT-BINDING`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/prefect_worker_binding.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/runtime_config.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_worker_binding.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/docker-compose.grace-worker.yml`
- `/opt/astro-project/scripts/grace_worker_smoke.sh`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING/REVIEWS/review-0002.md`

## Impacted Modules

- `M-GRACE-PREFECT-WORKER-BINDING`
- `M-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT`
- `M-GRACE-PREFECT-SUBMITTER`
- `M-GRACE-RUNTIME-ADAPTER`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/prefect_worker_binding.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/runtime_config.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_worker_binding.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_prefect_worker_binding.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_prefect_worker_binding.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`
- `/opt/astro-project/.worktrees/**`

## Must Preserve

- Dry-run is the default and creates zero Prefect flow runs.
- Real deployment apply requires `--apply-deployment`, an explicit real-apply
  flag, `--i-understand-prefect-mutation`, and
  `GRACE_PREFECT_BINDING_APPROVED=deployment`.
- Deployment apply may create or update only
  `prefect-grace-managed-packet-runner/live-managed-packet-runner`.
- The deployment entrypoint must be
  `prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow`.
- No live agents, persistent workers, packet flow runs, registry writes, source
  packet writes, Git mutations, backend, frontend, Docker service changes,
  Playwright, provider APIs, or credentials are used.
- CLI JSON envelope keeps `result == data`.

## Required Design Decisions

### 1. Explicit Apply Mode

Add a real mutation flag such as `--apply` or `--no-dry-run`. Plain
`--apply-deployment` must remain a dry-run plan unless the mutation flag and
approval gates are present.

### 2. Apply Helper Contract

The apply helper must return bounded before/after deployment metadata:

- deployment name;
- deployment id;
- work pool;
- work queue;
- entrypoint;
- working directory;
- created vs updated;
- `prefect_runs_created=0`;
- `live_agents_started=0`.

### 3. No Silent Success

If deployment apply cannot run because Prefect is unavailable, the deployment
API shape changed, the flow entrypoint is invalid, or approvals are missing,
the command must return `ok=false` and a structured blocker. It must not report
`deployment_mutation=applied`.

## Implementation Requirements

1. Add the real apply-mode CLI switch and tests.
2. Make `apply_managed_packet_deployment_helper(...)` validate the entrypoint
   before applying.
3. Add injected tests proving approved apply is reachable and creates zero flow
   runs.
4. Add regression tests for missing approval, dry-run would-apply, invalid
   entrypoint, and apply failure.
5. Keep real live Prefect apply out of automated verification unless the
   Architect explicitly approves it.

## Acceptance Criteria

- Dry-run binding reports deployment plan without mutation.
- Approved injected apply returns `deployment_mutation=applied` only when the
  helper actually applies.
- Missing gates block before any Prefect mutation.
- The live worker-container dry-run reaches Prefect and still creates zero
  flow runs.
- Manual `scripts/grace_worker_smoke.sh` remains green and leaves no persistent
  worker.

## Verification

Run:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_worker_binding.py \
  tests/test_prefect_grace_cli_prefect_worker_binding.py \
  tests/test_prefect_grace_cli_contracts.py
python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py prefect_grace/cli_commands
python3 scripts/grace_lint.py prefect_grace/platform/prefect_worker_binding.py
python3 scripts/grace_lint.py prefect_grace/platform/runtime_adapter.py
python3 scripts/grace_lint.py prefect_grace/cli_commands/prefect_worker_binding.py
python3 scripts/grace_lint.py prefect_grace/cli_commands/parser.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY/EXECUTION_PACKET.md \
  --strict --json
```

Also run worker-container dry-run proof and manual worker smoke. Do not run
real deployment apply unless the Architect explicitly approves the mutation.

## Expected Evidence

- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Strict packet validation output.
- Worker-container dry-run binding output.
- Manual worker smoke summary.
- Proof of zero Prefect flow runs, zero live agents, zero registry writes, zero
  source packet writes, and no persistent worker left running.

## Escalation Triggers

- Deployment apply creates a packet flow run.
- Apply is reachable without all approval gates.
- The deployment points to the wrong entrypoint, pool, queue, or working dir.
- Output includes secrets or unbounded logs.
