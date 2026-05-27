# Review 0002 — FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP

status: rework_required
reviewer: codex
reviewed-at: 2026-05-26

## Verdict

Rework attempt 0002 fixed the main design issues from review-0001, but the packet cannot be accepted yet.

Two remaining blockers are mechanical and should be quick to fix:

1. `synthetic_runner.py` does not pass GRACE lint because semantic block markers are unbalanced.
2. CLI text-mode failure rendering still references the old failure payload key and will crash on a failing matrix run.

The API-failure/rate-limit expansion discussed after the packet review is intentionally not a blocker for this packet. It has been captured as a follow-up architecture item and separate future packet.

## Resolved From Review 0001

- Real policy logic is now integrated: the runner calls `decide_rework_resume(...)` through real `PacketRegistryStore` state instead of relying on the old `_mock_resume_decision`.
- Smoke profile now includes `artifact_layout` and `scope`, so the scope and corrupt-artifact invariants are exercised.
- Registry state is reset per scenario, preventing cross-scenario leakage.
- Computed result fields were added: `merge_allowed`, `packet_accepted`, `blocked_reason`.
- Invariants now assert computed outcome fields instead of only dimension labels or command strings.
- JSON failure payload is materially better: it includes the failed invariant, assertion, command, expected pattern, and computed fields.
- Most GRACE contracts were added and targeted pytest coverage is green.

## Blockers

### 1. GRACE lint fails on `synthetic_runner.py`

`python3 scripts/grace_lint.py prefect_grace/platform/synthetic_runner.py` fails:

```text
[GRACE-LINT] Strict contract verification FAILED:
 - platform/synthetic_runner.py: Unbalanced blocks. START_BLOCK count (3) != END_BLOCK count (2).
```

Cause:

- `prefect_grace/platform/synthetic_runner.py:361` opens `# GRACE:START_BLOCK: mock_helpers`
- there is no matching `# GRACE:END_BLOCK: mock_helpers`

Required fix:

- either close the block with a matching `END_BLOCK`, or remove the unnecessary block marker;
- rerun GRACE lint for all four new modules:
  - `prefect_grace/platform/synthetic_edge_matrix.py`
  - `prefect_grace/platform/scenario_fixtures.py`
  - `prefect_grace/platform/synthetic_invariants.py`
  - `prefect_grace/platform/synthetic_runner.py`

### 2. CLI text mode crashes on failure payloads

The CLI JSON payload was updated to emit per-failure records with singular keys:

- `failed_invariant`
- `assertion`
- `actual_command`
- `expected_command_pattern`

But the text-mode branch still reads the old key:

- `prefect_grace/cli.py:878` uses `failure['failed_invariants']`

On an all-green matrix this does not execute, but on the first failing scenario the non-JSON CLI output will raise `KeyError` instead of printing a useful failure.

Required fix:

- update text rendering to use the new failure shape;
- add a test that forces at least one synthetic invariant failure and exercises non-JSON CLI output;
- keep JSON output shape unchanged.

## Major Notes

### Stale module map in `synthetic_runner.py`

The module map still describes removed/mock-only responsibilities:

- `prefect_grace/platform/synthetic_runner.py:15` references `_mock_resume_decision`
- `prefect_grace/platform/synthetic_runner.py:19` says the module uses mock policy decisions

This is now stale because attempt 0002 moved the decision path to real `decide_rework_resume(...)`.

Required fix:

- replace `_mock_resume_decision` with `_compute_resume_decision`;
- describe `_mock_launcher_command` as command planning/mocked command generation, not policy mocking;
- keep the contract aligned with the real runtime boundary: no live agents, but real deterministic policy logic.

## Verification Performed

Targeted tests:

```text
34 passed in 3.00s
```

Regression tests:

```text
50 passed in 39.52s
```

GRACE lint:

```text
prefect_grace/platform/synthetic_edge_matrix.py     PASS
prefect_grace/platform/scenario_fixtures.py         PASS
prefect_grace/platform/synthetic_invariants.py      PASS
prefect_grace/platform/synthetic_runner.py          FAIL
```

Because lint failed, the review gate stopped before accepting the packet.

## Required Rework

1. Fix the unbalanced GRACE block in `synthetic_runner.py`.
2. Fix CLI text-mode failure rendering for the new failure payload schema.
3. Update the stale module map in `synthetic_runner.py`.
4. Add/adjust a test for non-JSON CLI failure rendering.
5. Regenerate attempt evidence with:
   - targeted synthetic matrix tests;
   - relevant regression tests;
   - GRACE lint for all new modules;
   - `synthetic-edge-matrix --profile smoke --json`.

## Acceptance Criteria For Next Review

- All new modules pass `scripts/grace_lint.py`.
- CLI failure output works in both JSON and text mode.
- Smoke matrix still runs without live agent execution.
- Existing resume/source-hash regression tests remain green.
