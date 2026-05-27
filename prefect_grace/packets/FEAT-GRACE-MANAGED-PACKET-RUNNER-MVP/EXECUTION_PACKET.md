# Execution Packet: GRACE Managed Packet Runner MVP

## Objective

Add the first safe live-execution wrapper for a single GRACE packet.

This packet connects the already accepted primitives:

```text
single packet run
  -> isolated git worktree
  -> agent execution inside that worktree
  -> changed-file extraction
  -> scope guard validation
  -> Prefect-visible result and artifact
```

The important boundary: this MVP may run an agent for one packet, but it must
not merge, push, squash, accept the packet in registry, route to reviewer, run
multi-packet backlog submission, or modify the production feature pipeline.

The output is a machine-readable domain result that says whether the packet
execution produced an in-scope worktree diff. That result is safe input for a
later verifier/reviewer/merge-steward packet.

## Slice

- slice_id: `SLICE-GRACE-MANAGED-PACKET-RUNNER-MVP`
- slice_slug: `grace-managed-packet-runner-mvp`
- feature_id: `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP`
- packet_id: `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP-W01-PREFECT-LIFECYCLE-FLOW, FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP-W01-LIFECYCLE-GATE, FEAT-GRACE-WORKTREE-MANAGER-MVP-W01-WORKTREE-MANAGER, FEAT-GRACE-SCOPE-GUARD-MVP-W01-SCOPE-GUARD, FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-RESUME-GATE`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/flows/worktree_scope_lifecycle_flow.py`
- `/opt/astro-project/prefect_grace/tasks/worktree_scope_artifacts.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/cli.py`

## Impacted Modules

- `M-GRACE-MANAGED-PACKET-RUNNER`
- `M-GRACE-PREFECT-MANAGED-RUNNER-FLOW`
- `M-GRACE-CODEX-LAUNCHER-WORKDIR-OVERRIDE`
- `M-GRACE-WORKTREE-LIFECYCLE`
- `M-GRACE-PREFECT-ARTIFACTS`
- `M-GRACE-CLI`

## Recommended Role Assignment

- context collector: `Haiku` or cheap equivalent, optional, to inspect existing launcher/lifecycle APIs and tests.
- coder: `Sonnet high` or `Codex high`; this is orchestration glue with safety semantics, not broad architecture.
- verifier: `Codex medium`; must run temp-git tests, launcher dry-run tests, and CLI smoke without live agents.
- reviewer: `Opus` or `Codex xhigh`; must inspect fail-closed semantics, scope priority, and ensure no merge/push/acceptance slipped in.
- rework policy: fresh context if domain status semantics or launcher signature changes; light resume only for artifact markdown, CLI wording, or test fixture fixes.

## Required Design Decisions

### 1. Add A Managed Packet Runner Module

Add a new module:

```text
prefect_grace/platform/managed_packet_runner.py
```

Required public API:

```python
@dataclass(frozen=True)
class ManagedPacketRunResult:
    ok: bool
    domain_status: Literal["passed", "scope_blocked", "agent_failed", "runner_error"]
    packet_id: str
    attempt: int
    worktree_path: str
    branch_name: str
    changed_files: list[str]
    agent_result: dict[str, Any]
    lifecycle_result: dict[str, Any]
    scope_guard: dict[str, Any]
    artifact_ids: list[str] = field(default_factory=list)
    blocker_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        ...


def run_managed_packet(
    *,
    packet_file: Path,
    repo_root: Path,
    worktree_root: Path,
    project_key: str,
    packet_id: str,
    attempt: int,
    base_ref: str,
    dry_run: bool = True,
    execute_agent: bool = False,
    timeout_seconds: int = 3600,
    keep_worktree: bool = True,
    launcher: Callable[..., dict[str, Any]] | None = None,
) -> ManagedPacketRunResult:
    ...
```

`dry_run=True` is the safe default. A live agent may run only when
`execute_agent=True` and `dry_run=False`.

Required sequence:

1. Parse `EXECUTION_PACKET.md` with the existing packet parser.
2. Create or resolve the packet worktree with `WorktreeManager`.
3. Run the agent in that worktree.
4. Run `evaluate_worktree_scope(...)` after agent execution, using the same
   packet id, attempt, worktree root, repo root, and base ref.
5. Return a `ManagedPacketRunResult`.

Do not reimplement scope validation in this module. The post-agent scope result
must come from the accepted lifecycle gate.

### 2. Agent Execution Must Be Worktree-Bound

The managed runner must ensure the agent process uses the isolated worktree as
its working directory.

Add the smallest possible extension to `prefect_grace/tasks/codex_launcher.py`:

```python
def launch_codex_for_packet(
    packet_id: str,
    *,
    dry_run: bool = False,
    timeout_seconds: int = 3600,
    logger: logging.Logger | None = None,
    heartbeat_interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    stall_timeout_seconds: float | None = None,
    workdir_override: str | Path | None = None,
) -> dict[str, Any]:
    ...
```

Rules:

- When `workdir_override` is provided, it wins over config and packet
  `execution_hints.workdir`.
- `workdir_override` must be resolved to an existing directory.
- If `workdir_override` does not exist or is not a directory, return/fail
  closed as an agent launch error.
- Existing callers without `workdir_override` must behave exactly as before.
- Do not refactor `codex_launcher.py` in this packet.
- Do not change default model, reasoning, sandbox, approval, resume strategy,
  heartbeat, stall handling, or session storage.

This is intentionally a narrow launcher hook. Full executor registry and
Codex/Claude/agy rotation belong to later packets.

### 3. Domain Status Priority

The runner must classify outcomes deterministically:

```text
runner_error    -> setup/parsing/worktree/launcher invocation failed before a reliable post-scope result exists
scope_blocked   -> post-agent lifecycle scope check found frozen/outside/invalid path violations
agent_failed    -> agent returned non-zero/stalled/failed, but post-agent scope is clean
passed          -> agent returned success and post-agent scope is clean
```

If both agent failure and scope violation happen, `scope_blocked` wins because
scope safety is the higher-priority blocker. The result must still include
`agent_result` so reviewer can see the agent failure.

### 4. Add A Prefect Flow

Add a new module:

```text
prefect_grace/flows/managed_packet_runner_flow.py
```

Required flow:

```python
@flow(
    name="prefect-grace-managed-packet-runner",
    flow_run_name="managed-packet:{packet_id}:attempt-{attempt}",
)
def managed_packet_runner_flow(
    *,
    packet_file: str,
    repo_root: str,
    worktree_root: str,
    project_key: str,
    packet_id: str,
    attempt: int,
    base_ref: str,
    dry_run: bool = True,
    execute_agent: bool = False,
    timeout_seconds: int = 3600,
    keep_worktree: bool = True,
) -> dict[str, Any]:
    ...
```

Required tasks:

- `run_managed_packet_task(...)`;
- `publish_managed_packet_artifact_task(...)`.

The flow must complete as a Prefect run for domain statuses
`scope_blocked` and `agent_failed`. These are domain outcomes, not Python
programming exceptions.

Unexpected programming errors may still fail the flow.

### 5. Add Operator Artifact

Add a small dedicated helper:

```text
prefect_grace/tasks/managed_packet_artifacts.py
```

Required public function:

```python
def publish_managed_packet_run_artifact(result: dict[str, Any]) -> list[str]:
    ...
```

Artifact markdown must include:

- packet id;
- attempt;
- domain status;
- worktree path;
- branch name;
- changed files;
- agent return code / termination reason / session mode if present;
- lifecycle status;
- frozen violations;
- outside-allowed violations;
- invalid paths;
- blocker reason;
- run directory / stdout / stderr artifact paths if present in `agent_result`.

Artifact publication is best-effort:

- if Prefect artifacts are unavailable, return `[]`;
- if publication fails, return `[]`;
- do not change the domain status.

Do not modify `prefect_grace/tasks/prefect_artifacts.py` in this packet.

### 6. Add CLI Runner

Add a CLI command:

```bash
python3 -m prefect_grace.cli run-managed-packet \
  --packet prefect_grace/packets/.../EXECUTION_PACKET.md \
  --repo-root /path/to/repo \
  --worktree-root /tmp/grace-worktrees \
  --project-key astro-project \
  --packet-id FEAT-X-W01-PACKET \
  --attempt 1 \
  --base-ref HEAD \
  --dry-run \
  --json
```

CLI flags:

- `--dry-run` default behavior; must not launch a live agent.
- `--execute-agent` explicitly allows live execution.
- `--timeout-seconds N`.
- `--keep-worktree` default true.
- `--json`.

Safety rule:

- `--execute-agent` without explicitly disabling dry-run must fail closed with
  a clear input error.
- The CLI should require the operator to pass either `--dry-run` or
  `--execute-agent --no-dry-run` if a negative flag pattern is implemented.
- Tests must not use live agent execution.

CLI exit codes:

- `0` for `domain_status=passed`;
- `1` for `domain_status=scope_blocked`;
- `2` for `domain_status=agent_failed` or `runner_error` or command/input errors.

JSON output must include:

- `ok`;
- `domain_status`;
- `packet_id`;
- `attempt`;
- `worktree_path`;
- `changed_files`;
- `agent_result`;
- `lifecycle_result`;
- `scope_guard`;
- `artifact_ids`;
- `blocker_reason`.

### 7. Do Not Add Deployments Yet

This packet must not register Prefect deployments, schedules, queues, or work
pool changes.

Deployment creation and native queued submission belong to a later packet after
the single managed runner is accepted.

Do not modify:

- `prefect_grace/tasks/prefect_submitter.py`;
- deployment names;
- work pool / work queue config;
- systemd/docker/prefect server config.

### 8. No Merge, Push, Acceptance, Or Reviewer Routing

This packet must not:

- merge branches;
- squash commits;
- push to remote;
- accept packet in registry;
- mark packet as completed/accepted in registry;
- route to reviewer/verifier;
- modify reviewer/architect verdict logic;
- modify `feature_pipeline.py`;
- modify `packet_lifecycle.py`;
- modify `live_dashboard.py`.

The result is only an execution artifact and domain status.

### 9. Executor Registry Is Out Of Scope

Do not implement the full executor registry in this packet.

Acceptable design:

- hardcode the current Codex launcher as the only implemented executor;
- keep the managed runner function shaped so a later executor registry can
  replace the launcher callable;
- fail closed on unsupported executor names if an `executor_kind` parameter is
  added.

Do not implement Claude, agy, round-robin, model rotation, retry policies, or
executor fallback in this packet.

### 10. Tests Must Be Offline And Deterministic

Tests must not launch live Codex/Claude/agy.

Required test strategy:

- Use temporary git repositories for worktree tests.
- Use injected fake launcher callables for runner tests.
- Use `launch_codex_for_packet(..., dry_run=True, workdir_override=...)` for
  launcher workdir override tests.
- Assert the fake/launcher receives the worktree path, not `/opt/astro-project`.
- Simulate agent success/failure by returning dicts.
- Simulate in-scope and out-of-scope file changes by writing files directly to
  the temp worktree.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/tasks/managed_packet_artifacts.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_managed_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_managed_packet_runner_flow.py`
- `/opt/astro-project/tests/test_prefect_grace_managed_packet_artifacts.py`
- `/opt/astro-project/tests/test_prefect_grace_codex_launcher_workdir_override.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_managed_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/**`

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
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_artifacts.py`
- `/opt/astro-project/prefect_grace/tasks/worktree_scope_artifacts.py`
- `/opt/astro-project/prefect_grace/tasks/verifier_runner.py`
- `/opt/astro-project/prefect_grace/tasks/wave_executor.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing Worktree Manager, Scope Guard, lifecycle, and Prefect lifecycle flow tests remain green.
- Existing `launch_codex_for_packet(...)` callers without `workdir_override` behave exactly as before.
- Existing resume source-hash gate remains enforced inside `codex_launcher.py`.
- Existing CLI JSON envelopes remain backward-compatible.
- Packet strict validation keeps working.
- Tests use temporary git repositories, not `/opt/astro-project` as test repo.
- Tests do not start live agents, Prefect deployments, Docker containers, product backend/frontend services, remote push, merge, squash, deployment registration, or registry acceptance.
- `scope_blocked` remains a domain outcome with machine-readable scope details.
- Artifact publication remains best-effort and cannot hide runner/lifecycle result.

## Required Implementation Shape

### Managed Runner Module

`prefect_grace/platform/managed_packet_runner.py` must:

- include GRACE module/function contracts;
- expose `ManagedPacketRunResult`;
- expose `run_managed_packet(...)`;
- use `WorktreeManager` to create/resolve worktree before agent launch;
- call the launcher with the worktree path;
- call `evaluate_worktree_scope(...)` after agent launch;
- preserve the worktree by default;
- fail closed on parse/worktree/launcher/lifecycle errors;
- avoid shell interpolation and remote git operations.

### Codex Launcher Change

`prefect_grace/tasks/codex_launcher.py` change must be limited to:

- optional `workdir_override` parameter;
- resolution/validation of that override;
- tests proving dry-run command uses the override.

No prompt rewrite, model change, resume strategy change, heartbeat change,
stall timeout change, or config schema change is allowed.

### Flow Module

`prefect_grace/flows/managed_packet_runner_flow.py` must:

- use `prefect_grace.prefect_compat` imports;
- call `run_managed_packet(...)`;
- call artifact publication as a separate best-effort task;
- return the same result shape as CLI JSON;
- not require a Prefect server in tests.

### Artifact Module

`prefect_grace/tasks/managed_packet_artifacts.py` must:

- use lazy import for Prefect artifacts;
- avoid direct static `from prefect...` / `import prefect`;
- return `[]` when artifacts are unavailable;
- include enough markdown for operator diagnosis.

### CLI

`prefect_grace/cli.py` must:

- add `run-managed-packet`;
- support JSON and text mode;
- implement exit codes exactly as specified;
- fail closed on unsafe flag combinations.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_managed_packet_runner_flow.py \
  tests/test_prefect_grace_managed_packet_artifacts.py \
  tests/test_prefect_grace_codex_launcher_workdir_override.py \
  tests/test_prefect_grace_cli_managed_packet_runner.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run regression tests:

```bash
pytest -q \
  tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_worktree_scope_lifecycle_flow.py \
  tests/test_prefect_grace_worktree_manager.py \
  tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_codex_launcher_resume_gate.py \
  tests/test_prefect_grace_cli_worktree_scope_flow.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform/managed_packet_runner.py
python3 scripts/grace_lint.py prefect_grace/flows/managed_packet_runner_flow.py
python3 scripts/grace_lint.py prefect_grace/tasks/managed_packet_artifacts.py
python3 scripts/grace_lint.py prefect_grace/tasks/codex_launcher.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke in a temporary git repository with dry-run only:

```bash
tmp_repo="$(mktemp -d)"
git -C "$tmp_repo" init -q
git -C "$tmp_repo" config user.email test@example.invalid
git -C "$tmp_repo" config user.name "Test User"
printf 'base\n' > "$tmp_repo/README.md"
git -C "$tmp_repo" add README.md
git -C "$tmp_repo" commit -qm init
python3 -m prefect_grace.cli run-managed-packet \
  --packet prefect_grace/packets/FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP/EXECUTION_PACKET.md \
  --repo-root "$tmp_repo" \
  --worktree-root "$tmp_repo.worktrees" \
  --project-key test-project \
  --packet-id FEAT-TEST-W01-PACKET \
  --attempt 1 \
  --base-ref HEAD \
  --dry-run \
  --json
```

Expected dry-run smoke:

- exit `0`;
- `domain_status="passed"`;
- `changed_files=[]`;
- agent result proves no live agent was launched;
- worktree path is under the temp worktree root.

## Expected Evidence

- command outputs for all verification commands;
- JSON output for dry-run passed case;
- JSON output for simulated `scope_blocked` case;
- JSON output for simulated `agent_failed` case;
- artifact markdown sample or captured artifact creation payload;
- proof that launcher receives worktree path, not `/opt/astro-project`;
- proof tests used temporary git repositories;
- confirmation no live agents, Prefect deployments, Docker containers, product backend/frontend services, remote push, merge, squash, deployment registration, or registry acceptance were started;
- `git diff --name-only` limited to `Allowed Write Scope`;
- explicit confirmation `scripts/grace_lint.py` has no diff.

## Escalation Triggers

- implementation needs to modify `feature_pipeline.py`, `packet_lifecycle.py`, or `live_dashboard.py`;
- implementation needs to modify `scope_guard.py`, `worktree_manager.py`, or `worktree_scope_lifecycle.py`;
- implementation needs to modify `state_store.py` or registry acceptance state;
- implementation needs to register deployments or submit scheduled Prefect runs;
- implementation needs to start live Codex/Claude/agy in tests;
- implementation needs to push, merge, squash, or mutate remote refs;
- implementation needs to change Codex model, reasoning, sandbox, approval, resume strategy, prompt construction, heartbeat, stall timeout, or session persistence;
- implementation needs to modify `scripts/grace_lint.py`;
- implementation needs to support Claude/agy/executor fallback in this packet.

## Reviewer Gate

Reviewer must verify:

- the only production launcher change is `workdir_override`;
- default launcher behavior is backward-compatible;
- dry-run tests cannot accidentally launch live agents;
- live execution requires explicit unsafe/operator intent;
- worktree path is used for agent execution;
- scope guard runs after agent execution;
- `scope_blocked` wins over `agent_failed` when both apply;
- no merge/push/acceptance/deployment behavior exists;
- no files outside `Allowed Write Scope` are modified.
