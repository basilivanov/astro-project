"""
Tests for CLI run-managed-packet command.

Verifies CLI interface for managed packet execution.
"""

import json
import subprocess
import tempfile
from pathlib import Path


def _create_test_repo(tmp_path):
    """Create a test git repository."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    (repo_root / ".git").mkdir()

    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)

    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    return repo_root


def _create_test_packet(tmp_path, allowed_scope=None, frozen_scope=None):
    """Create a test packet file."""
    allowed_scope = allowed_scope or ["src/**"]
    frozen_scope = frozen_scope or ["backend/**"]

    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text(f"""# Test Packet

- packet_id: TEST-W01-PACKET
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet for CLI.

## Allowed Write Scope
{chr(10).join(f'- {scope}' for scope in allowed_scope)}

## Frozen Scope
{chr(10).join(f'- {scope}' for scope in frozen_scope)}

## Must Preserve
- Existing tests pass

## Verification
Run tests.

## Expected Evidence
- Test output

## Escalation Triggers
- Tests fail
""")
    return packet_file


def test_cli_run_managed_packet_dry_run_json_exits_0(tmp_path):
    """Verify CLI dry run with JSON output exits 0."""
    repo_root = _create_test_repo(tmp_path)
    packet_file = _create_test_packet(tmp_path)
    worktree_root = tmp_path / "worktrees"

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-managed-packet",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--packet-id", "TEST-W01-PACKET",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "run-managed-packet"
    assert output["result"]["domain_status"] == "passed"
    assert output["result"]["packet_id"] == "TEST-W01-PACKET"
    assert output["result"]["attempt"] == 1


def test_cli_run_managed_packet_dry_run_text_exits_0(tmp_path):
    """Verify CLI dry run with text output exits 0."""
    repo_root = _create_test_repo(tmp_path)
    packet_file = _create_test_packet(tmp_path)
    worktree_root = tmp_path / "worktrees"

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-managed-packet",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--packet-id", "TEST-W01-PACKET",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--dry-run",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Managed packet run: PASSED" in result.stdout
    assert "Packet: TEST-W01-PACKET" in result.stdout
    assert "Attempt: 1" in result.stdout


def test_cli_run_managed_packet_unsafe_flag_combination_exits_2(tmp_path):
    """Verify CLI rejects --execute-agent without explicit --no-dry-run."""
    repo_root = _create_test_repo(tmp_path)
    packet_file = _create_test_packet(tmp_path)
    worktree_root = tmp_path / "worktrees"

    # Test 1: --execute-agent without --no-dry-run should be rejected
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-managed-packet",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--packet-id", "TEST-W01-PACKET",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--execute-agent",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert len(output["errors"]) == 1
    assert output["errors"][0]["code"] == "MISSING_EXPLICIT_NO_DRY_RUN"

    # Test 2: --execute-agent with explicit --dry-run should also be rejected
    result2 = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-managed-packet",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--packet-id", "TEST-W01-PACKET",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--execute-agent",
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result2.returncode == 2
    output2 = json.loads(result2.stdout)
    assert output2["ok"] is False
    assert len(output2["errors"]) == 1
    # Both cases now return MISSING_EXPLICIT_NO_DRY_RUN since the check happens first
    assert output2["errors"][0]["code"] == "MISSING_EXPLICIT_NO_DRY_RUN"


def test_cli_run_managed_packet_missing_packet_exits_2(tmp_path):
    """Verify CLI exits 2 when packet file missing."""
    repo_root = _create_test_repo(tmp_path)
    worktree_root = tmp_path / "worktrees"
    missing_packet = tmp_path / "MISSING.md"

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-managed-packet",
            "--packet", str(missing_packet),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--packet-id", "TEST-W01-PACKET",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["result"]["domain_status"] == "runner_error"
    assert "No such file or directory" in output["result"]["blocker_reason"]


def test_cli_run_managed_packet_no_dry_run_flag(tmp_path):
    """Verify CLI --no-dry-run flag works."""
    repo_root = _create_test_repo(tmp_path)
    packet_file = _create_test_packet(tmp_path)
    worktree_root = tmp_path / "worktrees"

    # This should work without --execute-agent (dry_run=False but execute_agent=False)
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-managed-packet",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--packet-id", "TEST-W01-PACKET",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--no-dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True


def test_cli_run_managed_packet_keep_worktree_flag(tmp_path):
    """Verify CLI --keep-worktree flag works."""
    repo_root = _create_test_repo(tmp_path)
    packet_file = _create_test_packet(tmp_path)
    worktree_root = tmp_path / "worktrees"

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-managed-packet",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--packet-id", "TEST-W01-PACKET",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--dry-run",
            "--keep-worktree",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True

    # Verify worktree still exists
    worktree_path = Path(output["result"]["worktree_path"])
    assert worktree_path.exists()


def test_cli_run_managed_packet_timeout_seconds_flag(tmp_path):
    """Verify CLI --timeout-seconds flag works."""
    repo_root = _create_test_repo(tmp_path)
    packet_file = _create_test_packet(tmp_path)
    worktree_root = tmp_path / "worktrees"

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-managed-packet",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--packet-id", "TEST-W01-PACKET",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--dry-run",
            "--timeout-seconds", "7200",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True


def test_cli_run_managed_packet_help():
    """Verify CLI help works."""
    result = subprocess.run(
        ["python3", "-m", "prefect_grace.cli", "run-managed-packet", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "run-managed-packet" in result.stdout
    assert "--packet" in result.stdout
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--base-ref" in result.stdout
    assert "--dry-run" in result.stdout
    assert "--execute-agent" in result.stdout
    assert "--timeout-seconds" in result.stdout
    assert "--keep-worktree" in result.stdout
    assert "--json" in result.stdout


def test_cli_run_managed_packet_execute_agent_with_no_dry_run(tmp_path):
    """Verify CLI accepts --execute-agent with explicit --no-dry-run."""
    repo_root = _create_test_repo(tmp_path)
    packet_file = _create_test_packet(tmp_path)
    worktree_root = tmp_path / "worktrees"

    # This should not be rejected for safety (though it may fail for other reasons)
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-managed-packet",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--packet-id", "TEST-W01-PACKET",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--execute-agent",
            "--no-dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Should not be rejected for safety reasons
    output = json.loads(result.stdout)
    if not output["ok"]:
        # If it failed, it should not be due to safety checks
        if "errors" in output and len(output["errors"]) > 0:
            assert output["errors"][0]["code"] not in ["UNSAFE_FLAG_COMBINATION", "MISSING_EXPLICIT_NO_DRY_RUN"]


def test_cli_run_managed_packet_default_is_dry_run(tmp_path):
    """Verify CLI defaults to dry_run=True when no flags provided."""
    repo_root = _create_test_repo(tmp_path)
    packet_file = _create_test_packet(tmp_path)
    worktree_root = tmp_path / "worktrees"

    # Run without --dry-run or --no-dry-run flags
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "run-managed-packet",
            "--packet", str(packet_file),
            "--repo-root", str(repo_root),
            "--worktree-root", str(worktree_root),
            "--project-key", "test-project",
            "--packet-id", "TEST-W01-PACKET",
            "--attempt", "1",
            "--base-ref", "HEAD",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True

    # Verify dry_run was True (agent_result should indicate dry run)
    assert "data" in output
    assert "agent_result" in output["data"]
    assert output["data"]["agent_result"]["dry_run"] is True
