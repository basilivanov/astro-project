"""
Tests for single_live_packet_pilot module.

Verifies single packet pilot execution with managed runner and Git mutation gate.
Uses dependency injection for managed runner and Git gate.
"""

import tempfile
from pathlib import Path

import pytest

from prefect_grace.platform.single_live_packet_pilot import (
    SingleLivePacketPilotResult,
    run_single_live_packet_pilot,
)


def _create_minimal_packet(path: Path, packet_id: str = "TEST-W01-PACKET") -> None:
    """Create minimal valid packet for testing."""
    path.write_text(f"""# Test Packet

- packet_id: {packet_id}
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for single live packet pilot.

## Allowed Write Scope
- src/**

## Frozen Scope
- backend/**

## Must Preserve
- Existing tests pass

## Verification
Run tests.

## Expected Evidence
- Test output

## Escalation Triggers
- Tests fail
""")


def test_dry_run_no_mutations_passes(tmp_path):
    """Verify dry run with no Git mutations passes."""
    # Create temp git repo
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    # Initialize git
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    # Create initial commit
    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    # Create packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"

    # Mock managed runner that returns success
    def mock_runner(**kwargs):
        return {
            "ok": True,
            "domain_status": "passed",
            "packet_id": "TEST-W01-PACKET",
            "attempt": 1,
            "worktree_path": str(worktree_root / "test-worktree"),
            "branch_name": "agent/test/TEST-W01-PACKET/attempt-0001",
            "changed_files": [],
            "agent_result": {},
            "lifecycle_result": {},
            "scope_guard": {},
            "blocker_reason": None,
        }

    result = run_single_live_packet_pilot(
        packet=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        attempt=1,
        base_ref="HEAD",
        target_branch="master",
        remote="origin",
        dry_run=True,
        execute_agent=False,
        acknowledge_live_agent=False,
        commit=False,
        push=False,
        apply_git_mutations=False,
        timeout_seconds=3600,
        managed_runner=mock_runner,
    )

    assert result.ok is True
    assert result.packet_id == "TEST-W01-PACKET"
    assert result.status == "planned"
    assert result.dry_run is True
    assert result.live_opt_in_confirmed is True
    assert result.git_mutation_requested is False
    assert result.managed_runner_status == "passed"
    assert result.scope_status == "passed"
    assert result.live_agents_started == 0
    assert result.prefect_runs_created == 0
    assert len(result.blockers) == 0
    assert result.blocker_reason is None


def test_missing_live_opt_in_blocks(tmp_path):
    """Verify missing live opt-in blocks execution."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"

    result = run_single_live_packet_pilot(
        packet=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        attempt=1,
        base_ref="HEAD",
        target_branch="master",
        dry_run=False,
        execute_agent=True,
        acknowledge_live_agent=False,  # Missing acknowledgement
        opt_in_token=None,  # Missing token
        commit=False,
        push=False,
        timeout_seconds=3600,
    )

    assert result.ok is False
    assert result.status == "blocked"
    assert result.live_opt_in_confirmed is False
    assert result.live_agents_started == 0
    assert len(result.blockers) == 2
    assert any(b["code"] == "live_opt_in_ack_required" for b in result.blockers)
    assert any(b["code"] == "live_opt_in_token_required" for b in result.blockers)


def test_live_execution_with_opt_in_passes(tmp_path):
    """Verify live execution with all opt-ins passes."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"

    # Mock managed runner that returns success
    def mock_runner(**kwargs):
        return {
            "ok": True,
            "domain_status": "passed",
            "packet_id": "TEST-W01-PACKET",
            "attempt": 1,
            "worktree_path": str(worktree_root / "test-worktree"),
            "branch_name": "agent/test/TEST-W01-PACKET/attempt-0001",
            "changed_files": ["src/test.py"],
            "agent_result": {},
            "lifecycle_result": {},
            "scope_guard": {},
            "blocker_reason": None,
        }

    result = run_single_live_packet_pilot(
        packet=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        attempt=1,
        base_ref="HEAD",
        target_branch="master",
        dry_run=False,
        execute_agent=True,
        acknowledge_live_agent=True,
        opt_in_token="1",
        commit=False,
        push=False,
        timeout_seconds=3600,
        managed_runner=mock_runner,
    )

    assert result.ok is True
    assert result.status == "completed"
    assert result.live_opt_in_confirmed is True
    assert result.live_agents_started == 1
    assert result.managed_runner_status == "passed"
    assert len(result.blockers) == 0


def test_scope_blocked_fails(tmp_path):
    """Verify scope violations block execution."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"

    # Mock managed runner that returns scope_blocked
    def mock_runner(**kwargs):
        return {
            "ok": False,
            "domain_status": "scope_blocked",
            "packet_id": "TEST-W01-PACKET",
            "attempt": 1,
            "worktree_path": str(worktree_root / "test-worktree"),
            "branch_name": "agent/test/TEST-W01-PACKET/attempt-0001",
            "changed_files": ["backend/forbidden.py"],
            "agent_result": {},
            "lifecycle_result": {},
            "scope_guard": {"ok": False, "frozen_violations": [{"file_path": "backend/forbidden.py"}]},
            "blocker_reason": "scope_guard_failed",
        }

    result = run_single_live_packet_pilot(
        packet=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        attempt=1,
        base_ref="HEAD",
        target_branch="master",
        dry_run=True,
        execute_agent=False,
        commit=False,
        push=False,
        timeout_seconds=3600,
        managed_runner=mock_runner,
    )

    assert result.ok is False
    assert result.status == "blocked"
    assert result.managed_runner_status == "scope_blocked"
    assert result.scope_status == "blocked"
    assert len(result.blockers) == 1
    assert result.blockers[0]["code"] == "scope_guard_failed"


def test_agent_failed_blocks(tmp_path):
    """Verify agent failure blocks execution."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"

    # Mock managed runner that returns agent_failed
    def mock_runner(**kwargs):
        return {
            "ok": False,
            "domain_status": "agent_failed",
            "packet_id": "TEST-W01-PACKET",
            "attempt": 1,
            "worktree_path": str(worktree_root / "test-worktree"),
            "branch_name": "agent/test/TEST-W01-PACKET/attempt-0001",
            "changed_files": [],
            "agent_result": {"returncode": 1},
            "lifecycle_result": {},
            "scope_guard": {},
            "blocker_reason": "Agent failed: returncode=1",
        }

    result = run_single_live_packet_pilot(
        packet=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        attempt=1,
        base_ref="HEAD",
        target_branch="master",
        dry_run=True,
        execute_agent=False,
        commit=False,
        push=False,
        timeout_seconds=3600,
        managed_runner=mock_runner,
    )

    assert result.ok is False
    assert result.status == "blocked"
    assert result.managed_runner_status == "agent_failed"
    assert len(result.blockers) == 1
    assert result.blockers[0]["code"] == "agent_failed"


def test_git_mutation_dry_run_planned(tmp_path):
    """Verify Git mutation dry run returns planned status."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"

    # Mock managed runner that returns success
    def mock_runner(**kwargs):
        return {
            "ok": True,
            "domain_status": "passed",
            "packet_id": "TEST-W01-PACKET",
            "attempt": 1,
            "worktree_path": str(worktree_root / "test-worktree"),
            "branch_name": "agent/test/TEST-W01-PACKET/attempt-0001",
            "changed_files": ["src/test.py"],
            "agent_result": {},
            "lifecycle_result": {},
            "scope_guard": {},
            "blocker_reason": None,
        }

    # Mock git gate that returns planned
    def mock_git_gate(**kwargs):
        return {
            "packet_id": "TEST-W01-PACKET",
            "status": "planned",
            "dry_run": True,
            "ok": True,
            "mutations": {"commit": "planned", "push": "planned", "merge": "not_requested"},
            "changed_files_total": 1,
            "changed_files_sample": ["src/test.py"],
            "allowed_files_sample": ["src/test.py"],
            "commit_sha": None,
            "pushed_ref": None,
            "pushed_commit_sha": None,
            "merge_sha": None,
            "packet_branch": "agent/test/TEST-W01-PACKET/attempt-0001",
            "target_branch": "master",
            "remote": "origin",
            "blocker_reason": None,
            "blockers": [],
            "scope_guard": {"ok": True},
            "evidence": {"present": True, "valid": True},
            "review": {"present": True, "accepted": True},
        }

    result = run_single_live_packet_pilot(
        packet=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        attempt=1,
        base_ref="HEAD",
        target_branch="master",
        dry_run=True,
        execute_agent=False,
        commit=True,
        push=True,
        apply_git_mutations=False,
        timeout_seconds=3600,
        managed_runner=mock_runner,
        git_gate=mock_git_gate,
    )

    assert result.ok is True
    assert result.status == "planned"
    assert result.git_mutation_requested is True
    assert result.git_gate_status == "planned"
    assert result.evidence_status == "valid"
    assert result.review_status == "accepted"
    assert len(result.blockers) == 0


def test_git_mutation_missing_evidence_blocks(tmp_path):
    """Verify missing evidence blocks Git mutations."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"

    # Mock managed runner that returns success
    def mock_runner(**kwargs):
        return {
            "ok": True,
            "domain_status": "passed",
            "packet_id": "TEST-W01-PACKET",
            "attempt": 1,
            "worktree_path": str(worktree_root / "test-worktree"),
            "branch_name": "agent/test/TEST-W01-PACKET/attempt-0001",
            "changed_files": ["src/test.py"],
            "agent_result": {},
            "lifecycle_result": {},
            "scope_guard": {},
            "blocker_reason": None,
        }

    # Mock git gate that returns blocked due to missing evidence
    def mock_git_gate(**kwargs):
        return {
            "packet_id": "TEST-W01-PACKET",
            "status": "blocked",
            "dry_run": True,
            "ok": False,
            "mutations": {"commit": "blocked", "push": "blocked", "merge": "not_requested"},
            "blocker_reason": "invalid_evidence_manifest",
            "blockers": [{"code": "invalid_evidence_manifest", "message": "Required verification evidence is missing or invalid"}],
            "scope_guard": {"ok": True},
            "evidence": {"present": False, "valid": False},
            "review": {"present": True, "accepted": True},
        }

    result = run_single_live_packet_pilot(
        packet=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        attempt=1,
        base_ref="HEAD",
        target_branch="master",
        dry_run=True,
        execute_agent=False,
        commit=True,
        push=True,
        apply_git_mutations=False,
        timeout_seconds=3600,
        managed_runner=mock_runner,
        git_gate=mock_git_gate,
    )

    assert result.ok is False
    assert result.status == "blocked"
    assert result.git_gate_status == "blocked"
    assert result.evidence_status == "missing"
    assert result.review_status == "accepted"
    assert len(result.blockers) == 1
    assert result.blockers[0]["code"] == "invalid_evidence_manifest"


def test_git_mutation_missing_review_blocks(tmp_path):
    """Verify missing accepted review blocks Git mutations."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"

    # Mock managed runner that returns success
    def mock_runner(**kwargs):
        return {
            "ok": True,
            "domain_status": "passed",
            "packet_id": "TEST-W01-PACKET",
            "attempt": 1,
            "worktree_path": str(worktree_root / "test-worktree"),
            "branch_name": "agent/test/TEST-W01-PACKET/attempt-0001",
            "changed_files": ["src/test.py"],
            "agent_result": {},
            "lifecycle_result": {},
            "scope_guard": {},
            "blocker_reason": None,
        }

    # Mock git gate that returns blocked due to missing review
    def mock_git_gate(**kwargs):
        return {
            "packet_id": "TEST-W01-PACKET",
            "status": "blocked",
            "dry_run": True,
            "ok": False,
            "mutations": {"commit": "blocked", "push": "blocked", "merge": "not_requested"},
            "blocker_reason": "missing_accepted_review",
            "blockers": [{"code": "missing_accepted_review", "message": "Latest packet review is missing or not accepted"}],
            "scope_guard": {"ok": True},
            "evidence": {"present": True, "valid": True},
            "review": {"present": False, "accepted": False},
        }

    result = run_single_live_packet_pilot(
        packet=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        attempt=1,
        base_ref="HEAD",
        target_branch="master",
        dry_run=True,
        execute_agent=False,
        commit=True,
        push=True,
        apply_git_mutations=False,
        timeout_seconds=3600,
        managed_runner=mock_runner,
        git_gate=mock_git_gate,
    )

    assert result.ok is False
    assert result.status == "blocked"
    assert result.git_gate_status == "blocked"
    assert result.evidence_status == "valid"
    assert result.review_status == "missing"
    assert len(result.blockers) == 1
    assert result.blockers[0]["code"] == "missing_accepted_review"


def test_packet_parse_failure_blocks(tmp_path):
    """Verify packet parse failure blocks execution."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    packet_file = tmp_path / "INVALID_PACKET.md"
    packet_file.write_text("Invalid packet content")

    worktree_root = tmp_path / "worktrees"

    result = run_single_live_packet_pilot(
        packet=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        attempt=1,
        base_ref="HEAD",
        target_branch="master",
        dry_run=True,
        execute_agent=False,
        commit=False,
        push=False,
        timeout_seconds=3600,
    )

    assert result.ok is False
    assert result.packet_id == "unknown"
    assert result.status == "blocked"
    assert len(result.blockers) == 1
    assert result.blockers[0]["code"] == "packet_parse_failed"
