"""CLI integration tests for check-scope command."""

import json
import subprocess
from pathlib import Path

import pytest


def test_cli_json_success_exits_0(tmp_path):
    """Test CLI with valid scope exits 0 in JSON mode."""
    # Create test packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""
# Test Packet

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**
""")

    # Run CLI
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "check-scope",
            "--packet", str(packet_file),
            "--changed-file", "prefect_grace/platform/scope_guard.py",
            "--repo-root", str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["result"]["ok"] is True
    assert len(output["result"]["frozen_violations"]) == 0
    assert len(output["result"]["outside_allowed"]) == 0


def test_cli_json_frozen_violation_exits_1(tmp_path):
    """Test CLI with frozen violation exits 1 in JSON mode."""
    # Create test packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""
# Test Packet

## Allowed Write Scope
- prefect_grace/platform/**
- backend/**

## Frozen Scope
- prefect_grace/platform/state_store.py
""")

    # Run CLI
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "check-scope",
            "--packet", str(packet_file),
            "--changed-file", "prefect_grace/platform/state_store.py",
            "--repo-root", str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["result"]["ok"] is False
    assert len(output["result"]["frozen_violations"]) == 1
    assert output["result"]["frozen_violations"][0]["file_path"] == "prefect_grace/platform/state_store.py"


def test_cli_json_outside_allowed_exits_1(tmp_path):
    """Test CLI with file outside allowed scope exits 1."""
    # Create test packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""
# Test Packet

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**
""")

    # Run CLI
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "check-scope",
            "--packet", str(packet_file),
            "--changed-file", "scripts/deploy.sh",
            "--repo-root", str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert len(output["result"]["outside_allowed"]) == 1


def test_cli_text_mode_prints_summary(tmp_path):
    """Test CLI text mode prints readable summary."""
    # Create test packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""
# Test Packet

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**
""")

    # Run CLI - success case
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "check-scope",
            "--packet", str(packet_file),
            "--changed-file", "prefect_grace/platform/scope_guard.py",
            "--repo-root", str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Scope check: OK" in result.stdout
    assert "Changed:" in result.stdout
    assert "Allowed:" in result.stdout


def test_cli_text_mode_violation(tmp_path):
    """Test CLI text mode prints violations."""
    # Create test packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""
# Test Packet

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**
""")

    # Run CLI - frozen violation
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "check-scope",
            "--packet", str(packet_file),
            "--changed-file", "backend/app/main.py",
            "--repo-root", str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "Scope check: FAILED" in result.stdout
    assert "Frozen violations:" in result.stdout
    assert "backend/app/main.py" in result.stdout


def test_cli_missing_packet_exits_2(tmp_path):
    """Test CLI with missing packet exits 2."""
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "check-scope",
            "--packet", str(tmp_path / "nonexistent.md"),
            "--changed-file", "test.py",
            "--repo-root", str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert len(output["errors"]) > 0


def test_cli_no_changed_files_exits_2(tmp_path):
    """Test CLI with no changed files exits 2."""
    # Create test packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""
# Test Packet

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**
""")

    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "check-scope",
            "--packet", str(packet_file),
            "--repo-root", str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["ok"] is False


def test_cli_changed_files_file_input(tmp_path):
    """Test CLI with --changed-files-file option."""
    # Create test packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""
# Test Packet

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**
""")

    # Create changed files list
    changed_files_file = tmp_path / "changed_files.txt"
    changed_files_file.write_text(
        "prefect_grace/platform/scope_guard.py\n"
        "prefect_grace/platform/packet_parser.py\n"
    )

    # Run CLI
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "check-scope",
            "--packet", str(packet_file),
            "--changed-files-file", str(changed_files_file),
            "--repo-root", str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert len(output["result"]["changed_files"]) == 2


def test_cli_multiple_changed_files(tmp_path):
    """Test CLI with multiple --changed-file flags."""
    # Create test packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""
# Test Packet

## Allowed Write Scope
- prefect_grace/platform/**

## Frozen Scope
- backend/**
""")

    # Run CLI
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "check-scope",
            "--packet", str(packet_file),
            "--changed-file", "prefect_grace/platform/scope_guard.py",
            "--changed-file", "prefect_grace/platform/packet_parser.py",
            "--repo-root", str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert len(output["result"]["changed_files"]) == 2


def test_cli_repo_root_option(tmp_path):
    """Test CLI with custom --repo-root."""
    # Create test packet
    packet_file = tmp_path / "EXECUTION_PACKET.md"
    packet_file.write_text("""
# Test Packet

## Allowed Write Scope
- test/**

## Frozen Scope
- []
""")

    # Run CLI with custom repo root
    result = subprocess.run(
        [
            "python3", "-m", "prefect_grace.cli", "check-scope",
            "--packet", str(packet_file),
            "--changed-file", "test/file.py",
            "--repo-root", str(tmp_path),
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
