# Execution Packet: GRACE Controller Backlog Bootstrap

## Objective

Implement a controlled backlog bootstrap and hygiene layer for the portable
GRACE orchestrator.

The current prototype has strict source controller packets plus historical
runtime artifacts, but the portable runtime registry can be empty. This packet
must make the platform able to seed and audit runtime registry state from the
strict packet corpus and accepted packet artifacts without mutating source
packets or trusting legacy markdown noise.

The immediate goal is an operator-safe command that answers:

- which strict controller packets exist;
- which historical packets can be seeded as accepted, blocked, or ready;
- which evidence proves that inference;
- which packets remain waiting because evidence is missing;
- what `sync-packets` and `submit-packets` would do after bootstrap.

## Slice

- slice_id: `SLICE-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP`
- slice_slug: `grace-controller-backlog-bootstrap`
- feature_id: `FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP`
- packet_id: `FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP-W01-BACKLOG-BOOTSTRAP`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP2-BACKLOG-CONTROLLER/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP2-BACKLOG-CONTROLLER/SUMMARY.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-MVP2-BACKLOG-CONTROLLER/REVIEWS/review-0002-independent-acceptance.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-PACKET-ARTIFACT-LAYOUT-MVP/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/packet_artifact_layout.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/project.yaml`

## Impacted Modules

- `M-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-PACKET-ARTIFACT-LAYOUT`
- `M-GRACE-STRICT-PACKET-DISCOVERY`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Required Design Decisions

### 1. This Packet Is A Bootstrap Root

Do not add runtime `depends_on` for this packet.

Reason: the missing behavior is the registry bootstrap that would make
historical accepted dependencies visible. A dependency on those historical
packets would keep this packet blocked in an empty runtime registry.

The implementation may still read MVP-2 accepted artifacts as source-of-truth
evidence.

### 2. Source Packets Stay Immutable

Bootstrap must not write status, evidence, timestamps, Prefect URLs, or registry
metadata back into `EXECUTION_PACKET.md`.

Allowed mutation target is only the configured runtime registry under
`runtime_state_root`, and only when the operator chooses the apply mode.

### 3. Artifact Evidence Must Drive Historical Status

The bootstrapper must not trust source `status: accepted` alone.

Accepted or blocked historical state may be inferred only from bounded packet
artifacts such as:

- `SUMMARY.md` current status fields;
- latest accepted review under `REVIEWS/`;
- verifier/evidence manifests under `EVIDENCE/`;
- explicit operator-provided override input, if added later.

If evidence is ambiguous, the packet remains `ready`, `waiting_for_dependencies`,
or `bootstrap_evidence_missing`; it must not silently become accepted.

### 4. Dry-Run Is The Default

The operator command must default to dry-run and print a machine-readable plan.

Required plan fields:

- `packet_id`;
- `source_path`;
- `source_hash`;
- `current_registry_status`;
- `inferred_status`;
- `inference_reason`;
- `evidence_paths`;
- `planned_action`;
- `warnings`.

### 5. Apply Mode Is Explicit

Writing runtime registry state must require an explicit operator action such as
`--apply` or an equivalent non-default flag.

Dry-run must not write `/var/lib/grace-orchestrator/**`, `prefect_grace/state/**`,
source packet files, reviews, evidence, or product files.

### 6. Existing Sync Semantics Must Remain Stable

`sync-packets` must continue to scan strict controller packets, compute source
hashes, validate dependencies, and return the existing JSON envelope.

Bootstrap may add a separate command or a narrow flag, but it must not make
ordinary `sync-packets --dry-run` write registry state or infer terminal status
without explicit operator intent.

### 7. Legacy Warning Noise Must Become Operator-Readable

The strict scanner may still skip legacy role packets and evidence markdown, but
operator output must summarize skip classes instead of forcing a human to read
hundreds of repeated warnings.

The detailed skipped-file list may remain available in verbose/debug output or
an artifact.

### 8. No Live Runtime In This Packet

This packet must not launch live agents, live Prefect submissions, backend,
frontend, Docker, Playwright, or provider APIs.

It is a deterministic registry/bootstrap hygiene packet only.

## Required Implementation Shape

Add a small pure platform module or narrowly extend the backlog controller with
equivalent public functions:

```python
class BacklogBootstrapCandidate:
    packet_id: str
    source_path: str
    source_hash: str
    current_registry_status: str | None
    inferred_status: str | None
    inference_reason: str
    evidence_paths: list[str]
    planned_action: str
    warnings: list[str]


class BacklogBootstrapPlan:
    project_key: str
    dry_run: bool
    candidates: list[BacklogBootstrapCandidate]
    apply_count: int
    warnings: list[str]
    errors: list[str]
```

Preferred CLI shape:

```bash
python3 -m prefect_grace.cli bootstrap-backlog \
  --project prefect_grace/project.yaml \
  --dry-run \
  --json
```

If the implementation uses a different command name, it must still provide the
same dry-run/apply safety contract and JSON-safe result.

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/packet_artifact_layout.py`
- `/opt/astro-project/prefect_grace/platform/packet_summary.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/artifacts.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/tests/test_prefect_grace_controller_backlog_bootstrap.py`
- `/opt/astro-project/tests/test_prefect_grace_backlog_controller.py`
- `/opt/astro-project/tests/test_prefect_grace_packet_parser.py`
- `/opt/astro-project/tests/test_prefect_grace_packet_artifact_layout.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/tests/test_prefect_grace_yaml_state.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/tasks/telegram_notify.py`
- `/opt/astro-project/prefect_grace/prompts/**`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/astro-project/.env`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing `validate-project`, `scan-packets`, `sync-packets`, `submit-packets`, and `registry-dump` JSON envelopes stay stable.
- Existing strict source controller packet parsing stays deterministic.
- Existing MVP-2 fail-closed `submit-packets --execute` behavior remains intact.
- Source packet markdown is not mutated by sync, bootstrap, or submit commands.
- Dry-run commands do not write runtime registry state.
- Unit tests do not write into real `/var/lib/grace-orchestrator`.
- Historical accepted status is never inferred from source `status` alone.
- Unknown or ambiguous bootstrap evidence fails closed.
- Product backend/frontend files remain untouched.
- No live agents, provider APIs, Docker, backend, frontend, or Playwright are started.
- No secrets or raw env values are printed in JSON output, logs, errors, or artifacts.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_controller_backlog_bootstrap.py \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_packet_parser.py \
  tests/test_prefect_grace_packet_artifact_layout.py \
  tests/test_prefect_grace_cli_contracts.py \
  tests/test_prefect_grace_yaml_state.py
```

Run static checks:

```bash
python3 -m compileall -q prefect_grace/platform prefect_grace/cli.py
python3 scripts/grace_lint.py prefect_grace/platform prefect_grace/cli.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke:

```bash
python3 -m prefect_grace.cli bootstrap-backlog \
  --project prefect_grace/project.yaml \
  --dry-run \
  --json

python3 -m prefect_grace.cli sync-packets \
  --project prefect_grace/project.yaml \
  --dry-run \
  --json
```

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output.
- Compile and GRACE lint output.
- Dry-run bootstrap JSON showing candidate packets, inferred statuses, planned actions, and zero runtime writes.
- Apply-mode unit test evidence proving writes happen only to a temporary runtime registry.
- CLI smoke output proving `sync-packets --dry-run` still works and warning summaries are operator-readable.
- Confirmation that no source packet, `prefect_grace/state/*.yaml`, backend, frontend, live Prefect run, or live agent was touched.

## Escalation Triggers

- Bootstrap cannot infer historical status without trusting unbounded legacy markdown.
- Implementation requires modifying source packet files during sync or bootstrap.
- Implementation requires mutating `prefect_grace/state/*.yaml`.
- Implementation requires product backend/frontend changes.
- Implementation requires live Prefect, live agents, provider credentials, Docker, backend, frontend, or Playwright.
- Runtime registry schema changes would break existing `registry-dump` or `submit-packets` output.
- Historical packet artifacts disagree about accepted vs blocked terminal state.

## Reviewer Gate

Reviewer must reject this packet if:

- dry-run writes runtime state;
- accepted status is inferred from source `status` alone;
- source packets are mutated;
- legacy warning noise is not summarized;
- unknown evidence becomes accepted;
- live agents or product services are started;
- existing backlog controller safety gates are weakened.
