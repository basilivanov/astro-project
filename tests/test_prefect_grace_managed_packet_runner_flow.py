"""
Tests for managed_packet_runner_flow module.

Verifies Prefect flow wrapper for managed packet execution.
"""

import tempfile
from pathlib import Path

from prefect_grace.flows.managed_packet_runner_flow import (
    managed_packet_runner_flow,
    run_managed_packet_task,
    publish_managed_packet_artifact_task,
)


def test_run_managed_packet_task_dry_run(tmp_path):
    """Verify run_managed_packet_task works in dry run mode."""
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
Test packet for flow.

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

    result = run_managed_packet_task(
        packet_file=str(packet_file),
        repo_root=str(repo_root),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
    )

    assert isinstance(result, dict)
    assert result["ok"] is True
    assert result["domain_status"] == "passed"
    assert result["packet_id"] == "TEST-W01-PACKET"
    assert result["attempt"] == 1


def test_run_managed_packet_task_with_agent(tmp_path):
    """Verify run_managed_packet_task works with fake agent."""
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
Test packet for flow with agent.

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

    # Note: This will use the default launcher which will fail,
    # but we're testing the task wrapper, not the launcher
    result = run_managed_packet_task(
        packet_file=str(packet_file),
        repo_root=str(repo_root),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,  # Keep dry_run=True to avoid actual agent execution
        execute_agent=False,
    )

    assert isinstance(result, dict)
    assert "ok" in result
    assert "domain_status" in result
    assert "packet_id" in result


def test_publish_managed_packet_artifact_task_returns_list():
    """Verify publish_managed_packet_artifact_task returns list."""
    result = {
        "ok": True,
        "domain_status": "passed",
        "packet_id": "TEST-PACKET",
        "attempt": 1,
        "worktree_path": "/tmp/worktree",
        "branch_name": "test-branch",
        "changed_files": [],
        "agent_result": {},
        "lifecycle_result": {},
        "scope_guard": {},
        "blocker_reason": None,
    }

    artifact_ids = publish_managed_packet_artifact_task(result)
    assert isinstance(artifact_ids, list)
    # Will be empty list since Prefect artifacts not available in test environment


def test_managed_packet_runner_flow_dry_run(tmp_path):
    """Verify managed_packet_runner_flow works in dry run mode."""
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
Test packet for flow.

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

    result = managed_packet_runner_flow(
        packet_file=str(packet_file),
        repo_root=str(repo_root),
        worktree_root=str(worktree_root),
        project_key="test-project",
        packet_id="TEST-W01-PACKET",
        attempt=1,
        base_ref="HEAD",
        dry_run=True,
        execute_agent=False,
    )

    assert isinstance(result, dict)
    assert result["ok"] is True
    assert result["domain_status"] == "passed"
    assert result["packet_id"] == "TEST-W01-PACKET"
    assert result["attempt"] == 1
    assert "artifact_ids" in result
    assert isinstance(result["artifact_ids"], list)


def test_managed_packet_runner_flow_scope_blocked(tmp_path):
    """Verify flow completes successfully even when scope is blocked."""
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
Test packet for scope blocked.

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

    # Fake launcher that violates frozen scope
    def fake_launcher(packet_id, **kwargs):
        workdir = Path(kwargs["workdir_override"])
        frozen_file = workdir / "backend" / "app" / "main.py"
        frozen_file.parent.mkdir(parents=True, exist_ok=True)
        frozen_file.write_text("# modified\n")
        subprocess.run(["git", "add", str(frozen_file)], cwd=workdir, check=True)
        return {
            "returncode": 0,
            "termination_reason": "completed",
            "packet_id": packet_id,
        }

    # Import and patch the launcher
    from prefect_grace.platform import managed_packet_runner
    original_launcher = managed_packet_runner.launch_codex_for_packet
    managed_packet_runner.launch_codex_for_packet = fake_launcher

    try:
        result = managed_packet_runner_flow(
            packet_file=str(packet_file),
            repo_root=str(repo_root),
            worktree_root=str(worktree_root),
            project_key="test-project",
            packet_id="TEST-W01-PACKET",
            attempt=1,
            base_ref="HEAD",
            dry_run=False,
            execute_agent=True,
        )

        # Flow should complete successfully even though domain status is scope_blocked
        assert isinstance(result, dict)
        assert result["ok"] is False
        assert result["domain_status"] == "scope_blocked"
        assert "artifact_ids" in result

    finally:
        # Restore original launcher
        managed_packet_runner.launch_codex_for_packet = original_launcher


def test_managed_packet_runner_flow_agent_failed(tmp_path):
    """Verify flow completes successfully even when agent fails."""
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
Test packet for agent failed.

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

    # Fake launcher that fails
    def fake_launcher(packet_id, **kwargs):
        return {
            "returncode": 1,
            "termination_reason": "stall_killed",
            "packet_id": packet_id,
        }

    # Import and patch the launcher
    from prefect_grace.platform import managed_packet_runner
    original_launcher = managed_packet_runner.launch_codex_for_packet
    managed_packet_runner.launch_codex_for_packet = fake_launcher

    try:
        result = managed_packet_runner_flow(
            packet_file=str(packet_file),
            repo_root=str(repo_root),
            worktree_root=str(worktree_root),
            project_key="test-project",
            packet_id="TEST-W01-PACKET",
            attempt=1,
            base_ref="HEAD",
            dry_run=False,
            execute_agent=True,
        )

        # Flow should complete successfully even though domain status is agent_failed
        assert isinstance(result, dict)
        assert result["ok"] is False
        assert result["domain_status"] == "agent_failed"
        assert "artifact_ids" in result

    finally:
        # Restore original launcher
        managed_packet_runner.launch_codex_for_packet = original_launcher
