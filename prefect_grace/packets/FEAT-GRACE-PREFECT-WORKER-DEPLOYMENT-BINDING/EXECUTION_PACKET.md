# Execution Packet: FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING-W01-PREFECT-WORKER-DEPLOYMENT-BINDING

## Objective

Add a guarded Prefect binding layer that proves the portable GRACE
orchestrator is connected to the real Prefect stack before any live packet is
submitted.

This packet must bridge the gap between:

```text
GRACE source/runtime registry and submission code
  -> real Prefect API
  -> astro-process work pool
  -> grace-live / grace-monitoring queues
  -> GRACE worker container runtime
  -> managed packet runner deployment
```

It must not execute packets, start live agents, create packet flow runs, merge,
push product code, mutate source packet artifacts, or run product services.

The outcome should be an operator-safe command that says whether Prefect is
actually ready for one controlled live packet, and optionally registers or
refreshes the managed packet runner deployment under explicit approval.

## Slice

- slice_id: `SLICE-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING`
- slice_slug: `grace-prefect-worker-deployment-binding`
- feature_id: `FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING`
- packet_id: `FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING-W01-PREFECT-WORKER-DEPLOYMENT-BINDING`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP-W01-PREFECT-NATIVE-SUBMISSION, FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE-W01-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE, FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/runtime_config.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/docker-compose.grace-worker.yml`
- `/opt/astro-project/infra/grace-worker/Dockerfile`
- `/opt/astro-project/infra/grace-worker/entrypoint.sh`
- `/opt/astro-project/scripts/grace_worker_smoke.sh`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-LIVE-OPT-IN-SINGLE-SCRATCH-PACKET/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-GIT-MUTATION-GATE/EXECUTION_PACKET.md`

## Impacted Modules

- `M-GRACE-PREFECT-WORKER-BINDING`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-PREFECT-SUBMITTER`
- `M-GRACE-MANAGED-PACKET-RUNNER-FLOW`
- `M-GRACE-RUNTIME-CONFIG`
- `M-GRACE-WORKER-RUNTIME`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/prefect_worker_binding.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/runtime_config.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/docker-compose.grace-worker.yml`
- `/opt/astro-project/infra/grace-worker/Dockerfile`
- `/opt/astro-project/infra/grace-worker/entrypoint.sh`
- `/opt/astro-project/infra/grace-worker/requirements.txt`
- `/opt/astro-project/scripts/grace_worker_smoke.sh`
- `/opt/astro-project/tests/test_prefect_grace_prefect_worker_binding.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_prefect_worker_binding.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/nightly_dry_run_controller.py`
- `/opt/astro-project/prefect_grace/platform/nightly_batch_execution_guard.py`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/SUMMARY.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`
- `/opt/astro-project/.worktrees/**`

## Must Preserve

- Dry-run is the default and creates zero Prefect flow runs.
- Deployment registration or refresh requires explicit apply approval.
- Worker startup is not automatic in the binding command.
- No live agents, packet execution, Git commit, Git push, merge, registry apply,
  backend, frontend, Playwright, provider APIs, or credentials are used.
- Source packet artifacts remain read-only.
- Runtime registry state remains read-only.
- `submit-packets --dry-run` and existing smoke commands keep their safe
  defaults.
- Existing CLI JSON envelopes keep `result` equal to `data`.
- Prefect imports remain lazy outside worker/test code so host environments
  without Prefect still fail closed.
- Evidence remains bounded and excludes raw logs, screenshots, full registry
  dumps, secrets, and provider tokens.

## Recommended Role Assignment

- coder: `Codex high`; this is operational wiring with fail-closed behavior.
- verifier: `Codex high`; must verify both injected client behavior and real
  read-only Prefect preflight.
- reviewer: `Codex xhigh` or `Opus`; focus on accidental flow-run creation,
  deployment mutation gates, worker startup, and deployment/work-queue mismatch.
- rework policy: fresh session for any blocker involving live run creation,
  persistent worker startup, deployment mutation without approval, or queue
  routing mismatch; light resume only for CLI wording, tests, or evidence
  formatting.

## Required Design Decisions

### 1. Add A Prefect Binding Preflight Module

Add a platform module:

```text
prefect_grace/platform/prefect_worker_binding.py
```

Preferred public API:

```python
@dataclass(frozen=True)
class PrefectWorkerBindingResult:
    ok: bool
    project_key: str
    mode: str
    dry_run: bool
    prefect_api_url: str
    prefect_version: str | None
    server_healthy: bool
    work_pool_name: str
    work_pool_status: str | None
    work_pool_type: str | None
    required_queues: list[str]
    queue_statuses: dict[str, dict[str, Any]]
    deployment_name: str
    deployment_exists: bool
    deployment_work_pool_name: str | None
    deployment_work_queue_name: str | None
    deployment_parameters_valid: bool
    worker_runtime_smoke: dict[str, Any]
    deployment_mutation: str
    prefect_runs_created: int
    live_agents_started: int
    warnings: list[str]
    errors: list[dict[str, Any]]
```

Preferred function:

```python
def run_prefect_worker_binding_preflight(
    *,
    project_config: Path,
    dry_run: bool = True,
    apply_deployment: bool = False,
    acknowledge_prefect_mutation: bool = False,
    approval_token: str | None = None,
    run_worker_smoke: bool = False,
    prefect_client: Any | None = None,
) -> PrefectWorkerBindingResult:
    ...
```

The implementation may use a different internal model, but the JSON output must
expose equivalent health, queue, deployment, mutation, and side-effect counters.

### 2. Prefect Is Lazy And Fail-Closed

The host checkout and backend container may not have Prefect installed. The new
module must not import Prefect at module import time.

Rules:

- If Prefect is unavailable and no injected client is supplied, return
  `ok=false` with `PREFECT_UNAVAILABLE`.
- If the API URL is missing or unreachable, return `ok=false` with
  `PREFECT_API_UNREACHABLE`.
- If the work pool is missing, paused, unhealthy, wrong type, or not
  `process`, return `ok=false`.
- If required queues are missing or unhealthy, return `ok=false`.
- If the managed packet runner deployment is missing, return `ok=false` in
  dry-run mode and report what would be registered.

Do not silently create pools, queues, deployments, workers, blocks, or runs.

### 3. Validate The Real Routing Contract

The preflight must verify the same names the submitter uses:

- work pool: `astro-process` from project/runtime config;
- live queue: `grace-live`;
- monitoring queue: `grace-monitoring`;
- deployment: `prefect-grace-managed-packet-runner/live-managed-packet-runner`.

It must fail closed if:

- `prefect_submitter.MANAGED_PACKET_DEPLOYMENT_NAME` does not match the
  deployment checked by the binding command;
- `submit_ready_packets_to_prefect(...)` would target a different deployment;
- the deployment points at the wrong work pool or queue;
- the deployment working directory is not `/opt/astro-project` or an explicitly
  configured equivalent inside the worker container;
- required environment such as `PYTHONPATH=/opt/astro-project` is absent from
  the deployment job variables when those variables are inspectable.

### 4. Deployment Apply Is Explicit And Does Not Run Packets

Deployment registration or refresh is allowed only when all gates are present:

```bash
GRACE_PREFECT_BINDING_APPROVED=deployment \
python3 -m prefect_grace.cli prefect-worker-binding \
  --project prefect_grace/project.yaml \
  --apply-deployment \
  --i-understand-prefect-mutation \
  --json
```

Apply mode may create or update the managed packet runner deployment only. It
must not:

- create a flow run;
- start a worker;
- start an agent;
- mutate the runtime registry;
- commit, push, merge, or touch packet evidence.

The result must include bounded before/after deployment metadata and
`prefect_runs_created: 0`.

### 5. Worker Runtime Smoke Is Optional And Bounded

The binding command may optionally run the existing worker runtime smoke:

```bash
python3 -m prefect_grace.cli prefect-worker-binding \
  --project prefect_grace/project.yaml \
  --run-worker-smoke \
  --dry-run \
  --json
```

This smoke may build or run a one-shot worker container only. It must not leave
`grace_worker` running persistently and must not consume packet jobs.

The smoke summary must be bounded:

- image built or present;
- Prefect version inside worker;
- API health;
- work pool found;
- required queues found;
- CLI import ok;
- Docker socket ok;
- persistent worker containers left running count.

Do not include full Docker build logs or full container logs in JSON/evidence.

### 6. CLI Contract

Add a command:

```bash
python3 -m prefect_grace.cli prefect-worker-binding \
  --project prefect_grace/project.yaml \
  --dry-run \
  --json
```

CLI requirements:

- `--dry-run` is the default;
- `--apply-deployment` requires `--i-understand-prefect-mutation` and
  `GRACE_PREFECT_BINDING_APPROVED=deployment`;
- `--run-worker-smoke` is explicit and remains read-only with respect to packet
  execution;
- JSON envelope keeps `result == data`;
- non-JSON output is concise and operator-oriented;
- exit code `0` for ready binding, `1` for blocked preflight, `2` for command
  or unexpected internal errors.

### 7. Result Shape

Return JSON-safe bounded output similar to:

```json
{
  "mode": "prefect_worker_binding",
  "project_key": "astro-project",
  "dry_run": true,
  "ready_for_single_live_packet": false,
  "prefect": {
    "api_url": "http://prefect-server:4200/api",
    "server_healthy": true,
    "version": "3.6.25"
  },
  "work_pool": {
    "name": "astro-process",
    "type": "process",
    "status": "READY"
  },
  "queues": {
    "grace-live": {"exists": true, "status": "READY"},
    "grace-monitoring": {"exists": true, "status": "READY"}
  },
  "deployment": {
    "name": "prefect-grace-managed-packet-runner/live-managed-packet-runner",
    "exists": false,
    "work_pool_name": null,
    "work_queue_name": null,
    "mutation": "dry_run_would_register"
  },
  "worker_runtime": {
    "smoke_ran": false,
    "ok": null
  },
  "side_effects": {
    "prefect_runs_created": 0,
    "live_agents_started": 0,
    "registry_writes": 0,
    "source_packet_writes": 0,
    "persistent_workers_started": 0
  },
  "errors": []
}
```

### 8. Tests Must Use Injected Clients First

Unit tests must not require a live Prefect server.

Cover:

- Prefect unavailable fail-closed;
- API unreachable fail-closed;
- missing work pool;
- wrong work pool type;
- missing `grace-live` queue;
- missing `grace-monitoring` queue;
- missing deployment dry-run;
- deployment exists but wrong queue;
- deployment exists and matches routing;
- apply-deployment without approval blocked with zero mutations;
- apply-deployment with injected client updates deployment and creates zero
  flow runs;
- worker smoke parser keeps bounded output and reports no persistent worker.

### 9. Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_worker_binding.py \
  tests/test_prefect_grace_cli_prefect_worker_binding.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile and targeted lint:

```bash
python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py
python3 scripts/grace_lint.py \
  prefect_grace/platform/prefect_worker_binding.py \
  prefect_grace/tasks/prefect_submitter.py \
  prefect_grace/flows/managed_packet_runner_flow.py \
  prefect_grace/cli.py
```

Run packet validation:

```bash
python3 -m prefect_grace.cli validate-packet \
  --packet prefect_grace/packets/FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING/EXECUTION_PACKET.md \
  --strict \
  --json
```

Run real read-only proof when the local Prefect stack is available:

```bash
python3 -m prefect_grace.cli prefect-worker-binding \
  --project prefect_grace/project.yaml \
  --dry-run \
  --json
```

Optional worker smoke proof:

```bash
./scripts/grace_worker_smoke.sh
```

Do not run deployment apply unless the Architect explicitly approves it.

## Expected Evidence

- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Strict packet validation output.
- CLI dry-run JSON summary.
- Missing deployment or ready deployment routing proof.
- Optional worker smoke summary.
- Confirmation that `prefect_runs_created=0`, `live_agents_started=0`,
  `registry_writes=0`, `source_packet_writes=0`, `persistent_workers_started=0`.
- Post-test observability verdict: `clean`, `degraded-but-expected`,
  `unexpected-degradation`, or `no-evidence-blocker`.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_worker_binding.py \
  tests/test_prefect_grace_cli_prefect_worker_binding.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile and targeted lint:

```bash
python3 -m compileall -q prefect_grace/platform prefect_grace/tasks prefect_grace/flows prefect_grace/cli.py
python3 scripts/grace_lint.py \
  prefect_grace/platform/prefect_worker_binding.py \
  prefect_grace/tasks/prefect_submitter.py \
  prefect_grace/flows/managed_packet_runner_flow.py \
  prefect_grace/cli.py
```

Run packet validation:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PREFECT-WORKER-DEPLOYMENT-BINDING/EXECUTION_PACKET.md \
  --strict \
  --json
```

Run real read-only proof when the local Prefect stack is available:

```bash
python3 -m prefect_grace.cli prefect-worker-binding \
  --project prefect_grace/project.yaml \
  --dry-run \
  --json
```

Optional worker smoke proof:

```bash
./scripts/grace_worker_smoke.sh
```

Do not run deployment apply unless the Architect explicitly approves it.

## Acceptance Criteria

- A single CLI command can tell whether the real Prefect stack is ready for the
  next single live packet.
- Dry-run mode performs no Prefect mutations and creates no flow runs.
- Apply mode cannot run unless explicit deployment mutation approval is present.
- Managed packet runner deployment routing matches the submitter and project
  config.
- Worker runtime smoke is bounded and does not leave a persistent worker.
- Existing submission, nightly, live scratch, and Git gate defaults remain
  fail-closed.
- Evidence is committed under this packet and remains small.

## Escalation Triggers

- Any Prefect flow run is created by dry-run or deployment apply.
- Any live agent starts.
- A persistent worker is started without explicit operator action.
- Deployment routing points to the wrong pool, queue, command, or working dir.
- `submit-packets` and binding preflight disagree about deployment name.
- Prefect is imported at module import time and breaks host environments
  without Prefect.
- Output includes secrets, raw logs, screenshots, or unbounded registry data.

## Reviewer Gate

Reviewer must verify that this packet only binds and validates Prefect
infrastructure. It must not become the first real packet execution path.
