"""Tests for the Prefect E2E live smoke harness."""

from pathlib import Path

from prefect_grace.platform.prefect_e2e_live_smoke import (
    SMOKE_PACKET_ID,
    run_prefect_e2e_live_smoke,
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


def test_run_prefect_e2e_live_smoke_submits_one_e2e_packet(tmp_path):
    """Verify smoke creates one strict packet and submits it through E2E native submission."""
    config_path = _write_project_config(tmp_path)
    state_root = tmp_path / "state"
    worktree_root = tmp_path / "worktrees"
    packet_root = tmp_path / "packets"
    calls = []

    def fake_submitter(**kwargs):
        calls.append(kwargs)
        packet_id = kwargs["parameters"]["packet_id"]
        return {
            "flow_run_id": "flow-run-smoke",
            "flow_run_name": f"e2e-packet:{packet_id}:attempt-1",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "test-live",
            "url": "http://prefect.local/flow-runs/flow-run-smoke",
        }

    result = run_prefect_e2e_live_smoke(
        project_config=config_path,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=True,
        execute_agent=False,
        submitter=fake_submitter,
    )

    assert result.ok is True
    assert result.submitted is True
    assert result.status == "submitted"
    assert result.packet_id == SMOKE_PACKET_ID
    assert result.flow_run_id == "flow-run-smoke"
    assert result.deployment_name == E2E_PACKET_DEPLOYMENT_NAME
    assert result.runner_kind == "e2e"
    assert len(calls) == 1
    call = calls[0]
    assert call["parameters"]["packet_id"] == SMOKE_PACKET_ID
    assert call["parameters"]["dry_run"] is True
    assert call["parameters"]["execute_agent"] is False
    assert call["parameters"]["worktree_root"] == str(worktree_root)
    assert call["parameters"]["packet_path"].endswith("EXECUTION_PACKET.md")
    assert call["idempotency_key"].startswith("grace-packet:test-project:")
    assert "e2e" in call["tags"]

    registry = PacketRegistryStore(state_root / "state")
    packet = registry.load_packet(SMOKE_PACKET_ID)
    assert packet["registry_status"] == "submitted"
    assert packet["prefect_deployment_name"] == E2E_PACKET_DEPLOYMENT_NAME
    assert packet["submission_runner_kind"] == "e2e"


def test_run_prefect_e2e_live_smoke_blocks_unsafe_live_agent(tmp_path):
    """Verify live-agent smoke requires explicit guards."""
    result = run_prefect_e2e_live_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        dry_run=False,
        execute_agent=True,
        allow_live_agent_smoke=True,
        submitter=lambda **kwargs: {"flow_run_id": "should-not-run"},
    )

    assert result.ok is False
    assert result.submitted is False
    assert result.status == "blocked"
    assert result.errors[0]["code"] == "LIVE_AGENT_SMOKE_GUARD_FAILED"


def test_run_prefect_e2e_live_smoke_allows_guarded_live_agent(monkeypatch, tmp_path):
    """Verify all live-agent guards allow one fake-submitted packet."""
    monkeypatch.setenv("GRACE_ALLOW_LIVE_AGENT_SMOKE", "1")
    calls = []

    def fake_submitter(**kwargs):
        calls.append(kwargs)
        return {
            "flow_run_id": "flow-run-live-agent",
            "flow_run_name": f"e2e-packet:{kwargs['parameters']['packet_id']}:attempt-1",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "work_queue_name": "test-live",
        }

    result = run_prefect_e2e_live_smoke(
        project_config=_write_project_config(tmp_path),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        dry_run=False,
        execute_agent=True,
        allow_live_agent_smoke=True,
        limit=1,
        submitter=fake_submitter,
    )

    assert result.ok is True
    assert calls[0]["parameters"]["dry_run"] is False
    assert calls[0]["parameters"]["execute_agent"] is True


def test_run_prefect_e2e_live_smoke_refuses_multiple_ready_packets(tmp_path):
    """Verify smoke refuses to submit if registry would submit more than one packet."""
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

    result = run_prefect_e2e_live_smoke(
        project_config=config_path,
        state_root=state_root,
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packets",
        submitter=lambda **kwargs: {"flow_run_id": "should-not-run"},
    )

    assert result.ok is False
    assert result.submitted is False
    assert result.errors[0]["code"] == "LIVE_SMOKE_PACKET_COUNT_INVALID"
