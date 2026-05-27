# Execution Packet: GRACE End-To-End Packet Runner MVP

## Objective

Implement the first deterministic end-to-end packet runner that wires together
the existing GRACE orchestration primitives without launching live agents.

The runner must prove that a single `ready` controller packet can move through
the platform path:

```text
packet discovery
→ registry readiness
→ worktree creation/reuse
→ executor selection
→ managed packet runner dry-run
→ worktree scope lifecycle
→ verifier/reviewer handoff dry-run
→ registry domain status update
→ optional Prefect artifact publication
```

This packet is not a new agent executor and not a replacement for the existing
large `feature_pipeline.py`. It is a portable orchestration seam that can later
be called from Prefect deployments and from CLI batch submission.

## Slice

- slice_id: `SLICE-GRACE-END-TO-END-PACKET-RUNNER-MVP`
- slice_slug: `grace-end-to-end-packet-runner-mvp`
- feature_id: `FEAT-GRACE-END-TO-END-PACKET-RUNNER-MVP`
- packet_id: `FEAT-GRACE-END-TO-END-PACKET-RUNNER-MVP-W01-E2E-PACKET-RUNNER`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER, FEAT-GRACE-PREFECT-NATIVE-SUBMISSION-MVP-W01-PREFECT-NATIVE-SUBMISSION, FEAT-GRACE-VERIFIER-REVIEWER-HANDOFF-MVP-W01-VERIFIER-REVIEWER-HANDOFF, FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP-W01-API-FAILURE-CLASSIFIER`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-END-TO-END-PACKET-RUNNER-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/worktree_manager.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/executor_registry.py`
- `/opt/astro-project/prefect_grace/platform/verifier_reviewer_handoff.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/flows/managed_packet_runner_flow.py`
- `/opt/astro-project/prefect_grace/flows/verifier_reviewer_handoff_flow.py`
- `/opt/astro-project/prefect_grace/flows/worktree_scope_lifecycle_flow.py`

## Impacted Modules

- `M-GRACE-E2E-PACKET-RUNNER`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-MANAGED-PACKET-RUNNER`
- `M-GRACE-WORKTREE-SCOPE-LIFECYCLE`
- `M-GRACE-VERIFIER-REVIEWER-HANDOFF`
- `M-GRACE-PREFECT-ARTIFACTS`

## Recommended Role Assignment

- coder: `Sonnet high` or `Codex high`; integration-heavy, deterministic, no live agents.
- verifier: `Codex medium`; must run offline temp-repo tests and CLI smoke.
- reviewer: `Codex xhigh` or `Opus`; reviewer must focus on safety boundaries and status semantics.
- rework policy: fresh session for orchestration/status bugs; light resume only for CLI naming or import fixes.

## Required Design Decisions

### 1. Dry-Run First

The default runner mode must be dry-run and must not launch Codex, Claude,
agy, OpenRouter, OpenAI, cliproxy, Docker, backend, frontend, or any live
Prefect deployment.

Live agent execution is out of scope. The runner may expose an explicit future
flag shape, but this packet must not enable live execution by default and must
not require real credentials.

### 2. Platform Status Is Domain Status

The runner must separate:

- runtime execution status: `started`, `completed`, `failed`;
- domain packet status: `accepted`, `rework_required`, `blocked`,
  `scope_blocked`, `agent_failed`, `runner_error`.

Do not invent a third status vocabulary. If existing modules already expose
equivalent values, reuse them and normalize at this boundary.

### 3. Existing Primitives Are Source Of Truth

The runner must call existing primitives instead of reimplementing them:

- packet parsing/readiness: backlog/parser/registry layer;
- worktree operations: `WorktreeManager`;
- execution: `run_managed_packet(...)` or its current public equivalent;
- scope validation: `evaluate_worktree_scope(...)`;
- handoff validation: verifier/reviewer handoff module;
- artifact publication: existing best-effort artifact helpers.

If an existing primitive is missing a small parameter needed for composition,
add that parameter narrowly with tests. Do not fork the logic.

### 4. One Packet Only

This MVP runs exactly one packet per invocation. Batch execution and dependency
queue draining remain a later packet. The input contract may include
`packet_id`, `packet_path`, or `packet_dir`, but execution order planning must
not be expanded here.

### 5. No Merge Steward Yet

The runner must not merge, squash, push, or delete worktrees after success.
It may report that a packet is accepted and ready for a future merge steward,
but merge policy belongs to a later packet.

### 6. Handoff Uses Fake Agent Output

The verifier/reviewer handoff step must be exercised with deterministic fake
verifier/reviewer output in tests and dry-run CLI smoke. The platform validates
marker parsing, artifact paths, and routing, but does not ask a live LLM to
verify or review in this packet.

### 7. Prefect Is Optional Runtime Wrapper

The core runner must be importable and testable without a running Prefect
server. If a Prefect flow wrapper is added, it must be thin and may publish
artifacts best-effort. A Prefect artifact failure must not hide the domain
result.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/e2e_packet_runner.py`
- `/opt/astro-project/prefect_grace/cli.py`

Narrow integration changes if required:

- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/worktree_scope_lifecycle.py`
- `/opt/astro-project/prefect_grace/platform/verifier_reviewer_handoff.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_e2e_packet_runner.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_e2e_packet_runner.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-END-TO-END-PACKET-RUNNER-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/pipeline_helpers/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing managed packet runner tests keep passing.
- Existing worktree scope lifecycle tests keep passing.
- Existing verifier/reviewer handoff tests keep passing.
- Existing Prefect native submission tests keep passing.
- No product backend/frontend files are modified.
- No live agents or provider APIs are called by tests.
- No merge/push/squash/delete-worktree operation happens.
- The core runner remains usable without a live Prefect server.
- The CLI defaults to dry-run / fake-output-safe behavior.

## Required Implementation Shape

Add a pure orchestration module:

```python
class E2EPacketRunnerResult:
    ok: bool
    packet_id: str
    runtime_status: str
    domain_status: str
    worktree_path: str | None
    executor_id: str | None
    managed_runner_result: dict
    scope_result: dict
    handoff_result: dict
    artifact_paths: list[str]
    errors: list[str]
```

Add a public function:

```python
def run_e2e_packet(
    *,
    project_root: Path,
    packet_path: Path,
    state_root: Path,
    worktree_root: Path,
    dry_run: bool = True,
    fake_verifier_output: Path | None = None,
    fake_reviewer_output: Path | None = None,
) -> E2EPacketRunnerResult:
    ...
```

Implementation order:

1. Parse and validate the packet contract.
2. Ensure the packet is runnable or explicitly selected for dry-run execution.
3. Create or reuse a worktree using `WorktreeManager`.
4. Select executor metadata using `ExecutorRegistry` / project adapter config if available.
5. Run the managed packet runner with `dry_run=True` by default.
6. Evaluate worktree scope.
7. Run verifier/reviewer handoff in dry-run/fake-output mode.
8. Normalize the domain status.
9. Persist only runtime state necessary for visibility; do not mutate source packet markdown.
10. Publish optional artifacts best-effort if Prefect is available.

## CLI Contract

Add a command:

```bash
python3 -m prefect_grace.cli run-e2e-packet \
  --project-root /path/to/project \
  --packet /path/to/EXECUTION_PACKET.md \
  --state-root /tmp/grace-state \
  --worktree-root /tmp/grace-worktrees \
  --fake-verifier-output /tmp/verifier.txt \
  --fake-reviewer-output /tmp/reviewer.txt \
  --dry-run \
  --json
```

Default behavior:

- `--dry-run` is true unless explicitly disabled by a future packet.
- JSON output follows the existing CLI envelope:

```json
{
  "ok": true,
  "command": "run-e2e-packet",
  "result": {
    "runtime_status": "completed",
    "domain_status": "accepted"
  }
}
```

Exit codes:

- `0`: domain status is `accepted`;
- `1`: domain status is `rework_required`, `blocked`, `scope_blocked`, or `agent_failed`;
- `2`: runner/config/error path.

## Safety Assertions

Tests must assert:

- dry-run is the default;
- fake verifier/reviewer outputs are accepted and validated;
- no live agent command is invoked;
- no Prefect server is required;
- worktree path stays under `worktree_root`;
- scope failure returns `scope_blocked` and prevents acceptance;
- handoff blocker returns `rework_required` or `blocked` and prevents acceptance;
- successful dry-run returns `accepted`;
- source `EXECUTION_PACKET.md` is not mutated by runtime evidence;
- repeated dry-run on the same packet is idempotent or reports deterministic reuse;
- artifact publication failure does not convert an accepted domain result into runner failure.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_e2e_packet_runner.py \
  tests/test_prefect_grace_cli_e2e_packet_runner.py
```

Run integration regressions:

```bash
pytest -q \
  tests/test_prefect_grace_managed_packet_runner.py \
  tests/test_prefect_grace_worktree_scope_lifecycle.py \
  tests/test_prefect_grace_verifier_reviewer_handoff.py \
  tests/test_prefect_grace_prefect_native_submission.py \
  tests/test_prefect_grace_executor_registry.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace/platform/e2e_packet_runner.py prefect_grace/cli.py
python3 scripts/grace_lint.py prefect_grace/platform/e2e_packet_runner.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-END-TO-END-PACKET-RUNNER-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke in a temporary git repo/worktree root:

```bash
python3 -m prefect_grace.cli run-e2e-packet \
  --project-root "$TMP_PROJECT" \
  --packet "$TMP_PROJECT/prefect_grace/packets/SMOKE/EXECUTION_PACKET.md" \
  --state-root "$TMP_STATE" \
  --worktree-root "$TMP_WORKTREES" \
  --fake-verifier-output "$TMP_VERIFIER" \
  --fake-reviewer-output "$TMP_REVIEWER" \
  --dry-run \
  --json
```

## Expected Evidence

Write evidence under:

```text
EVIDENCE/attempt-0001/evidence_manifest.json
```

Evidence must include:

- targeted test output;
- integration regression output;
- static check output;
- CLI smoke JSON output;
- list of created/reused worktree paths;
- proof that `EXECUTION_PACKET.md` source hash did not change;
- proof that no live agents/providers were called;
- proof that no merge/push/squash/delete-worktree operation happened;
- domain status table for accepted, scope-blocked, and handoff-blocked cases.

## Escalation Triggers

Stop and ask controller if:

- live agent execution appears necessary;
- real Prefect server access appears necessary;
- merge/push/squash/delete-worktree appears necessary;
- `feature_pipeline.py` or `codex_launcher.py` appears necessary to edit;
- packet source markdown must be mutated to store runtime evidence;
- batch dependency execution appears necessary.

## Reviewer Gate

Reviewer must reject this packet if:

- dry-run is not the default;
- any live provider or agent is called by tests;
- `feature_pipeline.py` or `codex_launcher.py` is modified;
- packet source markdown is mutated by runtime evidence;
- scope-blocked packets can still become accepted;
- handoff-blocked packets can still become accepted;
- Prefect artifact failure hides or changes the domain result;
- merge/push/squash/delete-worktree behavior is added.
