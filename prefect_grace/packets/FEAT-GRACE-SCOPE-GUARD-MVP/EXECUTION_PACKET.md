# Execution Packet: GRACE Scope Guard MVP

## Objective

Implement a deterministic Scope Guard for the portable GRACE orchestrator.

The guard must answer one question without LLM calls:

```text
Given a packet contract and a set of changed files, is this change set inside
Allowed Write Scope and outside Frozen Scope?
```

This is a safety gate, not a merge engine. The packet must provide a pure
validator, stable JSON output, and tests for edge cases. It must not start
agents, Prefect deployments, Docker containers, or product services.

The MVP must make scope violations explicit before a reviewer/steward can
accept or merge a packet.

## Slice

- slice_id: `SLICE-GRACE-SCOPE-GUARD-MVP`
- slice_slug: `grace-scope-guard-mvp`
- feature_id: `FEAT-GRACE-SCOPE-GUARD-MVP`
- packet_id: `FEAT-GRACE-SCOPE-GUARD-MVP-W01-SCOPE-GUARD`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP-W01-SYNTHETIC-EDGE-MATRIX`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-SCOPE-GUARD-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_edge_matrix.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_invariants.py`
- `/opt/astro-project/prefect_grace/cli.py`

## Impacted Modules

- `M-GRACE-SCOPE-GUARD`
- `M-GRACE-PACKET-PARSER`
- `M-GRACE-CLI`
- `M-GRACE-SYNTHETIC-EDGE-MATRIX`

## Recommended Role Assignment

- context collector: `Haiku` or equivalent cheap model, optional, only to inspect adjacent CLI/parser patterns.
- coder: `Sonnet high` or `Codex high`; this is deterministic platform code and tests.
- verifier: `Codex medium`; must run targeted tests, CLI positive/negative examples, and GRACE lint.
- reviewer: `Opus` or `Codex xhigh`; reviewer must inspect path-normalization and fail-closed behavior.
- rework policy: fresh context if scope semantics change; light resume only for naming/test-output fixes.

## Required Design Decisions

### 1. Pure Scope Validator

Add a new module:

```text
prefect_grace/platform/scope_guard.py
```

Required public API:

```python
@dataclass(frozen=True)
class ScopeGuardViolation:
    file_path: str
    reason: str
    matched_pattern: str | None = None


@dataclass(frozen=True)
class ScopeGuardResult:
    ok: bool
    changed_files: list[str]
    allowed_files: list[str]
    outside_allowed: list[ScopeGuardViolation]
    frozen_violations: list[ScopeGuardViolation]
    invalid_paths: list[ScopeGuardViolation]


def validate_scope(
    changed_files: list[str],
    allowed_scope: list[str],
    frozen_scope: list[str],
    *,
    repo_root: Path,
) -> ScopeGuardResult:
    ...
```

Rules:

- no LLM calls;
- no Prefect dependency;
- no live agent execution;
- no mutation of registry/state;
- no filesystem existence requirement for changed paths;
- deterministic output ordering;
- fail closed on invalid paths or malformed patterns;
- `Frozen Scope` wins over `Allowed Write Scope`;
- a file outside allowed scope is blocked even when it is not frozen;
- an empty `Allowed Write Scope` blocks all changed files;
- deleted files are still checked by path.

### 2. Path Normalization

The validator must normalize all paths relative to `repo_root`.

It must accept:

- repo-relative paths: `prefect_grace/cli.py`;
- absolute paths under repo root: `/opt/astro-project/prefect_grace/cli.py`;
- `./prefect_grace/cli.py`;
- repeated slashes.

It must reject:

- path traversal escaping repo root, e.g. `../secret`;
- absolute paths outside repo root;
- empty paths;
- paths containing NUL bytes.

Returned paths must be stable repo-relative POSIX-style strings.

### 3. Pattern Semantics

Use deterministic Python matching. Do not invent a complex DSL.

Minimum supported patterns:

- exact file path;
- directory glob: `path/**`;
- file glob: `path/*.py`;
- nested glob: `path/**/*.py`.

`Frozen Scope` patterns must be evaluated before allowed success is accepted.

Examples:

```text
allowed = ["prefect_grace/platform/**"]
frozen = ["prefect_grace/platform/state_store.py"]
changed = ["prefect_grace/platform/scope_guard.py"]       -> ok
changed = ["prefect_grace/platform/state_store.py"]       -> frozen violation
changed = ["backend/app/main.py"]                         -> outside allowed
changed = ["../outside"]                                  -> invalid path
```

### 4. CLI Gate

Add a CLI command:

```bash
python3 -m prefect_grace.cli check-scope \
  --packet prefect_grace/packets/.../EXECUTION_PACKET.md \
  --changed-file prefect_grace/platform/scope_guard.py \
  --json
```

Required CLI inputs:

- `--packet PATH`: strict packet file to read `Allowed Write Scope` and
  `Frozen Scope` from;
- `--changed-file PATH`: repeatable;
- `--changed-files-file PATH`: optional newline-delimited file list;
- `--repo-root PATH`: optional, default current working directory;
- `--json`: stable machine-readable output.

Optional CLI input:

- `--git-diff-ref REF`: collect changed files from `git diff --name-only REF...`.
  This is allowed but must be covered by tests using a temporary git repository
  or mocked subprocess. Do not make this option required for MVP.

CLI behavior:

- exit `0` when `ScopeGuardResult.ok` is true;
- exit `1` when there are violations;
- exit `2` for command/input errors;
- JSON envelope must include `ok`, `changed_files`, `outside_allowed`,
  `frozen_violations`, and `invalid_paths`.

### 5. Synthetic Matrix Hook

Do not rewrite the synthetic matrix in this packet.

Minimum integration:

- add one or two targeted unit tests proving that frozen-scope and
  outside-allowed scenarios can be represented by the new `validate_scope`
  result;
- do not expand the full synthetic matrix dimensions unless this can be done
  without broad changes.

The matrix already has a scope dimension; this packet provides the real
validator that later packets can plug into the matrix/steward path.

### 6. No Merge Steward Yet

This packet must not implement merge, git branch management, worktree cleanup,
or reviewer acceptance routing.

It only creates the deterministic gate that those later pieces can call.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_scope_guard.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_scope_guard.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-SCOPE-GUARD-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
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

- Existing accepted platform tests keep passing.
- Existing CLI JSON envelopes remain backward-compatible.
- Packet strict validation keeps working.
- No live agents or Prefect deployments are started by tests.
- No product backend/frontend files are modified.
- Scope guard does not mutate registry, packet source, or runtime artifacts.
- Frozen scope always wins over allowed scope.

## Required Implementation Shape

### `scope_guard.py`

The module must include GRACE module contracts and function contracts.

Implementation must be small and deterministic:

- dataclasses for result/violations;
- path normalization helper;
- pattern matching helper;
- public `validate_scope(...)`;
- `to_dict()` or equivalent JSON-safe serializer.

Avoid broad abstractions until integration packets need them.

### CLI

The CLI command should use existing parser/CLI style.

It may read packet scopes through existing packet parsing utilities. If the
existing parser cannot expose scopes cleanly, do not rewrite the parser in this
packet; add a small local adapter in the CLI command and document the follow-up.

### Tests

Required test cases:

- exact allowed file passes;
- `path/**` allowed file passes;
- frozen file blocks even when also allowed;
- outside allowed blocks;
- empty allowed scope blocks all changed files;
- path traversal blocks;
- absolute path outside repo blocks;
- absolute path inside repo normalizes and passes;
- deleted/nonexistent changed file is checked by path and can pass;
- deterministic output ordering;
- CLI JSON success exits `0`;
- CLI JSON frozen violation exits `1`;
- CLI text mode prints a concise violation summary;
- CLI command error exits `2` for missing packet or missing changed files.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_cli_scope_guard.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run regression tests:

```bash
pytest -q \
  tests/test_prefect_grace_synthetic_edge_matrix.py \
  tests/test_prefect_grace_rework_resume_policy.py \
  tests/test_prefect_grace_state_store_resume.py \
  tests/test_prefect_grace_backlog_controller_resume_integration.py \
  tests/test_prefect_grace_codex_launcher_resume_gate.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform/scope_guard.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-SCOPE-GUARD-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke:

```bash
python3 -m prefect_grace.cli check-scope \
  --packet prefect_grace/packets/FEAT-GRACE-SCOPE-GUARD-MVP/EXECUTION_PACKET.md \
  --changed-file prefect_grace/platform/scope_guard.py \
  --json
```

Run CLI negative smoke:

```bash
python3 -m prefect_grace.cli check-scope \
  --packet prefect_grace/packets/FEAT-GRACE-SCOPE-GUARD-MVP/EXECUTION_PACKET.md \
  --changed-file backend/app/main.py \
  --json
```

Expected: positive smoke exits `0`; negative smoke exits `1` with
`outside_allowed` or `frozen_violations` populated.

## Expected Evidence

- command outputs for all verification commands;
- JSON output for positive CLI smoke;
- JSON output for negative CLI smoke;
- one text-mode violation example;
- confirmation that no live agents, Prefect deployments, Docker containers, or
  product services started;
- diff scope limited to `Allowed Write Scope`.

## Escalation Triggers

- implementation needs to modify packet parser internals;
- implementation needs to modify `feature_pipeline.py` or `codex_launcher.py`;
- tests require live Prefect, Docker, Codex, Claude, or agy;
- pattern matching needs a custom DSL beyond Python glob semantics;
- product backend/frontend files appear necessary;
- scope guard needs to mutate registry or packet state.

## Reviewer Gate

Reviewer must reject if:

- frozen scope does not override allowed scope;
- invalid paths are ignored instead of blocking;
- CLI exits `0` on any violation;
- JSON output is unstable or not machine-readable;
- tests rely on real git state from the working repository;
- any file outside `Allowed Write Scope` is modified.
