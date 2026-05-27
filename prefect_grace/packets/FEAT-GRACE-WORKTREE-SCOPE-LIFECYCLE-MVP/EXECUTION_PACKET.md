# Execution Packet: GRACE Worktree + Scope Lifecycle MVP

## Objective

Wire the accepted Worktree Manager and Scope Guard into the packet execution
lifecycle so a packet cannot proceed to verifier/reviewer when its worktree diff
violates `Allowed Write Scope` or `Frozen Scope`.

This packet connects already accepted primitives:

```text
packet execution
  -> isolated worktree
  -> changed file extraction
  -> scope guard validation
  -> pass/block before verifier/reviewer
```

This packet must not implement merge, push, release, large-file refactor,
executor registry, or ChangeSet Cache. It is the safety lifecycle gate that
must exist before broad refactors and live multi-packet execution.

## Slice

- slice_id: `SLICE-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP`
- slice_slug: `grace-worktree-scope-lifecycle-mvp`
- feature_id: `FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP`
- packet_id: `FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP-W01-LIFECYCLE-GATE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-SCOPE-GUARD-MVP-W01-SCOPE-GUARD, FEAT-GRACE-WORKTREE-MANAGER-MVP-W01-WORKTREE-MANAGER, FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP-W01-SYNTHETIC-EDGE-MATRIX`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/cli.py`

## Impacted Modules

- `M-GRACE-WORKTREE-LIFECYCLE`
- `M-GRACE-SCOPE-GUARD`
- `M-GRACE-WORKTREE-MANAGER`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-CLI`

## Recommended Role Assignment

- context collector: `Haiku` or cheap equivalent, optional, to inspect existing manager/guard APIs and CLI style.
- coder: `Sonnet high` or `Codex high`; deterministic orchestration glue and tests.
- verifier: `Codex medium`; must run temp-git lifecycle tests and CLI smoke.
- reviewer: `Opus` or `Codex xhigh`; must inspect fail-closed semantics and ensure no merge/push slipped in.
- rework policy: fresh context if lifecycle semantics change; light resume only for naming/serialization fixes.

## Required Design Decisions

### 1. Add A Lifecycle Gate Module

Add a new module:

```text
prefect_grace/platform/worktree_scope_lifecycle.py
```

Required public API:

```python
@dataclass(frozen=True)
class WorktreeScopeLifecycleResult:
    ok: bool
    packet_id: str
    attempt: int
    worktree_path: str
    branch_name: str
    changed_files: list[str]
    scope_guard: dict[str, Any]
    status: Literal["passed", "scope_blocked", "worktree_error"]
    blocker_reason: str | None = None


def evaluate_worktree_scope(
    *,
    packet_file: Path,
    repo_root: Path,
    worktree_root: Path,
    project_key: str,
    packet_id: str,
    attempt: int,
    base_ref: str,
    keep_on_failure: bool = True,
) -> WorktreeScopeLifecycleResult:
    ...
```

The function must:

1. Parse packet contract.
2. Create or resolve packet worktree using `WorktreeManager`.
3. Collect changed files from the worktree.
4. Run `validate_scope(...)` with packet `allowed_write_scope` and `frozen_scope`.
5. Return `passed` when scope is clean.
6. Return `scope_blocked` when scope guard fails.
7. Preserve worktree on blocked/failure by default.

This MVP may expose a lower-level function that accepts an existing
`WorktreeContext` to avoid always creating a worktree in unit tests. If so, the
full API above must still exist or be clearly represented by CLI behavior.

### 2. Do Not Run Live Agents

This lifecycle gate evaluates worktree state. It must not start:

- Codex;
- Claude;
- agy;
- Prefect deployments;
- Docker product containers;
- backend/frontend services.

Tests must simulate agent output by writing files directly inside temporary
worktrees.

### 3. Fail Closed

The lifecycle must fail closed when:

- packet parsing fails;
- worktree creation/status/diff fails;
- changed file extraction fails;
- scope guard returns invalid paths;
- any changed file is outside allowed scope;
- any changed file is frozen.

Fail-closed result must be machine-readable and must include enough data for a
reviewer/operator to understand the blocker:

- `packet_id`;
- `attempt`;
- `changed_files`;
- `scope_guard` result;
- `blocker_reason`;
- `worktree_path`;
- `branch_name`.

### 4. Preserve Worktree On Blocker

If scope is blocked, the worktree must remain available for inspection unless
the caller explicitly requests cleanup.

Default behavior:

```text
scope blocked -> keep worktree
worktree error -> keep worktree if it exists
scope passed -> may keep or cleanup according to explicit parameter
```

This packet must not add merge/push behavior.

### 5. CLI Surface

Add a CLI command:

```bash
python3 -m prefect_grace.cli worktree-scope-check \
  --packet prefect_grace/packets/.../EXECUTION_PACKET.md \
  --repo-root /path/to/repo \
  --worktree-root /tmp/grace-worktrees \
  --project-key astro-project \
  --packet-id FEAT-X-W01-PACKET \
  --attempt 1 \
  --base-ref HEAD \
  --json
```

CLI behavior:

- exit `0` when lifecycle status is `passed`;
- exit `1` when status is `scope_blocked`;
- exit `2` for command/input/worktree errors;
- JSON envelope must include `ok`, `status`, `changed_files`, `scope_guard`,
  `worktree_path`, `branch_name`, and `blocker_reason`;
- text mode must print a concise operator summary.

Optional CLI:

- `--keep-on-failure/--no-keep-on-failure`, default keep.
- `--existing-worktree PATH` may be added if it simplifies tests, but it must
  still validate the path is under `worktree_root`.

### 6. Backlog/Submit Guard

If `submit-packets --execute` exists and currently can claim live execution
without this lifecycle, change it to fail closed unless this lifecycle is
explicitly enabled and available.

Do not implement full submit execution in this packet.

Acceptable behavior:

```json
{
  "ok": false,
  "error": "worktree_scope_lifecycle_required"
}
```

### 7. Synthetic Matrix Hook

Add a small synthetic/regression hook proving scope-blocked lifecycle results
are distinguishable from implementation/test failures.

Do not expand the matrix broadly. One or two targeted tests are enough.

### 8. No Merge Steward Yet

This packet must not:

- merge branches;
- squash commits;
- push to remote;
- accept packet in registry;
- modify reviewer/architect verdict logic;
- refactor `feature_pipeline.py`;
- refactor `codex_launcher.py`.

Runtime integration into full Prefect live flow is a later packet after this
deterministic lifecycle gate is accepted.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_worktree_scope_lifecycle.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_worktree_scope_lifecycle.py`
- `/opt/astro-project/tests/test_prefect_grace_backlog_controller.py`
- `/opt/astro-project/tests/test_prefect_grace_synthetic_edge_matrix.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_runner.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_invariants.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing Scope Guard and Worktree Manager tests remain green.
- Existing CLI JSON envelopes remain backward-compatible.
- Packet strict validation keeps working.
- Tests use temporary git repositories, not `/opt/astro-project` as test repo.
- No live agents or Prefect deployments are started by tests.
- No product backend/frontend files are modified.
- No remote push, merge, squash, or registry acceptance is performed.
- Scope violations block before verifier/reviewer handoff.
- Blocked worktree is preserved by default for inspection.

## Required Implementation Shape

### `worktree_scope_lifecycle.py`

The module must include GRACE module contracts and function contracts.

Implementation should be small:

- dataclass result;
- packet parser adapter;
- manager/guard orchestration;
- JSON-safe serialization helper;
- no broad runtime abstraction.

### CLI

Follow existing `prefect_grace.cli` style.

The CLI can be a thin wrapper over `evaluate_worktree_scope(...)`.

### Tests

Required test cases:

- lifecycle passes when changed file is allowed;
- lifecycle blocks when changed file is frozen;
- lifecycle blocks when changed file is outside allowed scope;
- lifecycle preserves blocked worktree by default;
- lifecycle output includes changed files and scope guard details;
- invalid packet path returns command/input error;
- CLI JSON success exits `0`;
- CLI JSON scope violation exits `1`;
- CLI text mode prints concise blocked summary;
- no remote push/merge commands are executed;
- tests use temp git repos only;
- `submit-packets --execute`, if present, fails closed without lifecycle enablement.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_cli_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run regression tests:

```bash
pytest -q \
  tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_cli_scope_guard.py \
  tests/test_prefect_grace_worktree_manager.py \
  tests/test_prefect_grace_cli_worktree_manager.py \
  tests/test_prefect_grace_synthetic_edge_matrix.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform/worktree_scope_lifecycle.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP/EXECUTION_PACKET.md \
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
python3 -m prefect_grace.cli worktree-scope-check \
  --packet prefect_grace/packets/FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP/EXECUTION_PACKET.md \
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
- JSON output for lifecycle pass;
- JSON output for lifecycle scope-blocked case;
- text-mode blocked summary;
- proof tests used temporary git repositories;
- confirmation no live agents, Prefect deployments, Docker containers, product backend/frontend services, remote push, merge, squash, or registry acceptance were started;
- diff scope limited to `Allowed Write Scope`.

## Escalation Triggers

- implementation needs to modify `feature_pipeline.py` or `codex_launcher.py`;
- implementation needs to merge, squash, push, or accept packet registry state;
- tests need to use `/opt/astro-project` as the git test repository;
- lifecycle needs to start Codex, Claude, agy, Prefect, Docker, backend, or frontend;
- Scope Guard or Worktree Manager public APIs need incompatible changes;
- packet parser internals need a broad rewrite.

## Reviewer Gate

Reviewer must reject if:

- scope violations can reach verifier/reviewer as passed;
- changed-file extraction is skipped or mocked in lifecycle tests;
- blocked worktree is deleted by default;
- CLI exits `0` on scope violation;
- any remote push/merge/squash appears;
- tests mutate the main repo workspace;
- any file outside `Allowed Write Scope` is modified.
