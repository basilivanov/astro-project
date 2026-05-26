"""
Tests for CLI submit-packets command with native submission.

Verifies CLI interface for packet submission to Prefect.
"""

import json
import subprocess
import tempfile
from pathlib import Path


def _create_test_project(tmp_path):
    """Create minimal project structure."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    # Create runtime state directory
    runtime_state_root = tmp_path / "runtime_state"
    runtime_state_root.mkdir()
    state_dir = runtime_state_root / "state"
    state_dir.mkdir()

    # Create project.yaml with absolute path
    project_yaml = repo_root / "grace" / "project.yaml"
    project_yaml.parent.mkdir(parents=True, exist_ok=True)
    project_yaml.write_text(f"""
project_key: test-project
repo_root: .
runtime_state_root: {runtime_state_root}
packets_dir: packets
""")

    return repo_root, runtime_state_root


def _create_registry_with_ready_packet(state_dir, packet_id):
    """Create registry with ready packet."""
    from prefect_grace.platform.state_store import PacketRegistryStore

    registry = PacketRegistryStore(state_dir)
    registry.upsert_packet({
        "packet_id": packet_id,
        "project_key": "test-project",
        "feature_id": "TEST-FEATURE",
        "wave_id": "W01",
        "title": "Test Packet",
        "path": f"packets/{packet_id}.md",
        "source_hash": "abc123",
        "registry_status": "ready",
        "registry_reason": "test",
        "depends_on": [],
    })


def test_cli_submit_packets_dry_run_json_exits_0(tmp_path):
    """Verify CLI dry run with JSON output exits 0."""
    repo_root, runtime_state_root = _create_test_project(tmp_path)
    state_dir = runtime_state_root / "state"

    _create_registry_with_ready_packet(state_dir, "TEST-W01-PACKET")

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "submit-packets",
            "--project", str(repo_root / "grace" / "project.yaml"),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "submit-packets"
    assert output["result"]["dry_run"] is True
    assert len(output["result"]["submission_order"]) == 1


def test_cli_submit_packets_dry_run_text_exits_0(tmp_path):
    """Verify CLI dry run with text output exits 0."""
    repo_root, runtime_state_root = _create_test_project(tmp_path)
    state_dir = runtime_state_root / "state"

    _create_registry_with_ready_packet(state_dir, "TEST-W01-PACKET")

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "submit-packets",
            "--project", str(repo_root / "grace" / "project.yaml"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Submission plan for test-project" in result.stdout
    assert "Packets to submit: 1" in result.stdout


def test_cli_submit_packets_execute_requires_submitter(tmp_path):
    """Verify CLI execute mode requires submitter (offline test uses fake)."""
    repo_root, runtime_state_root = _create_test_project(tmp_path)
    state_dir = runtime_state_root / "state"

    _create_registry_with_ready_packet(state_dir, "TEST-W01-PACKET")

    # Create packet file
    packet_file = repo_root / "packets" / "TEST-W01-PACKET.md"
    packet_file.parent.mkdir(parents=True, exist_ok=True)
    packet_file.write_text("""# Test Packet

- packet_id: TEST-W01-PACKET
- feature_id: TEST-FEATURE
- wave_id: W01
- status: ready

## Objective
Test packet.

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

    # Execute mode without real Prefect will fail with NO_SUBMITTER_PROVIDED
    # This is expected behavior for offline tests
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "submit-packets",
            "--project", str(repo_root / "grace" / "project.yaml"),
            "--execute",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    # Should exit with error code 3 (submission error)
    assert result.returncode == 3
    output = json.loads(result.stdout)
    assert output["ok"] is False
    # Error could be NO_SUBMITTER_PROVIDED or Prefect unavailable
    assert len(output["result"]["errors"]) > 0


def test_cli_submit_packets_no_ready_packets_exits_0(tmp_path):
    """Verify CLI with no ready packets exits 0 with empty plan."""
    repo_root, runtime_state_root = _create_test_project(tmp_path)

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "submit-packets",
            "--project", str(repo_root / "grace" / "project.yaml"),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert len(output["result"]["submission_order"]) == 0


def test_cli_submit_packets_help():
    """Verify CLI help works."""
    result = subprocess.run(
        ["python3", "-m", "prefect_grace.cli", "submit-packets", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "submit-packets" in result.stdout
    assert "--project" in result.stdout
    assert "--execute" in result.stdout
    assert "--json" in result.stdout
