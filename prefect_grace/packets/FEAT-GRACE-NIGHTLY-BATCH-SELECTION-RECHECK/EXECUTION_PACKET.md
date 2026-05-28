# Execution Packet: FEAT-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK-W01-PREFLIGHT-RECHECK

## Objective

Add a final recheck gate for nightly batch selection immediately before any
controlled batch run.

The existing nightly selector can build a safe dry-run plan. This packet makes
that plan stale-safe: before execution, the controller must re-read source
packets, runtime registry, dependency state, Prefect binding status, and recent
review/evidence state, then either confirm the saved plan or produce a bounded
blocker report.

## Slice

- slice_id: `SLICE-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK`
- slice_slug: `grace-nightly-batch-selection-recheck`
- feature_id: `FEAT-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK`
- packet_id: `FEAT-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK-W01-PREFLIGHT-RECHECK`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-NIGHTLY-BATCH-DRY-RUN-SELECTION-W01-SAFE-BATCH-PLAN, FEAT-GRACE-PREFECT-MANAGED-RUNNER-DEPLOYMENT-APPLY-W01-APPROVED-DEPLOYMENT-APPLY, FEAT-GRACE-SINGLE-ASTRO-PACKET-PILOT-W01-ONE-SAFE-ASTRO-PACKET`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/nightly_batch_selection.py`
- `/opt/astro-project/prefect_grace/platform/nightly_dry_run_controller.py`
- `/opt/astro-project/prefect_grace/platform/prefect_worker_binding.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/runtime_lock.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`

## Impacted Modules

- `M-GRACE-NIGHTLY-BATCH-RECHECK`
- `M-GRACE-NIGHTLY-BATCH-SELECTION`
- `M-GRACE-PREFECT-WORKER-BINDING`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-RUNTIME-LOCK`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/nightly_batch_recheck.py`
- `/opt/astro-project/prefect_grace/platform/nightly_batch_selection.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_batch_recheck.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_nightly_batch_recheck.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_batch_selection.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK/**`

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

- Recheck is read-only and dry-run only.
- It starts no agents, creates no Prefect runs, creates no worktrees, applies
  no registry writes, and performs no Git mutations.
- It must reject stale plans where packet source hash, registry status,
  dependency state, review status, evidence status, or Prefect binding status
  changed.
- Output is bounded and keeps `result == data`.

## Required Design Decisions

### 1. Saved Plan Input

Accept a saved nightly selection JSON or generate one in-process, then re-read
all authoritative state before confirming it.

### 2. Staleness Rules

Block if:

- selected packet source hash changed;
- selected packet is no longer ready/runnable;
- a dependency is no longer accepted or selected earlier;
- latest review/evidence now blocks the packet;
- Prefect deployment/pool/queue binding is not ready;
- runtime lock cannot be acquired;
- selected batch exceeds current limits.

### 3. Bounded Output

Return selected count, confirmed count, blocked count, blocker classes, packet
samples, plan hash, recheck hash, and lock status. Do not dump full registry or
full packet corpus.

## Implementation Requirements

1. Add `prefect_grace/platform/nightly_batch_recheck.py`.
2. Add CLI command such as `nightly-recheck-batch`.
3. Add tests for stale source hash, stale registry status, dependency change,
   review blocker, Prefect binding blocker, lock unavailable, and clean recheck.
4. Add CLI contract tests.

## Acceptance Criteria

- Clean saved plan rechecks as ready.
- Any stale or blocked fact produces `preflight_status=blocked`.
- Runtime lock is released on all exits.
- No execution or mutation occurs.
- Output remains bounded.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_nightly_batch_recheck.py \
  tests/test_prefect_grace_cli_nightly_batch_recheck.py \
  tests/test_prefect_grace_nightly_batch_selection.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile, targeted lint, strict packet validation, and real project dry-run
recheck proof.

## Expected Evidence

- Strict validation output.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Clean recheck proof.
- Stale plan blocked proof.
- Lock release proof.
- Confirmation zero Prefect runs, zero live agents, zero registry writes, zero
  worktrees, zero Git mutations, no backend/frontend/Docker/Playwright.

## Escalation Triggers

- Recheck mutates state.
- Stale selected packets are allowed through.
- Lock leaks.
- Output requires unbounded logs or full registry dumps.
