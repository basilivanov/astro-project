# Implementation Summary: Worktree Scope Lifecycle Gate

**Packet ID:** FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP-W01-LIFECYCLE-GATE  
**Attempt:** 0001  
**Date:** 2026-05-26  
**Status:** Ready for Review

## Objective

Implement lifecycle gate connecting WorktreeManager + ScopeGuard to block packets with scope violations before verifier/reviewer runs.

## Implementation

### Core Module: `prefect_grace/platform/worktree_scope_lifecycle.py`

**Purpose:** Lifecycle gate that evaluates packet worktree against scope guard before execution proceeds.

**Key Components:**

1. **WorktreeScopeLifecycleResult** (dataclass, frozen)
   - Immutable result object with pass/block status
   - Contains: packet_id, attempt, worktree_path, branch_name, changed_files, scope_guard, status, blocker_reason
   - Status values: "passed", "scope_blocked", "worktree_error"
   - Provides `to_dict()` for JSON serialization

2. **evaluate_worktree_scope()** (main function)
   - Inputs: packet_file, repo_root, worktree_root, project_key, packet_id, attempt, base_ref, keep_on_failure
   - Returns: WorktreeScopeLifecycleResult
   - Lifecycle steps:
     1. Parse packet contract (allowed_write_scope, frozen_scope)
     2. Create or resolve packet worktree
     3. Collect changed files from worktree
     4. Run scope guard validation
     5. Return passed/scope_blocked/worktree_error

**Fail-Closed Behavior:**
- Packet parse error → worktree_error
- Worktree creation error → worktree_error
- Changed file extraction error → worktree_error
- Scope guard violation → scope_blocked
- Any changed file outside allowed → scope_blocked
- Any changed file frozen → scope_blocked

**Worktree Preservation:**
- scope_blocked → keep worktree (default)
- worktree_error → keep worktree if it exists (default)
- passed → may cleanup if keep_on_failure=False

**Critical Fix:** Added worktree existence check before creation to support re-evaluation:
```python
status = manager.status(packet_id=packet_id, attempt=attempt)
if status.exists:
    # Reuse existing worktree
    context = WorktreeContext(...)
else:
    # Create new worktree
    context = manager.create_packet_worktree(...)
```

### CLI Command: `worktree-scope-check`

**Location:** `prefect_grace/cli.py` → `_cmd_worktree_scope_check()`

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
- 0: passed (result.status == "passed")
- 1: scope_blocked (result.status == "scope_blocked")
- 2: worktree_error (result.status == "worktree_error")

**JSON Output:**
```json
{
  "ok": true/false,
  "command": "worktree-scope-check",
  "result": {
    "ok": true/false,
    "packet_id": "...",
    "attempt": 1,
    "worktree_path": "...",
    "branch_name": "...",
    "changed_files": [...],
    "scope_guard": {...},
    "status": "passed|scope_blocked|worktree_error",
    "blocker_reason": "..."
  }
}
```

**Text Output (passed):**
```
Lifecycle: PASSED
  Packet: TEST-PACKET-W01-TEST
  Attempt: 1
  Worktree: /tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0001
  Branch: astro-project/packet/TEST-PACKET-W01-TEST/attempt-0001
  Changed files: 2
```

**Text Output (scope_blocked):**
```
Lifecycle: SCOPE BLOCKED
  Packet: TEST-PACKET-W01-TEST
  Attempt: 1
  Worktree: /tmp/worktrees/TEST-PACKET-W01-TEST-attempt-0001
  Branch: astro-project/packet/TEST-PACKET-W01-TEST/attempt-0001
  Blocker: Scope violations: 1 frozen violation(s)
  Changed files: 2

  Frozen violations:
    - frozen/file.txt
```

## Testing

### Unit Tests: `tests/test_prefect_grace_worktree_scope_lifecycle.py`

7 tests covering:
1. Lifecycle passes when changed file is allowed
2. Lifecycle blocks when changed file is frozen
3. Lifecycle blocks when changed file is outside allowed
4. Lifecycle preserves blocked worktree by default
5. Lifecycle output includes changed files and scope details
6. Lifecycle returns error on invalid packet path
7. Lifecycle to_dict serialization

**Critical Fix:** Removed leading slashes from scope patterns in test fixtures:
```markdown
## Allowed Write Scope
- allowed/file.txt
- allowed/**

## Frozen Scope
- frozen/file.txt
- frozen/**
```

### CLI Integration Tests: `tests/test_prefect_grace_cli_worktree_scope_lifecycle.py`

6 tests covering:
1. JSON success output (exit 0)
2. JSON scope violation output (exit 1)
3. Text mode passed output
4. Text mode blocked output
5. Invalid packet handling (exit 2)
6. Exit code verification

### CLI Contract Test: `tests/test_prefect_grace_cli_contracts.py`

1 test verifying CLI surface:
- Command exists
- Required arguments present
- Help text correct

## Verification Results

### Targeted Tests
```
pytest -xvs tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_cli_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_cli_contracts.py::test_worktree_scope_check_cli_contract

Result: 14 passed in 2.31s
```

### Regression Tests
```
pytest -q tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_worktree_manager.py \
  tests/test_prefect_grace_packet_parser.py \
  tests/test_prefect_grace_cli_contracts.py

Result: 72 passed in 7.24s
```

### Static Checks
- **Compilation:** `python3 -m compileall -q prefect_grace` → PASS
- **GRACE Lint:** `python3 scripts/grace_lint.py prefect_grace/platform/worktree_scope_lifecycle.py` → PASS
- **Packet Validation:** `python3 -m prefect_grace.cli validate-packet ... --strict --json` → PASS

### CLI Smoke Test
```bash
python3 -m prefect_grace.cli worktree-scope-check \
  --packet prefect_grace/packets/FEAT-GRACE-WORKTREE-SCOPE-LIFECYCLE-MVP/EXECUTION_PACKET.md \
  --repo-root /opt/astro-project \
  --worktree-root /tmp/test-worktrees \
  --project-key astro-project \
  --packet-id TEST-PACKET-W01-TEST \
  --attempt 1 \
  --base-ref HEAD \
  --json

Result: exit 0, status="passed", ok=true
```

## Scope Compliance

### Allowed Write Scope
All changed files are within allowed scope:
- ✅ `prefect_grace/platform/worktree_scope_lifecycle.py`
- ✅ `prefect_grace/cli.py`
- ✅ `tests/test_prefect_grace_worktree_scope_lifecycle.py`
- ✅ `tests/test_prefect_grace_cli_worktree_scope_lifecycle.py`
- ✅ `tests/test_prefect_grace_cli_contracts.py`

### Frozen Scope
No frozen files modified:
- ✅ `prefect_grace/platform/scope_guard.py` (not modified)
- ✅ `prefect_grace/platform/worktree_manager.py` (not modified)
- ✅ `prefect_grace/flows/feature_pipeline.py` (not modified)
- ✅ `prefect_grace/tasks/codex_launcher.py` (not modified)

## Must Preserve Compliance

✅ **Fail-closed behavior:** All error paths return worktree_error or scope_blocked  
✅ **Worktree preservation:** Blocked worktrees preserved by default for inspection  
✅ **No merge/push/squash:** Implementation does NOT perform merge, push, squash, or registry acceptance  
✅ **No live agents:** Pure Python implementation with no LLM calls or live agents  
✅ **Exit codes:** 0=passed, 1=scope_blocked, 2=error  
✅ **JSON envelope:** Follows existing CLI pattern with `_json_envelope()` and `_print_json()`  
✅ **GRACE contracts:** All functions have MODULE_CONTRACT, FUNCTION_CONTRACT, MODULE_MAP  

## Design Decisions

1. **Worktree Reuse Pattern:** Added existence check before creation to support re-evaluation scenarios where the same packet/attempt is checked multiple times.

2. **Fail-Closed on All Errors:** Any packet parse, worktree, or scope error returns worktree_error status with descriptive blocker_reason.

3. **Frozen Wins Over Allowed:** Scope guard checks frozen scope first, so frozen violations block even if file is in allowed scope.

4. **Preserve by Default:** keep_on_failure=True by default to preserve blocked worktrees for operator inspection.

5. **Immutable Results:** WorktreeScopeLifecycleResult is frozen dataclass to prevent accidental mutation.

6. **Text Mode Operator UX:** Concise text output with clear lifecycle status and top 5 violations for quick operator triage.

## Integration Points

### Upstream Dependencies
- `prefect_grace.platform.packet_parser.parse_packet_markdown()` - Parse packet contract
- `prefect_grace.platform.scope_guard.validate_scope()` - Validate changed files
- `prefect_grace.platform.worktree_manager.WorktreeManager` - Manage worktrees

### Downstream Consumers (Future)
- Codex launcher (future packet) - Call evaluate_worktree_scope() before agent execution
- Feature pipeline (future packet) - Integrate lifecycle gate into packet execution flow
- Backlog controller (future packet) - Use lifecycle gate for packet readiness checks

## Known Limitations

1. **No git integration in CLI:** CLI requires explicit packet_id/attempt, does not auto-detect from git state
2. **No cleanup on passed:** keep_on_failure=False not tested in CLI (future enhancement)
3. **No worktree list command:** Operator must manually inspect worktree_root to find blocked worktrees
4. **No diff output:** Text mode shows violation list but not actual file diffs

## Future Enhancements (Out of Scope)

- Auto-detect packet_id/attempt from git branch name
- Add `--cleanup-on-passed` flag to CLI
- Add `worktree-list` command to show all packet worktrees
- Add `--show-diff` flag to include git diff in text output
- Add retry counter to WorktreeScopeLifecycleResult
- Add timestamp to WorktreeScopeLifecycleResult

## Conclusion

Implementation complete and verified. All 14 targeted tests pass, all 72 regression tests pass, static checks pass, CLI smoke test passes. Scope compliance verified: all changes within allowed scope, no frozen files modified. Ready for review.
