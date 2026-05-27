"""Tests for the Prefect E2E batch smoke harness."""

from pathlib import Path

from prefect_grace.platform.prefect_e2e_batch_smoke import (
    BATCH_SMOKE_FEATURE_ID,
    run_prefect_e2e_batch_smoke,
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


def test_run_prefect_e2e_batch_smoke_submits_two_e2e_packets(tmp_path):
    """Verify batch smoke submits two independent E2E records through native submission."""
    calls = []

    def fake_submitter(**kwargs):
        calls.append(kwargs)
        packet_id = kwargs["parameters"]["packet_id"]
        return {
            "flow_run_id": f"flow-run-{packet_id}",
            "flow_run_name": f"e2e-packet:{packet_id}:attempt-1",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "test-live",
            "url": f"http://prefect.local/flow-runs/{packet_id}",
        }

    result = run_prefect_e2e_batch_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        batch_size=2,
        submitter=fake_submitter,
    )

    assert result.ok is True
    assert result.mode == "prefect_agent_dry_run"
    assert result.batch_size == 2
    assert result.runner_kind == "e2e"
    assert result.deployment_name == E2E_PACKET_DEPLOYMENT_NAME
    assert result.work_queue_name == "test-live"
    assert len(result.packets_planned) == 2
    assert result.packets_submitted == result.packets_planned
    assert len(result.records) == 2
    assert len(calls) == 2
    assert [call["parameters"]["packet_id"] for call in calls] == result.packets_planned
    assert all(call["parameters"]["dry_run"] is True for call in calls)
    assert all(call["parameters"]["execute_agent"] is False for call in calls)
    assert all(call["parameters"]["worktree_root"] == str(tmp_path / "worktrees") for call in calls)
    assert all("e2e" in call["tags"] for call in calls)
    assert len({record["idempotency_key"] for record in result.records}) == 2
    assert all(record["deployment_name"] == E2E_PACKET_DEPLOYMENT_NAME for record in result.records)
    assert all(record["status"] == "submitted" for record in result.records)

    registry = PacketRegistryStore(tmp_path / "state" / "state")
    for packet_id in result.packets_submitted:
        packet = registry.load_packet(packet_id)
        assert packet["registry_status"] == "submitted"
        assert packet["prefect_deployment_name"] == E2E_PACKET_DEPLOYMENT_NAME
        assert packet["submission_runner_kind"] == "e2e"


def test_run_prefect_e2e_batch_smoke_accepts_three_packets(tmp_path):
    """Verify the upper bound of three packets is accepted."""
    result = run_prefect_e2e_batch_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        batch_size=3,
        submitter=lambda **kwargs: {
            "flow_run_id": f"flow-run-{kwargs['parameters']['packet_id']}",
            "flow_run_name": f"e2e-packet:{kwargs['parameters']['packet_id']}:attempt-1",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "test-live",
        },
    )

    assert result.ok is True
    assert result.batch_size == 3
    assert len(result.records) == 3
    assert result.packets_submitted == result.packets_planned


def test_run_prefect_e2e_batch_smoke_rejects_one_packet(tmp_path):
    """Verify operators are pointed back to single-packet smoke for batch_size=1."""
    calls = []

    result = run_prefect_e2e_batch_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        batch_size=1,
        submitter=lambda **kwargs: calls.append(kwargs) or {"flow_run_id": "should-not-run"},
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "BATCH_SMOKE_TOO_SMALL"
    assert "run-prefect-e2e-live-smoke" in result.errors[0]["message"]
    assert calls == []


def test_run_prefect_e2e_batch_smoke_rejects_more_than_three_packets(tmp_path):
    """Verify batch smoke fails closed above the maximum batch size."""
    result = run_prefect_e2e_batch_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        batch_size=4,
        submitter=lambda **kwargs: {"flow_run_id": "should-not-run"},
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "BATCH_SMOKE_TOO_LARGE"
    assert result.records == []


def test_run_prefect_e2e_batch_smoke_refuses_extra_ready_packets(tmp_path):
    """Verify smoke refuses to submit if registry contains an unexpected ready packet."""
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

    result = run_prefect_e2e_batch_smoke(
        project_config=config_path,
        state_root=state_root,
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        batch_size=2,
        submitter=lambda **kwargs: {"flow_run_id": "should-not-run"},
    )

    assert result.ok is False
    assert result.errors[0]["code"] == "BATCH_SMOKE_PACKET_SET_INVALID"
    assert BATCH_SMOKE_FEATURE_ID in result.errors[0]["message"]
