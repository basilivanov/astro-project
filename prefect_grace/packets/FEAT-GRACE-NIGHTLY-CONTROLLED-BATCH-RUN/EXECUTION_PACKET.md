# Execution Packet: FEAT-GRACE-NIGHTLY-CONTROLLED-BATCH-RUN-W01-CONCURRENCY-ONE-NO-MERGE

## Objective

Run the first small controlled nightly batch through the GRACE pipeline with
strict stop conditions.

This packet turns the accepted rechecked batch plan into a limited run:
concurrency one, small packet count, bounded timeout, stop-on-first unexpected
degradation, no auto-merge, and optional commit/push only through the packet
branch push gate. It is not a full autonomous night mode yet.

## Slice

- slice_id: `SLICE-GRACE-NIGHTLY-CONTROLLED-BATCH-RUN`
- slice_slug: `grace-nightly-controlled-batch-run`
- feature_id: `FEAT-GRACE-NIGHTLY-CONTROLLED-BATCH-RUN`
- packet_id: `FEAT-GRACE-NIGHTLY-CONTROLLED-BATCH-RUN-W01-CONCURRENCY-ONE-NO-MERGE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK-W01-PREFLIGHT-RECHECK, FEAT-GRACE-NIGHTLY-BATCH-EXECUTION-GUARD-W01-LIMITS-STOP-CONDITIONS, FEAT-GRACE-PACKET-BRANCH-PUSH-GATE-W01-ACCEPTED-PACKET-BRANCH-PUSH`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-CONTROLLED-BATCH-RUN`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/nightly_batch_execution_guard.py`
- `/opt/astro-project/prefect_grace/platform/nightly_batch_recheck.py`
- `/opt/astro-project/prefect_grace/platform/nightly_batch_selection.py`
- `/opt/astro-project/prefect_grace/platform/single_live_packet_pilot.py`
- `/opt/astro-project/prefect_grace/platform/packet_branch_push_gate.py`
- `/opt/astro-project/prefect_grace/platform/runtime_lock.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`

## Impacted Modules

- `M-GRACE-NIGHTLY-CONTROLLED-BATCH-RUN`
- `M-GRACE-NIGHTLY-BATCH-EXECUTION`
- `M-GRACE-NIGHTLY-BATCH-RECHECK`
- `M-GRACE-SINGLE-LIVE-PACKET-PILOT`
- `M-GRACE-PACKET-BRANCH-PUSH-GATE`
- `M-GRACE-RUNTIME-LOCK`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/nightly_controlled_batch_run.py`
- `/opt/astro-project/prefect_grace/platform/nightly_batch_execution_guard.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_controlled_batch_run.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_nightly_controlled_batch_run.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_batch_execution_guard.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-CONTROLLED-BATCH-RUN/**`
- `/tmp/grace-nightly-controlled-batch-run/**`

## Frozen Scope

- `/opt/astro-project/backend/** outside selected packet allowed scopes`
- `/opt/astro-project/frontend/** outside selected packet allowed scopes`
- `/opt/astro-project/prefect_grace/** outside allowed implementation files`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/docker-compose*.yml`
- `/opt/astro-project/.env`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/** outside current packet`
- `/opt/astro-project/.worktrees/**`

## Must Preserve

- Dry-run is default.
- Live batch requires `--execute`, `--i-understand-live-batch`, and
  `GRACE_NIGHTLY_BATCH_EXECUTION_APPROVED=1`.
- Concurrency is one for the first controlled batch.
- Max packet count defaults to a small value, such as three.
- Merge is never performed.
- Commit/push are optional and delegated only to packet branch push gate.
- Runtime lock is acquired before execution and released on all exits.
- Stop on first unexpected degradation, timeout, scope block, evidence block,
  review block, Git gate block, or Prefect/agent failure.
- Output is bounded and keeps `result == data`.

## Required Design Decisions

### 1. Execution Input

Accept only a rechecked batch plan produced by
`FEAT-GRACE-NIGHTLY-BATCH-SELECTION-RECHECK`. The command may also generate and
recheck a plan in-process, but execution cannot proceed without clean recheck.

### 2. Controlled Limits

Defaults:

- `max_packets=3`;
- `concurrency=1`;
- `timeout_seconds_per_packet` bounded;
- `max_failures=1`;
- `stop_on_degradation=true`;
- `allow_merge=false`.

### 3. Per-Packet Summary

For each packet, record only bounded facts: packet id, flow run id, agent count,
domain status, evidence/review status, scope status, branch push status, stop
reason, and sampled changed files.

## Implementation Requirements

1. Add `prefect_grace/platform/nightly_controlled_batch_run.py` or extend the
   existing batch execution guard with a controlled-run mode.
2. Add CLI command such as `run-nightly-controlled-batch`.
3. Add injected tests for clean dry-run, missing live approval, one success,
   first failure stop, timeout stop, degradation stop, branch push disabled,
   branch push delegated, lock unavailable, and bounded output.
4. Do not run real live batch in automated verification.

## Acceptance Criteria

- Dry-run executes nothing and returns the bounded plan.
- Missing live approval starts zero agents and creates zero Prefect runs.
- Injected live mode respects concurrency one, max packet count, timeout, and
  stop conditions.
- Merge is unreachable.
- Runtime lock is released after success, block, or failure.
- Output is bounded.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_nightly_controlled_batch_run.py \
  tests/test_prefect_grace_cli_nightly_controlled_batch_run.py \
  tests/test_prefect_grace_nightly_batch_execution_guard.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile, targeted lint, strict packet validation, dry-run CLI proof, and
missing-live-approval proof. Real live controlled batch requires explicit
Architect approval.

## Expected Evidence

- Strict validation output.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Dry-run proof.
- Missing approval blocked proof.
- Injected controlled batch proof.
- Lock release proof.
- Confirmation no merge, no product branch update, no unapproved push, no
  backend/frontend/Docker/Playwright/provider secrets, and bounded output.

## Escalation Triggers

- More than the configured packet limit can run.
- Concurrency exceeds one.
- Merge appears.
- Lock leaks.
- Batch continues after unexpected degradation.
- Output includes unbounded logs or secrets.
