# Execution Packet: FEAT-GRACE-NIGHTLY-PREFLIGHT-RISK-REPORT-W01-RISK-FLAGS

## Objective

Add a nightly preflight risk report for ready GRACE packets. The report should
explain which packets are runnable, blocked, risky, expensive, approval-gated,
or likely to conflict before any live execution starts.

This is a planning and observability packet only. It must not run agents, submit
Prefect runs, create worktrees, mutate registry state, commit, push, or merge.

## Slice

- slice_id: `SLICE-GRACE-NIGHTLY-PREFLIGHT-RISK-REPORT`
- slice_slug: `grace-nightly-preflight-risk-report`
- feature_id: `FEAT-GRACE-NIGHTLY-PREFLIGHT-RISK-REPORT`
- packet_id: `FEAT-GRACE-NIGHTLY-PREFLIGHT-RISK-REPORT-W01-RISK-FLAGS`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-NIGHTLY-DRY-RUN-CONTROLLER-W01-PLAN-LOCK-SUMMARY, FEAT-GRACE-GIT-MUTATION-GATE-W01-COMMIT-PUSH-MERGE-GATE, FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-W01-SOURCE-TO-RUNTIME`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-PREFLIGHT-RISK-REPORT`

## Source Of Truth

- `/opt/astro-project/prefect_grace/platform/nightly_dry_run_controller.py`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/project_adapter.py`
- `/opt/astro-project/prefect_grace/platform/artifact_validator.py`
- `/opt/astro-project/prefect_grace/platform/git_mutation_gate.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_dry_run_controller.py`

## Impacted Modules

- `M-GRACE-NIGHTLY-PREFLIGHT`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-PACKET-PARSER`
- `M-GRACE-RISK-REPORT`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/nightly_preflight_risk_report.py`
- `/opt/astro-project/prefect_grace/cli_commands/prefect_smokes.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_nightly_preflight_risk_report.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_nightly_preflight_risk_report.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-NIGHTLY-PREFLIGHT-RISK-REPORT/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/platform/nightly_dry_run_controller.py`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/.worktrees/**`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`

## Must Preserve

- Preflight is read-only and dry-run only.
- No live agents, Prefect runs, worktrees, Git mutations, registry writes, backend, frontend, Docker, Playwright, provider APIs, or credentials are used.
- Existing `run-nightly --dry-run` behavior is not weakened.
- Risk report uses bounded source packet, review, evidence, registry, and dry-run data.
- Large raw logs, full diffs, screenshots, full registry dumps, and secrets are not emitted.
- CLI JSON envelope keeps `result == data`.

## Recommended Role Assignment

- coder: `Codex high`; mostly deterministic analysis over existing packet metadata.
- verifier: `Codex medium`; must cover risk classification and bounded output.
- reviewer: `Codex high`; focus on false-safe classifications and read-only behavior.
- rework policy: light resume for report wording; fresh session for read-only or dependency-status bugs.

## Required Design Decisions

### 1. Risk Flags

Each packet in the report should include bounded flags such as:

- `dependency_blocked`;
- `source_runtime_mismatch`;
- `review_missing`;
- `evidence_missing`;
- `evidence_invalid`;
- `needs_live_agent`;
- `needs_prefect`;
- `needs_docker`;
- `needs_frontend`;
- `needs_backend`;
- `needs_git_commit`;
- `needs_git_push`;
- `needs_merge_approval`;
- `touches_frozen_scope`;
- `large_file_or_size_debt`;
- `known_legacy_debt`;
- `file_conflict_candidate`;
- `expensive_tests`;
- `operator_approval_required`.

### 2. Conflict Detection

Use allowed write scopes and declared impacted modules to detect likely file
conflicts between ready packets. This is a preflight warning, not a hard source
of truth for scope guard.

### 3. Cost Estimate

Infer rough test cost from verification commands and packet text:

- `unit`;
- `targeted`;
- `backend_quick`;
- `frontend_quick`;
- `docker_required`;
- `live_required`;
- `unknown`.

### 4. Output Shape

Return JSON with:

- project key;
- packet totals by status/risk;
- safe candidates;
- risky candidates;
- blocked candidates;
- approval-required candidates;
- conflict groups;
- warnings/errors.

Lists must be bounded with totals.

## Implementation Requirements

1. Add `prefect_grace/platform/nightly_preflight_risk_report.py`.
2. Add CLI command such as `nightly-preflight-risk-report`.
3. Reuse existing packet parser/bootstrap/dry-run summary where practical.
4. Add tests for dependency blocked, live approval required, git mutation required, conflict group, source/runtime mismatch, missing evidence, accepted safe packet, and bounded output.
5. Add CLI contract tests and JSON envelope assertions.
6. Add bounded evidence under `EVIDENCE/attempt-0001/`.

## Acceptance Criteria

- Command returns a deterministic read-only risk report for source packets.
- Ready packets are classified into safe/risky/blocked/approval-required groups.
- File-scope conflict candidates are detected and bounded.
- Live/Prefect/Docker/backend/frontend/git/merge approval needs are surfaced.
- Output is bounded and keeps `result == data`.
- No execution, worktree creation, registry apply, Git mutation, backend, frontend, Docker, Playwright, provider API, or credentialed service is used.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_nightly_preflight_risk_report.py \
  tests/test_prefect_grace_cli_nightly_preflight_risk_report.py \
  tests/test_prefect_grace_nightly_dry_run_controller.py \
  tests/test_prefect_grace_controller_backlog_bootstrap.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run compile checks:

```bash
python3 -m compileall -q \
  prefect_grace/platform/nightly_preflight_risk_report.py \
  prefect_grace/cli_commands/prefect_smokes.py \
  prefect_grace/cli_commands/parser.py \
  prefect_grace/cli.py
```

Run targeted GRACE lint and strict packet validation. Run a real project
preflight dry-run only; do not execute live paths.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output.
- Compile output.
- Targeted lint output.
- Real project preflight dry-run JSON summary with bounded counts.
- Proof no source packets, runtime registry, worktrees, Git refs, backend, frontend, Docker, Playwright, Prefect, live agents, provider APIs, or credentials were touched.
- Post-test observability verdict.

## Escalation Triggers

- Preflight requires mutation or execution.
- Report labels approval-required packets as safe.
- Conflict detection requires reading unbounded logs or diffs.
- Output includes secrets, full raw logs, screenshots, or full registry dumps.
- Existing nightly dry-run behavior changes unexpectedly.

## Reviewer Gate

Reviewer must verify the report is read-only and cannot be mistaken for an
execution approval.
