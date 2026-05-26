"""
Tests for executor registry CLI commands.

Validates list-executors and select-executor CLI output and exit codes.
"""

import json
import subprocess
import pytest
from pathlib import Path


def test_cli_list_executors_json(tmp_path):
    """Verify list-executors JSON output format."""
    # Create test project config
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    grace_dir = project_dir / "prefect_grace"
    grace_dir.mkdir()

    config_file = grace_dir / "project.yaml"
    config_file.write_text("""
version: 1
project:
  key: test-project
agent_executor:
  default: codex-cli
  command: codex1
""")

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "list-executors",
            "--project", str(project_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "list-executors"
    assert "executors" in output["result"]
    assert output["result"]["count"] == 1
    assert output["result"]["executors"][0]["executor_id"] == "codex-cli"


def test_cli_list_executors_text(tmp_path):
    """Verify list-executors text output format."""
    # Create test project config
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    grace_dir = project_dir / "prefect_grace"
    grace_dir.mkdir()

    config_file = grace_dir / "project.yaml"
    config_file.write_text("""
version: 1
project:
  key: test-project
agent_executor:
  default: codex-cli
  command: codex1
""")

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "list-executors",
            "--project", str(project_dir),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Executors: 1" in result.stdout
    assert "codex-cli" in result.stdout
    assert "codex" in result.stdout
    assert "enabled" in result.stdout


def test_cli_select_executor_json(tmp_path):
    """Verify select-executor JSON output format."""
    # Create test project config
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    grace_dir = project_dir / "prefect_grace"
    grace_dir.mkdir()

    config_file = grace_dir / "project.yaml"
    config_file.write_text("""
version: 1
project:
  key: test-project
runtime:
  state_root: %s
agent_executor:
  default: codex-cli
  command: codex1
""" % str(tmp_path / "state"))

    # Create state directory
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "select-executor",
            "--project", str(project_dir),
            "--packet-id", "TEST-PACKET",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "select-executor"
    assert output["result"]["ok"] is True
    assert output["result"]["packet_id"] == "TEST-PACKET"
    assert output["result"]["selected"]["executor_id"] == "codex-cli"


def test_cli_select_executor_text(tmp_path):
    """Verify select-executor text output format."""
    # Create test project config
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    grace_dir = project_dir / "prefect_grace"
    grace_dir.mkdir()

    config_file = grace_dir / "project.yaml"
    config_file.write_text("""
version: 1
project:
  key: test-project
runtime:
  state_root: %s
agent_executor:
  default: codex-cli
  command: codex1
""" % str(tmp_path / "state"))

    # Create state directory
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "select-executor",
            "--project", str(project_dir),
            "--packet-id", "TEST-PACKET",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Selected: codex-cli" in result.stdout
    assert "codex" in result.stdout


def test_cli_select_executor_exits_0_on_success(tmp_path):
    """Verify select-executor exits 0 on successful selection."""
    # Create test project config
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    grace_dir = project_dir / "prefect_grace"
    grace_dir.mkdir()

    config_file = grace_dir / "project.yaml"
    config_file.write_text("""
version: 1
project:
  key: test-project
runtime:
  state_root: %s
agent_executor:
  default: codex-cli
  command: codex1
""" % str(tmp_path / "state"))

    # Create state directory
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "select-executor",
            "--project", str(project_dir),
            "--packet-id", "TEST-PACKET",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0


def test_cli_select_executor_exits_1_on_failure(tmp_path):
    """Verify select-executor exits 1 when no executor available."""
    # Create test project config with role-incompatible executor
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()
    grace_dir = project_dir / "prefect_grace"
    grace_dir.mkdir()

    config_file = grace_dir / "project.yaml"
    config_file.write_text("""
version: 1
project:
  key: test-project
runtime:
  state_root: %s
agent_executor:
  default: codex-cli
  command: codex1
  executors:
    - executor_id: codex-reviewer
      kind: codex
      command: codex1
      enabled: true
      roles: [reviewer]
""" % str(tmp_path / "state"))

    # Create state directory
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    # Request coder role, but only reviewer available
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "select-executor",
            "--project", str(project_dir),
            "--packet-id", "TEST-PACKET",
            "--role", "coder",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["result"]["ok"] is False
