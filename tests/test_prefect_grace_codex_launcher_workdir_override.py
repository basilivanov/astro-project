"""
Tests for codex_launcher workdir_override parameter.

Verifies that workdir_override wins over config and packet hints,
validates existence and directory status, and maintains backward compatibility.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from prefect_grace.tasks.codex_launcher import launch_codex_for_packet
from prefect_grace.platform.state_store import PacketRegistryStore


def test_workdir_override_used_in_dry_run(tmp_path, monkeypatch):
    """Verify workdir_override is used in command when provided."""
    # Setup state directory
    state_root = tmp_path / "prefect_grace" / "state"
    state_root.mkdir(parents=True)
    runs_dir = tmp_path / "prefect_grace" / "state" / "runs"
    runs_dir.mkdir(parents=True)
    packets_dir = tmp_path / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True)

    # Monkeypatch paths
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.RUNS_DIR", runs_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.FEATURES_DIR", packets_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.ROOT_DIR", tmp_path)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.STATE_ROOT", state_root)

    # Create packet
    packet_id = "TEST-WORKDIR-OVERRIDE-W01-PACKET"
    packet_file = packets_dir / "packet.md"
    packet_file.write_text("# Test Packet\n")

    registry = PacketRegistryStore(state_root)
    registry.upsert_packet({
        "packet_id": packet_id,
        "role": "coder",
        "packet_path": str(packet_file),
        "feature_id": "TEST-FEATURE",
        "wave_id": "W01",
        "packet_type": "execution",
    })

    # Mock find_record
    def mock_find_record(store, collection, key, value):
        if value == packet_id:
            return registry.load_packet(packet_id)
        raise KeyError(f"Not found: {value}")

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.find_record", mock_find_record)

    # Mock update_record
    def mock_update_record(store, collection, key, value, patch):
        pass

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.update_record", mock_update_record)

    # Mock agent config
    mock_config = {
        "codex": {
            "binary": "codex1",
            "shared_model": "gpt-5.4",
            "workdir": str(tmp_path),
            "roles": {
                "coder": {
                    "reasoning": "high",
                    "sandbox": "workspace-write",
                    "approval": "never",
                }
            }
        }
    }
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.load_agent_config", lambda: mock_config)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.role_prompt_for", lambda role: "Test prompt")
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.build_packet_prompt", lambda p, rp: "Test packet prompt")
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.resolve_execution_workdir", lambda w: str(tmp_path))

    # Create override workdir
    override_workdir = tmp_path / "override-workdir"
    override_workdir.mkdir()

    # Launch with workdir_override
    result = launch_codex_for_packet(
        packet_id,
        dry_run=True,
        workdir_override=override_workdir,
    )

    assert result["returncode"] == 0
    assert result["termination_reason"] == "dry_run"

    # Verify command uses override workdir
    command = result["command"]
    assert "-C" in command
    c_index = command.index("-C")
    assert command[c_index + 1] == str(override_workdir)


def _setup_test_packet(tmp_path, monkeypatch, packet_id, **packet_fields):
    """Helper to set up test packet with mocks."""
    state_root = tmp_path / "prefect_grace" / "state"
    state_root.mkdir(parents=True, exist_ok=True)
    runs_dir = tmp_path / "prefect_grace" / "state" / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    packets_dir = tmp_path / "prefect_grace" / "packets"
    packets_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.RUNS_DIR", runs_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.FEATURES_DIR", packets_dir)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.ROOT_DIR", tmp_path)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.STATE_ROOT", state_root)

    packet_file = packets_dir / "packet.md"
    packet_file.write_text("# Test Packet\n")

    registry = PacketRegistryStore(state_root)
    packet_data = {
        "packet_id": packet_id,
        "role": "coder",
        "packet_path": str(packet_file),
        "feature_id": "TEST-FEATURE",
        "wave_id": "W01",
        "packet_type": "execution",
        **packet_fields,
    }
    registry.upsert_packet(packet_data)

    def mock_find_record(store, collection, key, value):
        if value == packet_id:
            return registry.load_packet(packet_id)
        raise KeyError(f"Not found: {value}")

    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.find_record", mock_find_record)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.update_record", lambda *a, **k: None)

    mock_config = {
        "codex": {
            "binary": "codex1",
            "shared_model": "gpt-5.4",
            "workdir": str(tmp_path),
            "roles": {"coder": {"reasoning": "high", "sandbox": "workspace-write", "approval": "never"}}
        }
    }
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.load_agent_config", lambda: mock_config)
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.role_prompt_for", lambda role: "Test prompt")
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.build_packet_prompt", lambda p, rp: "Test packet prompt")
    monkeypatch.setattr("prefect_grace.tasks.codex_launcher.resolve_execution_workdir", lambda w: str(tmp_path))

    return state_root, runs_dir, packets_dir


def test_workdir_override_nonexistent_fails_closed(tmp_path, monkeypatch):
    """Verify nonexistent workdir_override fails closed."""
    packet_id = "TEST-WORKDIR-NONEXISTENT-W01-PACKET"
    _setup_test_packet(tmp_path, monkeypatch, packet_id)

    nonexistent = tmp_path / "does-not-exist"

    result = launch_codex_for_packet(
        packet_id,
        dry_run=True,
        workdir_override=nonexistent,
    )

    assert result["returncode"] == 1
    assert result["termination_reason"] == "workdir_override_not_found"
    assert result["thread_id"] == ""
    assert result["attempt"] == 0


def test_workdir_override_not_directory_fails_closed(tmp_path, monkeypatch):
    """Verify workdir_override that is not a directory fails closed."""
    packet_id = "TEST-WORKDIR-NOT-DIR-W01-PACKET"
    _setup_test_packet(tmp_path, monkeypatch, packet_id)

    not_a_dir = tmp_path / "file.txt"
    not_a_dir.write_text("not a directory")

    result = launch_codex_for_packet(
        packet_id,
        dry_run=True,
        workdir_override=not_a_dir,
    )

    assert result["returncode"] == 1
    assert result["termination_reason"] == "workdir_override_not_directory"
    assert result["thread_id"] == ""
    assert result["attempt"] == 0


def test_workdir_override_wins_over_packet_hints(tmp_path, monkeypatch):
    """Verify workdir_override wins over packet execution_hints.workdir."""
    packet_id = "TEST-WORKDIR-PRIORITY-W01-PACKET"

    hint_workdir = tmp_path / "hint-workdir"
    hint_workdir.mkdir()
    override_workdir = tmp_path / "override-workdir"
    override_workdir.mkdir()

    _setup_test_packet(tmp_path, monkeypatch, packet_id, execution_hints={"workdir": str(hint_workdir)})

    result = launch_codex_for_packet(
        packet_id,
        dry_run=True,
        workdir_override=override_workdir,
    )

    assert result["returncode"] == 0
    command = result["command"]
    c_index = command.index("-C")
    assert command[c_index + 1] == str(override_workdir)
    assert str(hint_workdir) not in command


def test_backward_compatibility_without_override(tmp_path, monkeypatch):
    """Verify existing callers without workdir_override behave as before."""
    packet_id = "TEST-BACKWARD-COMPAT-W01-PACKET"
    _setup_test_packet(tmp_path, monkeypatch, packet_id)

    result = launch_codex_for_packet(
        packet_id,
        dry_run=True,
    )

    assert result["returncode"] == 0
    assert result["termination_reason"] == "dry_run"
    command = result["command"]
    assert "-C" in command


def test_workdir_override_with_string_path(tmp_path, monkeypatch):
    """Verify workdir_override accepts string path."""
    packet_id = "TEST-WORKDIR-STRING-W01-PACKET"
    _setup_test_packet(tmp_path, monkeypatch, packet_id)

    override_workdir = tmp_path / "override-workdir"
    override_workdir.mkdir()

    result = launch_codex_for_packet(
        packet_id,
        dry_run=True,
        workdir_override=str(override_workdir),
    )

    assert result["returncode"] == 0
    command = result["command"]
    c_index = command.index("-C")
    assert command[c_index + 1] == str(override_workdir)


def test_workdir_override_resolves_relative_path(tmp_path, monkeypatch):
    """Verify workdir_override resolves relative paths."""
    packet_id = "TEST-WORKDIR-RELATIVE-W01-PACKET"
    _setup_test_packet(tmp_path, monkeypatch, packet_id)

    override_workdir = tmp_path / "override-workdir"
    override_workdir.mkdir()

    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = launch_codex_for_packet(
            packet_id,
            dry_run=True,
            workdir_override="override-workdir",
        )
    finally:
        os.chdir(original_cwd)

    assert result["returncode"] == 0
    command = result["command"]
    c_index = command.index("-C")
    assert Path(command[c_index + 1]).is_absolute()
