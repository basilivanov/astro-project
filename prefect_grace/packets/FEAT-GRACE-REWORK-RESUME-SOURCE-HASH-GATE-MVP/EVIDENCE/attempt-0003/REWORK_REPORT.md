# Rework Attempt 0003 - Codex Launcher Integration

## Summary

Integrated rework resume policy enforcement into codex_launcher execution path. The launcher now checks `resume_allowed` from registry before allowing session resume, and records execution state after coder success.

## Changes Made

### 1. codex_launcher.py

**Added STATE_ROOT constant:**
```python
STATE_ROOT = Path(__file__).resolve().parents[1] / "state"
```

**Added _check_resume_allowed() function:**
- Checks `resume_allowed` field from PacketRegistryStore
- Returns False if `resume_allowed=False`, blocking resume
- Returns True if `resume_allowed=True` or None (backward compatible)
- Logs warning when resume is blocked
- Fails open on errors (allows resume for backward compatibility)

**Modified launch_codex_for_packet():**
- Calls `_check_resume_allowed()` before session lookup
- Blocks both `feature_role` and `packet_parent` resume strategies when `resume_allowed=False`
- Forces fresh `codex exec` when resume is blocked

**Added execution state recording:**
- After successful coder execution, records:
  - `last_executed_source_hash` (current source hash)
  - `latest_coder_session_id` (thread_id from execution)
- Only records for role="coder" with valid thread_id
- Fails gracefully on errors (logs warning, continues)

### 2. Tests

**Created test_prefect_grace_codex_launcher_resume_gate.py (2 tests):**

1. `test_launch_codex_blocks_resume_when_registry_disallows`
   - Sets up packet with `resume_allowed=False` and parent with thread_id
   - Verifies launcher forces `session_mode="exec"` (not "resume")
   - Verifies `resumed_from_thread_id=None` (parent thread ignored)

2. `test_launch_codex_allows_resume_when_registry_allows`
   - Sets up packet with `resume_allowed=True` and parent with thread_id
   - Verifies launcher uses `session_mode="resume"`
   - Verifies `resumed_from_thread_id` matches parent thread

## Test Results

- New tests: 2 passed, 0 failed
- Target tests: 43 passed, 0 failed
- Regression tests: 23 passed, 0 failed (existing codex_launcher tests)
- **Total: 68 tests passed, 0 failed**

## Blockers Status

- ✅ **Blocker #3** (enum compliance): Resolved in attempt-0001
- ✅ **Blocker #2** (session validation): Resolved in attempt-0001
- ✅ **Blocker #1** (orchestration integration): **Resolved**
  - ✅ Registry integration (attempt-0002)
  - ✅ Codex launcher enforcement (attempt-0003)

## Design Decisions

1. **Check before session lookup**: `_check_resume_allowed()` is called before `_feature_role_session()` or `_packet_parent_session()`, ensuring resume decision is enforced early
2. **Block all resume strategies**: Both `feature_role` and `packet_parent` are blocked when `resume_allowed=False`
3. **Fail open on errors**: If registry check fails, allow resume (backward compatibility)
4. **STATE_ROOT constant**: Extracted for testability (can be monkeypatched in tests)
5. **Record after success**: Execution state is recorded after successful launch, not before
6. **Coder-only tracking**: Only records state for `role="coder"` (not architect, planner, etc.)

## Runtime Behavior

**When source hash changes:**
1. `BacklogController.sync()` detects hash change
2. Sets `resume_allowed=False`, `resume_block_reason="contract_changed"`
3. Next coder launch: `launch_codex_for_packet()` checks registry
4. Finds `resume_allowed=False`, logs warning
5. Forces `existing_session=None`, ignoring parent thread
6. Launches fresh `codex exec` with new context

**When source hash unchanged:**
1. Registry has `resume_allowed=True` (or None)
2. `launch_codex_for_packet()` checks registry
3. Finds resume allowed, proceeds with normal strategy
4. Uses `packet_parent` or `feature_role` session if available
5. Launches `codex resume` with existing thread

## Feature Pipeline Note

Review-0002 mentioned feature_pipeline integration. However, feature_pipeline delegates coder execution to `launch_codex_for_packet()`, so the enforcement at launcher level is sufficient. The pipeline does not need separate integration.

## Next Steps

Packet is ready for reviewer acceptance. All three blockers are resolved:
- Source hash gate policy implemented and tested
- Registry tracks execution state
- Codex launcher enforces resume decision in live execution path
