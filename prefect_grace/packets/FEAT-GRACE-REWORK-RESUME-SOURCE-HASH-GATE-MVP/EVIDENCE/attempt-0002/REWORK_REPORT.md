# Rework Attempt 0002 - Registry Integration

## Summary

Integrated rework resume policy with state_store registry and backlog_controller sync operation. Registry now tracks source hash changes and automatically updates resume state.

## Changes Made

### 1. state_store.py
- Modified `upsert_packet()` to preserve existing resume state fields when updating
- Added `update_resume_state()` method to update resume decision fields:
  - source_hash
  - last_executed_source_hash
  - latest_coder_session_id
  - resume_allowed
  - resume_block_reason
  - recommended_rework_mode

### 2. backlog_controller.py
- Updated sync logic to call `update_resume_state()` when source hash changes
- Integrated for both "accepted" and "blocked" status transitions
- Sets resume_allowed=False, resume_block_reason="contract_changed", recommended_rework_mode="bounded_fresh" when hash changes

### 3. Tests
- Created `test_prefect_grace_state_store_resume.py` (6 tests)
  - Test upsert preserves resume state
  - Test update_resume_state adds/updates fields
  - Test partial updates
  - Test error handling
  - Test backward compatibility
  
- Created `test_prefect_grace_backlog_controller_resume_integration.py` (3 tests)
  - Test sync updates resume state on hash change (accepted packets)
  - Test sync updates resume state on blocked retry
  - Test sync preserves resume state when hash unchanged

## Test Results

- New tests: 9 passed, 0 failed
- Target tests: 33 passed, 0 failed
- Regression tests: 21 passed, 0 failed
- **Total: 63 tests passed, 0 failed**

## Blockers Status

- ✅ **Blocker #3** (enum compliance): Resolved in attempt-0001
- ✅ **Blocker #2** (session validation): Resolved in attempt-0001
- 🔄 **Blocker #1** (orchestration integration): **Partial**
  - ✅ Registry integration complete
  - ⏳ Orchestration wiring pending (feature_pipeline, codex_launcher)

## Design Decisions

1. **Backward compatibility**: `upsert_packet()` merges with existing record to preserve resume state fields
2. **Explicit update method**: `update_resume_state()` provides clear API for updating resume fields
3. **Automatic sync integration**: `backlog_controller.sync()` automatically updates resume state on hash changes
4. **Fail-safe defaults**: Missing resume fields don't break existing functionality

## Next Steps

Task #31: Wire into orchestration path
- Integrate `decide_rework_resume()` into `feature_pipeline`
- Integrate into `codex_launcher` before coder session launch
- Pass resume decision to coder agent context
