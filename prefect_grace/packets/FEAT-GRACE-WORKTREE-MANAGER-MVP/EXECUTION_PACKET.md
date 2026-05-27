# Execution Packet: GRACE Worktree Manager MVP

## Objective

Implement a deterministic Worktree Manager for the portable GRACE orchestrator.

The manager must create, inspect, and clean per-packet git worktrees so live
agent execution does not mutate the main repository workspace directly.

This packet is infrastructure only. It must not run live agents, submit Prefect
flows, merge branches, push to remotes, or touch product backend/frontend code.

The MVP goal is to provide the safe filesystem/git primitive required before
`submit-packets --execute` and parallel packet execution can be enabled.

## Slice

- slice_id: `SLICE-GRACE-WORKTREE-MANAGER-MVP`
- slice_slug: `grace-worktree-manager-mvp`
- feature_id: `FEAT-GRACE-WORKTREE-MANAGER-MVP`
- packet_id: `FEAT-GRACE-WORKTREE-MANAGER-MVP-W01-WORKTREE-MANAGER`
- wave_id: `W01`
- status: `complete`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-SCOPE-GUARD-MVP-W01-SCOPE-GUARD, FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP-W01-SYNTHETIC-EDGE-MATRIX`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-WORKTREE-MANAGER-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/project_adapter.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/cli.py`

## Impacted Modules

- `M-GRACE-WORKTREE-MANAGER`
- `M-GRACE-SCOPE-GUARD`
- `M-GRACE-CLI`
- `M-GRACE-PROJECT-ADAPTER`

## Recommended Role Assignment

- context collector: `Haiku` or cheap equivalent, optional, to inspect existing CLI/project adapter/test style.
- coder: `Sonnet high` or `Codex high`; this is deterministic git/filesystem code.
- verifier: `Codex medium`; must run tests in temporary git repositories.
- reviewer: `Opus` or `Codex xhigh`; reviewer must inspect cleanup safety and no-main-workspace mutation guarantees.
- rework policy: fresh context if branch/worktree semantics change; light resume only for formatting/test naming fixes.

## Required Design Decisions

### 1. Worktrees Are Runtime Sandboxes, Not Security Boundaries

Worktrees isolate git state and dirty files. They do not sandbox code execution.

This packet must not claim worktrees provide security isolation. Security
sandboxing belongs to executor/runtime policy, not this manager.

### 2. Pure Worktree Manager Module

Add a new module:

```text
prefect_grace/platform/worktree_manager.py
```

Required public API:

```python
@dataclass(frozen=True)
class WorktreeContext:
    packet_id: str
    attempt: int
    repo_root: Path
    worktree_path: Path
    branch_name: str
    base_ref: str
    created: bool


@dataclass(frozen=True)
class WorktreeStatus:
    packet_id: str
    attempt: int | None
    path: Path
    branch_name: str | None
    exists: bool
    dirty: bool
    changed_files: list[str]


class WorktreeManager:
    def __init__(self, *, repo_root: Path, worktree_root: Path, project_key: str) -> None: ...

    def create_packet_worktree(
        self,
        *,
        packet_id: str,
        attempt: int,
        base_ref: str,
    ) -> WorktreeContext: ...

    def get_changed_files(self, worktree_path: Path, *, base_ref: str) -> list[str]: ...

    def status(self, *, packet_id: str, attempt: int) -> WorktreeStatus: ...

    def cleanup_worktree(
        self,
        *,
        packet_id: str,
        attempt: int,
        keep_on_failure: bool,
    ) -> WorktreeStatus: ...

    def list_active_worktrees(self) -> list[WorktreeStatus]: ...
```

Rules:

- no LLM calls;
- no Prefect dependency;
- no live agent execution;
- no remote push;
- no merge/squash;
- no mutation of packet registry/state;
- all git commands must run with explicit `cwd`;
- all paths must stay inside configured `worktree_root`;
- branch names must be sanitized and deterministic;
- cleanup must fail closed when target path is outside `worktree_root`;
- cleanup with `keep_on_failure=True` must not remove the worktree;
- accepted cleanup may remove the worktree and delete the local branch only
  when safe.

### 3. Branch Naming

Use deterministic local branch names:

```text
agent/<project_key>/<packet_id>/attempt-<NNNN>
```

Sanitize:

- lowercase where safe;
- replace unsupported characters with `-`;
- collapse repeated separators;
- keep packet id readable;
- reject empty result.

The branch naming helper must be unit-tested separately.

### 4. Git Command Wrapper

Implement a tiny internal git runner.

Requirements:

- captures stdout/stderr;
- includes command and cwd in raised errors;
- does not use shell interpolation;
- supports tests against temporary git repos;
- never runs `git push`;
- never runs destructive commands outside `worktree_root`.

Allowed git commands for MVP:

- `git rev-parse --show-toplevel`
- `git rev-parse --verify <base_ref>`
- `git worktree add -B <branch> <path> <base_ref>`
- `git worktree list --porcelain`
- `git status --porcelain`
- `git diff --name-only <base_ref>...HEAD`
- `git diff --name-only`
- `git worktree remove <path>`
- `git branch -D <branch>` only after worktree removal succeeds and branch
  matches the manager branch prefix.

### 5. Changed-File Extraction

`get_changed_files(...)` must include:

- committed changes vs `base_ref`;
- unstaged changes;
- staged changes;
- untracked files.

Output must be deterministic, de-duplicated, repo-relative POSIX paths.

This output is designed for the Scope Guard created in
`FEAT-GRACE-SCOPE-GUARD-MVP`.

### 6. CLI Surface

Add CLI commands:

```bash
python3 -m prefect_grace.cli worktree-create \
  --repo-root /path/to/repo \
  --worktree-root /tmp/grace-worktrees \
  --project-key astro-project \
  --packet-id FEAT-X-W01-PACKET \
  --attempt 1 \
  --base-ref HEAD \
  --json

python3 -m prefect_grace.cli worktree-status ...

python3 -m prefect_grace.cli worktree-cleanup ...
```

Minimum CLI commands:

- `worktree-create`
- `worktree-status`
- `worktree-cleanup`

CLI behavior:

- JSON output is stable and machine-readable;
- exit `0` on success;
- exit `1` for worktree/git operation failures;
- exit `2` for invalid CLI inputs;
- text mode prints concise operator summaries.

Do not add `submit-packets --execute` wiring in this packet.

### 7. Scope Guard Compatibility

This packet should not reimplement scope guard.

It must provide changed-file output that can be passed directly into:

```python
validate_scope(
    changed_files=manager.get_changed_files(...),
    allowed_scope=packet.allowed_write_scope,
    frozen_scope=packet.frozen_scope,
    repo_root=repo_root,
)
```

Add one integration-style unit test using the real `validate_scope` if the
Scope Guard packet has been implemented. If Scope Guard is not available in
the current branch, mark this as deferred in evidence and do not fake it.

### 8. No Lifecycle Integration Yet

This packet must not modify:

- `feature_pipeline.py`
- `codex_launcher.py`
- `backlog_controller.py`
- live Prefect deployments

Runtime lifecycle integration is a later packet after Scope Guard and Worktree
Manager are both accepted.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_worktree_manager.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_worktree_manager.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-WORKTREE-MANAGER-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/project_adapter.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_edge_matrix.py`
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

- Main repository workspace must not be mutated by tests.
- Tests must create and use temporary git repositories.
- Existing accepted platform tests keep passing.
- Existing CLI JSON envelopes remain backward-compatible.
- Packet strict validation keeps working.
- No live agents or Prefect deployments are started by tests.
- No product backend/frontend files are modified.
- No remote push or merge is performed.
- Worktree cleanup must not remove paths outside configured `worktree_root`.

## Required Implementation Shape

### `worktree_manager.py`

The module must include GRACE module contracts and function contracts.

Implementation should be intentionally small:

- dataclasses;
- branch sanitizer;
- git runner helper;
- manager class;
- JSON-safe serialization helpers.

Do not introduce a general git abstraction layer beyond what this packet needs.

### CLI

Follow existing `prefect_grace.cli` style.

The commands may be thin wrappers over `WorktreeManager`.

Do not add project config loading unless needed for tests. Explicit CLI args are
acceptable for MVP.

### Tests

Required test cases:

- branch name sanitizer is deterministic and rejects empty names;
- create worktree from temporary git repo `HEAD`;
- created worktree path is under configured `worktree_root`;
- status reports clean worktree after creation;
- status reports dirty worktree after file modification;
- changed-file extraction includes committed, staged, unstaged, and untracked
  paths;
- cleanup removes accepted worktree when `keep_on_failure=False`;
- cleanup preserves worktree when `keep_on_failure=True`;
- cleanup refuses path outside `worktree_root`;
- list active worktrees returns only manager-owned worktrees where practical;
- CLI create emits JSON with `worktree_path`, `branch_name`, `created`;
- CLI status emits dirty/changed file data;
- CLI cleanup exits `0` on success;
- CLI invalid input exits `2`.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_worktree_manager.py \
  tests/test_prefect_grace_cli_worktree_manager.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run regression tests:

```bash
pytest -q \
  tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_cli_scope_guard.py \
  tests/test_prefect_grace_synthetic_edge_matrix.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform/worktree_manager.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-WORKTREE-MANAGER-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke in a temporary git repository, not in `/opt/astro-project`:

```bash
tmp_repo="$(mktemp -d)"
git -C "$tmp_repo" init
git -C "$tmp_repo" config user.email test@example.invalid
git -C "$tmp_repo" config user.name "Test User"
printf 'base\n' > "$tmp_repo/README.md"
git -C "$tmp_repo" add README.md
git -C "$tmp_repo" commit -m init
python3 -m prefect_grace.cli worktree-create \
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
- JSON output for CLI create/status/cleanup smoke;
- proof tests used temporary git repositories;
- `git worktree list --porcelain` sample from temp repo;
- confirmation no live agents, Prefect deployments, Docker containers, product backend/frontend services, remote push, or merge were started;
- diff scope limited to `Allowed Write Scope`.

## Escalation Triggers

- implementation needs to modify `feature_pipeline.py`, `codex_launcher.py`, or `backlog_controller.py`;
- implementation needs to push, merge, or contact a remote;
- tests need to use `/opt/astro-project` as the git test repository;
- cleanup requires deleting paths outside configured `worktree_root`;
- worktree manager needs to mutate packet registry/state;
- Scope Guard integration requires changing `scope_guard.py`.

## Reviewer Gate

Reviewer must reject if:

- tests mutate the main repository workspace;
- cleanup can delete outside `worktree_root`;
- branch names can escape the manager namespace;
- changed-file extraction misses untracked or unstaged files;
- CLI JSON output is not machine-readable;
- any git command uses shell interpolation;
- any remote push/merge operation appears;
- any file outside `Allowed Write Scope` is modified.

---

## Execution Results

**Status**: ✅ COMPLETE  
**Execution Date**: 2026-05-26  
**Attempt**: 0001

### Implementation Summary

All requirements successfully implemented:

- ✅ `WorktreeManager` class with full API surface
- ✅ Deterministic branch naming with sanitization
- ✅ Git command wrapper with safety constraints
- ✅ Changed-file extraction (committed, staged, unstaged, untracked)
- ✅ CLI commands: `worktree-create`, `worktree-status`, `worktree-cleanup`
- ✅ Scope Guard compatibility verified
- ✅ All tests use temporary git repositories (no main workspace mutation)
- ✅ Cleanup safety: refuses paths outside `worktree_root`

### Verification Results

**Targeted Tests**: 28 passed in 1.89s  
**Regression Tests**: 32 passed in 1.56s  
**Static Checks**: All passed  
**CLI Smoke Test**: Verified in temporary repository

### Evidence Location

`/opt/astro-project/prefect_grace/packets/FEAT-GRACE-WORKTREE-MANAGER-MVP/EVIDENCE/attempt-0001/`

- `evidence_manifest.json` - Complete verification command outputs
- `IMPLEMENTATION_SUMMARY.md` - Detailed implementation report
- All test outputs and CLI smoke test results captured

### Changed Files

- `prefect_grace/platform/worktree_manager.py` (new, 486 lines)
- `prefect_grace/cli.py` (extended with worktree commands)
- `tests/test_prefect_grace_worktree_manager.py` (new, 28 tests)
- `tests/test_prefect_grace_cli_worktree_manager.py` (new, CLI tests)
- `tests/test_prefect_grace_cli_contracts.py` (extended)

### Safety Confirmation

- ✅ No main repository workspace mutation
- ✅ No live agents or Prefect deployments started
- ✅ No remote push or merge operations
- ✅ No product backend/frontend files modified
- ✅ All changes within `Allowed Write Scope`
- ✅ Cleanup constrained to `worktree_root`
- ✅ No shell interpolation in git commands
