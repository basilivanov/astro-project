# Execution Packet: FEAT-GRACE-STRUCTURED-LOGGING-MVP-W01-LOG-ENVELOPE

## Objective

Implement structured logging foundation for GRACE orchestrator to enable log-driven
development as specified in GRACE Canon section 8.

The orchestrator currently has zero structured logging. All modules declare
`emitted_logs: None` in their contracts. This packet establishes the log envelope,
trace context, and critical path logging for packet execution flows, enabling
verification evidence through structured traces.

## Slice

- slice_id: `SLICE-GRACE-STRUCTURED-LOGGING-MVP`
- slice_slug: `grace-structured-logging-mvp`
- feature_id: `FEAT-GRACE-STRUCTURED-LOGGING-MVP`
- packet_id: `FEAT-GRACE-STRUCTURED-LOGGING-MVP-W01-LOG-ENVELOPE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT-W01-ONE-SAFE-ASTRO-PACKET, FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-STRUCTURED-LOGGING-MVP`

## Source Of Truth

GRACE Canon section 8: Structured logs и log-driven development
- `/opt/astro-project/GRACE.md` lines 361-427

## Impacted Modules

- `M-GRACE-STRUCTURED-LOGGER` (new)
- `M-GRACE-TRACE-CONTEXT` (new)
- `M-GRACE-LOG-COLLECTOR` (new)
- `M-GRACE-MANAGED-PACKET-RUNNER` (update)
- `M-GRACE-SINGLE-ASTRO-PACKET-PILOT` (update)
- `M-GRACE-PREFECT-NATIVE-SUBMISSION` (update)
- `M-GRACE-SCOPE-GUARD` (update)
- `M-GRACE-EVIDENCE-MANIFEST` (update)

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/structured_logger.py`
- `/opt/astro-project/prefect_grace/platform/trace_context.py`
- `/opt/astro-project/prefect_grace/platform/log_collector.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/single_astro_packet_pilot.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/scope_guard.py`
- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/prefect_grace/cli_commands/evidence.py`
- `/opt/astro-project/tests/test_prefect_grace_structured_logger.py`
- `/opt/astro-project/tests/test_prefect_grace_trace_context.py`
- `/opt/astro-project/tests/test_prefect_grace_log_collector.py`
- `/opt/astro-project/tests/test_prefect_grace_managed_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_single_astro_packet_pilot.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-STRUCTURED-LOGGING-MVP/**`

Scope note: `prefect_grace/cli_commands/evidence.py` is included narrowly for
the `validate-evidence-manifest` command to pass the same artifact roots into
structured trace validation that artifact reference validation already uses.
This CLI path is part of this packet's evidence acceptance criteria.

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/** outside current packet`
- `/opt/astro-project/.worktrees/**`

## Must Preserve

- Logging is opt-in and fail-safe: if logger fails, execution continues.
- Log envelope follows GRACE Canon format exactly (module, fn, block, event, result, trace_id, scenario_id, timestamp).
- Logs are written to bounded JSONL files in packet artifact directory.
- No unbounded log accumulation in memory.
- No external log shipping or third-party dependencies.
- Trace context is thread-safe and supports nested execution.
- All timestamps are ISO-8601 UTC.

## Required Design Decisions

### 1. Log Envelope Format

Implement GRACE Canon section 8.1 envelope:

```json
{
  "module": "M-GRACE-MANAGED-PACKET-RUNNER",
  "fn": "run_managed_packet",
  "block": "AGENT_EXECUTION",
  "event": "agent_started",
  "result": "ok|fail|retry|skip",
  "trace_id": "TRACE-PACKET-001-ATTEMPT-001",
  "scenario_id": "SCN-SINGLE-ASTRO-PILOT",
  "timestamp": "2026-03-27T10:30:00.123456Z",
  "packet_id": "FEAT-EXAMPLE-W01-TASK",
  "attempt": 1
}
```

### 2. Critical Path Events (GRACE Canon 8.2)

MUST log:
- External calls: Prefect API submission, Prefect status polling
- Queue/task handoff: packet submission to Prefect work queue
- Retries: packet retry decision and attempt increment
- Branching decisions: low-risk candidate selection, scope validation pass/fail
- Failure conversion: domain_status transitions (passed, scope_blocked, agent_failed, runner_error)
- Completion: packet accepted, rework, blocked

### 3. Trace Context Management

- Trace ID format: `TRACE-{packet_id}-ATTEMPT-{attempt:03d}`
- Scenario ID format: `SCN-{pilot_mode}` (e.g., `SCN-SINGLE-ASTRO-PILOT`)
- Context propagates through function calls via context manager
- Thread-local storage for concurrent execution safety

### 4. Log Collection and Evidence

- Logs written to `{artifact_root}/{packet_id}/execution_trace.jsonl`
- One JSON object per line (JSONL format)
- Bounded: max 10,000 events per packet execution
- Collector flushes on context exit
- Evidence manifest updated to include `execution_trace.jsonl` as trace evidence

### 5. Backward Compatibility

- Existing modules continue to work without logging
- Logging is injected via optional `trace_context` parameter
- Function contracts updated from `emitted_logs: None` to `emitted_logs: structured (see trace_context)`
- No breaking changes to existing function signatures

## Implementation Requirements

1. Create `prefect_grace/platform/structured_logger.py`:
   - `StructuredLogger` class with GRACE Canon envelope
   - `log_event(module, fn, block, event, result, **extra)` method
   - ISO-8601 timestamp generation
   - JSONL writer with bounded buffer

2. Create `prefect_grace/platform/trace_context.py`:
   - `TraceContext` dataclass with trace_id, scenario_id, packet_id, attempt
   - `create_trace_context(packet_id, attempt, scenario_id)` factory
   - Context manager for trace lifecycle
   - Thread-local storage for nested contexts

3. Create `prefect_grace/platform/log_collector.py`:
   - `LogCollector` class managing JSONL file writes
   - `collect(log_entry: dict)` method
   - `flush()` method for context exit
   - Bounded event limit (10,000 max)
   - Safe file creation in artifact directory

4. Update `prefect_grace/platform/managed_packet_runner.py`:
   - Add optional `trace_context` parameter to `run_managed_packet`
   - Log events: worktree_created, agent_started, agent_completed, scope_validation_started, scope_validation_completed, domain_status_determined
   - Update function contract `emitted_logs` field

5. Update `prefect_grace/platform/single_astro_packet_pilot.py`:
   - Add trace context creation for pilot execution
   - Log events: candidate_selection_started, candidate_selected, submission_planned, prefect_submitted, status_poll_started, status_received, scope_validated
   - Pass trace_context to managed_packet_runner

6. Update `prefect_grace/platform/prefect_native_submission.py`:
   - Add optional `trace_context` parameter
   - Log events: prefect_api_call_started, prefect_api_call_completed, flow_run_created
   - Update function contract

7. Update `prefect_grace/platform/scope_guard.py`:
   - Add optional `trace_context` parameter to `validate_scope`
   - Log events: scope_check_started, scope_violation_detected, scope_check_passed
   - Update function contract

8. Update `prefect_grace/platform/evidence_manifest.py`:
   - Add `execution_trace` to allowed evidence types
   - Validate `execution_trace.jsonl` format (JSONL with required envelope fields)

9. Add comprehensive tests:
   - `test_structured_logger.py`: envelope format, timestamp, JSONL output
   - `test_trace_context.py`: context creation, propagation, thread safety
   - `test_log_collector.py`: file writes, bounded limits, flush behavior
   - Update existing tests to verify trace files are created

## Acceptance Criteria

- All new modules pass GRACE lint (contracts, blocks, naming).
- Log envelope matches GRACE Canon section 8.1 exactly.
- Critical path events (section 8.2) are logged in managed_packet_runner and single_astro_packet_pilot.
- Trace context propagates through execution without breaking existing flows.
- `execution_trace.jsonl` is created in packet artifact directory.
- Evidence manifest validates trace files.
- Logging failures do not break packet execution (fail-safe).
- No unbounded memory accumulation (10,000 event limit enforced).
- All timestamps are ISO-8601 UTC.
- Existing tests continue to pass (backward compatible).

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_structured_logger.py \
  tests/test_prefect_grace_trace_context.py \
  tests/test_prefect_grace_log_collector.py \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_single_astro_packet_pilot.py
```

Run GRACE lint on new modules:

```bash
python3 scripts/grace_lint.py \
  prefect_grace/platform/structured_logger.py \
  prefect_grace/platform/trace_context.py \
  prefect_grace/platform/log_collector.py
```

Run compile and full test suite:

```bash
python3 -m compileall prefect_grace/platform/*.py -q
pytest tests/ -q
```

Verify trace file creation in real packet execution:

```bash
# Run single Astro packet pilot and verify execution_trace.jsonl exists
python3 -m prefect_grace.cli single-astro-packet --dry-run
ls -lh prefect_grace/state/artifacts/*/execution_trace.jsonl
```

## Expected Evidence

- Strict GRACE lint output for new modules.
- Targeted pytest output (all new tests pass).
- Compile output (no syntax errors).
- Sample `execution_trace.jsonl` with at least 10 critical path events.
- Evidence manifest validation output accepting trace files.
- Confirmation that existing packet execution flows continue to work.
- Confirmation zero backend/frontend/Docker/Playwright changes.
- Proof that logging failures do not break execution (fail-safe test).
- Proof that 10,000 event limit is enforced (bounded test).

## Escalation Triggers

- Log envelope deviates from GRACE Canon section 8.1 format.
- Logging failures break packet execution (not fail-safe).
- Unbounded log accumulation in memory or disk.
- Trace context breaks existing execution flows.
- Critical path events (section 8.2) are missing from logs.
- Timestamps are not ISO-8601 UTC.
- Evidence manifest rejects valid trace files.
- Existing tests fail (backward compatibility broken).
