"""
Tests for managed_packet_runner module.

Verifies packet execution in isolated worktree with agent and scope validation.
Uses temporary git repositories and fake launcher callables.
"""

import tempfile
from pathlib import Path

import pytest

from prefect_grace.platform.managed_packet_runner import (
    ManagedPacketRunResult,
    run_managed_packet,
)


def _create_minimal_packet(path: Path) -> None:
    """Create minimal valid packet for testing."""
    path.write_text("""# Test Packet

- packet_id: TEST-W01-PACKET
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for managed runner.

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


def test_managed_packet_run_dry_run_passes(tmp_path):
    """Verify dry run with no changes passes."""
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

    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
    )

    assert result.ok is True
    assert result.domain_status == "passed"
    assert result.packet_id == "TEST-W01-PACKET"
    assert result.attempt == 1
    assert len(result.changed_files) == 0
    assert result.blocker_reason is None


def test_managed_packet_run_scope_blocked_frozen(tmp_path):
    """Verify frozen scope violation blocks."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""# Test Packet

- packet_id: TEST-W01-PACKET
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for frozen scope violation.

## Allowed Write Scope
- src/**
- backend/**

## Frozen Scope
- backend/app/main.py

## Must Preserve
- Existing tests pass

## Verification
Run tests.

## Expected Evidence
- Test output

## Escalation Triggers
- Tests fail
""")

    worktree_root = tmp_path / "worktrees"

    # Fake launcher that writes to frozen file
    def fake_launcher(packet_id, **kwargs):
        workdir = Path(kwargs["workdir_override"])
        frozen_file = workdir / "backend" / "app" / "main.py"
        frozen_file.parent.mkdir(parents=True, exist_ok=True)
        frozen_file.write_text("# modified\n")

        import subprocess
        subprocess.run(["git", "add", str(frozen_file)], cwd=workdir, check=True)

        return {
            "returncode": 0,
            "termination_reason": "completed",
            "packet_id": packet_id,
            "thread_id": "fake-thread-123",
            "session_mode": "exec",
        }

    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=False,
        execute_agent=True,
        launcher=fake_launcher,
    )

    assert result.ok is False
    assert result.domain_status == "scope_blocked"
    assert len(result.scope_guard["frozen_violations"]) == 1
    assert result.scope_guard["frozen_violations"][0]["file_path"] == "backend/app/main.py"


def test_managed_packet_run_scope_blocked_outside_allowed(tmp_path):
    """Verify outside allowed scope violation blocks."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""# Test Packet

- packet_id: TEST-W01-PACKET
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for outside allowed scope violation.

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

    worktree_root = tmp_path / "worktrees"

    # Fake launcher that writes outside allowed
    def fake_launcher(packet_id, **kwargs):
        workdir = Path(kwargs["workdir_override"])
        outside_file = workdir / "scripts" / "deploy.sh"
        outside_file.parent.mkdir(parents=True, exist_ok=True)
        outside_file.write_text("#!/bin/bash\n")

        import subprocess
        subprocess.run(["git", "add", str(outside_file)], cwd=workdir, check=True)

        return {
            "returncode": 0,
            "termination_reason": "completed",
            "packet_id": packet_id,
        }

    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=False,
        execute_agent=True,
        launcher=fake_launcher,
    )

    assert result.ok is False
    assert result.domain_status == "scope_blocked"
    assert len(result.scope_guard["outside_allowed"]) == 1


def test_managed_packet_run_agent_failed(tmp_path):
    """Verify agent failure with clean scope returns agent_failed."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""# Test Packet

- packet_id: TEST-W01-PACKET
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for agent failure.

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

    worktree_root = tmp_path / "worktrees"

    # Fake launcher that fails but doesn't violate scope
    def fake_launcher(packet_id, **kwargs):
        return {
            "returncode": 1,
            "termination_reason": "stall_killed",
            "packet_id": packet_id,
        }

    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=False,
        execute_agent=True,
        launcher=fake_launcher,
    )

    assert result.ok is False
    assert result.domain_status == "agent_failed"
    assert "returncode=1" in result.blocker_reason


def test_managed_packet_run_scope_blocked_wins_over_agent_failed(tmp_path):
    """Verify scope_blocked wins when both agent fails and scope violates."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""# Test Packet

- packet_id: TEST-W01-PACKET
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for scope_blocked priority over agent_failed.

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

    worktree_root = tmp_path / "worktrees"

    # Fake launcher that fails AND violates frozen scope
    def fake_launcher(packet_id, **kwargs):
        workdir = Path(kwargs["workdir_override"])
        frozen_file = workdir / "backend" / "app" / "main.py"
        frozen_file.parent.mkdir(parents=True, exist_ok=True)
        frozen_file.write_text("# modified\n")

        import subprocess
        subprocess.run(["git", "add", str(frozen_file)], cwd=workdir, check=True)

        return {
            "returncode": 1,
            "termination_reason": "stall_killed",
            "packet_id": packet_id,
        }

    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=False,
        execute_agent=True,
        launcher=fake_launcher,
    )

    # scope_blocked wins over agent_failed
    assert result.ok is False
    assert result.domain_status == "scope_blocked"
    assert len(result.scope_guard["frozen_violations"]) == 1


def test_managed_packet_run_launcher_receives_worktree_path(tmp_path):
    """Verify launcher receives worktree path, not repo root."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""# Test Packet

- packet_id: TEST-W01-PACKET
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for launcher worktree path verification.

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

    worktree_root = tmp_path / "worktrees"

    received_workdir = []

    def fake_launcher(packet_id, **kwargs):
        received_workdir.append(str(kwargs["workdir_override"]))
        return {
            "returncode": 0,
            "termination_reason": "completed",
            "packet_id": packet_id,
        }

    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=False,
        execute_agent=True,
        launcher=fake_launcher,
    )

    assert result.ok is True
    assert len(received_workdir) == 1
    assert str(repo_root) not in received_workdir[0]
    assert str(worktree_root) in received_workdir[0]


def test_managed_packet_run_to_dict_serialization(tmp_path):
    """Verify ManagedPacketRunResult.to_dict() works."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""# Test Packet

- packet_id: TEST-W01-PACKET
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for to_dict serialization.

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

    worktree_root = tmp_path / "worktrees"

    result = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
    )

    result_dict = result.to_dict()

    assert result_dict["ok"] is True
    assert result_dict["domain_status"] == "passed"
    assert result_dict["packet_id"] == "TEST-W01-PACKET"
    assert result_dict["attempt"] == 1
    assert isinstance(result_dict["changed_files"], list)
    assert isinstance(result_dict["agent_result"], dict)
    assert isinstance(result_dict["lifecycle_result"], dict)
    assert isinstance(result_dict["scope_guard"], dict)


def test_managed_packet_run_reuses_existing_worktree(tmp_path):
    """Verify managed runner reuses existing worktree for same packet_id/attempt."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    _create_minimal_packet(packet_file)

    worktree_root = tmp_path / "worktrees"

    # First run - creates worktree
    result1 = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
    )

    assert result1.ok is True
    assert result1.domain_status == "passed"
    worktree_path_1 = result1.worktree_path

    # Second run - should reuse existing worktree
    result2 = run_managed_packet(
        packet_file=packet_file,
        repo_root=repo_root,
        worktree_root=worktree_root,
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
    )

    assert result2.ok is True
    assert result2.domain_status == "passed"
    worktree_path_2 = result2.worktree_path

    # Should be the same worktree path
    assert worktree_path_1 == worktree_path_2
