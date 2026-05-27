# Execution Packet: GRACE Rework Resume Source Hash Gate MVP

## Objective

Implement a deterministic safety gate for coder rework sessions. A coder session
must not be resumed when the source execution contract changed after the last
coder attempt.

The source execution contract is `EXECUTION_PACKET.md`. Runtime artifacts such
as `SUMMARY.md`, `REVIEWS/**`, `EVIDENCE/**`, and `REWORK/**` are operational
history and must not change source contract identity.

Core rule:

```text
reviewer requests small implementation rework without changing source contract
  -> light_resume may be allowed

architect or planner changes EXECUTION_PACKET.md source contract
  -> source_hash changes
  -> light_resume is forbidden
  -> coder receives bounded_fresh context
```

This packet is platform orchestration infrastructure only. It must not change
product backend/frontend behavior and must not start live agents or Prefect
runs in tests.

## Slice

- slice_id: `SLICE-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP`
- slice_slug: `grace-rework-resume-source-hash-gate-mvp`
- feature_id: `FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP`
- packet_id: `FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-SOURCE-HASH-GATE`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-PACKET-ARTIFACT-LAYOUT-MVP-W01-PACKET-ARTIFACT-LAYOUT`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/packet_artifact_layout.py`
- `/opt/astro-project/prefect_grace/platform/context_bundle.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`

## Impacted Modules

- `M-GRACE-REWORK-RESUME-POLICY`
- `M-GRACE-SOURCE-HASH-GATE`
- `M-GRACE-CONTEXT-BUNDLE`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-CODEX-LAUNCHER`
- `M-GRACE-FEATURE-PIPELINE`
- `M-GRACE-CLI`

## Required Design Decisions

### 1. Source Contract Change Invalidates Resume

The orchestrator must compare current source hash with the hash used by the
last executed coder attempt.

Required decision:

```python
if current_source_hash != last_executed_source_hash:
    resume_allowed = False
    resume_block_reason = "contract_changed"
    recommended_rework_mode = "bounded_fresh"
```

This rule is deterministic and must not depend on LLM reviewer language.

### 2. Reviewer-Only Small Rework May Resume

If `source_hash` is unchanged and the rework is a small implementation fix from
reviewer feedback, `light_resume` may remain available.

Examples:

- missing selector in UI;
- small assertion mismatch;
- typo in evidence manifest path;
- reviewer requested a narrow implementation adjustment without changing
  objective, scope, verification, or evidence requirements.

### 3. Architect/Planner Contract Rework Requires Fresh Context

If architect or planner changes any source contract field in
`EXECUTION_PACKET.md`, previous coder context is stale even if the old session
still exists.

Contract fields include:

- objective;
- allowed write scope;
- frozen scope;
- must preserve;
- required implementation shape;
- verification commands;
- evidence requirements;
- escalation triggers;
- reviewer gate.

### 4. Fresh Context Uses Artifact Layout, Not Full History

When resume is blocked, the coder must receive a bounded context bundle. Normal
mode must include only:

- `EXECUTION_PACKET.md`;
- `SUMMARY.md`;
- latest `REWORK/attempt-N.md`;
- latest `REVIEWS/review-N.md`;
- latest `EVIDENCE/attempt-N/evidence_manifest.json`;
- current diff summary if available.

Older runtime history is allowed only in explicit audit mode.

### 5. Registry Stores Hash And Session State

The packet registry must track enough state to make resume decisions without
reading historical session transcripts.

Minimum registry fields:

```yaml
packet_id: ...
source_hash: sha256:...
last_executed_source_hash: sha256:...
latest_coder_session_id: ...
latest_attempt: 2
resume_allowed: false
resume_block_reason: contract_changed
recommended_rework_mode: bounded_fresh
```

The fields must be backward-compatible with existing registry YAML records.

### 6. Do Not Start Live Agents In Tests

All tests for this packet are pure unit/integration tests against local files,
registry state, CLI JSON, and launcher command planning. They must not start
Codex, Claude, agy, Prefect deployments, or product containers.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/rework_resume_policy.py`
- `/opt/astro-project/prefect_grace/platform/context_bundle.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/packet_summary.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/scripts/grace_lint.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_rework_resume_policy.py`
- `/opt/astro-project/tests/test_prefect_grace_context_bundle.py`
- `/opt/astro-project/tests/test_prefect_grace_yaml_state.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/tests/test_prefect_grace_codex_launcher.py`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_dynamic.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/tasks/telegram_notify.py`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing packet strict validation keeps working.
- Existing packet artifact layout remains source-hash stable.
- Existing registry records remain loadable without migration.
- Existing rework mode names remain valid: `light_resume`, `bounded_fresh`,
  `fresh_session`, `decision_required`.
- Existing CLI JSON envelope remains stable.
- Existing launcher tests must not start live agents.
- Unit tests must not write into real `/var/lib/grace-orchestrator`.
- No secrets or raw env values are printed.
- Product backend/frontend files remain untouched.

## Required Implementation Shape

### Rework Resume Decision Model

Add a small typed model or dataclass:

```python
class ReworkResumeDecision:
    packet_id: str
    current_source_hash: str
    last_executed_source_hash: str | None
    resume_allowed: bool
    resume_block_reason: str | None
    recommended_rework_mode: str
    context_mode: str
    context_paths: list[str]
```

Accepted `resume_block_reason` values:

- `contract_changed`;
- `missing_last_executed_hash`;
- `missing_session`;
- `stale_session`;
- `attempt_policy_exceeded`;
- `decision_required`.

Accepted `context_mode` values:

- `normal_latest`;
- `bounded_fresh`;
- `audit_full_history`.

### Pure Policy Function

Add a pure policy function:

```python
def decide_rework_resume(
    packet_id: str,
    current_source_hash: str,
    last_executed_source_hash: str | None,
    requested_rework_mode: str,
    rework_reason: str,
    packet_dir: Path,
) -> ReworkResumeDecision:
    ...
```

Required rules:

- If `last_executed_source_hash` is missing, return
  `resume_allowed=False`, `resume_block_reason="missing_last_executed_hash"`,
  `recommended_rework_mode="bounded_fresh"`.
- If hashes differ, return `resume_allowed=False`,
  `resume_block_reason="contract_changed"`,
  `recommended_rework_mode="bounded_fresh"`.
- If hashes match and `requested_rework_mode=="light_resume"` with a
  reviewer implementation reason, allow resume.
- If session state is missing or stale, disallow resume and recommend
  `bounded_fresh`.
- If repeated quality rework exceeds configured threshold, return either
  `fresh_session` or `decision_required`. This may be a hook in this MVP.

### Registry Integration

Registry writes must update:

- `source_hash` when current packet source is parsed;
- `last_executed_source_hash` when a coder attempt starts;
- `latest_coder_session_id` when a coder session is launched or resumed;
- `latest_attempt` when a new attempt artifact directory is created;
- `resume_allowed`, `resume_block_reason`, and `recommended_rework_mode` when
  rework is routed.

Backward compatibility requirement:

- Missing new fields in old YAML records must load as `None` or safe defaults.
- Existing registry tests must not require fixture rewrites unless they are
  explicitly testing new fields.

### Context Bundle Integration

When resume is blocked by source hash mismatch, context bundle generation must
return `bounded_fresh` paths and must not include full historical artifact
directories.

The expected normal bundle is:

```text
EXECUTION_PACKET.md
SUMMARY.md
REWORK/latest-or-attempt-N.md
REVIEWS/latest-or-review-N.md
EVIDENCE/latest-or-attempt-N/evidence_manifest.json
```

### Codex Launcher Integration

The launcher must receive an explicit resume decision:

- `resume_allowed=True` means it may call `codex resume <thread_id>` or the
  equivalent launcher path.
- `resume_allowed=False` means it must use a fresh `codex exec` with bounded
  context and must not pass old session id.

The launcher must log a compact heartbeat field:

```text
resume_allowed=false resume_block_reason=contract_changed recommended_rework_mode=bounded_fresh
```

### CLI Contract

Add a deterministic CLI smoke endpoint:

```bash
python3 -m prefect_grace.cli decide-rework-resume \
  /opt/astro-project/prefect_grace/packets/FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP \
  --packet-id FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-SOURCE-HASH-GATE \
  --last-executed-source-hash sha256:old \
  --requested-mode light_resume \
  --reason contract_changed \
  --json
```

Expected JSON shape:

```json
{
  "ok": true,
  "packet_id": "FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-SOURCE-HASH-GATE",
  "resume_allowed": false,
  "resume_block_reason": "contract_changed",
  "recommended_rework_mode": "bounded_fresh"
}
```

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_rework_resume_policy.py \
  tests/test_prefect_grace_context_bundle.py \
  tests/test_prefect_grace_yaml_state.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run launcher and pipeline regression tests that cover resume planning without
live agents:

```bash
pytest -q \
  tests/test_prefect_grace_codex_launcher.py \
  tests/test_prefect_grace_feature_pipeline_dynamic.py
```

Run existing platform regression tests:

```bash
pytest -q \
  tests/test_prefect_grace_project_adapter.py \
  tests/test_prefect_grace_packet_parser.py \
  tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_yaml_state.py \
  tests/test_prefect_grace_cli_contracts.py \
  tests/test_prefect_grace_dag.py \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_backlog_controller_rework.py \
  tests/test_prefect_grace_runtime_adapter.py \
  tests/test_prefect_grace_packet_artifact_layout.py
```

Run static checks:

```bash
python3 -m compileall prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke:

```bash
python3 -m prefect_grace.cli decide-rework-resume \
  prefect_grace/packets/FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP \
  --packet-id FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-SOURCE-HASH-GATE \
  --last-executed-source-hash sha256:old \
  --requested-mode light_resume \
  --reason contract_changed \
  --json
```

Required test cases:

- same source hash plus reviewer implementation rework allows `light_resume`;
- changed source hash forbids `light_resume` and recommends `bounded_fresh`;
- missing previous source hash forbids resume;
- stale or missing session forbids resume;
- changed source hash returns bounded latest context paths;
- source hash excludes `SUMMARY.md`, `REVIEWS/**`, `EVIDENCE/**`, and
  `REWORK/**`;
- CLI emits valid JSON and stable exit codes;
- launcher never passes old session id when `resume_allowed=False`;
- tests do not start live Codex, Claude, agy, Prefect, or product containers.

## Expected Evidence

Do not append evidence to `EXECUTION_PACKET.md`. Write evidence under:

```text
EVIDENCE/attempt-0001/evidence_manifest.json
```

Evidence manifest must include:

- command outputs for all verification commands;
- JSON examples for same-hash `light_resume`;
- JSON examples for changed-hash `bounded_fresh`;
- context bundle path list for changed contract;
- confirmation that no live agents or Prefect runs were started;
- confirmation that no product backend/frontend files changed;
- `git diff --name-only` filtered to this packet's Allowed Write Scope.

## Escalation Triggers

Stop and ask controller if:

- source hash must include runtime artifacts to make tests pass;
- existing registry records cannot load without destructive migration;
- launcher requires live Codex to test resume decisions;
- feature pipeline requires a live Prefect server for unit tests;
- a product backend/frontend file appears necessary to modify;
- the implementation needs a broad new YAML config tree;
- existing accepted packet artifact layout must be broken.

## Reviewer Gate

Reviewer must reject this packet if:

- changed `EXECUTION_PACKET.md` source hash still allows `light_resume`;
- same source hash always forces fresh context without reason;
- normal context bundle includes full artifact history;
- registry additions break existing records;
- CLI JSON envelope is malformed or unstable;
- GRACE lint fails;
- tests start live agents or Prefect deployments;
- product backend/frontend files are modified.

