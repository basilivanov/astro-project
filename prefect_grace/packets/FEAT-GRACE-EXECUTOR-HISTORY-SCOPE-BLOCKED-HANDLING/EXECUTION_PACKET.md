# Execution Packet: FEAT-GRACE-EXECUTOR-HISTORY-SCOPE-BLOCKED-HANDLING

## Objective

Fix executor history to not treat `scope_blocked` as failure for rotation logic.

Currently `scope_blocked` can count toward `max_consecutive_failures`, causing
an executor to be rotated out even when the issue is a packet scope violation,
not an executor failure.

## Problem

Executor selection uses `_count_consecutive_failures()` in
`prefect_grace/platform/executor_registry.py` to decide whether an executor has
exceeded `max_consecutive_failures`.

`scope_blocked` is a packet/worktree scope outcome. It means the packet changed
files outside allowed scope or touched frozen scope. It should block the packet,
but it should not penalize the executor for future selection.

The subtle failure mode is records where:

```json
{
  "domain_status": "scope_blocked",
  "returncode": 1
}
```

`_is_executor_failure()` currently treats `returncode != 0` as failure before
checking `domain_status == "scope_blocked"`. The fix should make
`scope_blocked` non-counting for consecutive executor failure rotation.

## Solution Options

1. **Filter history**: Exclude `scope_blocked` from consecutive failure count.
2. **Increase limit**: Raise `max_consecutive_failures` from 3 to 10.
3. **Separate counters**: Track executor failures vs packet failures separately.

## Recommended Approach

Option 1 - modify `_count_consecutive_failures()` in `executor_registry.py` to
skip entries where `domain_status == "scope_blocked"`.

This keeps the change local, preserves existing status model semantics, and
avoids hiding true executor failures behind a larger failure threshold.

## Slice

- slice_id: `SLICE-GRACE-EXECUTOR-HISTORY-SCOPE-BLOCKED-HANDLING`
- slice_slug: `grace-executor-history-scope-blocked-handling`
- feature_id: `FEAT-GRACE-EXECUTOR-HISTORY-SCOPE-BLOCKED-HANDLING`
- packet_id: `FEAT-GRACE-EXECUTOR-HISTORY-SCOPE-BLOCKED-HANDLING-W01-FILTER-SCOPE-BLOCKED`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-EXECUTOR-REGISTRY-MVP-W01-EXECUTOR-REGISTRY, FEAT-GRACE-STATUS-MODEL-MVP-W01-STATUS-MODEL`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EXECUTOR-HISTORY-SCOPE-BLOCKED-HANDLING`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/executor_registry.py`
- `/opt/astro-project/prefect_grace/platform/status_model.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_executor_registry.py`
- `/opt/astro-project/tests/test_prefect_grace_managed_packet_runner_executor_registry.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EXECUTOR-REGISTRY-MVP/EXECUTION_PACKET.md`

## Impacted Modules

- `M-GRACE-EXECUTOR-REGISTRY`
- `M-GRACE-EXECUTOR-HISTORY`
- `M-GRACE-STATUS-MODEL`
- `M-GRACE-MANAGED-PACKET-RUNNER`

## Files

- `prefect_grace/platform/executor_registry.py` - update failure counting logic.
- `tests/test_prefect_grace_executor_registry.py` - add regression tests for `scope_blocked` filtering.

Note: the requested `tests/test_executor_registry.py` name does not exist in
this repository; the existing test module is
`tests/test_prefect_grace_executor_registry.py`.

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/executor_registry.py`
- `/opt/astro-project/tests/test_prefect_grace_executor_registry.py`
- `/opt/astro-project/tests/test_prefect_grace_managed_packet_runner_executor_registry.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-EXECUTOR-HISTORY-SCOPE-BLOCKED-HANDLING/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/status_model.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/.worktrees/**`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`

## Must Preserve

- True executor failures still count toward `max_consecutive_failures`.
- `agent_failed`, timeout, stall killed, rate limit, quota, auth failure, and non-scope nonzero return codes remain executor failures.
- `scope_blocked` remains a packet/blocking domain outcome for packet status.
- `scope_blocked` must not rotate out an executor by itself, even when `returncode` is nonzero.
- Source hash filtering behavior remains unchanged.
- Requested executor behavior remains unchanged.
- Executor priority sorting remains deterministic.
- No changes to managed packet runner status priority.
- No live agents, Prefect runs, worktrees, registry writes, backend, frontend, Docker, Playwright, provider APIs, credentials, Git push, or merge are used.

## Recommended Role Assignment

- coder: `Codex medium`; this is a small deterministic registry fix.
- verifier: `Codex medium`; must cover direct helper and selection behavior.
- reviewer: `Codex high`; focus on not masking true executor failures.
- rework policy: light resume for missing tests; fresh session if rotation semantics or status model behavior are changed.

## Required Design Decisions

### 1. Filter In Consecutive Count

Modify `_count_consecutive_failures()` so records with
`domain_status == "scope_blocked"` are skipped before `_is_executor_failure()`
is evaluated.

This avoids changing broad status model semantics and avoids changing how packet
outcomes are mapped elsewhere.

### 2. Do Not Increase Failure Limit

Do not change `max_consecutive_failures` defaults or project config values. A
larger threshold would hide real executor instability.

### 3. Preserve Stop-On-Success Semantics

For the same executor, counting should still stop at the first non-failure that
is not a skipped `scope_blocked` record. Scope-blocked records should not reset
the failure streak and should not increment it; they should be ignored for
executor-health rotation.

Example newest-first history:

```text
scope_blocked, returncode=1  -> ignored
agent_failed                 -> counts as 1
success                      -> stops
older failure                -> not counted
```

### 4. Test The Real Bug Shape

Add regression coverage where `scope_blocked` has a nonzero `returncode`, since
that is the case likely to be misclassified by the current returncode-first
logic.

## Implementation Requirements

1. Update `_count_consecutive_failures()` in `prefect_grace/platform/executor_registry.py`.
2. Add direct helper tests proving `scope_blocked` with `returncode=1` is skipped.
3. Add selection test proving repeated `scope_blocked` records do not rotate an executor out.
4. Add mixed-history test proving true executor failures still count around ignored `scope_blocked` records.
5. Keep existing executor registry tests passing.
6. Add bounded evidence under `EVIDENCE/attempt-0001/`.

## Acceptance Criteria

- `_count_consecutive_failures()` ignores `scope_blocked` records.
- `scope_blocked` with `returncode=1` does not count as executor failure.
- Two or more `scope_blocked` records do not rotate the executor when no true executor failures exist.
- True executor failures still rotate after `max_consecutive_failures`.
- Source hash filtering still works.
- Existing executor selection behavior remains deterministic.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_executor_registry.py \
  tests/test_prefect_grace_managed_packet_runner_executor_registry.py
```

Run compile checks:

```bash
python3 -m compileall -q prefect_grace/platform/executor_registry.py
```

Run targeted GRACE lint:

```bash
python3 scripts/grace_lint.py prefect_grace/platform/executor_registry.py
```

Validate this packet strictly:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-EXECUTOR-HISTORY-SCOPE-BLOCKED-HANDLING/EXECUTION_PACKET.md \
  --strict --json
```

Do not run live agents, Prefect, Docker, backend, frontend, Playwright,
provider APIs, registry apply, Git push, or merge for this packet.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Evidence that `scope_blocked + returncode=1` does not rotate executor.
- Evidence that true executor failures still rotate executor.
- Confirmation that no live agents, Prefect runs, worktrees, registry writes, backend, frontend, Docker, Playwright, provider APIs, credentials, Git push, merge, or `.worktrees/**` mutation occurred.
- Post-test observability verdict: `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.

## Escalation Triggers

- Fix requires changing `status_model.py`.
- Fix requires changing managed packet runner domain status priority.
- True executor failures stop counting.
- `scope_blocked` stops blocking packet status.
- Source hash filtering behavior changes.
- The implementation needs live agents, Prefect, Docker, backend, frontend, Playwright, provider APIs, registry apply, push, or merge.

## Reviewer Gate

Reviewer must verify that `scope_blocked` is ignored only for executor-health
rotation and still remains a blocking packet outcome elsewhere.
