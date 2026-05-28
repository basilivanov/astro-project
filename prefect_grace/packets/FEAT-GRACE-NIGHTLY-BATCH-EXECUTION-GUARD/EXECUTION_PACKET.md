# Execution Packet: FEAT-GRACE-NIGHTLY-BATCH-EXECUTION-GUARD-W01-LIMITS-STOP-CONDITIONS

## Objective

Add a guarded nightly batch execution controller that consumes a safe batch plan
and executes selected packets under strict limits: concurrency, timeout,
stop-on-degradation, bounded evidence, and fail-closed Git mutation behavior.

This packet should make batch execution possible in controlled dry-run and
injected modes first. Real live execution must require explicit operator
approval and must not include auto-merge.

## Slice

- slice_id: `SLICE-GRACE-NIGHTLY-BATCH-EXECUTION-GUARD`
- slice_slug: `grace-nightly-batch-execution-guard`
- feature_id: `FEAT-GRACE-NIGHTLY-BATCH-EXECUTION-GUARD`
- packet_id: `FEAT-GRACE-NIGHTLY-BATCH-EXECUTION-GUARD-W01-LIMITS-STOP-CONDITIONS`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-NIGHTLY-BATCH-DRY-RUN-SELECTION-W01-SAFE-BATCH-PLAN, FEAT-GRACE-SINGLE-LIVE-PACKET-PILOT-W01-PREFECT-WORKTREE-GIT-GATE, FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-BATCH-EXECUTION-GUARD`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/nightly_batch_selection.py`
- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/runtime_lock.py`
- `/opt/astro-project/prefect_grace/platform/nightly_dry_run_controller.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`

## Impacted Modules

- `M-GRACE-NIGHTLY-BATCH-EXECUTION`
- `M-GRACE-NIGHTLY-BATCH-SELECTION`
- `M-GRACE-SINGLE-LIVE-PACKET-PILOT`
- `M-GRACE-RUNTIME-LOCK`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/nightly_batch_execution_guard.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_batch_execution_guard.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_nightly_batch_execution_guard.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-BATCH-EXECUTION-GUARD/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/platform/nightly_batch_selection.py`
- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/platform/runtime_lock.py`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/.worktrees/**`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`

## Must Preserve

- Dry-run default executes nothing.
- Real execution requires explicit CLI approval and environment token.
- Merge is never performed by batch execution guard.
- Commit/push may only happen through Git mutation gate and only when explicitly enabled.
- Runtime lock is acquired before execution and released on all exits.
- Concurrency, timeout, max failures, and stop-on-degradation limits are enforced.
- Evidence output is bounded.
- CLI JSON envelope keeps `result == data`.
- No backend, frontend, Docker, Playwright, provider APIs, credentials, registry apply, or auto-merge is used.

## Recommended Role Assignment

- coder: `Codex high`; orchestrator safety logic with many stop conditions.
- verifier: `Codex high`; injected execution tests should cover stop conditions.
- reviewer: `Codex xhigh`; focus on concurrency, lock leaks, and live opt-in.
- rework policy: fresh session for lock, concurrency, or live execution bugs.

## Required Design Decisions

### 1. Batch Input

The guard should accept a saved batch selection JSON or generate one from the
project using the batch selector.

### 2. Execution Modes

Support:

- `--dry-run`: no execution;
- injected unit mode: fake per-packet pilot runner;
- live mode: requires `--execute`, `--i-understand-live-batch`, and
  `GRACE_NIGHTLY_BATCH_EXECUTION_APPROVED=1`.

### 3. Limits

Configurable limits:

- `--max-packets`;
- `--concurrency`;
- `--timeout-seconds-per-packet`;
- `--max-failures`;
- `--stop-on-degradation`;
- `--allow-git-commit`;
- `--allow-git-push`;
- no merge flag.

### 4. Stop Conditions

Stop when:

- runtime lock unavailable;
- preflight/selection no longer matches source state;
- a packet fails;
- scope/evidence/review/git gate blocks;
- max failures reached;
- timeout reached;
- unexpected degradation appears;
- output would become unbounded.

### 5. Result Shape

Return bounded per-packet summaries and aggregate status:

- selected count;
- executed count;
- skipped count;
- passed/blocked/failed counts;
- stop reason;
- lock status;
- live agents started;
- Prefect runs created;
- Git mutations count;
- packet summaries sample plus total.

## Implementation Requirements

1. Add `prefect_grace/platform/nightly_batch_execution_guard.py`.
2. Add CLI command such as `run-nightly-batch-guard`.
3. Use injected pilot runner for tests; no real live agent required.
4. Add tests for dry-run, live opt-in blocked, lock unavailable, concurrency limit, timeout, max failure stop, degradation stop, git mutation disabled, and bounded output.
5. Add CLI contract tests.
6. Add bounded evidence under `EVIDENCE/attempt-0001/`.

## Acceptance Criteria

- Dry-run returns planned execution without side effects.
- Missing live approval blocks execution with zero live agents and zero Git mutations.
- Injected execution respects ordering, concurrency, timeout, and stop conditions.
- Git commit/push are delegated to the single-packet pilot and Git mutation gate.
- Merge is not exposed.
- Runtime lock is released after success, block, or failure.
- Output is bounded and keeps `result == data`.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_nightly_batch_execution_guard.py \
  tests/test_prefect_grace_cli_nightly_batch_execution_guard.py \
  tests/test_prefect_grace_nightly_batch_selection.py \
  tests/test_prefect_grace_single_live_packet_pilot.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile, targeted GRACE lint, strict packet validation, and CLI dry-run
proof. Do not run live batch execution for this packet verification.

## Expected Evidence

- Strict validation output.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- CLI dry-run proof.
- Missing live approval blocked proof.
- Injected batch execution proof for pass/fail/stop conditions.
- Lock release proof.
- Confirmation no real live agents, Prefect runs, registry writes, backend, frontend, Docker, Playwright, provider APIs, credentials, product push, product merge, or `.worktrees/**` mutation occurred.
- Post-test observability verdict.

## Escalation Triggers

- Batch execution can run without explicit approval.
- Runtime lock leaks.
- Merge appears in this command.
- Git mutation bypasses the single-packet pilot/git gate.
- Concurrency or timeout limits are not enforced.
- Output becomes unbounded.

## Reviewer Gate

Reviewer must verify the guard cannot turn a dry-run batch plan into live
execution without the explicit approval chain.
