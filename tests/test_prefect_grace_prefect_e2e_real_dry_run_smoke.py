"""Tests for the Prefect real E2E dry-run smoke harness."""

from pathlib import Path

from prefect_grace.platform.prefect_e2e_real_dry_run_smoke import (
    SMOKE_PACKET_ID,
    run_prefect_e2e_real_dry_run_smoke,
)
from prefect_grace.platform.state_store import PacketRegistryStore
from prefect_grace.tasks.prefect_submitter import E2E_PACKET_DEPLOYMENT_NAME


def _write_project_config(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    config_path = tmp_path / "project.yaml"
    config_path.write_text(f"""
version: 1
project_key: test-project
repo_root: {repo_root}
default_branch: main
grace_dir: grace
packets_dir: packets
runtime_state_root: {tmp_path / "project-state"}
artifact_root: {tmp_path / "artifacts"}
worktree_root: {tmp_path / "project-worktrees"}
workflow_runtime: prefect
prefect:
  work_pool: test-pool
  live_queue: test-live
  monitoring_queue: test-monitoring
agent_executor:
  default: codex-cli
  command: codex1
""")
    return config_path


def test_run_prefect_e2e_real_dry_run_smoke_no_wait_submits_one_packet(tmp_path):
    """Verify smoke builds exactly one scratch packet and submits it via real submitter hook."""
    calls = []

    def fake_submitter(**kwargs):
        calls.append(kwargs)
        packet_id = kwargs["parameters"]["packet_id"]
        return {
            "flow_run_id": "flow-run-real-smoke",
            "flow_run_name": f"e2e-packet:{packet_id}:attempt-1",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "test-live",
            "url": "http://prefect.local/flow-runs/flow-run-real-smoke",
        }

    result = run_prefect_e2e_real_dry_run_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        wait=False,
        submitter=fake_submitter,
        status_reader=lambda flow_run_id: {"error": "status-reader should not be called"},
    )

    assert result.ok is True
    assert result.submitted is True
    assert result.waited is False
    assert result.packet_id == SMOKE_PACKET_ID
    assert result.flow_run_id == "flow-run-real-smoke"
    assert result.deployment_name == E2E_PACKET_DEPLOYMENT_NAME
    assert result.work_queue_name == "test-live"
    assert len(calls) == 1
    call = calls[0]
    assert call["parameters"]["packet_id"] == SMOKE_PACKET_ID
    assert call["parameters"]["dry_run"] is True
    assert call["parameters"]["execute_agent"] is False
    assert call["parameters"]["worktree_root"] == str(tmp_path / "worktrees")
    assert call["parameters"]["packet_path"].endswith("EXECUTION_PACKET.md")
    assert call["idempotency_key"].startswith("grace-packet:test-project:")

    registry = PacketRegistryStore(tmp_path / "state" / "state")
    packet = registry.load_packet(SMOKE_PACKET_ID)
    assert packet["registry_status"] == "submitted"
    assert packet["prefect_deployment_name"] == E2E_PACKET_DEPLOYMENT_NAME
    assert packet["submission_runner_kind"] == "e2e"

    packet_file = tmp_path / "packets" / "FEAT-GRACE-PREFECT-REAL-E2E-DRY-RUN-SMOKE-MVP" / "EXECUTION_PACKET.md"
    content = packet_file.read_text()
    assert "scratch/grace-real-e2e-smoke/**" in content


def test_run_prefect_e2e_real_dry_run_smoke_rejects_execute_agent(tmp_path):
    """Verify live-agent execution is rejected before submission."""
    calls = []

    result = run_prefect_e2e_real_dry_run_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        execute_agent=True,
        submitter=lambda **kwargs: calls.append(kwargs) or {"flow_run_id": "should-not-run"},
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "REAL_DRY_RUN_EXECUTE_AGENT_REJECTED"
    assert calls == []


def test_run_prefect_e2e_real_dry_run_smoke_refuses_extra_ready_packets(tmp_path):
    """Verify smoke refuses to submit if another ready packet is already present."""
    config_path = _write_project_config(tmp_path)
    state_root = tmp_path / "state"
    registry = PacketRegistryStore(state_root / "state")
    registry.upsert_packet({
        "packet_id": "OTHER-W01-PACKET",
        "project_key": "test-project",
        "feature_id": "OTHER",
        "wave_id": "W01",
        "title": "Other Packet",
        "path": "other.md",
        "source_hash": "sha256:other",
        "registry_status": "ready",
        "depends_on": [],
    })

    result = run_prefect_e2e_real_dry_run_smoke(
        project_config=config_path,
        state_root=state_root,
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        submitter=lambda **kwargs: {"flow_run_id": "should-not-run"},
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "REAL_DRY_RUN_PACKET_COUNT_INVALID"


def test_run_prefect_e2e_real_dry_run_smoke_rejects_unexpected_deployment(tmp_path):
    """Verify unexpected deployment name is rejected after submission."""
    result = run_prefect_e2e_real_dry_run_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        wait=False,
        submitter=lambda **kwargs: {
            "flow_run_id": "flow-run-real-smoke",
            "flow_run_name": "e2e-packet:bad:attempt-1",
            "deployment_name": "unexpected-deployment",
            "work_queue_name": "test-live",
        },
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "UNEXPECTED_E2E_DEPLOYMENT"


def test_run_prefect_e2e_real_dry_run_smoke_waits_for_completed_state(tmp_path):
    """Verify wait mode accepts completed state with accepted dry-run domain status."""
    result = run_prefect_e2e_real_dry_run_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        submitter=lambda **kwargs: {
            "flow_run_id": "flow-run-real-smoke",
            "flow_run_name": "e2e-packet:FEAT:attempt-1",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "test-live",
            "url": "http://prefect.local/flow-runs/flow-run-real-smoke",
        },
        status_reader=lambda flow_run_id: {
            "prefect_state_type": "completed",
            "prefect_state_name": "Completed",
            "domain_status": "accepted",
            "artifact_ids": ["artifact-1"],
        },
        sleep_fn=lambda seconds: None,
    )

    assert result.ok is True
    assert result.waited is True
    assert result.prefect_state_type == "completed"
    assert result.prefect_state_name == "Completed"
    assert result.domain_status == "accepted"
    assert result.artifact_ids == ["artifact-1"]


def test_run_prefect_e2e_real_dry_run_smoke_times_out(tmp_path):
    """Verify wait mode times out with a structured error."""
    result = run_prefect_e2e_real_dry_run_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        timeout_seconds=0,
        poll_interval_seconds=0,
        submitter=lambda **kwargs: {
            "flow_run_id": "flow-run-real-smoke",
            "flow_run_name": "e2e-packet:FEAT:attempt-1",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "test-live",
            "url": "http://prefect.local/flow-runs/flow-run-real-smoke",
        },
        status_reader=lambda flow_run_id: {
            "prefect_state_type": "running",
            "prefect_state_name": "Running",
            "domain_status": "unknown",
            "artifact_ids": [],
        },
        sleep_fn=lambda seconds: None,
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "PREFECT_DRY_RUN_TIMEOUT"
