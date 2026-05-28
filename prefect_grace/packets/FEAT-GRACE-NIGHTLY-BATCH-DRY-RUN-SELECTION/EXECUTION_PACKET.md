# Execution Packet: FEAT-GRACE-NIGHTLY-BATCH-DRY-RUN-SELECTION-W01-SAFE-BATCH-PLAN

## Objective

Add a safe nightly batch selector that consumes the preflight risk report and
produces a dependency-ordered dry-run batch plan. The selector should choose a
bounded set of low-risk, non-conflicting packets and explain why each excluded
packet was skipped.

This packet must not execute selected packets. It is selection and planning
only.

## Slice

- slice_id: `SLICE-GRACE-NIGHTLY-BATCH-DRY-RUN-SELECTION`
- slice_slug: `grace-nightly-batch-dry-run-selection`
- feature_id: `FEAT-GRACE-NIGHTLY-BATCH-DRY-RUN-SELECTION`
- packet_id: `FEAT-GRACE-NIGHTLY-BATCH-DRY-RUN-SELECTION-W01-SAFE-BATCH-PLAN`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-NIGHTLY-PREFLIGHT-RISK-REPORT-W01-RISK-FLAGS, FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER-W01-PLAN-LOCK-SUMMARY`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-BATCH-DRY-RUN-SELECTION`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/nightly_preflight_risk_report.py`
- `/opt/astro-project/prefect_grace/platform/nightly_dry_run_controller.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`

## Impacted Modules

- `M-GRACE-NIGHTLY-BATCH-SELECTION`
- `M-GRACE-NIGHTLY-PREFLIGHT`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/nightly_batch_selection.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_batch_selection.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_nightly_batch_selection.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-BATCH-DRY-RUN-SELECTION/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/platform/nightly_preflight_risk_report.py`
- `/opt/astro-project/prefect_grace/platform/nightly_dry_run_controller.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/.worktrees/**`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`

## Must Preserve

- Selector is dry-run/read-only only.
- It selects no packet with unresolved dependencies, approval-required risk, file conflict, missing evidence/review gate, or unknown high-risk status unless explicitly configured to include risky packets in dry-run output only.
- It never starts agents, submits Prefect runs, creates worktrees, applies registry, commits, pushes, merges, or touches backend/frontend/Docker/Playwright.
- Batch size and output lists are bounded.
- CLI JSON envelope keeps `result == data`.

## Recommended Role Assignment

- coder: `Codex high`; deterministic selection over preflight data.
- verifier: `Codex medium`; cover ordering, exclusion reasons, and bounds.
- reviewer: `Codex high`; focus on false inclusion of risky packets.
- rework policy: light resume for display changes; fresh session for dependency/conflict selection bugs.

## Required Design Decisions

### 1. Selection Inputs

The selector should accept either:

- a live preflight report generated in-process from project config; or
- a saved preflight JSON file for deterministic tests.

### 2. Safe Candidate Rules

A packet may be selected only if:

- dependencies are satisfied or selected earlier in the same plan;
- preflight category is safe;
- no approval-required flags are present;
- no file-scope conflict with earlier selected packet;
- test cost is within configured limit;
- packet count limit is not exceeded.

### 3. Exclusion Reasons

Excluded packets must include bounded reasons:

- dependency blocked;
- risk blocked;
- approval required;
- file conflict;
- test cost too high;
- batch limit reached;
- unknown/invalid metadata.

### 4. Output Shape

Return:

- selected packet ids in order;
- excluded packet ids with reasons;
- batch limits;
- conflict groups;
- estimated cost summary;
- stop reason;
- dry-run flag.

## Implementation Requirements

1. Add `prefect_grace/platform/nightly_batch_selection.py`.
2. Add CLI command such as `nightly-select-batch`.
3. Add tests for dependency ordering, conflict exclusion, approval exclusion, cost exclusion, max packet limit, saved-report input, and bounded output.
4. Add CLI contract tests.
5. Add bounded evidence under `EVIDENCE/attempt-0001/`.

## Acceptance Criteria

- Selector returns a deterministic safe batch plan.
- Risky, conflicting, approval-required, dependency-blocked, and expensive packets are excluded with reasons.
- Output remains bounded and keeps `result == data`.
- No execution or mutation occurs.
- Existing preflight and nightly dry-run tests still pass.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_nightly_batch_selection.py \
  tests/test_prefect_grace_cli_nightly_batch_selection.py \
  tests/test_prefect_grace_nightly_preflight_risk_report.py \
  tests/test_prefect_grace_nightly_dry_run_controller.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile, targeted GRACE lint, strict packet validation, and a real project
selection dry-run. Do not execute selected packets.

## Expected Evidence

- Strict validation output.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Real project batch selection dry-run summary.
- Proof no live agents, Prefect runs, worktrees, registry writes, Git mutations, backend, frontend, Docker, Playwright, provider APIs, credentials, or `.worktrees/**` were touched.
- Post-test observability verdict.

## Escalation Triggers

- Selector needs to mutate state or execute packets.
- Risky/approval-required packets are selected as safe.
- Dependency ordering is ambiguous or wrong.
- Output requires unbounded logs or full registry dumps.

## Reviewer Gate

Reviewer must verify that selected packets are genuinely safe according to the
preflight input, not just present in the ready backlog.
