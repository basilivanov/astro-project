# Execution Packet: GRACE Prefect Batch E2E Queue Smoke MVP

## Objective

Add the first controlled batch queue smoke for the portable GRACE packet
orchestrator.

This packet must run only after the one-packet Prefect E2E live smoke is
accepted. Its goal is to prove that a small pack of ready controller packets can
be submitted to Prefect as independent E2E flow runs and remain operator-visible
as a queue, without starting uncontrolled parallel work or bypassing GRACE
registry state.

Target proof:

```text
2-3 ready packets in registry
→ submit-packets --runner e2e --limit N
→ one Prefect flow run per packet
→ all records use E2E deployment
→ deterministic idempotency per packet/source hash
→ queue/concurrency metadata is visible
→ no product code, merge, or live-agent rollout
```

This packet is a queue smoke and safety proof. It is not a merge steward, not a
multi-wave planner, not a feature pipeline replacement, and not broad batch
automation for production features.

## Slice

- slice_id: `SLICE-GRACE-PREFECT-BATCH-E2E-QUEUE-SMOKE-MVP`
- slice_slug: `grace-prefect-batch-e2e-queue-smoke-mvp`
- feature_id: `FEAT-GRACE-PREFECT-BATCH-E2E-QUEUE-SMOKE-MVP`
- packet_id: `FEAT-GRACE-PREFECT-BATCH-E2E-QUEUE-SMOKE-MVP-W01-BATCH-E2E-QUEUE-SMOKE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PREFECT-E2E-LIVE-SMOKE-MVP-W01-E2E-LIVE-SMOKE`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-BATCH-E2E-QUEUE-SMOKE-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/prefect_e2e_live_smoke.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/deploy_live.py`
- `/opt/astro-project/prefect_grace/runtime_config.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/tests/test_prefect_grace_prefect_native_submission.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_submit_packets_prefect_native.py`
- `/opt/astro-project/tests/test_prefect_grace_prefect_e2e_live_smoke.py`

## Impacted Modules

- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-E2E-BATCH-SMOKE`
- `M-GRACE-PREFECT-QUEUE`
- `M-GRACE-REGISTRY-STATE`
- `M-GRACE-CLI`
- `M-GRACE-OBSERVABILITY`

## Recommended Role Assignment

- context collector: `Haiku` or equivalent cheap model, to inspect native submission, live smoke harness, and queue/deployment tests.
- coder: `Sonnet high` or `Codex high`; deterministic batch smoke harness with fake submitter tests.
- verifier: `Codex medium`; must run native submission, batch smoke, CLI, deployment, and E2E flow regressions.
- reviewer: `Codex xhigh` or `Opus`; must verify strict single-queue safety, no product writes, no live-agent batch, and no feature-pipeline coupling.
- rework policy: fresh context for queue/submission semantics changes; light resume only for text/JSON output or fixture naming fixes.

## Required Design Decisions

### 1. Batch Smoke Is Explicitly Dependent On Single-Packet Smoke

Do not implement or run this packet until `FEAT-GRACE-PREFECT-E2E-LIVE-SMOKE-MVP`
is accepted.

Reason: batch queue behavior is only meaningful after the one-packet E2E Prefect
path has proven deployment, submission, registry metadata, and operator
visibility.

### 2. Batch Size Is Small And Bounded

The smoke harness must support exactly small operator-safe batches.

Defaults:

```text
min_packets = 2
max_packets = 3
agent dry-run = true
runner_kind = e2e
```

Hard rules:

- default batch size: `2`;
- maximum accepted batch size: `3`;
- `limit > 3` must fail closed;
- `limit < 2` must tell the operator to use the single-packet smoke instead;
- unit tests must not submit more than 3 packets;
- optional operator live smoke must also stay within the same limit.

### 3. Reuse Native Submission, Do Not Fork Queue Logic

The batch smoke must call existing native submission primitives:

```python
submit_ready_packets_to_prefect(..., runner_kind="e2e", limit=batch_size)
```

Do not reimplement:

- backlog ordering;
- dependency readiness;
- registry storage;
- idempotency key generation;
- Prefect submitter calls;
- deployment name resolution.

If a small helper is missing, add it narrowly with tests.

### 4. Queue Semantics Belong To Prefect

The smoke must not create a local queue or dispatcher.

The operator-visible queue proof should rely on Prefect metadata:

- deployment name;
- work queue name;
- work pool name when available;
- flow run ids;
- flow run names;
- submitted order;
- idempotency keys.

If concurrency evidence is available from config/tests, assert it is `1` for the
live queue. If not available in offline tests, assert that submitted records
carry the queue metadata returned by the fake submitter.

### 5. Default Mode Is Prefect Live / Agent Dry-Run

The mandatory smoke mode submits real Prefect runs but keeps agent execution dry:

```text
dry_run=True
execute_agent=False
runner_kind=e2e
```

This proves Prefect queue behavior without spending model budget or modifying
product files.

### 6. Batch Live-Agent Mode Is Out Of Scope

This packet must not enable live-agent batch execution.

Even if single-packet live-agent smoke exists, batch live-agent mode requires a
separate controller decision and a later packet.

Fail closed if an operator attempts:

```text
batch_size > 1 and execute_agent=True
```

Allowed in this packet:

- batch Prefect run creation;
- agent dry-run inside E2E flows;
- fake submitter tests.

Forbidden in this packet:

- batch Codex/Claude/agy execution;
- provider API calls in tests;
- automatic rework loop for batch failures.

### 7. Smoke Packets Must Be Scratch-Only

Generated smoke packets must write only under:

```text
scratch/grace-batch-smoke/**
```

Frozen scope for generated smoke packets must include:

- `backend/**`;
- `frontend/**`;
- `prefect_grace/**` except generated packet artifact directories;
- `.env`;
- `docker-compose*.yml`;
- `scripts/**`;
- `tools/**`.

### 8. Result Must Be Operator-Readable

Add a JSON-safe result model for batch smoke.

Required fields:

```json
{
  "ok": true,
  "mode": "prefect_agent_dry_run",
  "batch_size": 2,
  "runner_kind": "e2e",
  "deployment_name": "prefect-grace-e2e-packet-runner/live-e2e-packet-runner",
  "work_queue_name": "grace-live",
  "packets_planned": ["..."],
  "packets_submitted": ["..."],
  "records": [
    {
      "packet_id": "...",
      "flow_run_id": "...",
      "flow_run_name": "...",
      "idempotency_key": "...",
      "status": "submitted"
    }
  ],
  "errors": []
}
```

The text output must show:

- batch size;
- submitted count;
- deployment name;
- queue name;
- each packet id and flow run id.

### 9. Add CLI Command

Preferred command:

```bash
python3 -m prefect_grace.cli run-prefect-e2e-batch-smoke \
  --project-config /opt/astro-project/prefect_grace/project.yaml \
  --state-root /tmp/grace-batch-smoke-state \
  --worktree-root /tmp/grace-batch-smoke-worktrees \
  --packet-root /tmp/grace-batch-smoke-packets \
  --batch-size 2 \
  --json
```

Required behavior:

- `--batch-size` default `2`;
- `--batch-size 2|3` accepted;
- `--batch-size 1` rejected with message pointing to single-packet smoke;
- `--batch-size >3` rejected;
- `--execute-agent` rejected for batch mode in this packet;
- `--json` follows the standard CLI envelope.

### 10. No Merge / Completion Claims

The batch smoke may report submission success, but must not mark packets as
accepted unless the E2E flow result later returns `domain_status=accepted`.

This packet should not implement polling-to-completion unless it is purely
optional and bounded. If polling is added, it must be off by default and must not
change registry status beyond submitted run metadata.

### 11. No Feature Pipeline Coupling

The batch smoke must not use:

- `prefect_grace/flows/feature_pipeline.py`;
- `prefect-grace-feature-pipeline/live-feature-pipeline`;
- old business feature pipeline run naming;
- old dispatcher/job queue code.

The queue smoke is for portable packet orchestration only.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/prefect_e2e_batch_smoke.py`
- `/opt/astro-project/prefect_grace/cli.py`

Narrow integration changes if required:

- `/opt/astro-project/prefect_grace/platform/prefect_e2e_live_smoke.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_prefect_e2e_batch_smoke.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_prefect_e2e_batch_smoke.py`
- `/opt/astro-project/tests/test_prefect_grace_prefect_native_submission.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_submit_packets_prefect_native.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PREFECT-BATCH-E2E-QUEUE-SMOKE-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/**`
- `/opt/astro-project/prefect_grace/flows/e2e_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/platform/e2e_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/status_model.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/verifier_reviewer_handoff.py`
- `/opt/astro-project/prefect_grace/platform/runtime_adapter.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/tasks/e2e_packet_artifacts.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/docker-compose*.yml`
- `/opt/solarsage-astro/**`

## Must Preserve

- Single-packet live smoke behavior remains unchanged.
- Native submission E2E behavior remains unchanged except batch smoke usage.
- `submit-packets` remains dry-run safe by default.
- Batch smoke submits at most 3 packets.
- Batch smoke rejects live-agent execution.
- Unit tests do not call live Prefect, live agents, provider APIs, Docker, backend, or frontend.
- No product backend/frontend files are modified.
- No merge, push, squash, accept, or delete-worktree behavior is added.
- Feature pipeline deployment and behavior remain unchanged.
- Idempotency keys remain deterministic and source-hash based.

## Required Implementation Shape

### Batch Smoke Result Model

Add:

```python
@dataclass(frozen=True)
class PrefectE2EBatchSmokeResult:
    ok: bool
    mode: str
    batch_size: int
    runner_kind: str
    deployment_name: str
    work_queue_name: str | None
    packets_planned: list[str]
    packets_submitted: list[str]
    records: list[dict[str, Any]]
    errors: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]: ...
```

### Batch Smoke Function

Add:

```python
def run_prefect_e2e_batch_smoke(
    *,
    project_config: Path,
    state_root: Path,
    worktree_root: Path,
    packet_root: Path,
    batch_size: int = 2,
    submitter: Callable[..., dict[str, Any]] | None = None,
) -> PrefectE2EBatchSmokeResult:
    ...
```

The function must:

1. validate `2 <= batch_size <= 3`;
2. generate exactly `batch_size` strict smoke packets;
3. create/load registry records for those packets;
4. call native submission with `runner_kind="e2e"` and `limit=batch_size`;
5. verify the number of submitted records equals `batch_size` in fake/execute mode;
6. return structured errors instead of raising for operator guard failures.

### CLI

Add:

```bash
python3 -m prefect_grace.cli run-prefect-e2e-batch-smoke --help
```

Required flags:

- `--project-config`;
- `--state-root`;
- `--worktree-root`;
- `--packet-root`;
- `--batch-size`;
- `--json`.

If `--execute-agent` is exposed, it must always fail closed in this packet.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_e2e_batch_smoke.py \
  tests/test_prefect_grace_cli_prefect_e2e_batch_smoke.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run focused regressions:

```bash
pytest -q \
  tests/test_prefect_grace_prefect_e2e_live_smoke.py \
  tests/test_prefect_grace_prefect_native_submission.py \
  tests/test_prefect_grace_cli_submit_packets_prefect_native.py \
  tests/test_prefect_grace_e2e_packet_runner_flow.py
```

Run static checks:

```bash
python3 -m compileall -q \
  prefect_grace/platform/prefect_e2e_batch_smoke.py \
  prefect_grace/cli.py

python3 scripts/grace_lint.py \
  prefect_grace/platform/prefect_e2e_batch_smoke.py

python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PREFECT-BATCH-E2E-QUEUE-SMOKE-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run offline CLI smoke with fake submitter/test fixture:

```bash
python3 -m prefect_grace.cli run-prefect-e2e-batch-smoke \
  --project-config /tmp/grace-batch-smoke/project.yaml \
  --state-root /tmp/grace-batch-smoke/state \
  --worktree-root /tmp/grace-batch-smoke/worktrees \
  --packet-root /tmp/grace-batch-smoke/packets \
  --batch-size 2 \
  --json
```

Optional operator live Prefect smoke after review acceptance:

```bash
python3 -m prefect_grace.cli run-prefect-e2e-batch-smoke \
  --project-config /opt/astro-project/prefect_grace/project.yaml \
  --state-root /tmp/grace-batch-smoke-state \
  --worktree-root /tmp/grace-batch-smoke-worktrees \
  --packet-root /tmp/grace-batch-smoke-packets \
  --batch-size 2 \
  --json
```

Do not run any batch live-agent mode in this packet.

## Expected Evidence

Attach under `EVIDENCE/attempt-XXXX/`:

- targeted pytest output;
- focused regression pytest output;
- compile output;
- GRACE lint output;
- packet validation JSON;
- offline CLI smoke JSON showing two E2E records;
- fake submitter execution evidence showing exactly two packets submitted to E2E deployment;
- guard test output for `batch_size=1`, `batch_size=4`, and live-agent rejection;
- `git diff --stat`;
- full changed file list;
- explicit note that unit tests did not call live agents, provider APIs, live Prefect, Docker, product backend/frontend services, merge, squash, or push;
- if optional operator live smoke is run, include both Prefect flow run ids, deployment name, queue name, and submitted order.

## Escalation Triggers

Stop and ask the controller if:

- implementation needs to modify product backend/frontend code;
- implementation needs to modify `feature_pipeline.py`;
- implementation needs to modify `codex_launcher.py`;
- implementation needs to change E2E runner status semantics;
- implementation needs a local queue or dispatcher;
- implementation needs batch live-agent execution;
- implementation needs more than 3 packets;
- smoke packet needs write scope outside `scratch/grace-batch-smoke/**`;
- tests require a live Prefect server.

## Reviewer Checklist

- Batch smoke depends on accepted single-packet live smoke.
- Batch size is limited to 2-3.
- E2E runner kind is enforced.
- Native submission is reused, not forked.
- Queue metadata is operator-visible.
- Live-agent batch execution is impossible.
- No feature-pipeline coupling is introduced.
- No product files are touched.
- Unit tests are offline and deterministic.
- Frozen scope is clean.
