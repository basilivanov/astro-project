# Execution Packet: GRACE Executor Registry MVP

## Objective

Introduce a deterministic executor registry for packet execution roles.

The platform currently has a hardcoded Codex launcher path. That is acceptable
for early MVPs, but the architecture needs a small stable layer that can answer:

```text
role + packet + project policy + recent attempts
  -> selected executor
  -> command/profile metadata
  -> rotation/fallback decision
  -> execution history record
```

This packet does not replace the managed packet runner with multiple live
executors yet. It creates the registry/policy layer, tests it offline, and
adds a narrow integration point so later packets can route Codex, Claude, agy,
or other agents without changing core lifecycle logic.

## Slice

- slice_id: `SLICE-GRACE-EXECUTOR-REGISTRY-MVP`
- slice_slug: `grace-executor-registry-mvp`
- feature_id: `FEAT-GRACE-EXECUTOR-REGISTRY-MVP`
- packet_id: `FEAT-GRACE-EXECUTOR-REGISTRY-MVP-W01-EXECUTOR-REGISTRY`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER, FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-RESUME-GATE, FEAT-GRACE-ORCHESTRATOR-MVP2-BACKLOG-CONTROLLER-W01-BACKLOG-CONTROLLER`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/project_adapter.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/cli.py`

## Impacted Modules

- `M-GRACE-EXECUTOR-REGISTRY`
- `M-GRACE-EXECUTOR-POLICY`
- `M-GRACE-EXECUTOR-HISTORY`
- `M-GRACE-PROJECT-ADAPTER`
- `M-GRACE-MANAGED-PACKET-RUNNER`
- `M-GRACE-CLI`

## Recommended Role Assignment

- context collector: `Haiku` or cheap equivalent, useful for mapping current `project_adapter` and `ExecutorHistoryStore`.
- coder: `Sonnet high` or `Codex high`; deterministic policy and tests.
- verifier: `Codex medium`; must run offline policy matrix and CLI tests.
- reviewer: `Opus` or `Codex xhigh`; must verify no live executor implementation beyond existing Codex path and no policy ambiguity.
- rework policy: fresh context if config schema changes; light resume only for naming/serialization fixes.

## Required Design Decisions

### 1. Add Executor Registry Module

Add:

```text
prefect_grace/platform/executor_registry.py
```

Required public API:

```python
@dataclass(frozen=True)
class ExecutorSpec:
    executor_id: str
    kind: Literal["codex", "claude", "agy", "mock"]
    command: str
    model: str | None = None
    reasoning: str | None = None
    roles: list[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 100
    max_consecutive_failures: int = 2
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class ExecutorSelection:
    ok: bool
    packet_id: str
    role: str
    selected: ExecutorSpec | None
    candidate_ids: list[str]
    rotated_from: str | None = None
    reason: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        ...


def load_executor_specs(project: Any) -> list[ExecutorSpec]:
    ...


def select_executor_for_packet(
    *,
    project: Any,
    packet: dict[str, Any],
    history: list[dict[str, Any]] | None = None,
    requested_executor: str | None = None,
) -> ExecutorSelection:
    ...


def record_executor_attempt(
    *,
    state_root: Path,
    packet_id: str,
    role: str,
    executor_id: str,
    result: dict[str, Any],
    attempt: int | None = None,
) -> dict[str, Any]:
    ...
```

All functions must be deterministic, file-backed, and testable without live
agents.

### 2. Project Config Schema

Extend `prefect_grace/platform/project_adapter.py` minimally so project config
may describe executors.

Accepted config shape:

```yaml
agent_executor:
  default: codex-cli
  command: codex1
  executors:
    - executor_id: codex-cli
      kind: codex
      command: codex1
      model: gpt-5.4
      reasoning: high
      roles: [coder, verifier, reviewer]
      enabled: true
      priority: 100
      max_consecutive_failures: 2
    - executor_id: claude-sonnet
      kind: claude
      command: claude
      model: sonnet
      roles: [coder, verifier]
      enabled: false
      priority: 200
```

Backward compatibility:

- existing configs with only `default` and `command` remain valid;
- if `executors` is absent, synthesize a single `codex-cli` spec from existing
  `default` and `command`;
- do not require existing projects to edit config.
- `project_adapter.py` may keep `executors` as raw JSON-safe dictionaries to
  avoid coupling the adapter to `executor_registry.py`; normalization into
  `ExecutorSpec` belongs in `load_executor_specs(project)`.
- invalid executor entries must fail closed during registry loading with a
  clear validation error; do not silently drop malformed enabled executors.

Do not add secrets or API keys to project config.

### 3. Selection Rules

Selection must be deterministic and explainable.

Rules:

1. If `requested_executor` is provided, select it only if enabled and role
   compatible.
2. Otherwise select enabled candidates that support the packet role.
3. Sort by `priority`, then `executor_id`.
4. Inspect recent history for the same packet and role.
5. If the best candidate has `max_consecutive_failures` or more consecutive
   failed attempts for that packet/role, rotate to the next enabled candidate.
6. If no candidate remains, return `ok=false` with reason
   `no_executor_available`.

Role compatibility:

- empty `roles` means all roles;
- otherwise packet role must be in `roles`.

Failure counting:

- failure means result returncode non-zero, domain status `agent_failed`, or
  termination reason in `stall_killed`, `timeout`, `rate_limit_exceeded`,
  `quota_exceeded`, `auth_failed`;
- `scope_blocked` is not executor failure by itself;
- missing/unknown result should not count as success.

History window:

- filter history to the same `packet_id` and `role`;
- count consecutive failures per `executor_id`, newest first;
- if both packet metadata and history record include `source_hash`, only records
  with the same `source_hash` may force rotation;
- stop counting at the first non-failure record for the same executor;
- older records from a previous packet contract/source hash must not rotate the
  executor for a fresh contract.

### 4. History Store Integration

Use existing `ExecutorHistoryStore` rather than creating a new file format.

Execution records must include:

```json
{
  "packet_id": "...",
  "feature_id": "...",
  "wave_id": "...",
  "source_hash": "sha256:...",
  "role": "coder",
  "executor_id": "codex-cli",
  "executor_kind": "codex",
  "attempt": 1,
  "status": "success|failed|scope_blocked|skipped",
  "returncode": 0,
  "termination_reason": "completed",
  "domain_status": "passed",
  "selection_reason": "selected|requested|rotated|no_executor_available|unsupported_executor_kind",
  "requested_executor": null,
  "run_dir": "...",
  "recorded_at": "..."
}
```

Do not mutate packet registry acceptance state in this packet.

### 5. Managed Runner Integration

Add only a narrow integration point to `prefect_grace/platform/managed_packet_runner.py`.

Acceptable change:

- resolve executor selection before calling launcher;
- record selected executor metadata in `agent_result`;
- record executor attempt after launcher result;
- if no executor is available, return `domain_status="runner_error"`.

Do not implement live Claude or agy launchers in this packet.

For now:

- `kind="codex"` may map to existing `launch_codex_for_packet`;
- `kind="mock"` may be used in tests only through injected launcher;
- `kind="claude"` and `kind="agy"` are selectable metadata but not executable
  by default unless a launcher is injected in tests.
- if the selected executor kind is not executable in the current runner, the
  runner must fail closed with `domain_status="runner_error"` and
  `blocker_reason="unsupported_executor_kind:<kind>"`;
- unsupported executor kinds must never fall back to Codex implicitly;
- unsupported executor-kind attempts should be recorded as `status="skipped"`
  with `selection_reason="unsupported_executor_kind"` when recording is
  possible.

### 6. CLI Surface

Add two CLI commands:

```bash
python3 -m prefect_grace.cli list-executors --project /opt/astro-project --json
python3 -m prefect_grace.cli select-executor --project /opt/astro-project --packet-id FEAT-X-W01-PACKET --json
```

`list-executors` output:

- all executor specs;
- enabled/disabled;
- roles;
- priority.

`select-executor` output:

- packet id;
- role;
- selected executor;
- candidate ids;
- rotation reason/warnings.

Do not start any agent from these commands.

### 7. No Executor Runtime Refactor

This packet must not:

- split `codex_launcher.py`;
- rewrite prompt construction;
- change Codex model/reasoning/sandbox/approval defaults;
- change resume source-hash behavior;
- implement Claude launcher;
- implement agy launcher;
- implement executor fallback retries inside one packet run;
- modify Prefect deployments or queues.

Fallback execution belongs to a later packet after registry selection is stable.

### 8. Tests Must Be Offline

Tests must not launch live Codex/Claude/agy.

Required test strategy:

- build fake project adapter configs in temp dirs;
- seed `ExecutorHistoryStore` with success/failure records;
- assert default backward-compatible synthesized executor;
- assert role filtering;
- assert requested executor selection;
- assert disabled executor is skipped;
- assert rotation after consecutive failures;
- assert `scope_blocked` does not count as executor failure;
- assert stale history with a different `source_hash` does not rotate a fresh
  packet contract;
- assert unsupported `claude`/`agy` executor kind returns runner_error without
  launching Codex when no injected launcher is provided;
- assert no candidate returns `ok=false`;
- assert CLI list/select JSON shape;
- assert managed runner can record selected executor metadata with injected fake launcher.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/executor_registry.py`
- `/opt/astro-project/prefect_grace/platform/project_adapter.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_executor_registry.py`
- `/opt/astro-project/tests/test_prefect_grace_executor_registry_cli.py`
- `/opt/astro-project/tests/test_prefect_grace_project_adapter_executors.py`
- `/opt/astro-project/tests/test_prefect_grace_managed_packet_runner_executor_registry.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_artifacts.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/packet_lifecycle.py`
- `/opt/astro-project/prefect_grace/flows/live_dashboard.py`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing project configs with `agent_executor.default` and `agent_executor.command` remain valid.
- Existing managed packet runner behavior remains valid when no explicit executor config exists.
- Existing Codex launcher behavior is unchanged.
- Existing resume source-hash gate remains enforced.
- No live agents are started in tests.
- No packet registry acceptance/completion state is mutated.
- No Prefect deployments/work queues are modified.
- No merge/push/squash/remote git operation is performed.

## Required Implementation Shape

### Executor Registry

`prefect_grace/platform/executor_registry.py` must:

- include GRACE module/function contracts;
- expose dataclasses and functions listed above;
- be deterministic;
- not import live executor SDKs;
- use only project config and history records;
- return JSON-safe dictionaries.

### Project Adapter

`prefect_grace/platform/project_adapter.py` must:

- keep backward-compatible parsing;
- add optional executor list support;
- synthesize default executor when absent;
- not require config migration.

### Managed Runner

`prefect_grace/platform/managed_packet_runner.py` must:

- integrate selection/recording narrowly;
- preserve injected launcher tests;
- include selected executor metadata in result;
- not implement executor fallback retries.

### CLI

`prefect_grace/cli.py` must:

- add `list-executors`;
- add `select-executor`;
- preserve JSON envelope shape;
- not launch agents.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_executor_registry.py \
  tests/test_prefect_grace_executor_registry_cli.py \
  tests/test_prefect_grace_project_adapter_executors.py \
  tests/test_prefect_grace_managed_packet_runner_executor_registry.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run regression tests:

```bash
pytest -q \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_codex_launcher_resume_gate.py \
  tests/test_prefect_grace_yaml_state.py \
  tests/test_prefect_grace_backlog_controller.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform/executor_registry.py
python3 scripts/grace_lint.py prefect_grace/platform/project_adapter.py
python3 scripts/grace_lint.py prefect_grace/platform/managed_packet_runner.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke without live agents:

```bash
python3 -m prefect_grace.cli list-executors --project /opt/astro-project --json
python3 -m prefect_grace.cli select-executor --project /opt/astro-project --packet-id SOME-PACKET --json
```

The second command may return `ok=false` if the packet id is absent; it must
not start an agent.

## Expected Evidence

- command outputs for all verification commands;
- JSON output for synthesized default executor;
- JSON output for configured multi-executor policy;
- rotation example after consecutive failures;
- stale source-hash history example proving old failures do not rotate a fresh packet contract;
- proof `scope_blocked` does not rotate executor by itself;
- proof unsupported `claude`/`agy` selection fails closed and does not fall back to Codex;
- CLI `list-executors` output;
- CLI `select-executor` output;
- managed runner test output proving selected executor metadata is recorded;
- confirmation no live agents, Prefect deployments, Docker containers, product backend/frontend services, remote push, merge, squash, deployment registration, or registry acceptance were started;
- `git diff --name-only` limited to `Allowed Write Scope`;
- explicit confirmation `scripts/grace_lint.py` has no diff.

## Escalation Triggers

- implementation needs to modify `codex_launcher.py`;
- implementation needs to implement Claude or agy launchers;
- implementation needs to change Codex prompt/model/reasoning/sandbox/approval/resume behavior;
- implementation needs executor fallback retries inside one run;
- implementation needs to modify `state_store.py`;
- implementation needs to modify Prefect submission/deployment code;
- implementation needs to start live agents in tests;
- implementation needs to mark packets accepted/completed;
- implementation needs to push, merge, squash, or mutate remote refs;
- implementation needs to modify `scripts/grace_lint.py`.

## Reviewer Gate

Reviewer must verify:

- executor selection is deterministic and explainable;
- default project config remains backward-compatible;
- disabled/role-incompatible executors are never selected;
- rotation happens only after executor failures, not scope blockers;
- no live Claude/agy launcher was added;
- `codex_launcher.py` was not modified;
- no files outside `Allowed Write Scope` are modified.
