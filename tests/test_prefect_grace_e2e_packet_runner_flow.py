"""Tests for the E2E packet Prefect flow wrapper."""

import subprocess

import prefect_grace.flows.e2e_packet_runner_flow as e2e_flow
from prefect_grace.flows.e2e_packet_runner_flow import (
    e2e_packet_runner_flow,
    publish_e2e_packet_artifact_task,
    run_e2e_packet_task,
)


def _create_repo_and_packet(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_root, check=True)
    (repo_root / "README.md").write_text("base\n")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo_root, check=True)

    packet_dir = repo_root / "prefect_grace" / "packets" / "TEST"
    packet_dir.mkdir(parents=True)
    packet_file = packet_dir / "EXECUTION_PACKET.md"
    packet_file.write_text("""# Test Packet

- packet_id: TEST-W01-E2E-FLOW
- feature_id: TEST
- wave_id: W01
- status: ready

## Objective
Test E2E Prefect flow wrapper.

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


def test_run_e2e_packet_task_returns_registry_transition(tmp_path):
    """Verify task delegates to E2E runner and returns its transition fields."""
    repo_root, packet_file = _create_repo_and_packet(tmp_path)

    result = run_e2e_packet_task(
        project_root=str(repo_root),
        packet_path=str(packet_file),
        state_root=str(tmp_path / "state"),
        worktree_root=str(tmp_path / "worktrees"),
        project_key="test",
        packet_id="TEST-W01-E2E-FLOW",
        dry_run=True,
        execute_agent=False,
    )

    assert result["domain_status"] == "accepted"
    assert result["registry_status"] == "accepted"
    assert result["registry_reason"] == "execution_accepted"
    assert result["registry_transition"]["registry_status"] == "accepted"
    assert result["ok"] is True


def test_publish_e2e_packet_artifact_task_delegates(monkeypatch):
    """Verify artifact task returns publisher IDs without changing result data."""
    result = {"domain_status": "accepted", "registry_status": "accepted"}
    monkeypatch.setattr(
        e2e_flow,
        "publish_e2e_packet_run_artifact",
        lambda received: ["artifact-1"] if received is result else [],
    )

    assert publish_e2e_packet_artifact_task(result) == ["artifact-1"]


def test_e2e_packet_runner_flow_returns_artifact_ids(monkeypatch, tmp_path):
    """Verify flow adds best-effort artifact IDs to an accepted E2E result."""
    repo_root, packet_file = _create_repo_and_packet(tmp_path)
    monkeypatch.setattr(e2e_flow, "publish_e2e_packet_run_artifact", lambda result: ["artifact-flow-1"])

    result = e2e_packet_runner_flow(
        project_root=str(repo_root),
        packet_path=str(packet_file),
        state_root=str(tmp_path / "state"),
        worktree_root=str(tmp_path / "worktrees"),
        project_key="test",
        packet_id="TEST-W01-E2E-FLOW",
        dry_run=True,
        execute_agent=False,
    )

    assert result["ok"] is True
    assert result["domain_status"] == "accepted"
    assert result["registry_status"] == "accepted"
    assert result["artifact_ids"] == ["artifact-flow-1"]


def test_e2e_packet_runner_flow_preserves_rework_outcome(tmp_path):
    """Verify rework is returned as a deterministic domain result."""
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

    result = e2e_packet_runner_flow(
        project_root=str(repo_root),
        packet_path=str(packet_file),
        state_root=str(tmp_path / "state"),
        worktree_root=str(tmp_path / "worktrees"),
        project_key="test",
        packet_id="TEST-W01-E2E-FLOW",
        dry_run=True,
        execute_agent=False,
        fake_reviewer_output=str(reviewer_output),
    )

    assert result["ok"] is False
    assert result["domain_status"] == "rework_required"
    assert result["registry_status"] == "ready_for_retry"
    assert result["registry_reason"] == "quality_rework"
    assert isinstance(result["artifact_ids"], list)
