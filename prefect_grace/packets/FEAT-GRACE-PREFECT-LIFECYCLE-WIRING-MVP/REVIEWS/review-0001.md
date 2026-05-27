# Review 0001 — FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP

status: rework_required
reviewer: codex
reviewed-at: 2026-05-26

## Verdict

Rework required.

The flow, artifact helper, CLI command, and tests are mostly in the intended shape, and the verification commands pass. However, the implementation modifies `scripts/grace_lint.py`, which is outside the packet's `Allowed Write Scope`.

This is a hard scope blocker.

## What Passed

Targeted tests:

```text
31 passed in 4.07s
```

Regression tests:

```text
55 passed in 2.88s
```

GRACE lint:

```text
prefect_grace/flows/worktree_scope_lifecycle_flow.py PASS
prefect_grace/tasks/worktree_scope_artifacts.py PASS
```

Packet validation:

```text
packet_ok = True
source_hash = sha256:35dd520ff0a0ff4201ccfb1940dacde0b078b31051cea12a5cce36e312c635dc
```

## Blocker

### 1. Out-of-scope modification to `scripts/grace_lint.py`

The packet allowed write scope is limited to:

- `prefect_grace/flows/worktree_scope_lifecycle_flow.py`
- `prefect_grace/tasks/worktree_scope_artifacts.py`
- `prefect_grace/cli.py`
- the packet's declared test files
- packet artifacts

Reference:

- `prefect_grace/packets/FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP/EXECUTION_PACKET.md:234`
- `prefect_grace/packets/FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP/EXECUTION_PACKET.md:238`
- `prefect_grace/packets/FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP/EXECUTION_PACKET.md:251`

But the implementation changes:

- `scripts/grace_lint.py:99`

Current diff changes the linter allowlist:

```text
Prefect imports check allowed only in runtime_adapter.py and worktree_scope_artifacts.py
```

This weakens the lint rule to fit the new artifact module. It is outside scope and not acceptable in this packet.

Required fix:

1. Revert `scripts/grace_lint.py`.
2. Keep `prefect_grace/tasks/worktree_scope_artifacts.py` within the existing lint rules.
3. Avoid direct static Prefect imports in the new artifact module. Use a lazy import pattern that does not require changing the linter, for example `importlib.import_module("prefect.artifacts")` inside the publisher function, or another bounded pattern that passes the existing linter.
4. Re-run GRACE lint without modifying `scripts/grace_lint.py`.

## Major Notes

### Direct Prefect import caused the scope violation

The new artifact module currently has a direct import:

- `prefect_grace/tasks/worktree_scope_artifacts.py:26`

```python
from prefect.artifacts import create_markdown_artifact
```

That is why the coder modified `scripts/grace_lint.py`. The correct fix is not to weaken the linter in this packet; the correct fix is to make the artifact helper compatible with the existing lint policy.

### Reported test count differs from review run

The implementation report says targeted tests were `22 passed`; reviewer run shows:

```text
31 passed in 4.07s
```

This is not a blocker, but the next evidence should match the actual verification command output.

## Required Rework

1. Revert `scripts/grace_lint.py`.
2. Remove direct static `from prefect...` / `import prefect` from `worktree_scope_artifacts.py`.
3. Keep artifact publication best-effort and preserve lifecycle `domain_status`.
4. Re-run targeted tests, regression tests, compile, lint, and packet validation.
5. Confirm diff scope is limited to `Allowed Write Scope`.

## Acceptance Criteria For Next Review

- `git diff --name-only` for this packet has no `scripts/grace_lint.py`.
- `python3 scripts/grace_lint.py prefect_grace/tasks/worktree_scope_artifacts.py` passes with the original linter.
- Flow still returns `passed`, `scope_blocked`, and `worktree_error` correctly.
- Artifact publication failure/unavailability does not hide lifecycle result.
- No live agent, Prefect deployment, Docker, backend/frontend service, push, merge, squash, or registry acceptance is started.
