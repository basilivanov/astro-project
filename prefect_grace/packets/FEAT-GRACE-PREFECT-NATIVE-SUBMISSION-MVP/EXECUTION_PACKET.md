# Execution Packet: GRACE Prefect Native Submission MVP

## Objective

Replace the current `submit-packets --execute` safety stub with real
Prefect-native packet submission.

This packet does not execute packets directly. It submits ready packets as
individual Prefect flow runs of the accepted managed packet runner:

```text
registry ready packets
  -> BacklogController submission plan
  -> one Prefect flow run per packet
  -> Prefect work queue controls execution order/concurrency
  -> registry records submitted run references
```

The key architecture rule:

```text
registry = packet inventory and domain status
Prefect = execution queue and run lifecycle
```

Do not reintroduce a local job queue. Do not use the old feature pipeline as
the packet queue. Do not merge, push, accept, review, or run multi-wave feature
logic in this packet.

## Slice

- slice_id: `SLICE-GRACE-PREFECT-NATIVE-SUBMISSION-MVP`
- slice_slug: `grace-prefect-native-submission-mvp`
- feature_id: `FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP`
- packet_id: `FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP-W01-PREFECT-NATIVE-SUBMISSION`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER, FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP-W01-PREFECT-LIFECYCLE-FLOW, FEAT-GRACE-ORCHESTRATOR-MVP2-BACKLOG-CONTROLLER-W01-BACKLOG-CONTROLLER`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/runtime_config.py`
- `/opt/astro-project/prefect_grace/cli.py`

## Impacted Modules

- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-RUNTIME-ADAPTER`
- `M-GRACE-PREFECT-SUBMITTER`
- `M-GRACE-REGISTRY-STATE`
- `M-GRACE-CLI`

## Recommended Role Assignment

- context collector: `Haiku` or cheap equivalent, useful for mapping current `submit-packets`, runtime adapter, and Prefect submitter behavior.
- coder: `Sonnet high` or `Codex high`; deterministic orchestration with mocked Prefect client.
- verifier: `Codex medium`; must run offline tests and CLI dry-run/execute-with-fake-runtime tests.
- reviewer: `Opus` or `Codex xhigh`; must verify no old queue, no feature-pipeline submission, and no merge/push/acceptance behavior.
- rework policy: fresh context if submission semantics or registry status model changes; light resume only for CLI text/JSON shape or idempotency-key formatting fixes.

## Required Design Decisions

### 1. Add Native Submission Module

Add a new module:

```text
prefect_grace/platform/prefect_native_submission.py
```

Required public API:

```python
@dataclass(frozen=True)
class PacketSubmissionRecord:
    packet_id: str
    feature_id: str
    wave_id: str
    attempt: int
    source_hash: str
    idempotency_key: str
    flow_run_id: str | None
    flow_run_name: str
    deployment_name: str
    work_queue_name: str | None
    status: Literal["submitted", "dry_run", "skipped", "failed"]
    url: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class NativeSubmissionResult:
    ok: bool
    project_key: str
    dry_run: bool
    packets_planned: list[str]
    packets_submitted: list[str]
    records: list[PacketSubmissionRecord]
    blocked_packets: list[str]
    warnings: list[str]
    errors: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        ...


def submit_ready_packets_to_prefect(
    *,
    project: Any,
    dry_run: bool = True,
    limit: int | None = None,
    execute_agent: bool = False,
    timeout_seconds: int = 3600,
    base_ref: str = "HEAD",
    worktree_root: Path | None = None,
    scheduled_for: str | None = None,
    continue_on_error: bool = False,
    submitter: Callable[..., dict[str, Any]] | None = None,
) -> NativeSubmissionResult:
    ...
```

Required behavior:

1. Use `BacklogController.plan_submission(project)` as the source of runnable
   packet order.
2. Load packet records from `PacketRegistryStore`.
3. Submit one Prefect run per packet in `submission_order`.
4. Build deterministic idempotency keys.
5. In dry-run mode, do not call Prefect.
6. In execute mode, call the submitter function.
7. After successful submit, update registry status to `submitted`.
8. On submit failure, record `failed` and stop unless `continue_on_error=True`.

### 2. Deterministic Idempotency Keys

Every submitted packet run must use a deterministic idempotency key:

```text
grace-packet:{project_key}:{packet_id}:attempt-{attempt}:{source_hash}
```

Rules:

- `source_hash` must come from packet registry/parsed packet data.
- If `source_hash` is missing, fail closed for that packet.
- Re-running `submit-packets --execute` must not create duplicate Prefect runs
  for the same packet attempt and source hash.
- If the packet source changes, the source hash changes, and a new idempotency
  key is allowed.

### 3. Registry Status Updates

Registry status is not an execution queue, but it must track submitted run
references for operator visibility.

After a successful Prefect submission, update the packet registry record:

```json
{
  "registry_status": "submitted",
  "registry_reason": "prefect_flow_run_submitted",
  "prefect_flow_run_id": "...",
  "prefect_flow_run_name": "packet:...",
  "prefect_deployment_name": "prefect-grace-managed-packet-runner/live-managed-packet-runner",
  "submission_idempotency_key": "...",
  "submitted_at": "..."
}
```

Do not mark packets as `accepted`, `completed`, `blocked`, or
`cascading_blocked` in this packet except for existing planner errors already
handled by `BacklogController.plan_submission`.

If a submit call fails, do not mutate the packet to `submitted`.

### 4. Add Managed Packet Prefect Submitter

Extend `prefect_grace/tasks/prefect_submitter.py` with managed packet
submission helpers.

Required constants/functions:

```python
MANAGED_PACKET_DEPLOYMENT_NAME = "prefect-grace-managed-packet-runner/live-managed-packet-runner"

def managed_packet_flow_run_name(packet_id: str, attempt: int, title: str | None = None) -> str:
    ...

def managed_packet_flow_parameters(...) -> dict[str, Any]:
    ...

def submit_managed_packet_flow_run(
    *,
    parameters: dict[str, Any],
    scheduled_for: str | None = None,
    tags: list[str] | None = None,
    idempotency_key: str | None = None,
    deployment_name: str = MANAGED_PACKET_DEPLOYMENT_NAME,
) -> dict[str, Any]:
    ...
```

`submit_managed_packet_flow_run(...)` must:

- use `load_runtime_config()`;
- set `PREFECT_API_URL`;
- read deployment by name;
- create a scheduled flow run from deployment;
- use `runtime.live_queue_name` as the work queue;
- return a JSON-safe dict, not a raw Prefect object;
- tag runs with:
  - `grace`;
  - `packet`;
  - `managed-runner`;
  - `packet:{packet_id}`;
  - `feature:{feature_id}`;
  - `wave:{wave_id}` when available.

Do not modify the existing feature submitter behavior except for harmless
shared helper extraction if needed.

### 5. Runtime Adapter Must Submit Managed Packet Runs

Update `prefect_grace/platform/runtime_adapter.py` so
`PrefectRuntimeAdapter.submit_packet_run(...)` submits the managed packet
runner deployment, not `prefect-grace-feature-pipeline/live-feature-pipeline`.

Rules:

- Keep `DryRunRuntime` behavior backward-compatible.
- Keep `WorkflowRuntime` interface stable.
- Return JSON-safe run references.
- Do not import Prefect at module import time.
- Do not submit feature pipeline runs from packet submission paths.

This fixes the architectural mismatch where packet submission could accidentally
route back into the feature pipeline.

### 6. Wire `submit-packets --execute`

Update CLI command:

```bash
python3 -m prefect_grace.cli submit-packets \
  --project /opt/astro-project \
  --execute \
  --json
```

Required flags:

- `--execute` submits Prefect runs.
- no `--execute` remains dry-run planning only.
- `--limit N` limits number of packet runs submitted.
- `--scheduled-for ISO8601` optionally schedules all submitted runs for a fixed time.
- `--timeout-seconds N` passed into managed packet runner flow params.
- `--worktree-root PATH` optional override; default is under project runtime state/root policy.
- `--execute-agent` explicitly sets managed packet params to live agent mode.
- `--continue-on-error` optional; default false.
- `--json`.

Safety rule:

- `--execute` means “submit Prefect flow runs”.
- `--execute-agent` means “submitted managed runner may launch live agents”.
- Without `--execute-agent`, submitted runs must use `dry_run=True` and
  `execute_agent=False`.

CLI exit codes:

- `0`: dry-run plan ok or all requested submissions succeeded.
- `3`: DAG/dependency/submission plan invalid.
- `4`: no runnable packets.
- `5`: Prefect submission failed or unsafe input.

Remove the old `SAFETY_GATE_NOT_READY` stub only after this packet's managed
runner dependency is assumed available.

### 7. One Packet = One Prefect Run

Do not batch multiple packet executions inside one Prefect run.

For a batch of 20 ready packets:

- `submit-packets --execute` creates up to 20 Prefect flow runs;
- each flow run has its own packet id, attempt, tags, idempotency key, and
  artifact;
- execution ordering/concurrency is controlled by Prefect work queue limits,
  not by an in-process local loop.

The submission function may loop to create runs, but it must not execute packet
work inline.

### 8. No Local Queue

This packet must not use or reintroduce:

- `job_queue`;
- dispatcher loops;
- local YAML queue files;
- local “pending jobs” scheduler.

Allowed state:

- packet registry status/reference updates;
- Prefect flow runs;
- Prefect work queue.

### 9. No Deployment Bootstrap Yet

This packet submits to an existing deployment name.

It must not:

- register deployments;
- create work pools;
- create work queues;
- mutate Prefect concurrency settings;
- edit systemd/docker/prefect server config.

If deployment is missing, return a structured submission error:

```json
{
  "code": "PREFECT_DEPLOYMENT_NOT_FOUND",
  "deployment_name": "prefect-grace-managed-packet-runner/live-managed-packet-runner"
}
```

Deployment bootstrap belongs to a separate operator packet.

### 10. Tests Must Be Offline

Tests must not require a live Prefect server.

Required test strategy:

- inject a fake submitter into `submit_ready_packets_to_prefect(...)`;
- use temp project adapters/state roots;
- seed registry records directly;
- test dry-run plan does not call submitter;
- test execute calls submitter once per runnable packet;
- test idempotency key stability;
- test registry status updates only on successful submit;
- test submit failure does not mark packet as submitted;
- test `--limit` caps submissions;
- test submitted parameters point to managed packet runner flow params;
- test no call path submits to `FEATURE_DEPLOYMENT_NAME`.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_prefect_native_submission.py`
- `/opt/astro-project/tests/test_prefect_grace_prefect_submitter_managed_packet.py`
- `/opt/astro-project/tests/test_prefect_grace_runtime_adapter_prefect_submission.py`
- `/opt/astro-project/tests/test_prefect_grace_runtime_adapter_submit_packet_run.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_submit_packets_prefect_native.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/tests/test_prefect_grace_backlog_controller_rework.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/packet_lifecycle.py`
- `/opt/astro-project/prefect_grace/flows/live_dashboard.py`
- `/opt/astro-project/prefect_grace/flows/worktree_scope_lifecycle_flow.py`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_artifacts.py`
- `/opt/astro-project/prefect_grace/tasks/worktree_scope_artifacts.py`
- `/opt/astro-project/prefect_grace/tasks/managed_packet_artifacts.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/runtime.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing backlog controller planning tests remain green.
- Existing managed packet runner tests remain green.
- Existing feature submission CLI behavior remains unchanged.
- Existing `submit-feature` still submits the feature pipeline deployment.
- `submit-packets` no longer claims local execution; it either plans or submits Prefect runs.
- No local queue files or dispatcher loops are introduced.
- No packet is marked accepted/completed by submission.
- No live agents are started in tests.
- No Prefect server is required in tests.
- No deployments/work pools/work queues are created or mutated.
- No merge/push/squash/remote git operation is performed.

## Required Implementation Shape

### Native Submission Module

`prefect_grace/platform/prefect_native_submission.py` must:

- include GRACE module/function contracts;
- use `BacklogController.plan_submission(project)`;
- use `PacketRegistryStore`;
- build managed packet flow parameters;
- submit through injectable submitter;
- update registry only after successful submission;
- return JSON-safe result dictionaries;
- fail closed on missing source hash, missing packet record, submitter failure,
  and invalid dependency plan.

### Prefect Submitter

`prefect_grace/tasks/prefect_submitter.py` must:

- keep `submit_feature_flow_run(...)` unchanged for feature flows;
- add managed packet submitter functions;
- use lazy Prefect imports inside functions;
- return JSON-safe dicts;
- use managed packet deployment name for packet submissions.

### Runtime Adapter

`prefect_grace/platform/runtime_adapter.py` must:

- keep interface stable;
- make `PrefectRuntimeAdapter.submit_packet_run(...)` use managed packet submitter;
- keep `DryRunRuntime` behavior unchanged;
- not import Prefect at module import time.

### CLI

`prefect_grace/cli.py` must:

- remove old `SAFETY_GATE_NOT_READY` behavior from `submit-packets --execute`;
- add `--limit`, `--scheduled-for`, `--timeout-seconds`, `--worktree-root`,
  `--execute-agent`, and `--continue-on-error`;
- preserve JSON envelope shape;
- include `records`, `packets_submitted`, `blocked_packets`, `warnings`, and
  `errors` in output.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_native_submission.py \
  tests/test_prefect_grace_prefect_submitter_managed_packet.py \
  tests/test_prefect_grace_runtime_adapter_prefect_submission.py \
  tests/test_prefect_grace_runtime_adapter_submit_packet_run.py \
  tests/test_prefect_grace_cli_submit_packets_prefect_native.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run regression tests:

```bash
pytest -q \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_backlog_controller_rework.py \
  tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_cli_worktree_scope_flow.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform/prefect_native_submission.py
python3 scripts/grace_lint.py prefect_grace/platform/runtime_adapter.py
python3 scripts/grace_lint.py prefect_grace/tasks/prefect_submitter.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke without Prefect server:

```bash
python3 -m prefect_grace.cli submit-packets \
  --project /tmp/grace-test-project \
  --json
```

Run CLI execute smoke with fake/injected submitter in tests only. Do not require
or contact a live Prefect server in automated tests.

## Expected Evidence

- command outputs for all verification commands;
- dry-run `submit-packets` JSON output;
- execute-mode test output proving fake submitter was called once per runnable packet;
- `PrefectRuntimeAdapter.submit_packet_run` regression output proving the public API delegates through the current feature submission signature;
- idempotency key examples;
- registry record after successful fake submit;
- registry record after failed fake submit showing it was not marked submitted;
- proof no call path used `FEATURE_DEPLOYMENT_NAME` for packet submission;
- proof no local queue files were created;
- confirmation no live agents, Prefect deployments, Docker containers, product backend/frontend services, remote push, merge, squash, deployment registration, or registry acceptance were started;
- `git diff --name-only` limited to `Allowed Write Scope`;
- explicit note if `tests/test_prefect_grace_backlog_controller_rework.py` changed only to remove the obsolete safety-gate assertion;
- explicit confirmation `scripts/grace_lint.py` has no diff.

## Escalation Triggers

- implementation needs to modify managed packet runner flow/module;
- implementation needs to modify worktree/scope lifecycle modules;
- implementation needs to modify state store schema classes;
- implementation needs to register deployments or mutate Prefect infra;
- implementation needs to start live Prefect server in tests;
- implementation needs to run live Codex/Claude/agy in tests;
- implementation needs a local job queue or dispatcher loop;
- implementation needs to submit feature pipeline runs for packets;
- implementation needs to mark packets accepted/completed;
- implementation needs to push, merge, squash, or mutate remote refs;
- implementation needs to modify `scripts/grace_lint.py`.

## Reviewer Gate

Reviewer must verify:

- `submit-packets --execute` creates Prefect managed packet run submissions, not local execution;
- one packet maps to one Prefect flow run;
- default submitted packet runs are dry-run unless `--execute-agent` is explicit;
- deterministic idempotency prevents duplicate runs for unchanged packet attempts;
- registry is updated only after successful submit;
- packet submission never uses `FEATURE_DEPLOYMENT_NAME`;
- no old local queue/dispatcher behavior exists;
- no deployment registration, merge, push, acceptance, or live-agent test behavior slipped in;
- no files outside `Allowed Write Scope` are modified.
