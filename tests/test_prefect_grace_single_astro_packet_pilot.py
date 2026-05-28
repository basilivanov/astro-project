"""Tests for single_astro_packet_pilot module."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from prefect_grace.platform.single_astro_packet_pilot import (
    run_single_astro_packet_pilot,
    _is_low_risk_candidate,
)


@dataclass
class FakeSubmitResult:
    """Fake submission result."""
    ok: bool
    records: list[dict]


def test_is_low_risk_candidate_accepts_narrow_scope():
    """Low-risk check accepts packet with narrow scope."""
    packet = {
        "packet_id": "TEST-PACKET-001",
        "status": "ready",
        "allowed_write_scope": [
            "/opt/astro-project/backend/utils/helper.py",
            "/opt/astro-project/tests/test_helper.py",
        ],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is True
    assert reason is None


def test_is_low_risk_candidate_rejects_not_ready():
    """Low-risk check rejects packet not in ready status."""
    packet = {
        "packet_id": "TEST-PACKET-002",
        "status": "blocked",
        "allowed_write_scope": ["/opt/astro-project/backend/utils/helper.py"],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "not ready" in reason


def test_is_low_risk_candidate_rejects_no_scope():
    """Low-risk check rejects packet with no allowed scope."""
    packet = {
        "packet_id": "TEST-PACKET-003",
        "status": "ready",
        "allowed_write_scope": [],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "no allowed_write_scope" in reason


def test_is_low_risk_candidate_rejects_broad_scope():
    """Low-risk check rejects packet with too many paths."""
    packet = {
        "packet_id": "TEST-PACKET-004",
        "status": "ready",
        "allowed_write_scope": [f"/opt/astro-project/backend/file{i}.py" for i in range(25)],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "broad scope" in reason


def test_is_low_risk_candidate_rejects_backend_wildcard():
    """Low-risk check rejects packet with backend/** scope."""
    packet = {
        "packet_id": "TEST-PACKET-005",
        "status": "ready",
        "allowed_write_scope": ["/opt/astro-project/backend/**"],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "broad backend scope" in reason


def test_is_low_risk_candidate_rejects_frontend_wildcard():
    """Low-risk check rejects packet with frontend/** scope."""
    packet = {
        "packet_id": "TEST-PACKET-006",
        "status": "ready",
        "allowed_write_scope": ["/opt/astro-project/frontend/**"],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "broad frontend scope" in reason


def test_is_low_risk_candidate_rejects_pipeline_modification():
    """Low-risk check rejects packet modifying pipeline.py."""
    packet = {
        "packet_id": "TEST-PACKET-007",
        "status": "ready",
        "allowed_write_scope": ["/opt/astro-project/scripts/pipeline.py"],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "pipeline.py" in reason


def test_is_low_risk_candidate_rejects_docker_compose():
    """Low-risk check rejects packet modifying docker-compose."""
    packet = {
        "packet_id": "TEST-PACKET-008",
        "status": "ready",
        "allowed_write_scope": ["/opt/astro-project/docker-compose.yml"],
    }
    is_low_risk, reason = _is_low_risk_candidate(packet)
    assert is_low_risk is False
    assert "Docker compose" in reason


def test_dry_run_selects_low_risk_packet(tmp_path):
    """Dry-run selects first low-risk ready packet."""
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text("project_key: test-project\npackets_dir: packets\n")

    state_root = tmp_path / "state"
    worktree_root = tmp_path / "worktrees"
    packet_root = tmp_path / "packets"

    state_root.mkdir()
    worktree_root.mkdir()
    packet_root.mkdir()

    # Mock registry with one low-risk packet
    def fake_load_registry_map(adapter):
        return {
            "LOW-RISK-PACKET-001": {
                "packet_id": "LOW-RISK-PACKET-001",
                "status": "ready",
                "allowed_write_scope": ["/opt/astro-project/backend/utils/helper.py"],
            },
        }

    # Mock submitter
    def fake_submitter(project_key, packet_ids, dry_run):
        return FakeSubmitResult(
            ok=True,
            records=[{"flow_run_id": None, "flow_run_name": None, "url": None, "status": "dry_run"}],
        )

    # Patch imports
    import prefect_grace.platform.single_astro_packet_pilot as module
    original_load = module._load_registry_map
    module._load_registry_map = fake_load_registry_map

    try:
        result = run_single_astro_packet_pilot(
            project_path=project_yaml,
            state_root=state_root,
            worktree_root=worktree_root,
            packet_root=packet_root,
            dry_run=True,
            submitter=fake_submitter,
        )

        assert result.ok is True
        assert result.selected_packet_id == "LOW-RISK-PACKET-001"
        assert result.prefect_runs_created == 0
        assert result.live_agents_started == 0
    finally:
        module._load_registry_map = original_load


def test_missing_approval_blocks_execution(tmp_path):
    """Missing approval blocks live execution."""
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text("project_key: test-project\npackets_dir: packets\n")

    state_root = tmp_path / "state"
    worktree_root = tmp_path / "worktrees"
    packet_root = tmp_path / "packets"

    state_root.mkdir()
    worktree_root.mkdir()
    packet_root.mkdir()

    result = run_single_astro_packet_pilot(
        project_path=project_yaml,
        state_root=state_root,
        worktree_root=worktree_root,
        packet_root=packet_root,
        dry_run=False,
        execute_agent=True,
        acknowledge_live_agent=False,  # Missing acknowledgment
    )

    assert result.ok is False
    assert result.opt_in_confirmed is False
    assert result.prefect_runs_created == 0
    assert result.live_agents_started == 0
    assert any(e["code"] == "LIVE_AGENT_NOT_ACKNOWLEDGED" for e in result.errors)


def test_explicit_packet_not_found(tmp_path):
    """Explicit packet ID not in registry returns error."""
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text("project_key: test-project\npackets_dir: packets\n")

    state_root = tmp_path / "state"
    worktree_root = tmp_path / "worktrees"
    packet_root = tmp_path / "packets"

    state_root.mkdir()
    worktree_root.mkdir()
    packet_root.mkdir()

    # Mock empty registry
    def fake_load_registry_map(adapter):
        return {}

    import prefect_grace.platform.single_astro_packet_pilot as module
    original_load = module._load_registry_map
    module._load_registry_map = fake_load_registry_map

    try:
        result = run_single_astro_packet_pilot(
            project_path=project_yaml,
            state_root=state_root,
            worktree_root=worktree_root,
            packet_root=packet_root,
            dry_run=True,
            packet_id="MISSING-PACKET",
        )

        assert result.ok is False
        assert result.selected_packet_id == "MISSING-PACKET"
        assert any(e["code"] == "PACKET_NOT_FOUND" for e in result.errors)
    finally:
        module._load_registry_map = original_load


def test_explicit_packet_not_low_risk(tmp_path):
    """Explicit packet ID that is not low-risk returns error."""
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text("project_key: test-project\npackets_dir: packets\n")

    state_root = tmp_path / "state"
    worktree_root = tmp_path / "worktrees"
    packet_root = tmp_path / "packets"

    state_root.mkdir()
    worktree_root.mkdir()
    packet_root.mkdir()

    # Mock registry with high-risk packet
    def fake_load_registry_map(adapter):
        return {
            "HIGH-RISK-PACKET": {
                "packet_id": "HIGH-RISK-PACKET",
                "status": "ready",
                "allowed_write_scope": ["/opt/astro-project/backend/**"],
            },
        }

    import prefect_grace.platform.single_astro_packet_pilot as module
    original_load = module._load_registry_map
    module._load_registry_map = fake_load_registry_map

    try:
        result = run_single_astro_packet_pilot(
            project_path=project_yaml,
            state_root=state_root,
            worktree_root=worktree_root,
            packet_root=packet_root,
            dry_run=True,
            packet_id="HIGH-RISK-PACKET",
        )

        assert result.ok is False
        assert result.selected_packet_id == "HIGH-RISK-PACKET"
        assert any(e["code"] == "PACKET_NOT_LOW_RISK" for e in result.errors)
    finally:
        module._load_registry_map = original_load


def test_no_low_risk_candidates(tmp_path):
    """No low-risk candidates returns error."""
    project_yaml = tmp_path / "project.yaml"
    project_yaml.write_text("project_key: test-project\npackets_dir: packets\n")

    state_root = tmp_path / "state"
    worktree_root = tmp_path / "worktrees"
    packet_root = tmp_path / "packets"

    state_root.mkdir()
    worktree_root.mkdir()
    packet_root.mkdir()

    # Mock registry with only high-risk packets
    def fake_load_registry_map(adapter):
        return {
            "HIGH-RISK-1": {
                "packet_id": "HIGH-RISK-1",
                "status": "ready",
                "allowed_write_scope": ["/opt/astro-project/backend/**"],
            },
            "HIGH-RISK-2": {
                "packet_id": "HIGH-RISK-2",
                "status": "blocked",
                "allowed_write_scope": ["/opt/astro-project/backend/utils/helper.py"],
            },
        }

    import prefect_grace.platform.single_astro_packet_pilot as module
    original_load = module._load_registry_map
    module._load_registry_map = fake_load_registry_map

    try:
        result = run_single_astro_packet_pilot(
            project_path=project_yaml,
            state_root=state_root,
            worktree_root=worktree_root,
            packet_root=packet_root,
            dry_run=True,
        )

        assert result.ok is False
        assert result.selected_packet_id is None
        assert any(e["code"] == "NO_LOW_RISK_CANDIDATE" for e in result.errors)
    finally:
        module._load_registry_map = original_load
