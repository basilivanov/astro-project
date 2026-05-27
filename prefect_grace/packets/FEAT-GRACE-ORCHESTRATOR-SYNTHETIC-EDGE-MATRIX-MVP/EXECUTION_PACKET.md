# Execution Packet: GRACE Orchestrator Synthetic Edge Matrix MVP

## Objective

Implement a synthetic scenario matrix for the GRACE orchestrator so safety
invariants are tested across many edge cases without starting live agents,
Prefect deployments, or product containers.

This packet must prove orchestrator behavior by generated fixtures, not by a
small number of hand-written examples. The first protected invariants are:

```text
source_hash_changed -> no resume command ever
resume_allowed_false -> fresh exec, no old thread id
registry_error_on_managed_resume -> no stale resume
frozen_scope_change -> blocked before merge
dependency_blocked -> dependent packet not executed
```

This packet is test/platform infrastructure only. It must not refactor large
runtime modules and must not change product backend/frontend behavior.

## Slice

- slice_id: `SLICE-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP`
- slice_slug: `grace-orchestrator-synthetic-edge-matrix-mvp`
- feature_id: `FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP`
- packet_id: `FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP-W01-SYNTHETIC-EDGE-MATRIX`
- wave_id: `W01`
- status: `ready`
- phase: `PHASE-GRACE-ORCHESTRATOR-PORTABLE-MVP`
- depends_on: `FEAT-GRACE-REWORK-RESUME-SOURCE-HASH-GATE-MVP-W01-SOURCE-HASH-GATE`
- feature_dir: `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP`

## Source Of Truth

- `/opt/astro-project/docs/architecture/PORTABLE_GRACE_ORCHESTRATION_PLATFORM.md`
- `/opt/astro-project/prefect_grace/platform/rework_resume_policy.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`

## Impacted Modules

- `M-GRACE-SYNTHETIC-EDGE-MATRIX`
- `M-GRACE-SCENARIO-FIXTURES`
- `M-GRACE-RESUME-SAFETY-INVARIANTS`
- `M-GRACE-BACKLOG-CONTROLLER`
- `M-GRACE-CODEX-LAUNCHER`
- `M-GRACE-FEATURE-PIPELINE`
- `M-GRACE-CLI`

## Recommended Role Assignment

- coder: `Sonnet` or `Codex high`; this is mostly test matrix and fixture code.
- verifier: `Codex medium`; must run the full synthetic matrix locally.
- reviewer: `Opus` or `Codex xhigh`; reviewer must inspect invariant quality, not only green test count.
- rework policy: fresh session if invariants are changed; light resume only for small fixture naming fixes.

## Required Design Decisions

### 1. Generated Matrix, Not Hand-Written Sprawl

The implementation must generate scenario combinations from dimensions:

- `source_hash`: same, changed, missing, malformed;
- `session`: exists, missing, stale, wrong packet, wrong role, killed/stalled;
- `resume_strategy`: none, feature_role, packet_parent;
- `resume_allowed`: true, false, missing;
- `resume_block_reason`: none, contract_changed, registry_blocked, missing_last_executed_hash, registry_error, missing_session, stale_session;
- `registry_error`: none, load_failed, corrupt_yaml, permission_denied;
- `execution_state`: no_prior_run, last_success, last_failed, last_timeout;
- `thread_state`: fresh, resumed, auto_resumed, stalled_killed;
- `rework_mode`: `light_resume`, `bounded_fresh`, `fresh_session`, `decision_required`;
- `rework_reason`: reviewer small fix, architect contract change, planner reslice, evidence blocker, ambiguous;
- `registry_status`: ready, running, accepted, blocked, changed_after_acceptance, ready_for_retry, cascading_blocked;
- `dependencies`: accepted, blocked, mixed, missing, cyclic;
- `artifact_layout`: complete, missing summary, missing latest review, corrupt evidence JSON, huge history;
- `launcher_state`: old thread present, no thread, auto-resume after timeout, parent thread from another packet;
- `scope`: allowed only, frozen only, mixed allowed/frozen, no changes.

The generator may prune impossible combinations, but pruning must be explicit
and tested.

### 1.1. Pruning Rules

The matrix must distinguish impossible combinations from deliberately invalid
state scenarios:

- `pruned_impossible`: combinations that cannot physically be represented by
  the fixture model and should not run;
- `invalid_state_scenarios`: corrupt or contradictory registry/session/artifact
  states that must run and must produce `blocked`, `fail_closed`, or
  `invalid`, never `accepted`.

Minimum `pruned_impossible` rules:

- `session=missing` + `thread_state=resumed`;
- `resume_strategy=none` + `thread_state=resumed`;
- `resume_strategy=none` + `registry_error!=none`;
- `registry_status=accepted` + `dependencies=blocked`;
- `registry_status=accepted` + `dependencies=cyclic`;
- `artifact_layout=missing latest review` + `rework_reason=reviewer small fix`
  when the scenario requires reviewer feedback.

Do not prune `source_hash=same + resume_allowed=false`. This is a valid safety
scenario when the registry blocks resume, the previous execution state is not
safe, a session is missing/stale, or a managed-resume registry error must
fail-closed. Only prune or mark invalid when `resume_allowed=false` has no
`resume_block_reason`.

Every pruned scenario must be counted in the JSON report with:

```json
{
  "scenario_id": "scenario-0042",
  "dimensions": {
    "session": "missing",
    "thread_state": "resumed"
  },
  "reason": "session_missing_cannot_resume_thread"
}
```

### 2. Invariants Are First-Class

Each scenario must assert named invariants. Minimum invariant names:

- `INV-NO-RESUME-ON-SOURCE-HASH-CHANGE`;
- `INV-NO-RESUME-WHEN-REGISTRY-BLOCKS`;
- `INV-NO-RESUME-ON-MISSING-SESSION`;
- `INV-DEPENDENCY-BLOCK-STOPS-DOWNSTREAM`;
- `INV-SCOPE-FROZEN-BLOCKS-MERGE`;
- `INV-CORRUPT-ARTIFACT-DOES-NOT-ACCEPT`;
- `INV-CLI-JSON-STABLE`;
- `INV-NO-LIVE-AGENTS`.

Failures must show scenario dimensions and the invariant name.

Invariant assertions must be deterministic functions. Examples:

```python
def assert_inv_no_resume_on_source_hash_change(result: SyntheticScenarioResult) -> None:
    if result.dimensions["source_hash"] == "changed":
        assert result.session_mode == "exec", (
            f"Expected exec mode when source_hash changed, got {result.session_mode}"
        )
        assert result.resumed_from_thread_id is None, (
            "Expected no thread resume when source_hash changed"
        )


def assert_inv_no_resume_when_registry_blocks(result: SyntheticScenarioResult) -> None:
    if result.dimensions["resume_allowed"] == "false":
        assert result.session_mode == "exec"
        assert result.resumed_from_thread_id is None


def assert_inv_registry_error_fail_closed(result: SyntheticScenarioResult) -> None:
    if (
        result.dimensions["resume_strategy"] in {"feature_role", "packet_parent"}
        and result.dimensions["registry_error"] != "none"
    ):
        assert result.resume_allowed is False
        assert result.session_mode == "exec"
        assert result.resumed_from_thread_id is None
```

### 3. No Live Runtime

The matrix must use fake packet dirs, fake registry YAML, fake session indexes,
and command planning. It must not start:

- Codex;
- Claude;
- agy;
- Prefect server/deployments;
- Docker product containers;
- product backend/frontend services.

### 4. Keep It Portable

The generator must not depend on `/opt/astro-project` except through temporary
test paths. Project-specific paths must be injected through fixtures.

### 5. Matrix Size Is Controlled

The default test run must be fast enough for normal PR verification. If the full
cartesian product is too large, implement:

- `smoke` profile for fast PR checks;
- `full` profile for nightly/local stress;
- deterministic seed;
- JSON report with counts of generated, pruned, passed, failed scenarios.

Performance budget:

- `smoke` profile: <= 30 seconds and >= 50 executed scenarios;
- `full` profile: <= 5 minutes and >= 500 executed scenarios;
- per-scenario average: <= 100 ms for pure matrix execution.

If the budget is exceeded, reduce fixture setup cost before reducing invariant
coverage:

- reuse immutable fixture fragments for identical dimensions;
- lazily generate files on first access;
- add optional pytest-xdist parallelism, but keep single-process execution
  deterministic and supported.

Seed determinism is mandatory:

```python
def build_synthetic_edge_matrix(
    profile: str = "smoke",
    seed: int = 1,
    dimensions_override: dict[str, list[str]] | None = None,
) -> list[SyntheticScenario]:
    """Build deterministic scenarios.

    The same seed and profile must produce the same scenario IDs, dimensions,
    pruning decisions, and ordering across runs. This is required for
    reproducible failures and commit-to-commit comparisons.
    """
```

## Allowed Write Scope

Implementation:

- `/opt/astro-project/prefect_grace/platform/synthetic_edge_matrix.py`
- `/opt/astro-project/prefect_grace/platform/scenario_fixtures.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_invariants.py`
- `/opt/astro-project/prefect_grace/platform/synthetic_runner.py`
- `/opt/astro-project/prefect_grace/platform/rework_resume_policy.py`
- `/opt/astro-project/prefect_grace/platform/state_store.py`
- `/opt/astro-project/prefect_grace/platform/backlog_controller.py`
- `/opt/astro-project/prefect_grace/tasks/codex_launcher.py`
- `/opt/astro-project/prefect_grace/flows/feature_pipeline.py`
- `/opt/astro-project/prefect_grace/cli.py`

Tests:

- `/opt/astro-project/tests/test_prefect_grace_synthetic_edge_matrix.py`
- `/opt/astro-project/tests/test_prefect_grace_rework_resume_policy.py`
- `/opt/astro-project/tests/test_prefect_grace_state_store_resume.py`
- `/opt/astro-project/tests/test_prefect_grace_backlog_controller_resume_integration.py`
- `/opt/astro-project/tests/test_prefect_grace_codex_launcher_resume_gate.py`
- `/opt/astro-project/tests/test_prefect_grace_feature_pipeline_dynamic.py`
- `/opt/astro-project/tests/test_prefect_grace_cli_contracts.py`

Packet artifacts:

- `/opt/astro-project/prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP/**`

## Frozen Scope

- `/opt/astro-project/backend/**`
- `/opt/astro-project/frontend/**`
- `/opt/astro-project/scripts/pipeline.py`
- `/opt/astro-project/scripts/run_e2e.sh`
- `/opt/astro-project/tools/post_test_review.py`
- `/opt/astro-project/prefect_grace/roles/**`
- `/opt/astro-project/prefect_grace/state/*.yaml`
- `/opt/astro-project/requirements.xml`
- `/opt/astro-project/technology.xml`
- `/opt/astro-project/development-plan.xml`
- `/opt/astro-project/knowledge-graph.xml`
- `/opt/astro-project/verification-matrix.md`
- `/opt/solarsage-astro/**`

## Must Preserve

- Existing accepted platform tests keep passing.
- Existing CLI JSON envelope remains stable.
- Existing packet parser strict validation keeps working.
- No live agents or Prefect deployments are started by tests.
- Synthetic fixtures write only under `tmp_path`.
- No product backend/frontend files are modified.
- No unrelated refactor of `feature_pipeline.py` or `codex_launcher.py`.

## Required Implementation Shape

Add a small scenario model:

```python
class SyntheticScenario:
    scenario_id: str
    dimensions: dict[str, str]
    expected_invariants: list[str]
```

Add a deterministic matrix builder:

```python
def build_synthetic_edge_matrix(
    profile: str = "smoke",
    seed: int = 1,
    dimensions_override: dict[str, list[str]] | None = None,
) -> list[SyntheticScenario]:
    ...
```

Add a generated fixture object:

```python
class SyntheticFixture:
    """Generated test fixture for one scenario."""

    packet_dir: Path
    registry_file: Path
    session_index: Path
    state_root: Path

    def setup(self) -> None:
        """Write only tmp_path-backed fixture files."""

    def teardown(self) -> None:
        """Remove transient files when the test owns cleanup."""
```

Add a runner that executes only pure/platform test functions:

```python
def run_synthetic_scenario(scenario: SyntheticScenario, tmp_path: Path) -> SyntheticScenarioResult:
    ...
```

Add a JSON-reporting CLI:

```bash
python3 -m prefect_grace.cli synthetic-edge-matrix --profile smoke --json
```

Required JSON fields:

```json
{
  "ok": true,
  "profile": "smoke",
  "seed": 1,
  "generated": 0,
  "pruned": 0,
  "passed": 0,
  "failed": 0,
  "pruned_scenarios": [],
  "failures": []
}
```

Failure payloads must be useful without reading pytest internals:

```json
{
  "failures": [
    {
      "scenario_id": "scenario-0042",
      "dimensions": {
        "source_hash": "changed",
        "resume_strategy": "packet_parent",
        "registry_error": "none"
      },
      "failed_invariant": "INV-NO-RESUME-ON-SOURCE-HASH-CHANGE",
      "assertion": "Expected exec mode, got resume",
      "actual_command": ["codex1", "exec", "resume", "thread-123", "-"],
      "expected_command_pattern": ["codex1", "exec", "-C", "...", "-"]
    }
  ]
}
```

### Integration With Existing Tests

The synthetic matrix complements but does not replace focused tests:

- `tests/test_prefect_grace_codex_launcher_resume_gate.py` keeps detailed
  launcher-level assertions;
- `tests/test_prefect_grace_backlog_controller_resume_integration.py` keeps
  registry/backlog integration assertions;
- `tests/test_prefect_grace_feature_pipeline_dynamic.py` keeps dynamic pipeline
  regression coverage.

The matrix provides breadth across many combinations. Existing tests provide
depth for specific behavior and regression details.

## Verification

Run targeted tests:

```bash
pytest -q \
  tests/test_prefect_grace_synthetic_edge_matrix.py \
  tests/test_prefect_grace_rework_resume_policy.py \
  tests/test_prefect_grace_state_store_resume.py \
  tests/test_prefect_grace_backlog_controller_resume_integration.py \
  tests/test_prefect_grace_codex_launcher_resume_gate.py
```

Run regression tests:

```bash
pytest -q \
  tests/test_prefect_grace_feature_pipeline_dynamic.py \
  tests/test_prefect_grace_cli_contracts.py \
  tests/test_prefect_grace_codex_launcher.py
```

Run static checks:

```bash
python3 -m compileall prefect_grace
python3 scripts/grace_lint.py prefect_grace/platform prefect_grace/tasks/codex_launcher.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Run CLI smoke:

```bash
python3 -m prefect_grace.cli synthetic-edge-matrix --profile smoke --json
```

## Expected Evidence

Do not append evidence to `EXECUTION_PACKET.md`. Write evidence under:

```text
EVIDENCE/attempt-0001/evidence_manifest.json
```

Evidence must include:

- command outputs for all verification commands;
- generated/pruned/passed/failed scenario counts;
- at least one example failure payload from an intentionally failing unit test or documented dry-run negative case;
- confirmation that no live agents or Prefect deployments started;
- diff scope limited to Allowed Write Scope.

## Escalation Triggers

Stop and ask controller if:

- tests need a live Prefect server;
- tests need a real Codex/Claude/agy run;
- matrix runtime becomes too slow for PR checks;
- feature pipeline or launcher must be refactored to implement the matrix;
- product backend/frontend files appear necessary.

## Reviewer Gate

Reviewer must reject this packet if:

- invariants are vague or only assert green test counts;
- source-hash changed can still produce a resume command in any scenario;
- registry error on managed resume can silently reuse an old thread;
- tests start live agents or Prefect deployments;
- matrix fixtures write outside temporary directories;
- unrelated large-file refactor appears in the diff.
