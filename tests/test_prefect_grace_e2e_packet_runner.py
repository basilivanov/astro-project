"""Tests for prefect_grace.platform.e2e_packet_runner module."""

import json
import tempfile
from pathlib import Path

import pytest

import prefect_grace.platform.e2e_packet_runner as e2e_runner
from prefect_grace.platform.e2e_packet_runner import (
    E2EPacketRunnerResult,
    run_e2e_packet,
    _create_fake_verifier_launcher,
    _create_fake_reviewer_launcher,
    _default_fake_verifier_output,
    _default_fake_reviewer_output,
)
from prefect_grace.platform.managed_packet_runner import ManagedPacketRunResult
from prefect_grace.platform.status_model import DomainStatus


@pytest.fixture
def temp_repo():
    """Create a temporary git repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir) / "repo"
        repo_root.mkdir()

        # Initialize git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_root, check=True, capture_output=True)

        # Create initial commit
        (repo_root / "README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_root, check=True, capture_output=True)

        yield repo_root


@pytest.fixture
def temp_packet(temp_repo):
    """Create a temporary test packet."""
    packet_dir = temp_repo / "prefect_grace" / "packets" / "TEST-PACKET"
    packet_dir.mkdir(parents=True)

    packet_content = """# Execution Packet: Test Packet

## Objective
Test packet for e2e runner testing.

## Slice
- packet_id: TEST-PACKET-W01-TEST
- feature_id: TEST-PACKET
- wave_id: W01
- status: ready

## Allowed Write Scope
- /tmp/**

## Frozen Scope
- /etc/**

## Must Preserve
- No live agents called
- No merge/push/squash operations

## Verification
Run pytest on test files.

## Expected Evidence
- EV-001: Test output (stage: packet_local, producer: pytest)

## Escalation Triggers
- Live agents required
"""

    packet_path = packet_dir / "EXECUTION_PACKET.md"
    packet_path.write_text(packet_content)

    return packet_path


def test_e2e_packet_dry_run_accepted(temp_repo, temp_packet):
    """Test e2e packet dry run with accepted verdict."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    result = run_e2e_packet(
        project_root=temp_repo,
        packet_path=temp_packet,
        state_root=state_root,
        worktree_root=worktree_root,
        project_key="test",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
        fake_verifier_output=None,
        fake_reviewer_output=None,
        timeout_seconds=60,
        keep_worktree=True,
    )

    assert result.packet_id == "TEST-PACKET-W01-TEST"
    assert result.attempt == 1
    assert result.runtime_status == "completed"
    assert result.domain_status == "accepted"
    assert result.registry_status == "accepted"
    assert result.registry_reason == "execution_accepted"
    assert result.registry_transition == {
        "registry_status": "accepted",
        "reason": "execution_accepted",
        "is_terminal": True,
        "is_failure": False,
    }
    assert result.ok is True
    assert result.worktree_path is not None
    assert result.branch_name is not None
    assert result.managed_runner_result is not None
    assert result.handoff_result is not None


def test_e2e_packet_dry_run_rework_required(temp_repo, temp_packet):
    """Test e2e packet dry run with rework_required verdict."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    # Create fake reviewer output with rework_required
    fake_reviewer_file = temp_repo / "fake_reviewer_rework.txt"
    fake_reviewer_file.write_text("""
Reviewer output with rework required.

FINAL_PACKET_DECISION_JSON
{
  "packet_verdict": "rework_required",
  "route_classification": "quality_rework",
  "rework_mode": "light_resume",
  "reasons": ["Test coverage insufficient"]
}
END_FINAL_PACKET_DECISION_JSON
""")

    result = run_e2e_packet(
        project_root=temp_repo,
        packet_path=temp_packet,
        state_root=state_root,
        worktree_root=worktree_root,
        project_key="test",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
        fake_verifier_output=None,
        fake_reviewer_output=fake_reviewer_file,
        timeout_seconds=60,
        keep_worktree=True,
    )

    assert result.packet_id == "TEST-PACKET-W01-TEST"
    assert result.domain_status == "rework_required"
    assert result.registry_status == "ready_for_retry"
    assert result.registry_reason == "quality_rework"
    assert result.ok is False  # rework_required is not accepted, so ok=False
    assert result.handoff_result is not None
    assert result.handoff_result["domain_status"] == "rework_required"


def test_e2e_packet_scope_blocked_prevents_handoff_and_maps_registry(monkeypatch, temp_repo, temp_packet):
    """Test managed runner scope_blocked prevents handoff and maps to registry blocked."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    def fake_managed_runner(**kwargs):
        return ManagedPacketRunResult(
            ok=False,
            domain_status=DomainStatus.SCOPE_BLOCKED.value,
            packet_id=kwargs["packet_id"],
            attempt=kwargs["attempt"],
            worktree_path=str(worktree_root / "TEST-PACKET-W01-TEST-attempt-1"),
            branch_name="grace/test/TEST-PACKET-W01-TEST/attempt-1",
            changed_files=["frozen/file.txt"],
            agent_result={"dry_run": True},
            lifecycle_result={"status": DomainStatus.SCOPE_BLOCKED.value},
            scope_guard={"ok": False, "frozen_violations": ["frozen/file.txt"]},
            artifact_ids=["artifact://scope-blocked"],
            blocker_reason="Scope violations: 1 frozen violation(s)",
        )

    def fail_handoff(**kwargs):
        raise AssertionError("handoff must not run when coder scope is blocked")

    monkeypatch.setattr(e2e_runner, "run_managed_packet", fake_managed_runner)
    monkeypatch.setattr(e2e_runner, "run_verifier_reviewer_handoff", fail_handoff)

    result = run_e2e_packet(
        project_root=temp_repo,
        packet_path=temp_packet,
        state_root=state_root,
        worktree_root=worktree_root,
        project_key="test",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
        fake_verifier_output=None,
        fake_reviewer_output=None,
        timeout_seconds=60,
        keep_worktree=True,
    )

    assert result.ok is False
    assert result.domain_status == "scope_blocked"
    assert result.registry_status == "blocked"
    assert result.registry_reason == "scope_violation"
    assert result.registry_transition == {
        "registry_status": "blocked",
        "reason": "scope_violation",
        "is_terminal": True,
        "is_failure": True,
    }
    assert result.handoff_result is None
    assert result.errors == ["Scope violations: 1 frozen violation(s)"]


def test_e2e_packet_result_to_dict(temp_repo, temp_packet):
    """Test E2EPacketRunnerResult serialization."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    result = run_e2e_packet(
        project_root=temp_repo,
        packet_path=temp_packet,
        state_root=state_root,
        worktree_root=worktree_root,
        project_key="test",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
        fake_verifier_output=None,
        fake_reviewer_output=None,
        timeout_seconds=60,
        keep_worktree=True,
    )

    result_dict = result.to_dict()

    assert isinstance(result_dict, dict)
    assert result_dict["ok"] is True
    assert result_dict["packet_id"] == "TEST-PACKET-W01-TEST"
    assert result_dict["attempt"] == 1
    assert result_dict["runtime_status"] == "completed"
    assert result_dict["domain_status"] == "accepted"
    assert result_dict["registry_status"] == "accepted"
    assert result_dict["registry_reason"] == "execution_accepted"
    assert result_dict["registry_transition"]["registry_status"] == "accepted"
    assert isinstance(result_dict["registry_status"], str)
    assert isinstance(result_dict["registry_reason"], str)
    assert isinstance(result_dict["registry_transition"]["registry_status"], str)
    assert result_dict["worktree_path"] is not None
    assert result_dict["branch_name"] is not None
    assert result_dict["managed_runner_result"] is not None
    assert result_dict["handoff_result"] is not None
    assert isinstance(result_dict["artifact_paths"], list)
    assert isinstance(result_dict["errors"], list)


def test_e2e_packet_custom_fake_outputs(temp_repo, temp_packet):
    """Test e2e packet with custom fake verifier/reviewer outputs."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    # Create custom fake outputs
    fake_verifier_file = temp_repo / "custom_verifier.txt"
    fake_verifier_file.write_text("""
Custom verifier output.

FINAL_VERIFIER_EVIDENCE_JSON
{
  "packet_id": "TEST-PACKET-W01-TEST",
  "generated_by": "verifier",
  "requirement_results": [
    {
      "id": "EV-CUSTOM-001",
      "status": "collected",
      "stage": "packet_local",
      "producer": "custom_verifier",
      "artifact_paths": [],
      "summary": "Custom evidence"
    }
  ]
}
END_FINAL_VERIFIER_EVIDENCE_JSON
""")

    fake_reviewer_file = temp_repo / "custom_reviewer.txt"
    fake_reviewer_file.write_text("""
Custom reviewer output.

FINAL_PACKET_DECISION_JSON
{
  "packet_verdict": "accepted",
  "route_classification": null,
  "rework_mode": null,
  "reasons": []
}
END_FINAL_PACKET_DECISION_JSON
""")

    result = run_e2e_packet(
        project_root=temp_repo,
        packet_path=temp_packet,
        state_root=state_root,
        worktree_root=worktree_root,
        project_key="test",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
        fake_verifier_output=fake_verifier_file,
        fake_reviewer_output=fake_reviewer_file,
        timeout_seconds=60,
        keep_worktree=True,
    )

    assert result.domain_status == "accepted"
    assert result.ok is True


def test_e2e_packet_invalid_packet_path():
    """Test e2e packet with invalid packet path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        packet_path = project_root / "nonexistent" / "EXECUTION_PACKET.md"
        state_root = project_root / "state"
        worktree_root = project_root / "worktrees"

        result = run_e2e_packet(
            project_root=project_root,
            packet_path=packet_path,
            state_root=state_root,
            worktree_root=worktree_root,
            project_key="test",
            attempt=1,
            base_ref="HEAD",
            dry_run=True,
            execute_agent=False,
            fake_verifier_output=None,
            fake_reviewer_output=None,
            timeout_seconds=60,
            keep_worktree=True,
        )

        assert result.ok is False
        assert result.runtime_status == "failed"
        assert result.domain_status == "runner_error"
        assert result.registry_status == "blocked"
        assert result.registry_reason == "runner_error"
        assert len(result.errors) > 0
        assert "parse" in result.errors[0].lower() or "not found" in result.errors[0].lower()


def test_create_fake_verifier_launcher_with_file(temp_repo):
    """Test fake verifier launcher with custom output file."""
    fake_output_file = temp_repo / "verifier_output.txt"
    fake_output_file.write_text("Custom verifier output with marker")

    launcher = _create_fake_verifier_launcher(fake_output_file)
    result = launcher(packet_id="TEST-PACKET")

    assert "raw_output" in result
    assert "Custom verifier output" in result["raw_output"]


def test_create_fake_verifier_launcher_without_file():
    """Test fake verifier launcher without custom output file."""
    launcher = _create_fake_verifier_launcher(None)
    result = launcher(packet_id="TEST-PACKET")

    assert "raw_output" in result
    assert "FINAL_VERIFIER_EVIDENCE_JSON" in result["raw_output"]
    assert "TEST-PACKET" in result["raw_output"]


def test_create_fake_reviewer_launcher_with_file(temp_repo):
    """Test fake reviewer launcher with custom output file."""
    fake_output_file = temp_repo / "reviewer_output.txt"
    fake_output_file.write_text("Custom reviewer output with marker")

    launcher = _create_fake_reviewer_launcher(fake_output_file)
    result = launcher(packet_id="TEST-PACKET")

    assert "raw_output" in result
    assert "Custom reviewer output" in result["raw_output"]


def test_create_fake_reviewer_launcher_without_file():
    """Test fake reviewer launcher without custom output file."""
    launcher = _create_fake_reviewer_launcher(None)
    result = launcher(packet_id="TEST-PACKET")

    assert "raw_output" in result
    assert "FINAL_PACKET_DECISION_JSON" in result["raw_output"]
    assert "TEST-PACKET" in result["raw_output"]


def test_default_fake_verifier_output():
    """Test default fake verifier output generation."""
    output = _default_fake_verifier_output("TEST-PACKET-123")

    assert "FINAL_VERIFIER_EVIDENCE_JSON" in output
    assert "END_FINAL_VERIFIER_EVIDENCE_JSON" in output
    assert "TEST-PACKET-123" in output
    assert "packet_id" in output
    assert "requirement_results" in output


def test_default_fake_reviewer_output():
    """Test default fake reviewer output generation."""
    output = _default_fake_reviewer_output("TEST-PACKET-123")

    assert "FINAL_PACKET_DECISION_JSON" in output
    assert "END_FINAL_PACKET_DECISION_JSON" in output
    assert "TEST-PACKET-123" in output
    assert "packet_verdict" in output
    assert "accepted" in output


def test_e2e_packet_worktree_reuse(temp_repo, temp_packet):
    """Test that repeated e2e packet runs reuse worktree."""
    state_root = temp_repo / "state"
    worktree_root = temp_repo / "worktrees"

    # First run
    result1 = run_e2e_packet(
        project_root=temp_repo,
        packet_path=temp_packet,
        state_root=state_root,
        worktree_root=worktree_root,
        project_key="test",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
        fake_verifier_output=None,
        fake_reviewer_output=None,
        timeout_seconds=60,
        keep_worktree=True,
    )

    worktree_path_1 = result1.worktree_path

    # Second run with same parameters
    result2 = run_e2e_packet(
        project_root=temp_repo,
        packet_path=temp_packet,
        state_root=state_root,
        worktree_root=worktree_root,
        project_key="test",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
        fake_verifier_output=None,
        fake_reviewer_output=None,
        timeout_seconds=60,
        keep_worktree=True,
    )

    worktree_path_2 = result2.worktree_path

    # Worktree paths should be the same (reused)
    assert worktree_path_1 == worktree_path_2
    assert result1.domain_status == "accepted"
    assert result2.domain_status == "accepted"
