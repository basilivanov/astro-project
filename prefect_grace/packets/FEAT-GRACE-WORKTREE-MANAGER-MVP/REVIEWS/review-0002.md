# Review 0002 — FEAT-GRACE-WORKTREE-MANAGER-MVP

status: rework_required
reviewer: codex
reviewed-at: 2026-05-26

## Verdict

Rework required.

The second attempt implements the actual Worktree Manager surface and most verification is green, but one safety blocker remains: worktree creation can escape `worktree_root` when `packet_id` is an absolute path.

This violates the packet's core invariant:

```text
all paths must stay inside configured worktree_root
```

## What Passed

Targeted tests:

```text
34 passed in 4.40s
```

Regression tests:

```text
43 passed in 4.33s
```

GRACE lint:

```text
prefect_grace/platform/worktree_manager.py PASS
```

Packet validation:

```text
packet_ok = True
source_hash = sha256:f9aec9cf47dc444104b6e5bcc7bba7ed118048d23b290cc27a216c2e85b780bd
```

CLI create smoke in temp repo:

```text
create_ok = True
branch = agent/test-project/FEAT-TEST-W01-PACKET/attempt-0001
```

## Blocker

### 1. `create_packet_worktree` can create outside `worktree_root`

The branch name is sanitized, but the filesystem path is built from the raw `packet_id`:

```python
worktree_path = self.worktree_root / f"{packet_id}-attempt-{attempt:04d}"
```

Reference:

- `prefect_grace/platform/worktree_manager.py:208`
- `prefect_grace/platform/worktree_manager.py:215`

If `packet_id` is absolute, `Path` join discards `worktree_root` and creates the worktree outside the configured root.

Reviewer reproduction in a temporary git repository:

```text
packet_id = /tmp/.../outside-absolute
created = /tmp/.../outside-absolute-attempt-0001
worktree_root = /tmp/.../worktrees
under_root = no
outside_exists = True
```

The CLI exposes `--packet-id` directly:

- `prefect_grace/cli.py:1391`
- `prefect_grace/cli.py:1401`
- `prefect_grace/cli.py:1410`

So this is reachable through operator input, not only internal API misuse.

Required fix:

1. Derive the worktree directory name from a sanitized path-safe packet slug, not raw `packet_id`.
2. Before `git worktree add`, resolve the target path and assert it is inside `worktree_root`.
3. Reject absolute packet IDs, `..`, path separators, empty slugs, and any value that resolves outside root.
4. Add tests proving `create_packet_worktree(packet_id="/tmp/evil", ...)` and traversal-style IDs fail before any worktree is created.
5. Keep cleanup safety, but do not rely on cleanup to catch a create-time escape.

## Major Notes

### Cleanup safety test is too weak

The current test named `test_cleanup_refuses_path_outside_worktree_root` only creates a normal packet and asserts the normal path is inside root:

- `tests/test_prefect_grace_worktree_manager.py:371`
- `tests/test_prefect_grace_worktree_manager.py:388`

It does not attempt an outside-root path. After fixing create-time validation, add a negative test that fails on the current implementation.

### Separate Scope Guard from Worktree commit

The workspace still contains accepted but uncommitted Scope Guard changes. Worktree acceptance should be committed separately or after Scope Guard is committed, otherwise raw git diff will mix two packets.

## Required Rework

1. Add a path-safe worktree directory slug helper.
2. Use that slug in `create_packet_worktree`, `status`, and `cleanup_worktree`.
3. Add create-time `worktree_root` containment validation.
4. Add negative tests for absolute/traversal packet IDs.
5. Re-run targeted tests, regression tests, GRACE lint, packet validation, and CLI smoke.

## Acceptance Criteria For Next Review

- Absolute or traversal `packet_id` cannot create a worktree outside `worktree_root`.
- Negative tests fail on the old implementation and pass after the fix.
- Normal worktree create/status/cleanup behavior remains green.
- No tests mutate `/opt/astro-project`.
- No remote push, merge, live agent, Prefect deployment, Docker container, or product service is started.
