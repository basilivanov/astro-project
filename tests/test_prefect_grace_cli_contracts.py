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
