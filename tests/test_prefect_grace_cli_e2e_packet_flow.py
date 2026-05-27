"""Tests for CLI run-e2e-packet-flow command."""

import json
import subprocess


def _create_repo_and_packet(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)
    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    packet_dir = repo_root / "prefect_grace" / "packets" / "CLI-FLOW"
    packet_dir.mkdir(parents=True)
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("""# CLI Flow Packet

- packet_id: CLI-FLOW-W01-E2E
- feature_id: CLI-FLOW
- wave_id: W01
- status: ready

## Objective
Test CLI E2E packet flow wrapper.

## Allowed Write Scope
- src/**

## Frozen Scope
- backend/**

## Must Preserve
- No live agents

## Verification
Run tests.

## Expected Evidence
- Test output

## Escalation Triggers
- Live execution required
""")
    return repo_root, packet_file


def _base_cmd(repo_root, packet_file, tmp_path):
    return [
        "python3", "-m", "prefect_grace.cli", "run-e2e-packet-flow",
        "--project-root", str(repo_root),
        "--packet", str(packet_file),
        "--state-root", str(tmp_path / "state"),
        "--worktree-root", str(tmp_path / "worktrees"),
        "--project-key", "test",
        "--packet-id", "CLI-FLOW-W01-E2E",
        "--attempt", "1",
        "--base-ref", "HEAD",
    ]


def test_cli_run_e2e_packet_flow_help():
    """Verify run-e2e-packet-flow help includes required flags."""
    result = subprocess.run(
        ["python3", "-m", "prefect_grace.cli", "run-e2e-packet-flow", "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "run-e2e-packet-flow" in result.stdout
    assert "--project-root" in result.stdout
    assert "--packet-id" in result.stdout
    assert "--fake-verifier-output" in result.stdout
    assert "--fake-reviewer-output" in result.stdout
    assert "--json" in result.stdout


def test_cli_run_e2e_packet_flow_json_accepted(tmp_path):
    """Verify JSON output includes domain, registry, and artifact fields."""
    repo_root, packet_file = _create_repo_and_packet(tmp_path)

    result = subprocess.run(
        [*_base_cmd(repo_root, packet_file, tmp_path), "--dry-run", "--json"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    output = json.loads(result.stdout)
    assert output["ok"] is True
    assert output["command"] == "run-e2e-packet-flow"
    assert output["result"]["packet_id"] == "CLI-FLOW-W01-E2E"
    assert output["result"]["attempt"] == 1
    assert output["result"]["domain_status"] == "accepted"
    assert output["result"]["registry_status"] == "accepted"
    assert output["result"]["registry_reason"] == "execution_accepted"
    assert output["result"]["registry_transition"]["registry_status"] == "accepted"
    assert isinstance(output["result"]["artifact_ids"], list)


def test_cli_run_e2e_packet_flow_rework_exits_1(tmp_path):
    """Verify non-accepted domain outcome exits 1, not 2."""
    repo_root, packet_file = _create_repo_and_packet(tmp_path)
    reviewer_output = tmp_path / "reviewer.md"
    reviewer_output.write_text("""
FINAL_PACKET_DECISION_JSON
{
  "packet_verdict": "rework_required",
  "route_classification": "quality_rework",
  "rework_mode": "light_resume",
  "reasons": ["Needs adjustment"]
}
END_FINAL_PACKET_DECISION_JSON
""")

    result = subprocess.run(
        [
            *_base_cmd(repo_root, packet_file, tmp_path),
            "--fake-reviewer-output", str(reviewer_output),
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["result"]["domain_status"] == "rework_required"
    assert output["result"]["registry_status"] == "ready_for_retry"
    assert output["result"]["registry_reason"] == "quality_rework"


def test_cli_run_e2e_packet_flow_text_output(tmp_path):
    """Verify text output shows packet and registry details."""
    repo_root, packet_file = _create_repo_and_packet(tmp_path)

    result = subprocess.run(
        [*_base_cmd(repo_root, packet_file, tmp_path), "--dry-run"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "E2E packet flow: accepted" in result.stdout
    assert "Packet: CLI-FLOW-W01-E2E" in result.stdout
    assert "Registry status: accepted" in result.stdout
    assert "Registry reason: execution_accepted" in result.stdout
    assert "Artifacts:" in result.stdout


def test_cli_run_e2e_packet_flow_rejects_unsafe_execute_agent(tmp_path):
    """Verify live agent execution requires explicit --no-dry-run."""
    repo_root, packet_file = _create_repo_and_packet(tmp_path)

    result = subprocess.run(
        [*_base_cmd(repo_root, packet_file, tmp_path), "--execute-agent", "--json"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    output = json.loads(result.stdout)
    assert output["ok"] is False
    assert output["errors"][0]["code"] == "MISSING_EXPLICIT_NO_DRY_RUN"
