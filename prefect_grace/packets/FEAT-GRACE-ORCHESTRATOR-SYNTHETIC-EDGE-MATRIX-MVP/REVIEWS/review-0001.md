# Review 0001: Synthetic Edge Matrix MVP

## Verdict

`rework_required`

The implementation is a good start: it adds a deterministic matrix, fixture
generation, invariant functions, a runner, CLI output, and tests. However, the
current version does not yet satisfy the packet contract because the matrix
mostly validates its own mock logic instead of the real orchestrator policy,
the smoke profile misses required invariant classes, and the static GRACE lint
gate fails.

## Blockers

### 1. Matrix runner does not exercise the real resume/orchestrator logic

`synthetic_runner.py` imports `decide_rework_resume` but never calls it. The
runner uses `_mock_resume_decision()` and `_mock_launcher_command()` to generate
the expected behavior directly from dimensions. That means the matrix can pass
even if `rework_resume_policy.py`, `PacketRegistryStore`, or the launcher
resume gate regresses.

Required fix:

- Route scenarios through the real pure policy where possible:
  - `decide_rework_resume(...)` for source-hash/resume decisions;
  - real `PacketRegistryStore` fixture reads for registry state;
  - a real command-planning abstraction if available, or a small extracted
    command planner if that can be done without launching Codex.
- Keep live agents disabled, but do not duplicate the safety behavior only in
  mocks.

References:

- `prefect_grace/platform/synthetic_runner.py:27`
- `prefect_grace/platform/synthetic_runner.py:80`
- `prefect_grace/platform/synthetic_runner.py:126`
- `prefect_grace/platform/synthetic_runner.py:182`

### 2. GRACE lint fails on every new platform module

The packet verification requires static checks. Current implementation fails
`scripts/grace_lint.py` because public functions/methods are missing
`FUNCTION_CONTRACT` blocks.

Observed failures:

- `synthetic_edge_matrix.py`: `prune_impossible_scenarios`,
  `build_synthetic_edge_matrix`;
- `scenario_fixtures.py`: `setup`, `teardown`,
  `generate_fixture_for_scenario`;
- `synthetic_invariants.py`: all public invariant functions and
  `assert_all_invariants`;
- `synthetic_runner.py`: `run_synthetic_scenario`.

Required fix:

- Add GRACE function contracts for every public function/method flagged by the
  lint command.
- Re-run lint for all four new modules.

References:

- `prefect_grace/platform/synthetic_edge_matrix.py:156`
- `prefect_grace/platform/synthetic_edge_matrix.py:222`
- `prefect_grace/platform/scenario_fixtures.py:46`
- `prefect_grace/platform/scenario_fixtures.py:82`
- `prefect_grace/platform/scenario_fixtures.py:208`
- `prefect_grace/platform/synthetic_invariants.py:38`
- `prefect_grace/platform/synthetic_runner.py:35`

### 3. Smoke profile does not cover all required invariant classes

The smoke profile executes 192 scenarios, but its selected dimensions omit
`artifact_layout`, `scope`, `execution_state`, `thread_state`,
`launcher_state`, `rework_mode`, and `rework_reason`. As a result, the smoke
CLI gate never exercises:

- `INV-SCOPE-FROZEN-BLOCKS-MERGE`;
- `INV-CORRUPT-ARTIFACT-DOES-NOT-ACCEPT`;
- stalled/auto-resume/timeout edge cases that the packet explicitly added.

The full profile contains some of these, but the evidence does not run the full
profile, and the CLI verification only runs smoke.

Required fix:

- Ensure smoke includes at least one executed scenario for every named required
  invariant.
- Add a test that asserts invariant coverage by profile, especially for smoke.
- Include `thread_state`, `execution_state`, and `launcher_state` in smoke with
  a bounded scenario selection rather than a full cartesian explosion.

References:

- `prefect_grace/platform/synthetic_edge_matrix.py:244`
- `prefect_grace/platform/synthetic_edge_matrix.py:255`
- `prefect_grace/platform/synthetic_edge_matrix.py:202`
- `prefect_grace/platform/synthetic_edge_matrix.py:208`

## Major Issues

### 4. Fixture state leaks between scenarios for `registry_error=load_failed`

CLI execution reuses one `tmp_path` for many scenarios. For `load_failed`,
`SyntheticFixture.setup()` intentionally does not create `packet_registry.yaml`,
but it also does not remove a registry file left by a previous scenario. This
means `load_failed` can read stale state from an earlier scenario in the same
CLI run.

Required fix:

- Make each scenario state root unique, or remove `registry_file` before the
  `load_failed` branch.
- Add a regression test that runs a valid-registry scenario followed by a
  `load_failed` scenario in the same temp root and proves no stale registry is
  reused.

References:

- `prefect_grace/platform/scenario_fixtures.py:63`
- `prefect_grace/platform/scenario_fixtures.py:71`

### 5. Some invariants are too weak to prove the safety behavior

`INV-SCOPE-FROZEN-BLOCKS-MERGE` passes when the command simply does not contain
the word `merge`, even if the scenario otherwise returns success. That does not
prove "frozen scope blocks merge".

`INV-CORRUPT-ARTIFACT-DOES-NOT-ACCEPT` checks the input dimension
`registry_status != accepted`, not a computed runner verdict. This can catch
some contradictory scenarios, but it does not prove that corrupt artifact input
is rejected by the orchestrator.

Required fix:

- Add explicit result fields such as `domain_status`, `merge_allowed`,
  `packet_accepted`, or `blocked_reason`.
- Assert against computed result state, not only dimensions or command strings.

References:

- `prefect_grace/platform/synthetic_invariants.py:116`
- `prefect_grace/platform/synthetic_invariants.py:130`

### 6. CLI failure payload does not match the contract shape

The packet asks for failure payloads that include fields like
`failed_invariant`, `assertion`, `actual_command`, and
`expected_command_pattern`. The current CLI emits `failed_invariants`,
`passed_invariants`, `command`, and `returncode`. It is usable, but weaker than
the requested review/debug format.

Required fix:

- Keep the current aggregate fields if useful, but add per-failure records with
  `failed_invariant`, `assertion`, `actual_command`,
  `expected_command_pattern`, and scenario dimensions.

References:

- `prefect_grace/cli.py:811`
- `prefect_grace/cli.py:822`

## Verification Performed

Commands run during review:

```bash
pytest -q tests/test_prefect_grace_synthetic_edge_matrix.py
python3 -m prefect_grace.cli synthetic-edge-matrix --profile smoke --json
python3 -m compileall prefect_grace/platform/synthetic_edge_matrix.py \
  prefect_grace/platform/scenario_fixtures.py \
  prefect_grace/platform/synthetic_invariants.py \
  prefect_grace/platform/synthetic_runner.py \
  prefect_grace/cli.py
python3 scripts/grace_lint.py prefect_grace/platform/synthetic_edge_matrix.py
python3 scripts/grace_lint.py prefect_grace/platform/scenario_fixtures.py
python3 scripts/grace_lint.py prefect_grace/platform/synthetic_invariants.py
python3 scripts/grace_lint.py prefect_grace/platform/synthetic_runner.py
python3 -m prefect_grace.cli validate-packet \
  prefect_grace/packets/FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP/EXECUTION_PACKET.md \
  --strict --json
```

Results:

- pytest synthetic tests: `12 passed`;
- CLI smoke: `ok=true`, `generated=256`, `pruned=64`, `passed=192`,
  `failed=0`;
- compileall: passed;
- packet strict validation: passed;
- GRACE lint: failed on all four new platform modules.

## Notes

API/provider failure classification was intentionally not added as a blocker to
this packet. It has been captured separately as MVP-7D and a future packet:
`FEAT-GRACE-AGENT-API-FAILURE-CLASSIFICATION-MVP`.
