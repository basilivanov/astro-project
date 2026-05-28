# Execution Packet: FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-W01-SOURCE-TO-RUNTIME

## Objective

Add a guarded operator path that reconciles the real GRACE runtime registry from
accepted strict source packet evidence.

The source packet corpus is now accepted, but runtime registry dry-runs still
show stale ready/blocked entries because most bootstrap/apply work has been
verified only in temporary state roots. This packet must close that
source-to-runtime gap without starting agents, creating Prefect runs, touching
product services, or mutating source packet artifacts.

The result should let an operator prove the planned runtime registry mutation,
capture bounded before/after evidence, and then explicitly apply it to the
configured project runtime state when approved.

## Slice

- slice_id: `SLICE-GRACE-REGISTRY-BOOTSTRAP-APPLY`
- slice_slug: `grace-registry-bootstrap-apply`
- feature_id: `FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY`
- packet_id: `FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY-W01-SOURCE-TO-RUNTIME`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-ORCHESTRATOR-MVP1-W01-PROJECT-ADAPTER-CONTRACTS, FEAT-GRACE-REGISTRY-APPLY-SMOKE-W01-REGISTRY-APPLY-SMOKE, FEAT-GRACE-FEATURE-PIPELINE-FLOW-BODY-SPLIT-W01-FLOW-PHASE-RUNNERS`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/packet_parser.py`
- `/opt/astro-project/prefect_grace/platform/packet_artifact_layout.py`
- `/opt/astro-project/prefect_grace/platform/registry_apply_smoke.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/cli_commands/project_registry.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_submission.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REGISTRY-APPLY-SMOKE/EXECUTION_PACKET.md`

## Impacted Modules

- `M-GRACE-CONTROLLER-BACKLOG-BOOTSTRAP`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-PACKET-REGISTRY`
- `M-GRACE-RUNTIME-STATE`
- `M-GRACE-PROJECT-ADAPTER`
- `M-GRACE-STRICT-PACKET-DISCOVERY`
- `M-GRACE-PREFECT-NATIVE-SUBMISSION`
- `M-GRACE-CLI`
- `M-GRACE-OPERATOR-JSON`

## Allowed Write Scope

- `/opt/astro-project/prefect_grace/platform/controller_backlog_bootstrap.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/registry_apply_smoke.py`
- `/opt/astro-project/prefect_grace/platform/registry_bootstrap_apply.py`
- `/opt/astro-project/prefect_grace/cli.py`
- `/opt/astro-project/prefect_grace/cli_commands/project_registry.py`
- `/opt/astro-project/prefect_grace/cli_commands/packet_submission.py`
- `/opt/astro-project/prefect_grace/cli_commands/parser.py`
- `/opt/astro-project/tests/test_prefect_grace_controller_backlog_bootstrap.py`
- `/opt/astro-project/tests/test_prefect_grace_backlog_controller.py`
- `/opt/astro-project/tests/test_prefect_grace_registry_apply_smoke.py`
- `/opt/astro-project/tests/test_prefect_grace_registry_bootstrap_apply.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`
- `/opt/astro-project/tests/test_prefect_grace_yaml_state.py`
- `/opt/astro-project/tests/test_prefect_grace_packet_parser.py`
- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY/**`
- `/var/lib/grace-orchestrator/astro-project/state/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/prefect_grace/flows/**`
- `/opt/astro-project/prefect_grace/tasks/**`
- `/opt/astro-project/prefect_grace/prompts/**`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/astro-project/prefect_grace/project.yaml`
- `/opt/astro-project/prefect_grace/policies/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/prefect_grace/packets/**/EXECUTION_PACKET.md`
- `/opt/astro-project/prefect_grace/packets/**/REVIEWS/** outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/SUMMARY.md outside current packet`
- `/opt/astro-project/prefect_grace/packets/**/EVIDENCE/** outside current packet`
- `/opt/astro-project/.worktrees/**`
- `/tmp/**`

## Must Preserve

- Dry-run remains the default for runtime registry reconciliation.
- Real runtime mutation requires an explicit apply opt-in and explicit project config.
- Source packets, reviews, summaries, and evidence remain read-only inputs to runtime apply.
- Terminal runtime status is inferred only from bounded terminal evidence.
- Source `status: accepted` and generic or nested `status: passed` never seed accepted registry state.
- Existing accepted or blocked entries are not downgraded when source hash is unchanged and evidence is weaker or missing.
- `submit-packets --dry-run` creates zero Prefect runs.
- Existing CLI JSON envelopes keep `result` equal to `data`.
- No live agents, live Prefect runs, Docker, backend, frontend, Playwright, provider APIs, or credentials are used.
- Evidence remains bounded and excludes large raw logs, huge scans, screenshots, and full registry dumps.

## Recommended Role Assignment

- coder: `Codex high` or `Sonnet high`; this is a state mutation safety packet.
- verifier: `Codex medium`; must verify temp-state apply first, then real-state
  dry-run summaries, and only run real apply if explicitly approved.
- reviewer: `Codex xhigh` or `Opus`; reviewer must focus on write roots,
  source-evidence trust boundaries, idempotence, and no live execution.
- rework policy: fresh session for write-scope, status inference, or idempotence
  failures; light resume only for CLI wording, tests, or evidence formatting.

## Required Design Decisions

### 1. This Packet Reconciles Runtime State Only

The implementation may add a small operator command or smoke harness, but the
purpose is not another isolated unit smoke. It must prove and perform the real
source-to-runtime bootstrap apply path for the project registry.

Do not start the nightly runner, batch execution, agents, live Prefect
submissions, Docker, backend, frontend, or Playwright in this packet.

### 2. Dry-Run Is The Default

Any new or changed operator command must default to dry-run. Runtime mutation
requires an explicit apply flag and an explicit project config:

```bash
python3 -m prefect_grace.cli bootstrap-backlog \
  --project prefect_grace/project.yaml \
  --apply --json
```

If a wrapper command is introduced, it must preserve the same default:

```bash
python3 -m prefect_grace.cli registry-bootstrap-apply \
  --project prefect_grace/project.yaml \
  --dry-run --json
```

Apply mode must print a bounded JSON summary and must not require parsing
human-readable logs.

### 3. Guard Real Runtime Writes

Runtime writes are allowed only under the configured `runtime_state_root` from
the explicitly supplied project config:

```text
/var/lib/grace-orchestrator/astro-project
```

Tests must use `tmp_path` or another explicit temporary project config/state
root. Tests must assert that no write escapes the selected state root.

The implementation must not write to:

```text
prefect_grace/state/*.yaml
prefect_grace/packets/**
grace/packets/**
.worktrees/**
/tmp/**
```

except for explicit test fixtures under pytest temporary directories.

### 4. Source Packets Remain Read-Only

The apply path may scan `EXECUTION_PACKET.md`, `SUMMARY.md`, `REVIEWS/**`, and
`EVIDENCE/attempt-*` bounded evidence, but it must never update source packet
files or create new source packet evidence as a side effect of runtime apply.

Evidence for this packet must be written only by the implementing agent as
normal packet evidence, not by the runtime apply command.

### 5. Terminal Status Comes Only From Bounded Evidence

Accepted or blocked runtime entries may be seeded only from bounded terminal
packet evidence already accepted by the bootstrap contract.

The apply path must not trust:

- source `status: accepted`;
- nested or generic `status: passed`;
- CLI command success alone;
- stale runtime registry entries whose `source_hash` no longer matches;
- review/rework markdown outside the bounded packet artifact layout.

Existing accepted or blocked runtime entries must not be downgraded when their
source hash is unchanged and source evidence is weaker or missing.

### 6. Preflight Must Be Explicit And Fail-Closed

Before any real apply, the command or documented operator sequence must capture
a bounded preflight summary containing:

- source packet candidate count;
- candidate status counts;
- errors and warnings count;
- planned runtime upserts by packet id and target status;
- write root;
- whether source hashes match current runtime entries;
- whether source evidence is terminal, non-terminal, weak, missing, or
  conflicting;
- whether live submission/execution is disabled.

Apply must fail closed if:

- bootstrap dry-run has parser errors;
- strict source discovery cannot run;
- planned write root cannot be resolved from the explicit project config;
- planned writes escape `runtime_state_root`;
- terminal evidence is conflicting;
- a source packet would be marked accepted from source status or generic passed
  evidence only;
- the command would create Prefect runs or start agents.

### 7. Backup And Idempotence Are Required

Before mutating the real runtime registry, the operator path must capture a
bounded before snapshot or backup of the existing packet registry. The snapshot
must be small enough for committed evidence summaries and must not dump
kilometer-scale logs.

After apply:

- re-running the same dry-run must show zero or explicitly unchanged planned
  mutations;
- accepted packets with unchanged source hashes must not become ready again;
- previously blocked packets must not become accepted unless terminal accepted
  evidence exists for the same source hash;
- `submit-packets --dry-run` must create no Prefect runs and should have
  nothing runnable when all strict source packets are accepted.

### 8. JSON Envelope Remains Stable

Existing CLI commands must keep the established JSON envelope:

```json
{
  "ok": true,
  "project_key": "astro-project",
  "command": "...",
  "result": {},
  "data": {},
  "warnings": [],
  "errors": []
}
```

For commands touched by this packet, `result` must remain equal to `data`.

### 9. Keep Evidence Bounded

Do not commit full packet scans, large logs, screenshots, full registry dumps,
or raw command outputs if they are large. Commit short summaries and manifests
that preserve the decision-critical facts:

- command;
- exit status;
- counts;
- relevant packet ids;
- status transitions;
- write roots;
- error/warning classes;
- post-test observability verdict.

## Implementation Requirements

1. Inspect the current source/runtime mismatch with dry-run commands before
   changing code.
2. Add the smallest operator guard or smoke wrapper needed to make real apply
   reviewable and repeatable. Reuse `bootstrap-backlog`, `sync-packets`,
   `registry-dump`, and `submit-packets` contracts instead of duplicating
   registry logic.
3. Add regression tests for dry-run default, explicit apply requirement,
   source-read-only behavior, write-root containment, terminal evidence trust,
   unchanged-source idempotence, and dry-run submit creating zero Prefect runs.
4. Verify the real project path in dry-run first. Do not run real apply until
   the dry-run summary is clean and the packet implementation explicitly records
   that apply was intentional.
5. If real apply is executed, record before/after bounded summaries and prove a
   second dry-run is idempotent.
6. Do not modify product backend/frontend files or unrelated GRACE platform
   modules.

## Acceptance Criteria

- A deterministic operator path exists for project runtime registry bootstrap
  apply, or the existing CLI path is guarded and documented strongly enough for
  repeatable operation.
- Dry-run is the default and real mutation requires explicit apply opt-in.
- Tests prove write containment under temporary state roots.
- Tests prove source packets and packet evidence are not mutated by runtime
  apply.
- Tests prove terminal status is inferred only from bounded terminal evidence.
- Tests prove source `status: accepted` and generic `status: passed` cannot seed
  accepted runtime entries.
- Tests prove existing terminal runtime entries are not downgraded when source
  hash is unchanged and evidence is weaker or missing.
- Before/after registry summaries are bounded and suitable for committed
  evidence.
- Real project dry-run shows the expected source/runtime reconciliation plan.
- If real apply is executed, follow-up dry-run shows idempotence and
  `sync-packets --dry-run` no longer reports stale ready/blocked statuses for
  already accepted source packets, except for explicitly documented remaining
  inconsistencies.
- `submit-packets --dry-run` creates zero Prefect runs.
- No live agents, live Prefect runs, Docker, backend, frontend, Playwright,
  provider APIs, or credentials are used.
- Existing CLI JSON envelope remains stable.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_controller_backlog_bootstrap.py \
  tests/test_prefect_grace_backlog_controller.py \
  tests/test_prefect_grace_registry_apply_smoke.py \
  tests/test_prefect_grace_cli_contracts.py
```

Run state and parser regressions if touched:

```bash
pytest -q \
  tests/test_prefect_grace_yaml_state.py \
  tests/test_prefect_grace_packet_parser.py
```

Run compile checks:

```bash
python3 -m compileall -q \
  prefect_grace/platform \
  prefect_grace/cli.py \
  prefect_grace/cli_commands
```

Run targeted GRACE lint for changed modules. If platform modules are touched,
the preferred check is:

```bash
python3 scripts/grace_lint.py prefect_grace/platform
```

Validate this packet strictly:

```bash
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-REGISTRY-BOOTSTRAP-APPLY/EXECUTION_PACKET.md \
  --strict --json
```

Run real project dry-runs:

```bash
python3 -m prefect_grace.cli bootstrap-backlog \
  --project prefect_grace/project.yaml \
  --dry-run --json

python3 -m prefect_grace.cli sync-packets \
  --project prefect_grace/project.yaml \
  --dry-run --json

python3 -m prefect_grace.cli registry-dump \
  --project prefect_grace/project.yaml \
  --json

python3 -m prefect_grace.cli submit-packets \
  --project prefect_grace/project.yaml \
  --dry-run --json
```

If an apply wrapper command is introduced, run it first against a temporary
project config/state root, then against the real project only when the preflight
summary is clean:

```bash
python3 -m prefect_grace.cli registry-bootstrap-apply \
  --project /tmp/grace-registry-bootstrap-apply/project.yaml \
  --apply --json
```

Do not run Docker, backend, frontend, Playwright, live Prefect submissions, or
live agents for this packet.

## Expected Evidence

- Strict validation output for this `EXECUTION_PACKET.md`.
- Targeted pytest output.
- Compile output.
- Targeted lint output for changed modules.
- Temp-state apply proof showing write containment and zero source packet mutations.
- Real project `bootstrap-backlog --dry-run --json` bounded summary.
- Real project `sync-packets --dry-run --json` bounded summary before apply.
- Real project registry before snapshot summary.
- Real project apply summary if apply was intentionally executed.
- Real project registry after snapshot summary if apply was executed.
- Idempotence dry-run summary after apply.
- `submit-packets --dry-run --json` summary showing zero Prefect runs created.
- Evidence that stale source/runtime statuses are resolved or explicitly listed as expected remaining inconsistencies.
- Confirmation that no live agents, live Prefect runs, Docker, backend, frontend, Playwright, provider APIs, credentials, product files, source packet files, or `.worktrees/**` were touched.
- Post-test observability verdict: `clean`, `degraded-but-expected`, `unexpected-degradation`, or `no-evidence-blocker`.

## Escalation Triggers

- Runtime apply cannot be guarded behind an explicit opt-in.
- The write root cannot be proven to be the explicit project `runtime_state_root`.
- Apply would mutate source packets, evidence, `.worktrees/**`, product files, or legacy `prefect_grace/state/*.yaml`.
- Terminal status inference needs source `status: accepted` or generic `status: passed`.
- Existing terminal runtime entries would be downgraded without a changed source hash and stronger evidence.
- The real project dry-run shows conflicting terminal evidence.
- `sync-packets --dry-run` remains stale after apply without a clear expected reason.
- `submit-packets --dry-run` would create Prefect runs or submit accepted packets again.
- Implementation requires live agents, live Prefect, Docker, backend, frontend, Playwright, provider credentials, or network calls.
- Evidence cannot be bounded without losing decision-critical facts.

## Reviewer Gate

Reviewer must reject this packet if:

- runtime mutation can happen without explicit apply opt-in;
- apply writes outside the explicit project runtime state root;
- source packets, reviews, summaries, evidence, or `.worktrees/**` are mutated
  by bootstrap/sync/submit/apply commands;
- `prefect_grace/state/*.yaml` is mutated;
- source `status: accepted` can seed accepted runtime registry state;
- generic or nested `status: passed` can seed accepted runtime registry state;
- existing accepted/blocked entries with unchanged source hashes can be
  downgraded by weaker source evidence;
- conflicting bounded evidence is silently accepted;
- stale source/runtime status mismatches remain after apply without an explicit
  documented reason;
- `submit-packets --dry-run` creates Prefect runs;
- any live agent, live Prefect run, Docker, backend, frontend, Playwright,
  provider API, or credential is used;
- JSON envelope compatibility breaks for existing CLI commands;
- evidence includes large raw logs, huge packet scans, screenshots, or full
  registry dumps instead of bounded summaries.
