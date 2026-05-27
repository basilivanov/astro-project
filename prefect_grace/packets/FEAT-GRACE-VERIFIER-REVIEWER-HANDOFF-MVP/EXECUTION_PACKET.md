# Execution Packet: GRACE Verifier Reviewer Handoff MVP

## Objective

Implement the formal handoff from a completed coder packet run to verifier and
reviewer agents.

The goal is to stop treating evidence as an informal Markdown note and make the
packet acceptance path explicit:

```text
coder managed packet result
  -> verifier handoff bundle
  -> verifier agent produces evidence manifest
  -> deterministic evidence validation
  -> reviewer handoff bundle
  -> reviewer agent produces packet decision
  -> deterministic decision/routing record
```

The verifier and reviewer remain LLM agents. They are not replaced by scripts.
The platform layer only controls context shape, marker parsing, manifest
validation, artifact existence checks, and routing semantics.

This packet must not merge, push, accept wave-level architecture, create
feature-level plans, register deployments, or run production backend/frontend
services in tests.

Hard prerequisite: this packet is executable only after
`FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS` and
`FEAT-GRACE-EXECUTOR-REGISTRY-MVP-W01-EXECUTOR-REGISTRY` are accepted. If the
evidence modules (`evidence_contract.py`, `evidence_manifest.py`,
`artifact_validator.py`, `blocker_routing.py`) are missing, do not implement
them here; stop and report dependency_not_ready.

## Slice

- slice_id: `SLICE-GRACE-VERIFIER-REVIEWER-HANDOFF-MVP`
- slice_slug: `grace-verifier-reviewer-handoff-mvp`
- feature_id: `FEAT-GRACE-VERIFIER-REVIEWER-HANDOFF-MVP`
- packet_id: `FEAT-GRACE-VERIFIER-REVIEWER-HANDOFF-MVP-W01-HANDOFF`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-EVIDENCE-CONTRACTS-MVP-W01-EVIDENCE-CONTRACTS, FEAT-GRACE-MANAGED-PACKET-RUNNER-MVP-W01-MANAGED-PACKET-RUNNER, FEAT-GRACE-EXECUTOR-REGISTRY-MVP-W01-EXECUTOR-REGISTRY, FEAT-GRACE-PACKET-ARTIFACT-LAYOUT-MVP-W01-PACKET-ARTIFACT-LAYOUT`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-VERIFIER-REVIEWER-HANDOFF-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/evidence_contract.py`
- `/opt/astro-project/prefect_grace/platform/evidence_manifest.py`
- `/opt/astro-project/prefect_grace/platform/artifact_validator.py`
- `/opt/astro-project/prefect_grace/platform/blocker_routing.py`
- `/opt/astro-project/prefect_grace/platform/packet_artifact_layout.py`
- `/opt/astro-project/prefect_grace/platform/context_bundle.py`
- `/opt/astro-project/prefect_grace/platform/packet_artifacts.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/executor_registry.py`
- `/opt/astro-project/prefect_grace/tasks/agent_output_parser.py` (marker names
  and legacy semantics only; do not mutate it in this packet)
- `/opt/astro-project/prefect_grace/prompts/verifier_prompt.md`
- `/opt/astro-project/prefect_grace/prompts/reviewer_prompt.md`
- `/opt/astro-project/prefect_grace/cli.py`

## Impacted Modules

- `M-GRACE-HANDOFF-CONTROLLER`
- `M-GRACE-VERIFIER-HANDOFF`
- `M-GRACE-REVIEWER-HANDOFF`
- `M-GRACE-EVIDENCE-MANIFEST`
- `M-GRACE-PACKET-DECISION`
- `M-GRACE-BLOCKER-ROUTING`
- `M-GRACE-PACKET-ARTIFACTS`
- `M-GRACE-CLI`

## Recommended Role Assignment

- context collector: `Haiku` or cheap equivalent, useful for mapping existing prompts, evidence schema, and artifact layout.
- coder: `Sonnet high` or `Codex high`; deterministic parsers/flow/CLI, no product code.
- verifier: `Codex medium`; must run offline tests with fake agent outputs and marker parsing.
- reviewer: `Opus` or `Codex xhigh`; must verify routing semantics and ensure verifier/reviewer remain agents.
- rework policy: fresh context if JSON marker schemas or domain statuses change; light resume only for markdown/text output formatting fixes.

## Required Design Decisions

### 1. Add Handoff Controller Module

Add:

```text
prefect_grace/platform/verifier_reviewer_handoff.py
```

Required public API:

```python
@dataclass(frozen=True)
class HandoffAgentResult:
    ok: bool
    role: Literal["verifier", "reviewer"]
    packet_id: str
    raw_output: str
    parsed_json: dict[str, Any] | None
    marker_found: bool
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class PacketHandoffResult:
    ok: bool
    domain_status: Literal[
        "accepted",
        "rework_required",
        "blocked",
        "escalate_to_architect",
        "verifier_failed",
        "reviewer_failed",
        "handoff_error",
    ]
    packet_id: str
    attempt: int
    verifier: HandoffAgentResult
    reviewer: HandoffAgentResult | None
    evidence_manifest_path: str | None
    review_path: str | None
    rework_path: str | None
    route_classification: str | None = None
    rework_mode: str | None = None
    blocker_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        ...


def run_verifier_reviewer_handoff(
    *,
    packet_dir: Path,
    packet_file: Path,
    attempt: int,
    coder_result: dict[str, Any],
    verifier_launcher: Callable[..., dict[str, Any]],
    reviewer_launcher: Callable[..., dict[str, Any]],
    project: Any | None = None,
    dry_run: bool = True,
) -> PacketHandoffResult:
    ...
```

Tests must use fake `verifier_launcher` and `reviewer_launcher` callables. No
live agents are launched in tests.

Launcher output contract:

- fake/offline launchers may return `{"raw_output": "..."}`;
- live-compatible launchers may return `last_message_path` and/or `stdout_path`
  following existing Codex launcher conventions;
- handoff controller must read bounded final text from those fields and must
  not assume a specific vendor runtime.

### 2. Verifier Agent Contract

The verifier launcher receives a bounded handoff bundle, not the entire packet
history.

Verifier bundle must include:

- packet contract path;
- packet id;
- attempt;
- coder managed packet result;
- changed files;
- scope guard result;
- evidence requirements from the packet/evidence contract layer;
- latest `SUMMARY.md` when present;
- latest relevant `REWORK` and `REVIEWS` files when present;
- allowed artifact roots;
- exact required final marker schema.

Verifier must return a text output ending with:

```text
FINAL_VERIFIER_EVIDENCE_JSON
{ ... }
END_FINAL_VERIFIER_EVIDENCE_JSON
```

The handoff controller must parse that marker and fail closed when:

- marker is missing;
- JSON is invalid;
- required fields are missing;
- claimed artifact paths are invalid or outside allowed roots;
- required packet-local evidence is missing.

Allowed verifier evidence fields:

```json
{
  "test_verdict": "passed | failed | not_run",
  "observability_verdict": "clean | degraded-but-expected | unexpected-degradation | no-evidence-blocker",
  "frontend_visual_verdict": "sufficient | insufficient | not_applicable",
  "commands_run": ["..."],
  "evidence_paths": ["..."],
  "blocking_issues": ["..."],
  "requirement_results": [
    {
      "id": "EV-...",
      "status": "collected | missing | deferred | not_applicable | failed | artifact_reference_invalid | contract_invalid",
      "stage": "packet_local | wave_final | release_final",
      "artifact_paths": ["..."],
      "notes": "..."
    }
  ]
}
```

`requirement_results[*].status` must align with the Evidence Contracts MVP
manifest statuses. Do not invent a second verifier status vocabulary such as
`satisfied` or `invalid`; those values must be normalized to the canonical
manifest vocabulary before artifact validation.

### 3. Reviewer Agent Contract

Reviewer receives a bounded bundle:

- packet contract path;
- coder result;
- verifier parsed manifest;
- evidence validation result;
- changed files;
- scope guard result;
- latest relevant summary/rework/review context;
- exact required final marker schema.

Reviewer must return:

```text
FINAL_PACKET_DECISION_JSON
{ ... }
END_FINAL_PACKET_DECISION_JSON
```

Allowed reviewer decision fields:

```json
{
  "packet_verdict": "accepted | rework_required | blocked | escalate_to_architect",
  "follow_up_action": "none | localized_rework | architect_decision",
  "route_classification": "self_resolvable_rework | requires_user_decision | requires_planner | pipeline_repair",
  "rework_mode": "light_resume | bounded_fresh | decision_required",
  "packet_type": "execution | rework | gate_decision",
  "reasons": ["..."]
}
```

The platform must fail closed when marker/JSON/schema is invalid.

The handoff controller may implement local marker parsing in
`verifier_reviewer_handoff.py` for the stricter schema above. Do not modify
`tasks/agent_output_parser.py` in this packet unless a reviewer explicitly
approves widening the legacy feature pipeline parser.

### 4. Evidence Validation Happens Before Reviewer Acceptance

The handoff controller must not let reviewer accept a packet if deterministic
evidence validation failed.

Required validation:

- required packet-local evidence is explicitly represented in the manifest;
- required packet-local evidence is acceptable only when every required
  `packet_local` requirement is `collected` or `not_applicable` with an
  explicit reason accepted by the contract layer;
- statuses `missing`, `failed`, `artifact_reference_invalid`, or
  `contract_invalid` on required `packet_local` evidence fail before reviewer
  acceptance;
- wave-final evidence does not block packet-local acceptance unless this packet
  owns the wave-final gate;
- claimed artifact paths exist and are under allowed artifact roots;
- malformed or impossible evidence requirements route as
  `evidence_contract_invalid`;
- `no-evidence-blocker` is accepted only when the packet actually required the
  missing evidence at `packet_local` stage.

If evidence validation fails before reviewer runs, return:

```text
domain_status = verifier_failed
```

with a blocker reason that routes to verifier rework, architect/planner repair,
or pipeline repair according to `blocker_routing.py`.

Allowed artifact roots:

- the packet artifact directory (`EVIDENCE/`, `REVIEWS/`, `REWORK/`);
- the managed runner `worktree_path` from `coder_result`, when present;
- explicitly passed test fixture roots in offline tests.

Absolute paths are allowed only if they resolve under one of those roots. Plain
relative paths resolve against `packet_dir` first, then `worktree_path` when
present.

### 5. Artifact Writes

Use existing packet artifact layout:

```text
EVIDENCE/attempt-XXXX/evidence_manifest.json
REVIEWS/review-XXXX.md
REWORK/attempt-XXXX.md
SUMMARY.md
```

Required writes:

- verifier parsed JSON becomes `EVIDENCE/attempt-XXXX/evidence_manifest.json`;
- reviewer accepted/rejected decision becomes `REVIEWS/review-XXXX.md`;
- when reviewer returns `rework_required`, write `REWORK/attempt-XXXX.md`;
- update or create bounded `SUMMARY.md` with latest handoff status.

Do not append handoff history into `EXECUTION_PACKET.md`.

### 6. Domain Status Mapping

Map reviewer decision to handoff domain status:

```text
accepted              -> accepted
rework_required       -> rework_required
blocked               -> blocked
escalate_to_architect -> escalate_to_architect
```

Verifier failures map to `verifier_failed`.
Reviewer marker/JSON/schema failures map to `reviewer_failed`.
Unexpected controller errors map to `handoff_error`.

The handoff controller must not mark packet registry as accepted/completed.
Registry mutation belongs to a later merge/acceptance steward packet.

### 7. Rework Routing Rules

When reviewer returns `rework_required`, the platform writes a rework artifact
but does not create or submit a new rework packet in this MVP.

The rework artifact must include:

- source packet id;
- attempt;
- route classification;
- rework mode;
- reasons;
- whether light resume is requested;
- whether source hash gate must be checked before resume.

Do not call old `create_rework_from_review(...)` in this packet.

### 8. Prefect Flow

Add:

```text
prefect_grace/flows/verifier_reviewer_handoff_flow.py
```

Required flow:

```python
@flow(
    name="prefect-grace-verifier-reviewer-handoff",
    flow_run_name="handoff:{packet_id}:attempt-{attempt}",
)
def verifier_reviewer_handoff_flow(...) -> dict[str, Any]:
    ...
```

The flow may run with fake launchers in tests. It must not require a Prefect
server in tests.

Domain statuses `verifier_failed`, `reviewer_failed`, `rework_required`,
`blocked`, and `escalate_to_architect` are domain outcomes, not Python
programming exceptions.

### 9. CLI Surface

Add:

```bash
python3 -m prefect_grace.cli run-handoff \
  --packet-dir prefect_grace/packets/FEATURE \
  --packet prefect_grace/packets/FEATURE/EXECUTION_PACKET.md \
  --attempt 1 \
  --coder-result path/to/managed_packet_result.json \
  --dry-run \
  --fake-verifier-output path/to/verifier_output.txt \
  --fake-reviewer-output path/to/reviewer_output.txt \
  --json
```

Required behavior:

- default `--dry-run` must not launch live agents;
- in dry-run, CLI must require explicit `--fake-verifier-output` and
  `--fake-reviewer-output` files for offline execution;
- without fake output files and without a live launcher, CLI must exit 2 with
  an input error instead of inventing successful evidence;
- live verifier/reviewer execution is out of scope for CLI unless implemented
  through injected/test launchers;
- JSON output preserves standard envelope shape.

CLI exit codes:

- `0`: `accepted`;
- `1`: `rework_required`;
- `2`: `blocked`, `escalate_to_architect`, `verifier_failed`,
  `reviewer_failed`, `handoff_error`, or input errors.

### 10. Tests Must Be Offline

Tests must not launch live Codex/Claude/agy or contact Prefect server.

Required test strategy:

- fake verifier output with valid `FINAL_VERIFIER_EVIDENCE_JSON`;
- fake verifier output missing marker -> `verifier_failed`;
- fake verifier output with invalid artifact path -> `verifier_failed`;
- fake verifier output using non-canonical `satisfied`/`invalid` statuses fails
  schema validation or is explicitly normalized before validation;
- fake reviewer output accepted -> review artifact written;
- fake reviewer output rework_required -> review and rework artifacts written;
- fake reviewer output missing marker -> `reviewer_failed`;
- wave-final evidence deferred does not block packet-local acceptance;
- packet-local required evidence missing blocks before acceptance;
- CLI dry-run without fake verifier/reviewer output files exits 2;
- `EXECUTION_PACKET.md` is not mutated;
- context bundle remains bounded and does not include full historical evidence.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/verifier_reviewer_handoff.py`
- `/opt/astro-project/prefect_grace/flows/verifier_reviewer_handoff_flow.py`
- `/opt/astro-project/prefect_grace/tasks/handoff_artifacts.py`
- `/opt/astro-project/prefect_grace/platform/packet_artifacts.py`
- `/opt/astro-project/prefect_grace/platform/packet_summary.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/prompts/verifier_prompt.md`
- `/opt/astro-project/prefect_grace/prompts/reviewer_prompt.md`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_verifier_reviewer_handoff.py`
- `/opt/astro-project/tests/test_prefect_grace_verifier_reviewer_handoff_flow.py`
- `/opt/astro-project/tests/test_prefect_grace_handoff_artifacts.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_handoff.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-VERIFIER-REVIEWER-HANDOFF-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/scripts/grace_lint.py`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/prefect_submitter.py`
- `/opt/astro-project/prefect_grace/tasks/review_router.py`
- `/opt/astro-project/prefect_grace/tasks/agent_output_parser.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/flows/packet_lifecycle.py`
- `/opt/astro-project/prefect_grace/flows/live_dashboard.py`
- `/opt/astro-project/prefect_grace/platform/managed_packet_runner.py`
- `/opt/astro-project/prefect_grace/platform/executor_registry.py`
- `/opt/astro-project/prefect_grace/platform/prefect_native_submission.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Verifier remains an agent role.
- Reviewer remains an agent role.
- Deterministic scripts validate contracts/artifacts/routing only.
- Existing evidence contract tests remain green.
- Existing packet artifact layout tests remain green.
- Existing managed packet runner tests remain green.
- Existing reviewer prompt semantics remain compatible.
- No live agents are started in tests.
- No Prefect server is required in tests.
- No packet registry acceptance/completion state is mutated.
- No rework packet is created/submitted in this MVP.
- No merge/push/squash/remote git operation is performed.
- `EXECUTION_PACKET.md` is never mutated by handoff.

## Required Implementation Shape

### Handoff Controller

`prefect_grace/platform/verifier_reviewer_handoff.py` must:

- include GRACE module/function contracts;
- parse verifier and reviewer final marker JSON;
- validate required fields;
- call evidence/artifact validation layer;
- write evidence/review/rework/summary artifacts;
- return JSON-safe `PacketHandoffResult`;
- not import Prefect at module import time;
- not call live launchers in tests.

### Handoff Artifacts

`prefect_grace/tasks/handoff_artifacts.py` must:

- provide small helpers for writing handoff artifacts;
- reuse `packet_artifacts.py` and `packet_summary.py` where possible;
- avoid duplicating large write logic;
- not modify source packet markdown.

### Flow

`prefect_grace/flows/verifier_reviewer_handoff_flow.py` must:

- use `prefect_grace.prefect_compat`;
- call the handoff controller;
- return domain statuses as data;
- not require Prefect server in tests.

### CLI

`prefect_grace/cli.py` must:

- add `run-handoff`;
- preserve JSON envelope shape;
- provide text summary mode;
- implement exit codes exactly as specified;
- not start live agents by default.

### Prompts

Prompt updates must be narrow:

- verifier prompt must explicitly return `requirement_results`;
- reviewer prompt must keep final marker schema;
- reviewer prompt must distinguish product rework from evidence contract/pipeline repair.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_verifier_reviewer_handoff.py \
  tests/test_prefect_grace_verifier_reviewer_handoff_flow.py \
  tests/test_prefect_grace_handoff_artifacts.py \
  tests/test_prefect_grace_cli_handoff.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run regression tests:

```bash
pytest -q \
  tests/test_prefect_grace_evidence_contract.py \
  tests/test_prefect_grace_evidence_manifest.py \
  tests/test_prefect_grace_artifact_validator.py \
  tests/test_prefect_grace_packet_artifact_layout.py \
  tests/test_prefect_grace_managed_packet_runner.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform/verifier_reviewer_handoff.py
python3 scripts/grace_lint.py prefect_grace/flows/verifier_reviewer_handoff_flow.py
python3 scripts/grace_lint.py prefect_grace/tasks/handoff_artifacts.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-VERIFIER-REVIEWER-HANDOFF-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke with fake/offline mode only:

```bash
python3 -m prefect_grace.cli run-handoff \
  --packet-dir /tmp/grace-handoff-packet \
  --packet /tmp/grace-handoff-packet/EXECUTION_PACKET.md \
  --attempt 1 \
  --coder-result /tmp/grace-handoff-packet/managed_packet_result.json \
  --dry-run \
  --fake-verifier-output /tmp/grace-handoff-packet/verifier_output.txt \
  --fake-reviewer-output /tmp/grace-handoff-packet/reviewer_output.txt \
  --json
```

The smoke may use a temp fixture packet. It must not launch live agents.

## Expected Evidence

- command outputs for all verification commands;
- verifier success marker parsing example;
- verifier missing marker failure example;
- reviewer accepted marker parsing example;
- reviewer rework marker parsing example;
- evidence manifest file path;
- review artifact file path;
- rework artifact file path for rework case;
- summary update sample;
- proof wave-final deferred evidence does not block packet-local acceptance;
- proof packet-local missing required evidence fails closed;
- confirmation no live agents, Prefect deployments, Docker containers, product backend/frontend services, remote push, merge, squash, deployment registration, registry acceptance, or rework packet creation were started;
- `git diff --name-only` limited to `Allowed Write Scope`;
- explicit confirmation `scripts/grace_lint.py` has no diff.

## Escalation Triggers

- implementation needs to modify `codex_launcher.py`;
- implementation needs to modify `review_router.py`;
- implementation needs to modify `state_store.py`;
- implementation needs to create/submit rework packets;
- implementation needs to mark packets accepted/completed in registry;
- implementation needs to implement architect wave acceptance;
- implementation needs to merge/push/squash;
- implementation needs live agents or Prefect server in tests;
- implementation needs product backend/frontend changes;
- implementation needs to modify `scripts/grace_lint.py`.

## Reviewer Gate

Reviewer must verify:

- verifier and reviewer are still agent roles, not replaced by scripts;
- deterministic layer validates marker JSON and artifacts;
- invalid/missing verifier evidence cannot be accepted;
- wave-final evidence is not incorrectly forced onto packet-local coder work;
- `rework_required` writes rework artifact but does not create/submit a new packet;
- no registry acceptance/completion mutation exists;
- CLI dry-run cannot fabricate successful verifier/reviewer output;
- no live agent or Prefect server is required in tests;
- no files outside `Allowed Write Scope` are modified.
