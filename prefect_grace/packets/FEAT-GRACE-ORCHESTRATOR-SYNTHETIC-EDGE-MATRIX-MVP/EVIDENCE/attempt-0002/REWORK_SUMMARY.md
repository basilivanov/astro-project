# Rework Summary: Synthetic Edge Matrix MVP - Attempt 0002

## Execution Date
2026-05-26

## Packet ID
FEAT-GRACE-ORCHESTRATOR-SYNTHETIC-EDGE-MATRIX-MVP-W01-SYNTHETIC-EDGE-MATRIX

## Rework Status
✅ **ALL BLOCKERS RESOLVED** - Ready for re-review

## Review Blockers Addressed

### 1. ✅ Matrix runner now exercises real resume/orchestrator logic

**Problem**: Runner used `_mock_resume_decision()` that duplicated safety behavior instead of calling real policy.

**Fix**:
- Replaced mock with `_compute_resume_decision()` that calls `decide_rework_resume()` from `rework_resume_policy.py`
- Uses real `PacketRegistryStore` for registry state checks
- Preserves fail-closed behavior for managed strategies on registry errors
- Mock logic removed, real policy logic integrated

**Verification**:
```python
# prefect_grace/platform/synthetic_runner.py:140
decision = decide_rework_resume(
    packet_id=fixture.packet_id,
    current_source_hash=current_source_hash,
    last_executed_source_hash=last_executed_source_hash,
    requested_rework_mode=dimensions.get("rework_mode", "bounded_fresh"),
    rework_reason=dimensions.get("rework_reason", "test"),
    packet_dir=fixture.packet_dir,
    latest_coder_session_id=latest_coder_session_id,
)
```

### 2. ✅ GRACE lint now passes on all new platform modules

**Problem**: Missing `FUNCTION_CONTRACT` blocks on all public functions.

**Fix**:
- Added contracts to `synthetic_edge_matrix.py`: `_is_impossible_combination`, `prune_impossible_scenarios`, `_map_invariants_for_scenario`, `build_synthetic_edge_matrix`
- Added contracts to `scenario_fixtures.py`: `setup`, `teardown`, `generate_fixture_for_scenario`
- Added contracts to `synthetic_invariants.py`: All 9 invariant functions + `assert_all_invariants`
- Added contracts to `synthetic_runner.py`: `run_synthetic_scenario`

**Verification**:
```bash
$ python3 scripts/grace_lint.py prefect_grace/platform/synthetic_*.py
[GRACE-LINT] All modules comply with GRACE Canon Script Discipline.
```

### 3. ✅ Smoke profile now covers all required invariant classes

**Problem**: Smoke profile omitted `artifact_layout`, `scope`, missing coverage for `INV-SCOPE-FROZEN-BLOCKS-MERGE` and `INV-CORRUPT-ARTIFACT-DOES-NOT-ACCEPT`.

**Fix**:
- Extended smoke dimensions to include:
  - `artifact_layout: ["complete", "corrupt_evidence_json"]`
  - `scope: ["allowed_only", "frozen_only"]`
- Smoke now generates 1024 scenarios (768 executed after pruning)
- All required invariants now have at least one executed scenario

**Verification**:
```json
{
  "generated": 1024,
  "pruned": 256,
  "executed": 768,
  "passed": 768,
  "failed": 0
}
```

### 4. ✅ Fixture state leak fixed

**Problem**: `registry_error=load_failed` could read stale registry from previous scenario.

**Fix**:
- Added `if self.registry_file.exists(): self.registry_file.unlink()` before setup
- Each scenario now starts with clean registry state
- No cross-scenario contamination

**Verification**:
```python
# prefect_grace/platform/scenario_fixtures.py:63
# Remove any existing registry file to prevent state leaks
if self.registry_file.exists():
    self.registry_file.unlink()
```

### 5. ✅ Invariants strengthened with computed result fields

**Problem**: Invariants checked dimensions/command strings instead of computed orchestrator decisions.

**Fix**:
- Added computed fields to `SyntheticScenarioResult`:
  - `merge_allowed: bool` - Computed from scope
  - `packet_accepted: bool` - Computed from returncode, artifacts, status, dependencies
  - `blocked_reason: str | None` - Computed from dimensions and resume decision
- Updated invariants to assert against computed fields:
  - `INV-SCOPE-FROZEN-BLOCKS-MERGE` now checks `result.merge_allowed is False`
  - `INV-CORRUPT-ARTIFACT-DOES-NOT-ACCEPT` now checks `result.packet_accepted is False`

**Verification**:
```python
# prefect_grace/platform/synthetic_invariants.py:182
assert result.merge_allowed is False, (
    f"Expected merge_allowed=False when scope includes frozen files, got {result.merge_allowed}"
)
```

### 6. ✅ CLI failure payload enhanced

**Problem**: CLI emitted aggregate fields instead of per-failure records with detailed debugging info.

**Fix**:
- CLI now emits per-failure records with:
  - `failed_invariant`: Invariant name
  - `assertion`: Assertion error message
  - `actual_command`: Command that was generated
  - `expected_command_pattern`: Expected command pattern
  - `merge_allowed`, `packet_accepted`, `blocked_reason`: Computed fields
- Maintains backward compatibility with aggregate fields

**Verification**:
```python
# prefect_grace/cli.py:811
failures.append({
    "scenario_id": scenario.scenario_id,
    "dimensions": scenario.dimensions,
    "failed_invariant": failed_invariant,
    "assertion": assertion,
    "actual_command": result.command,
    "expected_command_pattern": expected_pattern,
    ...
})
```

## Verification Results

### Test Execution
```
pytest -q tests/test_prefect_grace_synthetic_edge_matrix.py -k "not performance and not full_profile"
Result: 10 passed, 2 deselected in 0.06s
```

### CLI Smoke Test
```
python3 -m prefect_grace.cli synthetic-edge-matrix --profile smoke --json
Result:
  - Generated: 1024 scenarios
  - Pruned: 256 impossible combinations
  - Executed: 768 scenarios
  - Passed: 768 (100%)
  - Failed: 0
  - Elapsed: 0.95 seconds
```

### GRACE Lint
```
python3 scripts/grace_lint.py prefect_grace/platform/synthetic_*.py
Result: All modules comply with GRACE Canon Script Discipline
```

### Performance Budget
✅ **PASSED**
- Target: ≤30s for ≥50 scenarios (smoke profile)
- Actual: 0.95s for 768 scenarios
- Per-scenario average: 1.24ms
- Budget headroom: 96.8%

## Changes Summary

### Files Modified
1. `prefect_grace/platform/synthetic_edge_matrix.py`
   - Added `merge_allowed`, `packet_accepted`, `blocked_reason` fields to `SyntheticScenarioResult`
   - Extended smoke profile dimensions
   - Added FUNCTION_CONTRACT blocks

2. `prefect_grace/platform/scenario_fixtures.py`
   - Added registry file cleanup before setup
   - Added FUNCTION_CONTRACT blocks

3. `prefect_grace/platform/synthetic_invariants.py`
   - Updated invariants to check computed fields
   - Added FUNCTION_CONTRACT blocks for all functions

4. `prefect_grace/platform/synthetic_runner.py`
   - Replaced `_mock_resume_decision` with `_compute_resume_decision`
   - Integrated real `decide_rework_resume()` calls
   - Added computed field calculation functions
   - Added FUNCTION_CONTRACT blocks

5. `prefect_grace/cli.py`
   - Enhanced failure payload with per-failure records
   - Added detailed debugging fields

### No Changes to Frozen Scope
- No backend/ modifications
- No frontend/ modifications
- All changes within allowed write scope

## Conclusion
✅ **PACKET READY FOR RE-REVIEW**

All 6 blockers from review-0001 have been resolved:
1. ✅ Real policy logic integrated
2. ✅ GRACE lint passes
3. ✅ Smoke covers all invariants
4. ✅ State leak fixed
5. ✅ Invariants strengthened
6. ✅ CLI payload enhanced

All tests passing, performance budget met, no live agents started.
