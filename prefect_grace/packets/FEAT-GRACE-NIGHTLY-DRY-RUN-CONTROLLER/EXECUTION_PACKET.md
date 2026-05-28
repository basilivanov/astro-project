# Execution Packet: FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER-W01-PLAN-LOCK-SUMMARY

## Objective

Replace the current contract-only `run-nightly` stub with a deterministic
nightly dry-run controller that builds the same backlog plan a real nightly run
would use, acquires a bounded project lock, and emits a concise machine-readable
summary.

This packet is the bridge between "we can reconcile the runtime registry" and
"we can safely leave a batch for an overnight run". It must not execute packets,
submit Prefect runs, start agents, mutate source packet artifacts, merge code,
or touch product services.

The output should tell the operator whether the project is ready for a future
nightly execution packet, what would run, what is blocked, what would stop the
run, and whether the runtime registry is clean enough to trust.

## Slice

- slice_id: `SLICE-GRACE-NIGHTLY-DRY-RUN-CONTROLLER`
- slice_slug: `grace-nightly-dry-run-controller`
- feature_id: `FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER`
- packet_id: `FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER-W01-PLAN-LOCK-SUMMARY`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-W01-SOURCE-TO-RUNTIME, FEAT-GRACE-PREFECT-BATCH-E2E-QUEUE-SMOKE-MVP-W01-BATCH-E2E-QUEUE-SMOKE, FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE-W01-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/project_registry.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_submission.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/prefect_e2e_batch_smoke.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-BATCH-E2E-QUEUE-SMOKE-MVP/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-REAL-DRY-RUN-SEEDED-SMOKE/EXECUTION_PACKET.md`

## Impacted Modules

- `M-GRACE-NIGHTLY-DRY-RUN-CONTROLLER`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-RUNTIME-LOCKS`
- `M-GRACE-STRICT-PACKET-DISCOVERY`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`
- `M-GRACE-OBSERVABILITY-SUMMARY`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/nightly_dry_run_controller.py`
- `/opt/astro-project/prefect_grace/platform/runtime_lock.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli_commands/project_registry.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_submission.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_dry_run_controller.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_nightly_dry_run.py`
- `/opt/astro-project/tests/test_prefect_grace_backlog_controller.py`
- `/opt/astro-project/tests/test_prefect_grace_controller_backlog_bootstrap.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/tests/test_prefect_grace_registry_bootstrap_apply.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER/**`
- `/var/lib/grace-orchestrator/astro-project/state/locks/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/prompts/**`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/policies/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/SUMMARY.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`
- `/opt/astro-project/.worktrees/**`

## Must Preserve

- `run-nightly` remains fail-closed for real execution in this packet.
- Dry-run planning creates zero Prefect runs and starts zero agents.
- Source packets, reviews, summaries, and evidence remain read-only inputs.
- Runtime registry reconciliation remains owned by the registry bootstrap apply packet.
- Accepted packets with unchanged source hashes are not planned for rerun.
- Dependency readiness is computed from runtime registry state, not source status alone.
- Blocked dependencies produce blocked or cascading output, not accepted output.
- Existing CLI JSON envelopes keep `result` equal to `data`.
- Lock files are bounded, project-scoped, and removed or reported deterministically.
- Evidence remains bounded and excludes large raw logs, huge scans, screenshots, and full registry dumps.

## Recommended Role Assignment

- coder: `Codex high` or `Sonnet high`; this is controller behavior with lock
  and state-read safety.
- verifier: `Codex medium`; must verify dry-run mode, lock behavior, zero
  submissions, and bounded summary output.
- reviewer: `Codex xhigh` or `Opus`; reviewer must focus on fail-closed real
  execution, source/runtime trust boundaries, lock cleanup, and no live runs.
- rework policy: fresh session for lock leaks, run submission, registry mutation,
  or dependency-order regressions; light resume only for CLI help, tests, or
  evidence formatting.

## Required Design Decisions

### 1. This Packet Implements Planning, Not Execution

`run-nightly` must stop being a pure placeholder, but this packet must not enable
real nightly execution.

Allowed behavior:

- scan or read strict source packet metadata;
- read runtime registry state;
- run bootstrap/sync/submission planning in dry-run mode;
- acquire and release a bounded project lock;
- build a deterministic nightly plan summary;
- return JSON and optional concise text output.

Forbidden behavior:

- `submit-packets --execute`;
- live Prefect flow run creation;
- agent launch;
- worktree creation;
- verifier/reviewer loop execution;
- merge or push;
- source packet mutation;
- registry bootstrap apply.

### 2. CLI Contract

Extend the existing command instead of adding a parallel nightly command unless
there is a strong compatibility reason:

```bash
python3 -m prefect_grace.cli run-nightly \
  --project prefect_grace/project.yaml \
  --dry-run \
  --until-blocked \
  --json
```

`--dry-run` must be the default. If `--execute`, `--submit`, or any future live
flag is present in this packet, it must return `ok=false` with an explicit
fail-closed error such as `NIGHTLY_EXECUTION_NOT_ENABLED`.

Existing `run-nightly --json` callers must still receive the normal JSON
envelope. The old warning `NIGHTLY_EXECUTION_NOT_ENABLED` may be replaced by a
more precise warning when the command successfully returns a dry-run plan.

### 3. Runtime Registry Must Be Trusted Before Planning

The nightly dry-run controller must preflight the registry before returning a
plan suitable for an overnight run.

Minimum preflight facts:

- strict source candidate count;
- source status counts;
- bootstrap dry-run errors and warning classes;
- runtime registry packet count;
- sync dry-run ready, blocked, waiting, accepted, and stale mismatch counts;
- submit dry-run packets that would be submitted;
- whether any accepted source packet still appears ready or blocked in runtime;
- whether source/runtime mismatch blocks nightly execution.

If registry bootstrap apply has not been performed or stale source/runtime
state remains, the command must return a bounded plan with
`preflight_status: blocked` and must not pretend the nightly is ready.

### 4. Project Lock Is Bounded And Observable

The dry-run must use a project-scoped controller lock compatible with the
architecture:

```text
<runtime_state_root>/state/locks/backlog-controller.lock
```

Tests must use temporary project configs and temporary state roots. Tests must
prove:

- second lock acquisition reports `controller_already_running`;
- stale locks are handled only by explicit max-age logic;
- lock files are released on success and failure;
- lock files are never written outside the configured state root;
- real project dry-run evidence either uses no persistent lock or proves the
  lock was released.

### 5. Planning Must Use Existing Backlog Semantics

The controller must reuse existing registry and backlog planning contracts
instead of implementing a second DAG resolver.

It may call:

- `build_backlog_bootstrap_plan(..., dry_run=True)`;
- `BacklogController.sync(..., dry_run=True)`;
- `BacklogController.plan_submission(...)`;
- existing JSON serialization helpers.

It must not call apply mode, submit execute mode, or native Prefect submission
with a live submitter.

### 6. Plan Lock Summary Shape

Return a JSON-safe result with stable fields. The exact model may evolve during
implementation, but it must include at least:

```json
{
  "mode": "nightly_dry_run",
  "project_key": "astro-project",
  "until_blocked": true,
  "preflight_status": "ready|blocked",
  "plan_id": "sha256:...",
  "plan_hash": "sha256:...",
  "state_root": "/var/lib/grace-orchestrator/astro-project",
  "lock": {
    "path": ".../state/locks/backlog-controller.lock",
    "acquired": true,
    "released": true,
    "already_running": false
  },
  "source": {
    "candidates_total": 0,
    "status_counts": {},
    "errors": 0,
    "warning_classes": 0
  },
  "runtime": {
    "registry_packets_total": 0,
    "accepted": 0,
    "ready": 0,
    "blocked": 0,
    "waiting": 0,
    "cascading_blocked": 0,
    "stale_source_runtime_mismatches": []
  },
  "plan": {
    "would_submit": [],
    "submission_order": [],
    "blocked_packets": [],
    "stop_reason": null
  },
  "side_effects": {
    "registry_updates": 0,
    "prefect_runs_created": 0,
    "live_agents_started": 0,
    "source_files_changed": 0
  }
}
```

The summary must be bounded even for hundreds of packets. If packet lists are
large, include counts and the first few packet IDs plus a total.

### 7. Stop Policy Is Reported, Not Executed

`--until-blocked` must affect the dry-run plan summary only. It may compute
which blocker would stop a future run, but it must not execute anything.

The controller must distinguish:

- no runnable packets because everything is accepted;
- no runnable packets because registry is stale;
- no runnable packets because dependencies are waiting;
- runnable packets exist and would be submitted in order;
- runnable packets exist but a configured stop policy would stop after a
  blocker.

### 8. No Runtime Registry Mutation

This packet may create and remove a lock file under the configured state root.
It must not mutate packet registry YAML, run history, source packets, evidence,
or worktrees during dry-run planning.

If a plan artifact file is introduced, it must be opt-in and bounded. The
default `run-nightly --dry-run --json` must be safe for repeated operator use.

### 9. JSON Envelope Remains Stable

All touched CLI commands must keep:

```json
{
  "ok": true,
  "project_key": "astro-project",
  "command": "...",
  "result": {},
  "data": {},
  "warnings": [],
  "errors": []
}
```

For commands touched by this packet, `result` must remain equal to `data`.

## Implementation Requirements

1. Add a bounded nightly dry-run controller module, preferably `prefect_grace/platform/nightly_dry_run_controller.py`.
2. Add or reuse a small runtime lock helper with project-root containment tests.
3. Extend `run-nightly` CLI arguments with `--dry-run` while preserving old `--json` and `--until-blocked`.
4. Keep real execution fail-closed; do not add a successful live submit path in this packet.
5. Reuse existing bootstrap, sync, and submission plan contracts.
6. Add tests for clean all-accepted registry, stale source/runtime registry, runnable dependency chain, blocked dependency cascade, already-running lock, stale lock handling, lock cleanup on failure, and CLI JSON envelope compatibility.
7. Add bounded evidence manifest and summaries; do not commit full CLI dumps if they are large.
8. Do not modify product backend/frontend files or unrelated GRACE flows/tasks.

## Acceptance Criteria

- `run-nightly --project ... --dry-run --until-blocked --json` returns a deterministic nightly dry-run summary.
- `run-nightly --project ... --json` remains safe and defaults to dry-run planning.
- Any execute/submit/live mode remains fail-closed in this packet.
- A project-scoped lock is acquired and released, with already-running and stale-lock behavior covered by tests.
- Runtime registry stale state blocks the nightly-ready verdict with a clear reason.
- All-accepted registry returns no runnable packets and `prefect_runs_created=0`.
- Runnable ready packets are listed in dependency order without creating Prefect runs.
- Blocked dependencies appear as blocked or cascading, not accepted.
- Accepted packets with unchanged source hashes are not planned for rerun.
- Dry-run planning does not mutate packet registry YAML, source packets, worktrees, run history, or evidence.
- CLI JSON envelope remains stable and `result == data`.
- Evidence is bounded and includes post-test observability verdict.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_nightly_dry_run_controller.py \
  tests/test_prefect_grace_cli_nightly_dry_run.py \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_controller_backlog_bootstrap.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run registry and submission regressions:

```bash
pytest -q \
  tests/test_prefect_grace_registry_apply_smoke.py \
  tests/test_prefect_grace_registry_bootstrap_apply.py \
  tests/test_prefect_grace_cli_submit_packets_prefect_native.py
```

Run compile checks:

```bash
python3 -m compileall -q \
  prefect_grace/platform \
  prefect_grace/cli.py \
  prefect_grace/cli_commands
```

Run targeted GRACE lint:

```bash
python3 scripts/grace_lint.py \
  prefect_grace/platform/nightly_dry_run_controller.py \
  prefect_grace/platform/runtime_lock.py \
  prefect_grace/cli_commands/prefect_smokes.py \
  prefect_grace/cli_commands/parser.py \
  prefect_grace/cli.py
```

Validate this packet strictly:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI dry-run evidence:

```bash
python3 -m prefect_grace.cli run-nightly \
  --project prefect_grace/project.yaml \
  --dry-run \
  --until-blocked \
  --json
```

Run guard evidence:

```bash
python3 -m prefect_grace.cli run-nightly \
  --project prefect_grace/project.yaml \
  --until-blocked \
  --execute \
  --json
```

If `--execute` is not added as a parser option, the guard evidence may instead
be the CLI parser rejection for unknown live/execute flags.

Do not run Docker, backend, frontend, Playwright, live Prefect submissions, live
agents, provider APIs, or credentialed services for this packet.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output for nightly dry-run controller, CLI, backlog, bootstrap, and CLI contracts.
- Registry and submission regression pytest output.
- Compile output.
- Targeted lint output for changed modules.
- CLI `run-nightly --dry-run --until-blocked --json` bounded summary.
- CLI execute/live guard output showing fail-closed behavior or parser rejection.
- Temp-state lock evidence for acquired, already-running, stale-lock, and cleanup paths.
- Evidence that registry stale state blocks nightly-ready verdict.
- Evidence that all-accepted registry creates no runnable submissions and zero Prefect runs.
- Evidence that runnable packets are ordered by dependencies without live submission.
- Evidence that blocked dependencies stay blocked or cascading.
- Evidence that source packets, runtime registry YAML, run history, worktrees, backend, frontend, Docker, Playwright, live Prefect, live agents, provider APIs, credentials, and unrelated files were not touched.
- Post-test observability verdict: `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.

## Escalation Triggers

- Implementing this packet requires enabling live nightly execution.
- `run-nightly --json` cannot remain backward-compatible.
- Lock acquisition cannot be proven contained under the explicit runtime state root.
- Lock files leak after successful or failed dry-run planning.
- Dry-run planning mutates packet registry YAML or source packet artifacts.
- Runtime registry stale state cannot be detected before planning.
- Backlog planning requires a second DAG resolver instead of existing controller contracts.
- Accepted unchanged packets would be planned for rerun.
- `run-nightly` would create Prefect runs, worktrees, agent sessions, commits, merges, or pushes.
- Evidence cannot be bounded without losing decision-critical facts.

## Reviewer Gate

Reviewer must reject this packet if:

- real nightly execution is enabled;
- any Prefect run is created by `run-nightly --dry-run`;
- any live agent is started;
- `run-nightly` mutates source packets, reviews, summaries, evidence, worktrees, product files, or runtime registry YAML;
- lock files can be written outside the configured runtime state root;
- lock files leak after success or failure;
- stale runtime registry state can produce a nightly-ready verdict;
- accepted packets with unchanged source hashes appear in `would_submit`;
- blocked dependencies become accepted or runnable;
- CLI JSON envelope compatibility breaks;
- large raw logs, full packet scans, screenshots, or full registry dumps are committed as evidence;
- Docker, backend, frontend, Playwright, provider APIs, or credentials are used.
