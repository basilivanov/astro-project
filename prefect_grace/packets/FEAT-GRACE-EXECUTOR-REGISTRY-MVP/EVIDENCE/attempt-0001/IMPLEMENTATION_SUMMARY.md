# Implementation Summary: FEAT-GRACE-EXECUTOR-REGISTRY-MVP

**Attempt:** 0001  
**Date:** 2026-05-26  
**Status:** Complete

## Objective

Introduce a deterministic executor registry for packet execution roles that can select between Codex, Claude, agy, or other executors based on project configuration, role compatibility, and failure history.

## Implementation

### 1. Created `prefect_grace/platform/executor_registry.py`

**Core Components:**
- `ExecutorSpec` dataclass: executor metadata (id, kind, command, model, roles, priority, max_consecutive_failures)
- `ExecutorSelection` dataclass: selection result with rotation logic
- `load_executor_specs()`: parse executor list from project config with backward compatibility
- `select_executor_for_packet()`: deterministic selection with rotation after consecutive failures
- `record_executor_attempt()`: append execution records to ExecutorHistoryStore

**Selection Rules:**
1. If `requested_executor` provided, select it if enabled and role-compatible
2. Otherwise filter enabled candidates by role (empty roles = all roles)
3. Sort by `(priority, executor_id)` for deterministic ordering
4. Check history for consecutive failures per executor
5. Rotate if best candidate has `max_consecutive_failures` or more consecutive failures
6. Return `ok=false` if no candidate remains

**Failure Detection:**
- Failure: `returncode != 0` OR `domain_status == "agent_failed"` OR `termination_reason` in `["stall_killed", "timeout", "rate_limit_exceeded", "quota_exceeded", "auth_failed"]`
- NOT failure: `domain_status == "scope_blocked"` OR `status == "skipped"`

**Source Hash Filtering:**
- If both packet and history record have `source_hash`, only records with matching `source_hash` count for rotation
- Prevents stale failures from old packet contracts from rotating fresh attempts

**ParsedPacket Support:**
- `select_executor_for_packet()` accepts both `dict[str, Any]` and `ParsedPacket` dataclass
- Handles attribute access for dataclass vs dict.get() for dict

### 2. Extended `prefect_grace/platform/project_adapter.py`

**Changes:**
- Added optional `executors: list[dict[str, Any]] | None` field to `AgentExecutorConfig`
- Updated `from_dict()` to parse `executors` list if present
- Updated `to_dict()` to include `executors` if present
- Backward compatible: existing configs without `executors` continue working

**Config Schema:**
```yaml
agent_executor:
  default: codex-cli
  command: codex1
  executors:  # optional
    - executor_id: codex-cli
      kind: codex
      command: codex1
      model: gpt-5.4
      reasoning: high
      roles: [coder, verifier]
      enabled: true
      priority: 100
      max_consecutive_failures: 2
```

### 3. Integrated with `prefect_grace/platform/managed_packet_runner.py`

**Changes:**
- Added optional `project: Any | None` parameter to `run_managed_packet()`
- Select executor before worktree creation if `project` provided
- Fail closed if selected executor kind not in `["codex", "mock"]`
- Record executor attempt after agent execution
- Include executor metadata (`executor_id`, `executor_kind`) in `agent_result`
- Handle `ParsedPacket` dataclass fields (`.packet_id`, `.feature_id`, `.wave_id`, `.source_hash`)

**Fail-Closed Behavior:**
- Unsupported executor kinds (`claude`, `agy`) return `domain_status="runner_error"` with `blocker_reason="unsupported_executor_kind:<kind>"`
- No executor available returns `domain_status="runner_error"` with `blocker_reason="no_executor_available: <reason>"`
- Never fall back to Codex implicitly

### 4. Added CLI Commands

**`list-executors`:**
- Lists all executor specs from project config
- JSON and text output modes
- Shows executor_id, kind, enabled status, roles, priority

**`select-executor`:**
- Selects executor for packet with given role
- JSON and text output modes
- Exit codes: 0=success, 1=no executor available, 2=command error
- Shows selected executor, rotation reason, warnings

### 5. Tests

**Created test files:**
- `tests/test_prefect_grace_executor_registry.py` (17 tests)
- `tests/test_prefect_grace_project_adapter_executors.py` (4 tests)
- `tests/test_prefect_grace_executor_registry_cli.py` (6 tests)
- `tests/test_prefect_grace_managed_packet_runner_executor_registry.py` (6 tests)
- Updated `tests/test_prefect_grace_cli_contracts.py` (2 tests)

**Test Coverage:**
- Backward compatibility: synthesize default executor from legacy config
- Executor spec loading and validation
- Default selection (highest priority enabled)
- Requested executor selection
- Role filtering
- Disabled executor skipping
- Rotation after consecutive failures
- `scope_blocked` doesn't count as executor failure
- Source hash filtering (stale history doesn't rotate)
- No candidate available returns `ok=false`
- Executor attempt recording
- CLI JSON and text output
- CLI exit codes
- Managed runner integration with ParsedPacket
- Mock executor with injected launcher

## Verification Results

**Targeted Tests:** 43 passed in 3.84s  
**Regression Tests:** 23 passed in 0.47s  
**GRACE Lint:** All modules comply  
**Compileall:** PASS  

## Key Design Decisions

1. **Backward Compatibility:** Legacy configs with only `default`/`command` synthesize single codex-cli executor
2. **Fail-Closed:** Unsupported executor kinds return `runner_error`, never fall back to Codex implicitly
3. **Deterministic Selection:** Sort by `(priority, executor_id)`, same inputs always produce same output
4. **Minimal Integration:** `project` parameter optional in `run_managed_packet()`, existing tests continue working
5. **No Live Executors:** No Claude/agy launcher implementation, only metadata selection layer
6. **ParsedPacket Support:** Handle both dict and dataclass packet representations

## Scope Compliance

**Modified Files (all in allowed scope):**
- `prefect_grace/cli.py`
- `prefect_grace/platform/executor_registry.py` (new)
- `prefect_grace/platform/managed_packet_runner.py`
- `prefect_grace/platform/project_adapter.py`
- `tests/test_prefect_grace_cli_contracts.py`
- `tests/test_prefect_grace_executor_registry_cli.py` (new)
- `tests/test_prefect_grace_executor_registry.py` (new)
- `tests/test_prefect_grace_managed_packet_runner_executor_registry.py` (new)
- `tests/test_prefect_grace_project_adapter_executors.py` (new)

**Frozen Scope Preserved:**
- `prefect_grace/tasks/codex_launcher.py` unchanged
- `prefect_grace/platform/state_store.py` unchanged (only ExecutorHistoryStore usage)
- `scripts/grace_lint.py` unchanged
- No backend/frontend modifications
- No Prefect deployments/queues modified

## Confirmation

- ✓ All targeted tests pass (43 tests)
- ✓ All regression tests pass (23 tests)
- ✓ GRACE lint passes on all modified files
- ✓ Rotation happens after consecutive failures
- ✓ Stale source_hash history doesn't rotate fresh packet
- ✓ `scope_blocked` doesn't count as executor failure
- ✓ Unsupported claude/agy kinds fail closed without launching Codex
- ✓ No live agents started in tests
- ✓ No files outside allowed scope modified
- ✓ `codex_launcher.py` unchanged
- ✓ `state_store.py` unchanged
- ✓ Frozen scope preserved
- ✓ ParsedPacket dataclass support added
- ✓ Managed runner integration tests pass
