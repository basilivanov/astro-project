# Execution Packet: GRACE Packet Artifact Layout MVP

## Objective

Implement a small platform rule that keeps source controller packets short and
stable. Runtime evidence, reviewer notes, rework instructions, and attempt
history must not be appended to `EXECUTION_PACKET.md`.

The source packet is the execution contract. Runtime history lives beside it in
bounded files that agents can read selectively:

```text
SUMMARY.md
REVIEWS/
EVIDENCE/
REWORK/
```

This prevents agents from repeatedly reading 1000+ line packet files, reduces
token waste, keeps source hashes stable, and makes rework prompts use only the
latest relevant context.

This packet is platform/documentation infrastructure only. It must not change
product backend/frontend behavior and must not start live agents or Prefect
runs in tests.

## Slice

- slice_id: `SLICE-GRACE-PACKET-ARTIFACT-LAYOUT-MVP`
- slice_slug: `grace-packet-artifact-layout-mvp`
- feature_id: `FEAT-GRACE-PACKET-ARTIFACT-LAYOUT-MVP`
- packet_id: `FEAT-GRACE-PACKET-ARTIFACT-LAYOUT-MVP-W01-PACKET-ARTIFACT-LAYOUT`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-ORCHESTRATOR-MVP1-W01-PROJECT-ADAPTER-CONTRACTS`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PACKET-ARTIFACT-LAYOUT-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/artifacts.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/scripts/grace_lint.py`

## Impacted Modules

- `M-GRACE-PACKET-ARTIFACT-LAYOUT`
- `M-GRACE-PACKET-SUMMARY`
- `M-GRACE-REVIEW-ARTIFACTS`
- `M-GRACE-EVIDENCE-ARTIFACTS`
- `M-GRACE-REWORK-CONTEXT`
- `M-GRACE-CONTEXT-BUNDLE`
- `M-GRACE-CLI`

## Required Design Decisions

### 1. Source Packet Is Contract Only

`EXECUTION_PACKET.md` must contain only source-of-truth execution contract:

- objective;
- slice metadata;
- source references;
- impacted modules;
- design decisions;
- allowed/frozen scope;
- must preserve;
- implementation shape;
- verification;
- expected evidence;
- escalation triggers;
- reviewer gate.

Runtime results, repeated reviews, attempt logs, and evidence output must not be
appended to the source packet.

### 2. Runtime History Goes Into Bounded Files

Every source packet directory should support this layout:

```text
EXECUTION_PACKET.md
SUMMARY.md
REVIEWS/
  review-0001.md
  review-0002.md
EVIDENCE/
  attempt-0001/
    evidence_manifest.json
    test-output.md
    cli-smoke.json
  attempt-0002/
    evidence_manifest.json
REWORK/
  attempt-0002.md
  attempt-0003.md
```

Historical artifacts are preserved, but agents read only the latest relevant
files unless audit mode is requested.

### 3. SUMMARY.md Is The Current State Index

`SUMMARY.md` is the small operational entrypoint for agents. It must remain
short and current.

Minimum fields:

```yaml
packet_id: ...
current_status: ready|running|accepted|rework_required|blocked
current_attempt: 1
latest_review: REVIEWS/review-0001.md
latest_evidence: EVIDENCE/attempt-0001/evidence_manifest.json
latest_rework: REWORK/attempt-0002.md
open_blockers: []
next_action: ...
```

Target size: under 120 lines.

### 4. Rework Uses Compact Context Bundle

Coder rework must not reread full packet history. The context bundle for normal
rework should include only:

- `EXECUTION_PACKET.md`;
- `SUMMARY.md`;
- latest `REWORK/attempt-N.md`;
- latest `REVIEWS/review-N.md`;
- latest `EVIDENCE/attempt-N/evidence_manifest.json`;
- current changed files/diff summary.

Older history is read only in explicit audit/debug mode.

### 5. Source Hash Ignores Runtime Artifact Dirs

Source hash must be computed from `EXECUTION_PACKET.md` contract content only.
Changing `SUMMARY.md`, `REVIEWS/**`, `EVIDENCE/**`, or `REWORK/**` must not
trigger source packet rerun by itself.

### 6. Do Not Add Large Config Surface

Avoid another broad config system. If needed, add a compact policy/default in
platform code or one minimal policy entry. Do not create a large YAML tree for
this MVP.

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/packet_artifact_layout.py`
- `/opt/astro-project/prefect_grace/platform/context_bundle.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/artifacts.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/scripts/grace_lint.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_packet_artifact_layout.py`
- `/opt/astro-project/tests/test_prefect_grace_context_bundle.py`
- `/opt/astro-project/tests/test_prefect_grace_packet_parser.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PACKET-ARTIFACT-LAYOUT-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/telegram_notify.py`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing packet parser strict validation keeps working.
- Existing CLI JSON envelope remains stable.
- Existing MVP-1/MVP-2 tests continue to pass.
- `EXECUTION_PACKET.md` source hash is not affected by review/evidence/rework
  artifact files.
- Validation commands do not start agents.
- Unit tests do not write into real `/var/lib/grace-orchestrator`.
- No secrets or raw env values are printed.
- Product backend/frontend files remain untouched.

## Required Implementation Shape

### Artifact Layout Model

Add a small typed model or pure helpers that resolve packet artifact paths:

```python
class PacketArtifactLayout:
    packet_dir: Path
    source_packet: Path
    summary: Path
    reviews_dir: Path
    evidence_dir: Path
    rework_dir: Path
```

Expected helpers:

```python
resolve_packet_layout(packet_dir: Path) -> PacketArtifactLayout
latest_review(layout: PacketArtifactLayout) -> Path | None
latest_evidence_manifest(layout: PacketArtifactLayout) -> Path | None
latest_rework(layout: PacketArtifactLayout) -> Path | None
```

### Summary Writer

Add a deterministic helper that writes or updates `SUMMARY.md` from structured
state.

It must not append indefinitely. It should rewrite bounded current state.

Minimum output sections:

- packet metadata;
- current status;
- latest verdict;
- open blockers;
- next action;
- latest artifact links;
- last verification summary.

### Review Writer

Add a helper or CLI command for review output:

```bash
python3 -m prefect_grace.cli write-review <packet_dir> --verdict rework_required --body <path> --json
```

MVP can implement helper functions first and CLI second, but tests must prove
reviews go to `REVIEWS/review-XXXX.md`, not into `EXECUTION_PACKET.md`.

### Evidence Writer

Add a helper or CLI command for evidence output:

```bash
python3 -m prefect_grace.cli write-evidence <packet_dir> --attempt 1 --manifest <path> --json
```

MVP can create/copy manifest files under `EVIDENCE/attempt-XXXX/`.

### Rework Writer

Add a helper for rework instructions:

```bash
python3 -m prefect_grace.cli write-rework <packet_dir> --attempt 2 --body <path> --json
```

Rework output must include only current blockers and required next actions, not
full old history.

### Context Bundle Builder

Add a pure function that returns the minimal file list for a role:

```python
build_context_bundle(packet_dir: Path, role: str, mode: str = "normal") -> list[Path]
```

Expected behavior:

- coder normal rework: source packet, summary, latest review, latest rework,
  latest evidence manifest;
- reviewer: source packet, summary, latest evidence manifest, current diff
  summary path if available;
- architect: source packet, summary, latest review/rework;
- audit mode: may include full history.

### Line Limit Guard

Add a guard that flags oversized source packets:

- recommended max `EXECUTION_PACKET.md`: 400 lines;
- hard warning over 600 lines;
- source packet over 1000 lines must be treated as context-risk blocker unless
  explicitly waived.

This guard should not fail historical packets by default, but new strict
controller packets should report warnings.

## Verification

Run these commands from `/opt/astro-project`:

```bash
python3 -m pytest -q \
  tests/test_prefect_grace_packet_artifact_layout.py \
  tests/test_prefect_grace_context_bundle.py \
  tests/test_prefect_grace_packet_parser.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run MVP regression tests:

```bash
python3 -m pytest -q \
  tests/test_prefect_grace_project_adapter.py \
  tests/test_prefect_grace_packet_parser.py \
  tests/test_prefect_grace_scope_guard.py \
  tests/test_prefect_grace_yaml_state.py \
  tests/test_prefect_grace_cli_contracts.py \
  tests/test_prefect_grace_dag.py \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_runtime_adapter.py
```

Run compile check:

```bash
python3 -m compileall -q prefect_grace
```

Run strict GRACE marker lint:

```bash
python3 scripts/grace_lint.py prefect_grace/platform
```

Run CLI smoke checks:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-PACKET-ARTIFACT-LAYOUT-MVP/EXECUTION_PACKET.md \
  --strict \
  --json
```

## Expected Evidence

Attach under `## Evidence`:

- `git diff --stat`.
- Full list of changed files.
- Output of new artifact layout tests.
- Output of MVP regression tests.
- Output of compile check.
- Output of `python3 scripts/grace_lint.py prefect_grace/platform`.
- JSON output of CLI smoke checks.
- Example `SUMMARY.md` generated by tests.
- Example review written under `REVIEWS/`.
- Example evidence manifest stored under `EVIDENCE/attempt-0001/`.
- Example rework instruction written under `REWORK/attempt-0002.md`.
- Explicit note that `EXECUTION_PACKET.md` was not appended by helper commands.
- Explicit note that source hash is unchanged by review/evidence/rework files.
- Explicit note that no product backend/frontend files changed.

## Escalation Triggers

Stop and ask Controller if:

- implementing this requires changing live agent execution;
- implementing this requires changing product backend/frontend code;
- helper commands need to mutate source `EXECUTION_PACKET.md`;
- packet source hash cannot be kept independent from runtime artifact files;
- a broad new config system seems necessary;
- tests require real Prefect, live agents, browser, or external logs.

## Reviewer Gate

Reviewer must reject if:

- review/evidence/rework output is appended to `EXECUTION_PACKET.md`;
- context bundle includes full artifact history in normal mode;
- source hash changes after writing review/evidence/rework files;
- summary grows unbounded instead of being rewritten as current state;
- CLI JSON output is not parseable or lacks stable envelope fields;
- new modules fail GRACE marker lint;
- live agents or real Prefect runs start during tests;
- product backend/frontend files appear in the diff.

## Evidence

Worker fills this section.

## Reviewer Notes

Reviewer fills this section.
