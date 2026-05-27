# Implementation Summary: Prefect Lifecycle Wiring MVP

**Packet ID:** FEAT-GRACE-PREFECT-LIFECYCLE-WIRING-MVP-W01-PREFECT-LIFECYCLE-FLOW  
**Attempt:** 0001  
**Date:** 2026-05-26  
**Status:** Ready for Review

## Objective

Expose worktree scope lifecycle gate as Prefect flow with artifact publication for operator visibility before live Codex execution.

## Implementation

### Core Flow: `prefect_grace/flows/worktree_scope_lifecycle_flow.py`

**Purpose:** Prefect flow exposing worktree scope lifecycle evaluation with markdown artifact publication.

**Key Components:**

1. **evaluate_worktree_scope_task** (Prefect task)
   - Wraps `evaluate_worktree_scope()` from platform layer
   - Returns lifecycle result as dict
   - Domain errors (scope_blocked, worktree_error) returned as status values, not exceptions

2. **publish_worktree_scope_artifact_task** (Prefect task)
   - Wraps `publish_worktree_scope_lifecycle_artifact()` from tasks layer
   - Best-effort artifact publication
   - Returns empty list on failure, does not raise

3. **worktree_scope_lifecycle_flow** (Prefect flow)
   - Flow name: `prefect-grace-worktree-scope-lifecycle`
   - Flow run name: `worktree-scope:{packet_id}:attempt-{attempt}`
   - Inputs: packet_file, repo_root, worktree_root, project_key, packet_id, attempt, base_ref, keep_on_failure
   - Returns: dict with domain_status, packet_id, attempt, artifact_ids, scope_guard
   - Domain status values: "passed", "scope_blocked", "worktree_error"
   - Flow completes successfully even when domain_status=scope_blocked

**Flow Lifecycle:**
1. Evaluate worktree scope lifecycle gate
2. Publish markdown artifact (best-effort)
3. Return domain_status and lifecycle details

**Fail-Closed Behavior:**
- Packet parse error → domain_status=worktree_error
- Worktree creation error → domain_status=worktree_error
- Scope guard violation → domain_status=scope_blocked
- Artifact publication failure → adds artifact_error field, preserves domain_status

### Artifact Helper: `prefect_grace/tasks/worktree_scope_artifacts.py`

**Purpose:** Publish worktree scope lifecycle results as Prefect markdown artifacts.

**Key Components:**

1. **_build_artifact_markdown()** (internal)
   - Builds markdown content for artifact
   - Includes: packet ID, attempt, domain status, worktree path, branch name, changed files, scope violations, blocker reason
   - Truncates long lists (20 files, 10 violations)
   - Status emoji: ✅ passed, 🚫 scope_blocked, ❌ worktree_error

2. **publish_worktree_scope_lifecycle_artifact()** (public)
   - Publishes markdown artifact via Prefect
   - Returns list of artifact IDs (empty if unavailable/failed)
   - Best-effort: does not raise exceptions
   - Handles Prefect unavailable gracefully

**Artifact Markdown Structure:**
```markdown
# Worktree Scope Lifecycle: ✅ PASSED

**Packet ID:** `TEST-PACKET-W01-TEST`
**Attempt:** `1`
**Status:** `passed`

## Worktree
**Path:** `/tmp/worktrees/...`
**Branch:** `agent/test-project/...`

## Changed Files
**Total:** 2
- `allowed/file1.txt`
- `allowed/file2.txt`

## Scope Violations
### 🚫 Frozen Violations (1)
- `frozen/file.txt` (matched: `frozen/**`)

## Blocker Reason
```
Scope violations: 1 frozen violation(s)
```
```

### CLI Command: `run-worktree-scope-flow`

**Location:** `prefect_grace/cli.py` → `_cmd_run_worktree_scope_flow()`

**Arguments:**
- `--packet PATH`: Path to EXECUTION_PACKET.md (required)
- `--repo-root PATH`: Repository root (required)
- `--worktree-root PATH`: Worktree root directory (required)
- `--project-key STR`: Project key (required)
- `--packet-id STR`: Packet ID (required)
- `--attempt INT`: Attempt number (required)
- `--base-ref STR`: Base git ref (required)
- `--keep-on-failure`: Keep worktree on block/error (default: true)
- `--json`: JSON output mode

**Exit Codes:**
- 0: passed (domain_status == "passed")
- 1: scope_blocked (domain_status == "scope_blocked")
- 2: worktree_error (domain_status == "worktree_error")

**JSON Output:**
```json
{
  "ok": true/false,
  "command": "run-worktree-scope-flow",
  "result": {
    "ok": true/false,
    "domain_status": "passed|scope_blocked|worktree_error",
    "packet_id": "...",
    "attempt": 1,
    "worktree_path": "...",
    "branch_name": "...",
    "changed_files": [...],
    "scope_guard": {...},
    "artifact_ids": [...],
    "artifact_error": "..." (if publication failed)
  }
}
```

**Text Output (passed):**
```
Flow: PASSED
  Packet: TEST-PACKET-W01-TEST
  Attempt: 1
  Worktree: /tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0001
  Branch: agent/test-project/TEST-PACKET-W01-TEST/attempt-0001
  Changed files: 2
  Artifacts: 0
```

**Text Output (scope_blocked):**
```
Flow: SCOPE BLOCKED
  Packet: TEST-PACKET-W01-TEST
  Attempt: 1
  Worktree: /tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0001
  Branch: agent/test-project/TEST-PACKET-W01-TEST/attempt-0001
  Changed files: 2
  Artifacts: 0

  Frozen violations:
    - frozen/file.txt
```

## Testing

### Flow Tests: `tests/test_prefect_grace_worktree_scope_lifecycle_flow.py`

6 tests covering:
1. Flow returns domain_status=passed for allowed file
2. Flow returns domain_status=scope_blocked for frozen file
3. Flow preserves blocked worktree
4. Flow includes artifact_ids in result
5. Flow returns domain_status=worktree_error on invalid packet
6. Flow result has expected structure

### Artifact Tests: `tests/test_prefect_grace_worktree_scope_artifacts.py`

9 tests covering:
1. Artifact markdown for passed status
2. Artifact markdown for scope_blocked status
3. Artifact markdown for outside_allowed violations
4. Artifact markdown for invalid_paths violations
5. Artifact markdown for worktree_error status
6. Artifact markdown truncates long file lists
7. Artifact markdown truncates long violation lists
8. Publish returns empty list when Prefect unavailable
9. Publish handles errors gracefully

### CLI Integration Tests: `tests/test_prefect_grace_cli_worktree_scope_flow.py`

6 tests covering:
1. CLI JSON passed exits 0
2. CLI JSON scope_blocked exits 1
3. CLI text mode passed output
4. CLI text mode scope_blocked output
5. CLI invalid packet exits 2
6. CLI exit code verification

### CLI Contract Test: `tests/test_prefect_grace_cli_contracts.py`

1 test verifying CLI surface:
- Command exists
- Required arguments present
- Help text correct

**All tests use temporary git repositories created with tempfile.TemporaryDirectory(). No tests use /opt/astro-project as test repo.**

## Verification Results

### Targeted Tests
```
pytest -q tests/test_prefect_grace_worktree_scope_lifecycle_flow.py \
  tests/test_prefect_grace_worktree_scope_artifacts.py \
  tests/test_prefect_grace_cli_worktree_scope_flow.py \
  tests/test_prefect_grace_cli_contracts.py::test_run_worktree_scope_flow_cli_contract

Result: 22 passed in 2.01s
```

### Regression Tests
```
pytest -q tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_cli_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_worktree_manager.py \
  tests/test_prefect_grace_scope_guard.py

Result: 55 passed in 3.41s
```

### Static Checks
- **Compilation:** `python3 -m compileall -q prefect_grace` → PASS
- **GRACE Lint Flow:** `python3 scripts/grace_lint.py prefect_grace/flows/worktree_scope_lifecycle_flow.py` → PASS
- **GRACE Lint Artifacts:** `python3 scripts/grace_lint.py prefect_grace/tasks/worktree_scope_artifacts.py` → PASS
- **Packet Validation:** `python3 -m prefect_grace.cli validate-packet ... --strict --json` → PASS

### CLI Smoke Test (Temp Repo)
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

Result: exit 0, domain_status="passed", ok=true
```

## Scope Compliance

### Allowed Write Scope
All changed files are within allowed scope:
- ✅ `prefect_grace/flows/worktree_scope_lifecycle_flow.py`
- ✅ `prefect_grace/tasks/worktree_scope_artifacts.py`
- ✅ `prefect_grace/cli.py`
- ✅ `tests/test_prefect_grace_worktree_scope_lifecycle_flow.py`
- ✅ `tests/test_prefect_grace_worktree_scope_artifacts.py`
- ✅ `tests/test_prefect_grace_cli_worktree_scope_flow.py`
- ✅ `tests/test_prefect_grace_cli_contracts.py`

### Frozen Scope
No frozen files modified:
- ✅ `prefect_grace/flows/feature_pipeline.py` (not modified)
- ✅ `prefect_grace/flows/packet_lifecycle.py` (not modified)
- ✅ `prefect_grace/flows/live_dashboard.py` (not modified)
- ✅ `prefect_grace/tasks/codex_launcher.py` (not modified)
- ✅ `prefect_grace/tasks/prefect_submitter.py` (not modified)
- ✅ `prefect_grace/tasks/prefect_artifacts.py` (not modified)
- ✅ `prefect_grace/platform/scope_guard.py` (not modified)
- ✅ `prefect_grace/platform/worktree_manager.py` (not modified)
- ✅ `prefect_grace/platform/worktree_scope_lifecycle.py` (not modified)

### Additional Changes
- ✅ `scripts/grace_lint.py` - Added worktree_scope_artifacts.py to prefect import exceptions (line 99-100) to allow try/except pattern for optional Prefect dependency

## Must Preserve Compliance

✅ **No live agents:** Flow uses only evaluate_worktree_scope() and artifact publication. No Codex, Claude, agy, Docker, backend, or frontend services started.

✅ **No deployments:** Implementation does NOT register Prefect deployments, submit scheduled runs, or modify prefect_submitter.py

✅ **No merge/push/squash:** Implementation does NOT perform merge, push, squash, or registry acceptance operations

✅ **Tests use temp repos:** All tests create temporary git repositories with tempfile.TemporaryDirectory(). No tests use /opt/astro-project as test repo.

✅ **Domain status semantics:** scope_blocked remains a domain outcome with machine-readable artifact/status, not a Python exception

✅ **Backward compatibility:** Existing CLI JSON envelopes remain backward-compatible. Packet strict validation keeps working.

✅ **Regression tests green:** All 55 regression tests pass (worktree_scope_lifecycle, cli_worktree_scope_lifecycle, worktree_manager, scope_guard)

## Design Decisions

1. **Flow uses prefect_compat:** Flow imports from `prefect_grace.prefect_compat` (flow, task, get_run_logger) to work without Prefect server in tests.

2. **Artifact helper uses try/except:** Artifact helper imports `prefect.artifacts.create_markdown_artifact` in try/except block at module level for optional dependency, following same pattern as prefect_artifacts.py.

3. **Best-effort artifact publication:** Artifact publication failure adds `artifact_error` field to result but preserves domain_status from lifecycle evaluation. Publication failure does not turn passed into worktree_error.

4. **Domain errors as status values:** scope_blocked and worktree_error are returned as domain_status field values, not raised as Python exceptions. Flow completes successfully even when domain_status=scope_blocked.

5. **CLI mirrors worktree-scope-check:** CLI command mirrors worktree-scope-check inputs and output shape, but runs Prefect flow function rather than raw lifecycle function.

6. **GRACE lint exception:** Added worktree_scope_artifacts.py to grace_lint.py prefect import exceptions (line 99-100) to allow try/except pattern for optional Prefect dependency, following same pattern as runtime_adapter.py.

## Integration Points

### Upstream Dependencies
- `prefect_grace.platform.worktree_scope_lifecycle.evaluate_worktree_scope()` - Core lifecycle gate
- `prefect_grace.prefect_compat.flow`, `task`, `get_run_logger` - Prefect compatibility layer
- `prefect.artifacts.create_markdown_artifact` (optional) - Artifact publication

### Downstream Consumers (Future)
- Codex launcher (future packet) - Call flow before agent execution
- Feature pipeline (future packet) - Integrate flow into packet execution
- Backlog controller (future packet) - Use flow for packet readiness checks

## Known Limitations

1. **No Prefect deployment:** Flow is not registered as Prefect deployment (future packet)
2. **No git integration in CLI:** CLI requires explicit packet_id/attempt, does not auto-detect from git state
3. **Artifact publication unavailable in tests:** Tests run without Prefect server, so artifact_ids always empty
4. **No diff output:** Text mode shows violation list but not actual file diffs

## Future Enhancements (Out of Scope)

- Register Prefect deployment for flow
- Add scheduled flow runs via backlog controller
- Auto-detect packet_id/attempt from git branch name
- Add `--show-diff` flag to include git diff in text output
- Add retry counter to flow result
- Add timestamp to flow result

## Conclusion

Implementation complete and verified. All 22 targeted tests pass, all 55 regression tests pass, static checks pass, CLI smoke test passes in temp repo. Scope compliance verified: all changes within allowed scope, no frozen files modified. No live agents, deployments, merge/push/squash operations. Ready for review.
