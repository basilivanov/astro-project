# Execution Packet: GRACE E2E Runner Status Transition MVP

## Objective

Wire the accepted `status_model` into the accepted dry-run E2E packet runner so
the runner reports both execution domain outcome and the deterministic registry
transition that should follow.

The current E2E runner can return a domain status such as `accepted`,
`rework_required`, `scope_blocked`, or `runner_error`, but it does not yet expose
the canonical registry transition from `apply_domain_result_to_registry(...)`.
Before live execution, this boundary must be explicit and tested.

This packet must not launch live agents and must not implement batch execution.

## Slice

- slice_id: `SLICE-GRACE-E2E-RUNNER-STATUS-TRANSITION-MVP`
- slice_slug: `grace-e2e-runner-status-transition-mvp`
- feature_id: `FEAT-GRACE-E2E-RUNNER-STATUS-TRANSITION-MVP`
- packet_id: `FEAT-GRACE-E2E-RUNNER-STATUS-TRANSITION-MVP-W01-E2E-STATUS-TRANSITION`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-STATUS-MODEL-MVP-W01-STATUS-MODEL, FEAT-GRACE-END-TO-END-PACKET-RUNNER-MVP-W01-E2E-PACKET-RUNNER`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-STATUS-TRANSITION-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/status_model.py`
- `/opt/astro-project/prefect_grace/platform/e2e_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/verifier_reviewer_handoff.py`

## Impacted Modules

- `M-GRACE-E2E-PACKET-RUNNER`
- `M-GRACE-STATUS-MODEL`
- `M-GRACE-WORKTREE-SCOPE-LIFECYCLE`
- `M-GRACE-VERIFIER-REVIEWER-HANDOFF`

## Recommended Role Assignment

- coder: `Sonnet high` or `Codex high`; narrow integration with tests.
- verifier: `Codex medium`; must run E2E runner and status model regressions.
- reviewer: `Codex xhigh` or `Opus`; reviewer must ensure statuses do not drift.
- rework policy: light resume for test/import fixes; fresh session if runner behavior changes broadly.

## Required Design Decisions

### 1. Domain Status Is Not Registry Status

The E2E runner must keep both concepts visible:

```json
{
  "domain_status": "rework_required",
  "registry_status": "ready_for_retry",
  "registry_reason": "quality_rework"
}
```

`domain_status` comes from execution. `registry_status` comes from
`apply_domain_result_to_registry(domain_status)`.

### 2. Only `accepted` Is OK

Runner `ok` must remain:

```python
ok = domain_status == DomainStatus.ACCEPTED.value
```

`rework_required`, `blocked`, `scope_blocked`, `agent_failed`,
`runner_error`, and `handoff_error` must produce `ok=False`.

### 3. Close The Skipped Scope-Blocked Test

The previous E2E runner packet left a skipped scope-blocked test. This packet
must either:

- unskip and implement the scope-blocked case; or
- replace it with a deterministic test that proves a managed runner
  `scope_blocked` result prevents handoff and maps to registry `blocked` with
  reason `scope_violation`.

Do not keep the scope-blocked coverage skipped.

### 4. CLI Must Expose Transition Fields

`run-e2e-packet --json` must include:

- `domain_status`;
- `registry_status`;
- `registry_reason`;
- `ok`.

Text output may include the same fields, but JSON is the contract.

### 5. Dry-Run Only

This packet must not enable live execution. It may preserve existing CLI flags,
but tests must not invoke live agents or provider APIs.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/e2e_packet_runner.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_e2e_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_e2e_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_status_model.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-STATUS-TRANSITION-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/platform/status_model.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/verifier_reviewer_handoff.py`
- `/opt/astro-project/prefect_grace/platform/executor_registry.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/solarsage-astro/**`

## Must Preserve

- E2E runner still defaults to dry-run.
- Public domain status strings stay unchanged.
- CLI exit codes stay unchanged:
  - `0` accepted;
  - `1` domain rework/blocker;
  - `2` runner/config error.
- Status model behavior stays unchanged.
- No live agents or provider APIs are called.
- No product backend/frontend files are modified.
- No merge/push/squash/delete-worktree behavior is added.

## Required Implementation Shape

Extend `E2EPacketRunnerResult` with:

```python
registry_status: str
registry_reason: str
registry_transition: dict[str, Any]
```

The serialized output must remain JSON-safe and string-based:

```json
{
  "domain_status": "scope_blocked",
  "registry_status": "blocked",
  "registry_reason": "scope_violation",
  "registry_transition": {
    "registry_status": "blocked",
    "reason": "scope_violation",
    "is_terminal": true,
    "is_failure": true
  }
}
```

Use:

```python
from prefect_grace.platform.status_model import (
    DomainStatus,
    apply_domain_result_to_registry,
)
```

Do not duplicate transition tables in the E2E runner.

## Safety Assertions

Tests must assert:

- accepted maps to registry `accepted` and reason `execution_accepted`;
- rework_required maps to registry `ready_for_retry` and reason `quality_rework`;
- scope_blocked maps to registry `blocked` and reason `scope_violation`;
- runner_error maps to registry `blocked` and reason `runner_error`;
- `ok` is true only for domain `accepted`;
- `run-e2e-packet --json` includes the new registry fields as strings;
- previous skipped scope-blocked coverage is no longer skipped;
- no live launcher is invoked.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_e2e_packet_runner.py \
  tests/test_prefect_grace_cli_e2e_packet_runner.py \
  tests/test_prefect_grace_status_model.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run focused regressions:

```bash
pytest -q \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_verifier_reviewer_handoff.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace/platform/e2e_packet_runner.py prefect_grace/cli.py
python3 scripts/grace_lint.py prefect_grace/platform/e2e_packet_runner.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-E2E-RUNNER-STATUS-TRANSITION-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run frozen-scope check:

```bash
git diff --name-only -- \
  backend frontend \
  prefect_grace/flows/feature_pipeline.py \
  prefect_grace/tasks/codex_launcher.py \
  prefect_grace/platform/status_model.py \
  prefect_grace/platform/backlog_controller.py \
  prefect_grace/platform/managed_packet_runner.py \
  prefect_grace/platform/worktree_scope_lifecycle.py \
  prefect_grace/platform/verifier_reviewer_handoff.py \
  prefect_grace/platform/executor_registry.py \
  prefect_grace/state \
  scripts/pipeline.py scripts/run_e2e.sh scripts/grace_lint.py \
  tools/post_test_review.py
```

Expected output: empty.

## Expected Evidence

Write evidence under:

```text
EVIDENCE/attempt-0001/evidence_manifest.json
```

Evidence must include:

- transition table for accepted/rework/scope/runner error cases;
- targeted test output;
- focused regression output;
- static check output;
- CLI JSON smoke showing registry fields;
- proof that skipped scope-blocked coverage was closed;
- proof that frozen scope was untouched;
- confirmation that no live agents/providers were called.

## Escalation Triggers

Stop and ask controller if:

- status model behavior needs to change;
- managed packet runner behavior needs to change;
- worktree scope lifecycle behavior needs to change;
- live execution appears necessary;
- CLI exit codes must change;
- source packet markdown must be mutated for runtime state.

## Reviewer Gate

Reviewer must reject this packet if:

- `domain_status` and `registry_status` are conflated;
- transition mapping is duplicated instead of using status model;
- `rework_required` returns `ok=True`;
- scope-blocked coverage remains skipped;
- CLI JSON omits registry transition fields;
- frozen scope is modified;
- live agents are invoked.
