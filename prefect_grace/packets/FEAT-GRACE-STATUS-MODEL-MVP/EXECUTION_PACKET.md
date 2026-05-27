# Execution Packet: GRACE Status Model MVP

## Objective

Introduce a strict, centralized status model for GRACE orchestration so source
packet intent, runtime registry state, and execution domain outcomes stop
drifting across modules.

The current platform uses overlapping string statuses in several layers:

```text
source packet status   → ready / blocked / accepted
registry status        → ready / running / accepted / blocked / cascading_blocked / waiting_for_dependencies / ready_for_retry / changed_after_acceptance
domain execution       → passed / accepted / rework_required / blocked / scope_blocked / agent_failed / verifier_failed / reviewer_failed / handoff_error / runner_error
```

This packet must create a typed status model and deterministic transition
helpers. It must not rewrite the legacy `feature_pipeline.py` state machine in
this wave. The goal is to give new orchestration code, especially
`FEAT-GRACE-END-TO-END-PACKET-RUNNER-MVP`, one canonical status vocabulary.

## Slice

- slice_id: `SLICE-GRACE-STATUS-MODEL-MVP`
- slice_slug: `grace-status-model-mvp`
- feature_id: `FEAT-GRACE-STATUS-MODEL-MVP`
- packet_id: `FEAT-GRACE-STATUS-MODEL-MVP-W01-STATUS-MODEL`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER, FEAT-GRACE-VERIFIER-REVIEWER-HANDOFF-MVP-W01-VERIFIER-REVIEWER-HANDOFF, FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-STATUS-MODEL-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/verifier_reviewer_handoff.py`
- `/opt/astro-project/prefect_grace/platform/executor_registry.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`

## Impacted Modules

- `M-GRACE-STATUS-MODEL`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-MANAGED-PACKET-RUNNER`
- `M-GRACE-WORKTREE-SCOPE-LIFECYCLE`
- `M-GRACE-VERIFIER-REVIEWER-HANDOFF`
- `M-GRACE-EXECUTOR-REGISTRY`

## Recommended Role Assignment

- coder: `Sonnet high` or `Codex high`; enum/model extraction plus narrow integration.
- verifier: `Codex medium`; must run transition table tests and existing runner/handoff regressions.
- reviewer: `Codex xhigh` or `Opus`; reviewer must reject broad rewrites or hidden status renames.
- rework policy: light resume for enum naming/test fixes; fresh session if state machine semantics change.

## Required Design Decisions

### 1. Three Status Layers

The model must separate three layers:

```python
class SourcePacketStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    BLOCKED = "blocked"
    SUPERSEDED = "superseded"
    ACCEPTED = "accepted"  # legacy-compatible only

class RegistryStatus(str, Enum):
    READY = "ready"
    READY_FOR_RETRY = "ready_for_retry"
    WAITING_FOR_DEPENDENCIES = "waiting_for_dependencies"
    RUNNING = "running"
    BLOCKED = "blocked"
    CASCADING_BLOCKED = "cascading_blocked"
    ACCEPTED = "accepted"
    CHANGED_AFTER_ACCEPTANCE = "changed_after_acceptance"

class DomainStatus(str, Enum):
    ACCEPTED = "accepted"
    REWORK_REQUIRED = "rework_required"
    BLOCKED = "blocked"
    SCOPE_BLOCKED = "scope_blocked"
    AGENT_FAILED = "agent_failed"
    VERIFIER_FAILED = "verifier_failed"
    REVIEWER_FAILED = "reviewer_failed"
    RUNNER_ERROR = "runner_error"
    HANDOFF_ERROR = "handoff_error"
    CHECK_PASSED = "passed"  # compatibility alias for local gates only
```

`passed` must not be used as the preferred final packet domain status in new
code. New end-to-end packet execution should normalize successful local gate
passes to `accepted` only after verifier/reviewer acceptance.

### 2. Domain Result Drives Registry Transition

`DomainStatus` is an execution result. It is not the registry state. It must
map through explicit transition helpers:

```python
apply_domain_result_to_registry(
    domain_status: DomainStatus | str,
    current_registry_status: RegistryStatus | str | None = None,
    *,
    api_failure_category: str | None = None,
) -> StatusTransition
```

Minimum transition table:

| Domain status | Registry status | Reason |
| --- | --- | --- |
| `accepted` | `accepted` | `execution_accepted` |
| `passed` | `accepted` | `local_gate_passed` |
| `rework_required` | `ready_for_retry` | `quality_rework` |
| `blocked` | `blocked` | `domain_blocked` |
| `scope_blocked` | `blocked` | `scope_violation` |
| `agent_failed` | `blocked` | `agent_execution_failed` |
| `verifier_failed` | `blocked` | `verifier_failed` |
| `reviewer_failed` | `blocked` | `reviewer_failed` |
| `runner_error` | `blocked` | `runner_error` |
| `handoff_error` | `blocked` | `handoff_error` |
| unknown string | `blocked` | `unknown_domain_status:<value>` |

API failure metadata may refine the reason but must not introduce ad-hoc
registry statuses in this packet.

### 3. Legacy String Normalization

Existing code uses strings. This packet must support legacy inputs without
breaking callers:

```python
normalize_source_status(value: SourcePacketStatus | str | None) -> SourcePacketStatus
normalize_registry_status(value: RegistryStatus | str | None) -> RegistryStatus
normalize_domain_status(value: DomainStatus | str | None) -> DomainStatus
```

Normalization rules:

- exact enum values pass through;
- known strings map to their enum;
- missing source status defaults to `SourcePacketStatus.READY` only where the
  parser currently behaves that way;
- missing domain status maps to a safe blocked/runner-error path, not to
  accepted;
- unknown status strings must not silently become success.

### 4. Narrow Integration Only

Integrate the status model only where it reduces drift without broad rewrites:

- `backlog_controller.py`: registry status constants and transition helper use
  in focused places;
- `managed_packet_runner.py`: `domain_status` constants/normalization;
- `worktree_scope_lifecycle.py`: `passed` / `scope_blocked` normalization;
- `verifier_reviewer_handoff.py`: accepted/rework/blocked/handoff error values;
- `executor_registry.py`: failure classification should use normalized domain
  status instead of raw string checks where practical.

Do not rewrite `feature_pipeline.py` in this packet. It is explicitly deferred
to later refactor packets.

### 5. No Behavior Change Unless Covered

The first implementation may preserve string outputs in public JSON/CLI
responses. Enums are an internal safety model; external output remains strings.

Any changed public status value is a behavior change and must have an explicit
test and reviewer approval.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/status_model.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/verifier_reviewer_handoff.py`
- `/opt/astro-project/prefect_grace/platform/executor_registry.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_status_model.py`
- `/opt/astro-project/tests/test_prefect_grace_backlog_controller.py`
- `/opt/astro-project/tests/test_prefect_grace_managed_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_worktree_scope_lifecycle.py`
- `/opt/astro-project/tests/test_prefect_grace_verifier_reviewer_handoff.py`
- `/opt/astro-project/tests/test_prefect_grace_executor_registry.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-STATUS-MODEL-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/**`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing public CLI/JSON status strings stay stable unless explicitly tested.
- Existing backlog controller tests keep passing.
- Existing managed packet runner tests keep passing.
- Existing worktree scope lifecycle tests keep passing.
- Existing verifier/reviewer handoff tests keep passing.
- Existing executor registry tests keep passing.
- No product backend/frontend files are modified.
- No live agents, provider APIs, Prefect deployments, Docker services, or e2e
  browsers are launched by tests.

## Required Implementation Shape

Add `prefect_grace/platform/status_model.py` with:

- `SourcePacketStatus`;
- `RegistryStatus`;
- `DomainStatus`;
- `StatusTransition`;
- `normalize_source_status(...)`;
- `normalize_registry_status(...)`;
- `normalize_domain_status(...)`;
- `apply_domain_result_to_registry(...)`;
- helper predicates:
  - `is_terminal_registry_status(...)`;
  - `is_runnable_registry_status(...)`;
  - `is_failure_domain_status(...)`;
  - `is_scope_domain_status(...)`.

Every public function must have GRACE function contracts.

## Safety Assertions

Tests must assert:

- all known legacy strings normalize to the expected enum;
- unknown domain status maps to blocked transition, never accepted;
- `accepted` domain result maps to `accepted` registry status;
- `passed` maps to `accepted` only as compatibility/local-gate transition;
- `rework_required` maps to `ready_for_retry`;
- `scope_blocked` maps to `blocked` with `scope_violation`;
- `agent_failed` maps to `blocked` and does not count as quality rework;
- public `.to_dict()` / CLI JSON outputs still contain strings, not raw enum objects;
- `feature_pipeline.py` and `codex_launcher.py` are unchanged.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_status_model.py \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_verifier_reviewer_handoff.py \
  tests/test_prefect_grace_executor_registry.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py
python3 scripts/grace_lint.py prefect_grace/platform/status_model.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-STATUS-MODEL-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run frozen-scope check:

```bash
git diff --name-only -- \
  backend frontend \
  prefect_grace/flows/feature_pipeline.py \
  prefect_grace/flows/pipeline_helpers \
  prefect_grace/tasks/codex_launcher.py \
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

- status transition table;
- normalization table for legacy strings;
- targeted test output;
- static check output;
- frozen-scope check output;
- confirmation that public JSON statuses remain strings;
- confirmation that `feature_pipeline.py` and `codex_launcher.py` were not touched.

## Escalation Triggers

Stop and ask controller if:

- `feature_pipeline.py` appears necessary to edit;
- `codex_launcher.py` appears necessary to edit;
- public JSON status strings must be renamed;
- a fourth status layer appears necessary;
- live execution or Prefect server access appears necessary;
- unknown status handling would have to become success-compatible.

## Reviewer Gate

Reviewer must reject this packet if:

- unknown statuses can become accepted;
- `passed` becomes the preferred final packet status in new orchestration code;
- enums leak into public JSON responses;
- `feature_pipeline.py` or `codex_launcher.py` is modified;
- registry status and domain status are still used interchangeably;
- broad behavioral rewrites are mixed into the enum migration.
