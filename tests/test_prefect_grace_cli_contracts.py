import json
import subprocess
import sys
from pathlib import Path


def test_cli_validate_project() -> None:
    res = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "validate-project", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())
    assert data["ok"] is True
    assert data["project_key"] == "astro-project"
    assert data["command"] == "validate-project"
    assert data["result"] == data["data"]
    assert "project" in data["data"]
    assert "verification_profiles" in data["data"]
    assert data["warnings"] == []
    assert data["errors"] == []


def test_cli_scan_packets() -> None:
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "scan-packets",
            "--mode",
            "legacy_warn",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())
    assert data["ok"] is True
    assert data["project_key"] == "astro-project"
    assert data["command"] == "scan-packets"
    assert data["result"] == data["data"]
    assert "packets" in data["data"]
    # Check that we scanned some packets (there are many in the directory)
    assert len(data["data"]["packets"]) > 0


def test_cli_validate_packet() -> None:
    packet_path = (
        Path(__file__).resolve().parents[1]
        / "prefect_grace"
        / "packets"
        / "FEAT-GRACE-ORCHESTRATOR-MVP1"
        / "EXECUTION_PACKET.md"
    )
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "validate-packet",
            str(packet_path),
            "--strict",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())
    assert data["ok"] is True
    assert data["command"] == "validate-packet"
    assert data["result"] == data["data"]
    assert data["data"]["packet_id"] == "FEAT-GRACE-ORCHESTRATOR-MVP1-W01-PROJECT-ADAPTER-CONTRACTS"
    assert data["data"]["feature_id"] == "FEAT-GRACE-ORCHESTRATOR-MVP1"
    assert data["data"]["wave_id"] == "W01"
    assert "allowed_write_scope" in data["data"]
    assert "frozen_scope" in data["data"]


def test_cli_sync_packets_dry_run() -> None:
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "sync-packets",
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(res.stdout.strip())
    assert data["ok"] is True
    assert data["project_key"] == "astro-project"
    assert data["command"] == "sync-packets"
    assert data["result"] == data["data"]
    assert data["data"]["dry_run"] is True
    assert data["data"]["registry_updates"] == 0
    assert data["data"]["packets_total"] > 0
    assert "ready" in data["data"]
    assert "accepted" in data["data"]
    assert "blocked" in data["data"]


def test_check_scope_cli_contract() -> None:
    """Verify check-scope CLI follows contract."""
    # Test that command exists and has required args
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "check-scope", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--packet" in result.stdout
    assert "--changed-file" in result.stdout
    assert "--json" in result.stdout
    assert "--repo-root" in result.stdout
    assert "--changed-files-file" in result.stdout


def test_worktree_create_cli_contract() -> None:
    """Verify worktree-create CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "worktree-create", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--base-ref" in result.stdout
    assert "--json" in result.stdout


def test_worktree_status_cli_contract() -> None:
    """Verify worktree-status CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "worktree-status", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--json" in result.stdout


def test_worktree_cleanup_cli_contract() -> None:
    """Verify worktree-cleanup CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "worktree-cleanup", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--keep-on-failure" in result.stdout
    assert "--json" in result.stdout


def test_worktree_scope_check_cli_contract() -> None:
    """Verify worktree-scope-check CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "worktree-scope-check", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--packet" in result.stdout
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--base-ref" in result.stdout
    assert "--keep-on-failure" in result.stdout
    assert "--json" in result.stdout


def test_run_worktree_scope_flow_cli_contract() -> None:
    """Verify run-worktree-scope-flow CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "run-worktree-scope-flow", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--packet" in result.stdout
    assert "--repo-root" in result.stdout
    assert "--worktree-root" in result.stdout
    assert "--project-key" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--attempt" in result.stdout
    assert "--base-ref" in result.stdout
    assert "--keep-on-failure" in result.stdout
    assert "--json" in result.stdout


def test_list_executors_cli_contract() -> None:
    """Verify list-executors CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "list-executors", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--json" in result.stdout


def test_select_executor_cli_contract() -> None:
    """Verify select-executor CLI follows contract."""
    result = subprocess.run(
        [sys.executable, "-m", "prefect_grace.cli", "select-executor", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "--project" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--role" in result.stdout
    assert "--requested-executor" in result.stdout
    assert "--json" in result.stdout
