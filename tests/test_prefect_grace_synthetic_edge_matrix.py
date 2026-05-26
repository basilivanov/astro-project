# ############################################################################
# TEST: synthetic_edge_matrix
# ROLE: Test synthetic edge matrix generation and invariant checking.
# ############################################################################

from __future__ import annotations

import json
from pathlib import Path

import pytest

from prefect_grace.platform.scenario_fixtures import generate_fixture_for_scenario
from prefect_grace.platform.synthetic_edge_matrix import (
    SyntheticScenario,
    build_synthetic_edge_matrix,
    prune_impossible_scenarios,
)
from prefect_grace.platform.synthetic_invariants import assert_all_invariants
from prefect_grace.platform.synthetic_runner import run_synthetic_scenario


class TestSyntheticEdgeMatrix:
    """Test synthetic edge matrix generation."""

    def test_build_smoke_profile(self):
        """Test smoke profile generates scenarios within budget."""
        scenarios = build_synthetic_edge_matrix(profile="smoke", seed=1)

        # Count non-pruned scenarios
        executed = [s for s in scenarios if not s.pruned]

        # Smoke profile should have >= 50 executed scenarios
        assert len(executed) >= 50, f"Expected >= 50 scenarios, got {len(executed)}"

        # All scenarios should have IDs and dimensions
        for scenario in scenarios:
            assert scenario.scenario_id
            assert isinstance(scenario.dimensions, dict)
            assert len(scenario.dimensions) > 0

    def test_build_full_profile(self):
        """Test full profile generates comprehensive scenarios."""
        scenarios = build_synthetic_edge_matrix(profile="full", seed=1)

        # Count non-pruned scenarios
        executed = [s for s in scenarios if not s.pruned]

        # Full profile should have >= 500 executed scenarios
        assert len(executed) >= 500, f"Expected >= 500 scenarios, got {len(executed)}"

    def test_deterministic_generation(self):
        """Test same seed produces same scenarios."""
        scenarios1 = build_synthetic_edge_matrix(profile="smoke", seed=42)
        scenarios2 = build_synthetic_edge_matrix(profile="smoke", seed=42)

        assert len(scenarios1) == len(scenarios2)

        for s1, s2 in zip(scenarios1, scenarios2):
            assert s1.scenario_id == s2.scenario_id
            assert s1.dimensions == s2.dimensions
            assert s1.pruned == s2.pruned

    def test_pruning_impossible_combinations(self):
        """Test impossible combinations are pruned."""
        # Create a scenario with impossible combination
        scenario = SyntheticScenario(
            scenario_id="test-001",
            dimensions={
                "session": "missing",
                "thread_state": "resumed",
            },
            expected_invariants=[],
        )

        pruned = prune_impossible_scenarios([scenario])

        assert pruned[0].pruned is True
        assert pruned[0].prune_reason == "session_missing_cannot_resume_thread"

    def test_invariant_mapping(self):
        """Test invariants are correctly mapped to scenarios."""
        scenarios = build_synthetic_edge_matrix(profile="smoke", seed=1)

        # Find a scenario with source_hash=changed
        changed_scenarios = [
            s for s in scenarios if s.dimensions.get("source_hash") == "changed"
        ]

        assert len(changed_scenarios) > 0

        # Should have INV-NO-RESUME-ON-SOURCE-HASH-CHANGE
        for scenario in changed_scenarios:
            assert "INV-NO-RESUME-ON-SOURCE-HASH-CHANGE" in scenario.expected_invariants


class TestSyntheticRunner:
    """Test synthetic scenario runner."""

    def test_run_scenario_source_hash_changed(self, tmp_path: Path):
        """Test scenario with source_hash=changed blocks resume."""
        scenario = SyntheticScenario(
            scenario_id="test-hash-changed",
            dimensions={
                "source_hash": "changed",
                "session": "exists",
                "resume_strategy": "packet_parent",
                "resume_allowed": "true",
                "resume_block_reason": "none",
                "registry_error": "none",
                "execution_state": "last_success",
                "thread_state": "fresh",
                "rework_mode": "bounded_fresh",
                "rework_reason": "architect_contract_change",
                "registry_status": "ready",
                "dependencies": "accepted",
                "artifact_layout": "complete",
                "launcher_state": "old_thread_present",
                "scope": "allowed_only",
            },
            expected_invariants=["INV-NO-RESUME-ON-SOURCE-HASH-CHANGE"],
        )

        result = run_synthetic_scenario(scenario, tmp_path)

        # Should use exec mode, not resume
        assert result.session_mode == "exec"
        assert result.resumed_from_thread_id is None

        # Check invariant
        passed, failed = assert_all_invariants(result, scenario.expected_invariants)
        assert len(failed) == 0, f"Failed invariants: {failed}"

    def test_run_scenario_resume_allowed_false(self, tmp_path: Path):
        """Test scenario with resume_allowed=false blocks resume."""
        scenario = SyntheticScenario(
            scenario_id="test-resume-blocked",
            dimensions={
                "source_hash": "same",
                "session": "exists",
                "resume_strategy": "packet_parent",
                "resume_allowed": "false",
                "resume_block_reason": "contract_changed",
                "registry_error": "none",
                "execution_state": "last_success",
                "thread_state": "fresh",
                "rework_mode": "bounded_fresh",
                "rework_reason": "architect_contract_change",
                "registry_status": "ready",
                "dependencies": "accepted",
                "artifact_layout": "complete",
                "launcher_state": "old_thread_present",
                "scope": "allowed_only",
            },
            expected_invariants=["INV-NO-RESUME-WHEN-REGISTRY-BLOCKS"],
        )

        result = run_synthetic_scenario(scenario, tmp_path)

        # Should use exec mode, not resume
        assert result.session_mode == "exec"
        assert result.resumed_from_thread_id is None

        # Check invariant
        passed, failed = assert_all_invariants(result, scenario.expected_invariants)
        assert len(failed) == 0, f"Failed invariants: {failed}"

    def test_run_scenario_missing_session(self, tmp_path: Path):
        """Test scenario with missing session blocks resume."""
        scenario = SyntheticScenario(
            scenario_id="test-missing-session",
            dimensions={
                "source_hash": "same",
                "session": "missing",
                "resume_strategy": "packet_parent",
                "resume_allowed": "true",
                "resume_block_reason": "none",
                "registry_error": "none",
                "execution_state": "no_prior_run",
                "thread_state": "fresh",
                "rework_mode": "bounded_fresh",
                "rework_reason": "architect_contract_change",
                "registry_status": "ready",
                "dependencies": "accepted",
                "artifact_layout": "complete",
                "launcher_state": "no_thread",
                "scope": "allowed_only",
            },
            expected_invariants=["INV-NO-RESUME-ON-MISSING-SESSION"],
        )

        result = run_synthetic_scenario(scenario, tmp_path)

        # Should use exec mode, not resume
        assert result.session_mode == "exec"
        assert result.resumed_from_thread_id is None

        # Check invariant
        passed, failed = assert_all_invariants(result, scenario.expected_invariants)
        assert len(failed) == 0, f"Failed invariants: {failed}"

    def test_run_scenario_registry_error_fail_closed(self, tmp_path: Path):
        """Test registry error on managed strategy fails closed."""
        scenario = SyntheticScenario(
            scenario_id="test-registry-error",
            dimensions={
                "source_hash": "same",
                "session": "exists",
                "resume_strategy": "packet_parent",
                "resume_allowed": "true",
                "resume_block_reason": "none",
                "registry_error": "load_failed",
                "execution_state": "last_success",
                "thread_state": "fresh",
                "rework_mode": "bounded_fresh",
                "rework_reason": "architect_contract_change",
                "registry_status": "ready",
                "dependencies": "accepted",
                "artifact_layout": "complete",
                "launcher_state": "old_thread_present",
                "scope": "allowed_only",
            },
            expected_invariants=["INV-REGISTRY-ERROR-FAIL-CLOSED"],
        )

        result = run_synthetic_scenario(scenario, tmp_path)

        # Should fail closed: no resume
        assert result.session_mode == "exec"
        assert result.resumed_from_thread_id is None
        assert result.resume_allowed is False


class TestSyntheticMatrixPerformance:
    """Test synthetic matrix performance budgets."""

    def test_smoke_profile_performance(self, tmp_path: Path):
        """Test smoke profile meets performance budget."""
        import time

        scenarios = build_synthetic_edge_matrix(profile="smoke", seed=1)
        executed_scenarios = [s for s in scenarios if not s.pruned]

        # Should have >= 50 scenarios
        assert len(executed_scenarios) >= 50

        # Run scenarios and measure time
        start = time.time()
        results = []
        for scenario in executed_scenarios[:50]:  # Run first 50
            result = run_synthetic_scenario(scenario, tmp_path)
            results.append(result)
        elapsed = time.time() - start

        # Should complete in <= 30 seconds
        assert elapsed <= 30.0, f"Smoke profile took {elapsed:.1f}s, expected <= 30s"

        # Average per-scenario should be <= 100ms
        avg_per_scenario = elapsed / len(results)
        assert avg_per_scenario <= 0.1, f"Average per-scenario {avg_per_scenario:.3f}s, expected <= 0.1s"


class TestFixtureGeneration:
    """Test fixture generation."""

    def test_generate_fixture(self, tmp_path: Path):
        """Test fixture generation creates required files."""
        fixture = generate_fixture_for_scenario(
            scenario_id="test-001",
            dimensions={
                "source_hash": "same",
                "session": "exists",
                "resume_strategy": "packet_parent",
                "resume_allowed": "true",
                "resume_block_reason": "none",
                "registry_error": "none",
                "registry_status": "ready",
            },
            tmp_path=tmp_path,
        )

        fixture.setup()

        # Check files exist
        assert fixture.packet_dir.exists()
        assert (fixture.packet_dir / "EXECUTION_PACKET.md").exists()
        assert fixture.registry_file.exists()
        assert fixture.session_index.exists()

        # Check registry content
        import yaml
        with open(fixture.registry_file, "r") as f:
            registry = yaml.safe_load(f)

        assert fixture.packet_id in registry
        assert registry[fixture.packet_id]["resume_allowed"] is True

    def test_generate_fixture_corrupt_yaml(self, tmp_path: Path):
        """Test fixture with corrupt YAML."""
        fixture = generate_fixture_for_scenario(
            scenario_id="test-corrupt",
            dimensions={
                "source_hash": "same",
                "session": "exists",
                "resume_strategy": "packet_parent",
                "resume_allowed": "true",
                "resume_block_reason": "none",
                "registry_error": "corrupt_yaml",
                "registry_status": "ready",
            },
            tmp_path=tmp_path,
        )

        fixture.setup()

        # Registry file should exist but be invalid YAML
        assert fixture.registry_file.exists()

        import yaml
        with pytest.raises(yaml.YAMLError):
            with open(fixture.registry_file, "r") as f:
                yaml.safe_load(f)
