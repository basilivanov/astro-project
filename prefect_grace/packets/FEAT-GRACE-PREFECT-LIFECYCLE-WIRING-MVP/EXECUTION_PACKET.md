# Execution Packet: GRACE Prefect Lifecycle Wiring MVP

## Objective

Expose the accepted Worktree + Scope lifecycle gate as a Prefect-visible dry/mock
flow so operators can see packet lifecycle status in Prefect before live Codex
execution is wired in.

This packet connects:

```text
Prefect flow run
  -> worktree_scope_lifecycle evaluation
  -> markdown artifact publication
  -> domain status returned to operator
```

It must not start live agents, submit real Codex work, merge, push, squash,
deploy product services, or refactor `feature_pipeline.py` / `codex_launcher.py`.

This is the first point where the new safety lifecycle becomes visible through
Prefect execution, but it remains dry/mock with temporary git repositories in
tests.

## Slice

- slice_id: `SLICE-GRACE-PREFECT-LIFECYCLE-WIRING-MVP`
- slice_slug: `grace-prefect-lifecycle-wiring-mvp`
- feature_id: `FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP`
- packet_id: `FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP-W01-PREFECT-LIFECYCLE-FLOW`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP-W01-LIFECYCLE-GATE, FEAT-GRACE-WORKTREE-MANAGER-MVP-W01-WORKTREE-MANAGER, FEAT-GRACE-SCOPE-GUARD-MVP-W01-SCOPE-GUARD`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/prefect_compat.py`
- `/opt/astro-project/prefect_grace/flows/packet_lifecycle.py`
- `/opt/astro-project/prefect_grace/flows/live_dashboard.py`
- `/opt/astro-project/prefect_grace/cli.py`

## Impacted Modules

- `M-GRACE-PREFECT-LIFECYCLE-FLOW`
- `M-GRACE-WORKTREE-LIFECYCLE`
- `M-GRACE-PREFECT-ARTIFACTS`
- `M-GRACE-CLI`

## Recommended Role Assignment

- context collector: `Haiku` or cheap equivalent, optional, to inspect existing Prefect flow/artifact style.
- coder: `Sonnet high` or `Codex high`; small deterministic flow/task/CLI wiring.
- verifier: `Codex medium`; must run flow tests without Prefect server and CLI smoke in temp git repo.
- reviewer: `Opus` or `Codex xhigh`; must verify no live agent/merge/push/deployment behavior slipped in.
- rework policy: fresh context if flow status semantics change; light resume only for naming/artifact markdown fixes.

## Required Design Decisions

### 1. Add A Dedicated Prefect Flow

Add a new module:

```text
prefect_grace/flows/worktree_scope_lifecycle_flow.py
```

Required flow:

```python
@flow(
    name="prefect-grace-worktree-scope-lifecycle",
    flow_run_name="worktree-scope:{packet_id}:attempt-{attempt}",
)
def worktree_scope_lifecycle_flow(
    *,
    packet_file: str,
    repo_root: str,
    worktree_root: str,
    project_key: str,
    packet_id: str,
    attempt: int,
    base_ref: str,
    keep_on_failure: bool = True,
) -> dict[str, Any]:
    ...
```

Required tasks:

- `evaluate_worktree_scope_task(...)`;
- `publish_worktree_scope_artifact_task(...)`.

Flow return shape:

```json
{
  "ok": true,
  "domain_status": "passed",
  "packet_id": "...",
  "attempt": 1,
  "worktree_path": "...",
  "branch_name": "...",
  "changed_files": [],
  "scope_guard": {},
  "artifact_ids": []
}
```

Allowed `domain_status` values:

- `passed`;
- `scope_blocked`;
- `worktree_error`.

The Prefect flow should normally complete as a Prefect run even when
`domain_status=scope_blocked`; scope blockers are domain outcomes, not Python
exceptions. Unexpected programming errors may still fail the flow.

### 2. Publish Operator Artifact

Prefer a small dedicated artifact helper rather than expanding the already
large `prefect_artifacts.py`.

Add:

```text
prefect_grace/tasks/worktree_scope_artifacts.py
```

Required public function:

```python
def publish_worktree_scope_lifecycle_artifact(result: dict[str, Any]) -> list[str]:
    ...
```

Artifact markdown must include:

- packet id;
- attempt;
- domain status;
- worktree path;
- branch name;
- changed files;
- frozen violations;
- outside-allowed violations;
- invalid paths;
- blocker reason.

If Prefect artifacts are unavailable, function returns `[]` and does not fail.

### 3. Add CLI Runner For Local/Operational Smoke

Add a CLI command:

```bash
python3 -m prefect_grace.cli run-worktree-scope-flow \
  --packet prefect_grace/packets/.../EXECUTION_PACKET.md \
  --repo-root /path/to/repo \
  --worktree-root /tmp/grace-worktrees \
  --project-key astro-project \
  --packet-id FEAT-X-W01-PACKET \
  --attempt 1 \
  --base-ref HEAD \
  --json
```

This command may call the flow function directly. It must not require a Prefect
server in tests.

CLI exit codes:

- `0` for `domain_status=passed`;
- `1` for `domain_status=scope_blocked`;
- `2` for `domain_status=worktree_error` or command/input errors.

JSON output must include `ok`, `domain_status`, `packet_id`, `attempt`,
`artifact_ids`, and `scope_guard`.

### 4. No Deployment Yet

This packet must not register a Prefect deployment or submit scheduled runs.

Deployment creation belongs to the next operator packet after this flow is
accepted.

Do not modify:

- `prefect_grace/tasks/prefect_submitter.py`;
- deployment names;
- work pool/queue config;
- systemd/docker/prefect server config.

### 5. No Live Agent Execution

This flow evaluates filesystem/git state. It must not start:

- Codex;
- Claude;
- agy;
- `codex_launcher.py`;
- product backend/frontend services;
- Docker containers.

Tests simulate packet changes by writing files directly inside temporary
worktrees.

### 6. Preserve Existing Lifecycle Semantics

The flow must consume `evaluate_worktree_scope(...)` as the source of truth.

Do not reimplement scope validation or worktree changed-file extraction inside
the flow.

`scope_guard.py`, `worktree_manager.py`, and `worktree_scope_lifecycle.py` are
frozen for this packet.

### 7. Artifact Publication Is Best-Effort

Artifact publication failure must not turn `passed` into `worktree_error`.

If artifact publication fails:

- include an `artifact_error` field in the returned dict;
- keep the lifecycle domain status from `evaluate_worktree_scope(...)`;
- do not hide the lifecycle result.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/flows/worktree_scope_lifecycle_flow.py`
- `/opt/astro-project/prefect_grace/tasks/worktree_scope_artifacts.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_worktree_scope_lifecycle_flow.py`
- `/opt/astro-project/tests/test_prefect_grace_worktree_scope_artifacts.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_worktree_scope_flow.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/packet_lifecycle.py`
- `/opt/astro-project/prefect_grace/flows/live_dashboard.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_artifacts.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing Worktree Manager, Scope Guard, and lifecycle tests remain green.
- Existing CLI JSON envelopes remain backward-compatible.
- Packet strict validation keeps working.
- Tests use temporary git repositories, not `/opt/astro-project` as test repo.
- No live agents or Prefect deployments are started by tests.
- No product backend/frontend files are modified.
- No remote push, merge, squash, deployment registration, or registry acceptance is performed.
- `scope_blocked` remains a domain outcome with machine-readable artifact/status.

## Required Implementation Shape

### Flow Module

The module must include GRACE module contracts and function contracts.

Implementation should be small:

- one evaluate task;
- one artifact task;
- one flow;
- no custom runtime framework.

Use `prefect_grace.prefect_compat.flow` and `task` so tests run without Prefect
server.

### Artifact Module

The artifact module should be bounded and independent.

Do not edit `prefect_artifacts.py` unless there is a hard blocker.

### CLI

The CLI command should mirror `worktree-scope-check` inputs and output shape,
but run the Prefect flow function rather than the raw lifecycle function.

### Tests

Required test cases:

- flow returns `domain_status=passed` for allowed changed file;
- flow returns `domain_status=scope_blocked` for frozen changed file;
- flow preserves blocked worktree;
- flow publishes artifact when artifact backend is available;
- artifact helper returns `[]` when Prefect artifacts are unavailable;
- artifact markdown includes changed files and violations;
- CLI JSON passed exits `0`;
- CLI JSON scope-blocked exits `1`;
- CLI text summary includes domain status and worktree path;
- tests use temp git repos only;
- no live agents, deployments, push, merge, or Docker calls are made.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_worktree_scope_lifecycle_flow.py \
  tests/test_prefect_grace_worktree_scope_artifacts.py \
  tests/test_prefect_grace_cli_worktree_scope_flow.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run regression tests:

```bash
pytest -q \
  tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_cli_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_worktree_manager.py \
  tests/test_prefect_grace_scope_guard.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/flows/worktree_scope_lifecycle_flow.py
python3 scripts/grace_lint.py prefect_grace/tasks/worktree_scope_artifacts.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke in a temporary git repository:

```bash
tmp_repo="$(mktemp -d)"
git -C "$tmp_repo" init -q
git -C "$tmp_repo" config user.email test@example.invalid
git -C "$tmp_repo" config user.name "Test User"
printf 'base\n' > "$tmp_repo/README.md"
git -C "$tmp_repo" add README.md
git -C "$tmp_repo" commit -qm init
python3 -m prefect_grace.cli run-worktree-scope-flow \
  --packet prefect_grace/packets/FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP/EXECUTION_PACKET.md \
  --repo-root "$tmp_repo" \
  --worktree-root "$tmp_repo.worktrees" \
  --project-key test-project \
  --packet-id FEAT-TEST-W01-PACKET \
  --attempt 1 \
  --base-ref HEAD \
  --json
```

## Expected Evidence

- command outputs for all verification commands;
- JSON output for flow passed case;
- JSON output for flow scope-blocked case;
- artifact markdown sample or captured artifact creation payload;
- text-mode operator summary;
- proof tests used temporary git repositories;
- confirmation no live agents, Prefect deployments, Docker containers, product backend/frontend services, remote push, merge, squash, deployment registration, or registry acceptance were started;
- diff scope limited to `Allowed Write Scope`.

## Escalation Triggers

- implementation needs to modify `feature_pipeline.py`, `packet_lifecycle.py`, or `live_dashboard.py`;
- implementation needs to modify `scope_guard.py`, `worktree_manager.py`, or `worktree_scope_lifecycle.py`;
- implementation needs to register deployments or submit scheduled Prefect runs;
- implementation needs to start Codex, Claude, agy, Docker, backend, or frontend;
- implementation needs to push, merge, squash, or mutate registry acceptance state;
- artifact requirements require editing `prefect_artifacts.py`.

## Reviewer Gate

Reviewer must reject if:

- flow bypasses `evaluate_worktree_scope(...)`;
- flow reports `passed` when lifecycle returned `scope_blocked`;
- CLI exits `0` on `scope_blocked`;
- artifact publication failure hides lifecycle result;
- tests require a live Prefect server;
- any live agent/deployment/merge/push behavior appears;
- any file outside `Allowed Write Scope` is modified.
