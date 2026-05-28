"""
Unit tests for nightly batch selection platform module.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from prefect_grace.platform.nightly_batch_selection import (
    BatchSelectionResult,
    ExcludedPacket,
    select_safe_batch,
    _cost_exceeds_limit,
    _estimate_batch_cost,
    _topological_sort,
)
from prefect_grace.platform.nightly_preflight_risk_report import (
    PacketRiskFlags,
    PacketRiskSummary,
)
from prefect_grace.platform.status_model import RegistryStatus


def test_cost_exceeds_limit():
    """Test cost comparison logic."""
    assert not _cost_exceeds_limit("unit", "live_required")
    assert not _cost_exceeds_limit("targeted", "live_required")
    assert not _cost_exceeds_limit("backend_quick", "live_required")
    assert not _cost_exceeds_limit("live_required", "live_required")
    assert _cost_exceeds_limit("live_required", "backend_quick")
    assert _cost_exceeds_limit("docker_required", "targeted")
    assert _cost_exceeds_limit("unknown_cost", "live_required")


def test_estimate_batch_cost():
    """Test batch cost estimation."""
    assert _estimate_batch_cost([]) == "unknown"
    assert _estimate_batch_cost(["unit"]) == "unit"
    assert _estimate_batch_cost(["unit", "targeted"]) == "targeted"
    assert _estimate_batch_cost(["unit", "live_required", "targeted"]) == "live_required"
    assert _estimate_batch_cost(["backend_quick", "frontend_quick"]) == "frontend_quick"


def test_topological_sort_no_dependencies():
    """Test topological sort with no dependencies."""
    mock_registry = MagicMock()
    mock_registry.load_packet.return_value = {"depends_on": []}

    summaries = [
        PacketRiskSummary(
            packet_id="PKT-A",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
        ),
        PacketRiskSummary(
            packet_id="PKT-B",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
        ),
    ]

    result = _topological_sort(summaries, mock_registry)
    assert len(result) == 2
    assert set(result) == {"PKT-A", "PKT-B"}


def test_topological_sort_with_dependencies():
    """Test topological sort with dependencies."""
    mock_registry = MagicMock()

    def mock_load(packet_id):
        if packet_id == "PKT-A":
            return {"packet_id": "PKT-A", "depends_on": []}
        elif packet_id == "PKT-B":
            return {"packet_id": "PKT-B", "depends_on": ["PKT-A"]}
        elif packet_id == "PKT-C":
            return {"packet_id": "PKT-C", "depends_on": ["PKT-B"]}
        return None

    mock_registry.load_packet.side_effect = mock_load

    summaries = [
        PacketRiskSummary(
            packet_id="PKT-C",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
        ),
        PacketRiskSummary(
            packet_id="PKT-A",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
        ),
        PacketRiskSummary(
            packet_id="PKT-B",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
        ),
    ]

    result = _topological_sort(summaries, mock_registry)
    assert result == ["PKT-A", "PKT-B", "PKT-C"]


def test_select_safe_batch_project_load_failure():
    """Test batch selection with project load failure."""
    with patch("prefect_grace.platform.nightly_batch_selection.load_project_adapter") as mock_load:
        mock_load.side_effect = Exception("Project not found")

        result = select_safe_batch(project_config="/nonexistent/project.yaml")

        assert not result.ok
        assert result.project_key == ""
        assert len(result.errors) == 1
        assert result.errors[0]["code"] == "PROJECT_LOAD_FAILED"


def test_select_safe_batch_empty_candidates():
    """Test batch selection with no safe candidates."""
    with patch("prefect_grace.platform.nightly_batch_selection.load_project_adapter") as mock_load, \
         patch("prefect_grace.platform.nightly_batch_selection.generate_nightly_preflight_risk_report") as mock_preflight, \
         patch("prefect_grace.platform.nightly_batch_selection.PacketRegistryStore") as mock_registry_cls:

        mock_project = MagicMock()
        mock_project.project_key = "test-project"
        mock_project.repo_root = "/test/repo"
        mock_project.runtime_state_root = "/test/state"
        mock_load.return_value = mock_project

        mock_report = MagicMock()
        mock_report.ok = True
        mock_report.safe_candidates = []
        mock_report.risky_candidates = []
        mock_report.blocked_candidates = []
        mock_report.approval_required_candidates = []
        mock_report.packet_summaries = []
        mock_report.conflict_groups_total = 0
        mock_preflight.return_value = mock_report

        result = select_safe_batch(project_config="/test/project.yaml")

        assert result.ok
        assert result.project_key == "test-project"
        assert result.selected_total == 0
        assert result.stop_reason == "no_safe_candidates"


def test_select_safe_batch_dependency_ordering():
    """Test batch selection respects dependency ordering."""
    with patch("prefect_grace.platform.nightly_batch_selection.load_project_adapter") as mock_load, \
         patch("prefect_grace.platform.nightly_batch_selection.generate_nightly_preflight_risk_report") as mock_preflight, \
         patch("prefect_grace.platform.nightly_batch_selection.PacketRegistryStore") as mock_registry_cls:

        mock_project = MagicMock()
        mock_project.project_key = "test-project"
        mock_project.repo_root = "/test/repo"
        mock_project.runtime_state_root = "/test/state"
        mock_load.return_value = mock_project

        # Create mock registry
        mock_registry = MagicMock()

        def mock_load_packet(packet_id):
            if packet_id == "PKT-A":
                return {
                    "packet_id": "PKT-A",
                    "depends_on": [],
                    "registry_status": RegistryStatus.READY.value,
                }
            elif packet_id == "PKT-B":
                return {
                    "packet_id": "PKT-B",
                    "depends_on": ["PKT-A"],
                    "registry_status": RegistryStatus.READY.value,
                }
            return None

        mock_registry.load_packet.side_effect = mock_load_packet
        mock_registry_cls.return_value = mock_registry

        # Create summaries
        summary_a = PacketRiskSummary(
            packet_id="PKT-A",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
            allowed_write_scope=["/test/file_a.py"],
        )
        summary_b = PacketRiskSummary(
            packet_id="PKT-B",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
            allowed_write_scope=["/test/file_b.py"],
        )

        mock_report = MagicMock()
        mock_report.ok = True
        mock_report.safe_candidates = ["PKT-B", "PKT-A"]  # Intentionally reversed
        mock_report.risky_candidates = []
        mock_report.blocked_candidates = []
        mock_report.approval_required_candidates = []
        mock_report.packet_summaries = [summary_b, summary_a]
        mock_report.conflict_groups_total = 0
        mock_preflight.return_value = mock_report

        result = select_safe_batch(project_config="/test/project.yaml", max_packets=10)

        assert result.ok
        assert result.selected_total == 2
        # PKT-A should come before PKT-B due to dependency
        assert result.selected_packets == ["PKT-A", "PKT-B"]


def test_select_safe_batch_file_conflict_exclusion():
    """Test batch selection excludes packets with file conflicts."""
    with patch("prefect_grace.platform.nightly_batch_selection.load_project_adapter") as mock_load, \
         patch("prefect_grace.platform.nightly_batch_selection.generate_nightly_preflight_risk_report") as mock_preflight, \
         patch("prefect_grace.platform.nightly_batch_selection.PacketRegistryStore") as mock_registry_cls:

        mock_project = MagicMock()
        mock_project.project_key = "test-project"
        mock_project.repo_root = "/test/repo"
        mock_project.runtime_state_root = "/test/state"
        mock_load.return_value = mock_project

        mock_registry = MagicMock()
        mock_registry.load_packet.return_value = {
            "depends_on": [],
            "registry_status": RegistryStatus.READY.value,
        }
        mock_registry_cls.return_value = mock_registry

        # Create summaries with conflicting paths
        flags_conflict = PacketRiskFlags(file_conflict_candidate=True)
        summary_a = PacketRiskSummary(
            packet_id="PKT-A",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
            allowed_write_scope=["/test/shared.py"],
        )
        summary_b = PacketRiskSummary(
            packet_id="PKT-B",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=flags_conflict,
            cost_estimate="unit",
            allowed_write_scope=["/test/shared.py"],  # Conflicts with PKT-A
        )

        mock_report = MagicMock()
        mock_report.ok = True
        mock_report.safe_candidates = ["PKT-A", "PKT-B"]
        mock_report.risky_candidates = []
        mock_report.blocked_candidates = []
        mock_report.approval_required_candidates = []
        mock_report.packet_summaries = [summary_a, summary_b]
        mock_report.conflict_groups_total = 1
        mock_preflight.return_value = mock_report

        result = select_safe_batch(project_config="/test/project.yaml", allow_conflicts=False)

        assert result.ok
        assert result.selected_total == 1
        assert "PKT-A" in result.selected_packets
        assert "PKT-B" not in result.selected_packets
        # PKT-B should be excluded due to conflict
        excluded_ids = [e.packet_id for e in result.excluded_packets]
        assert "PKT-B" in excluded_ids
        excluded_b = next(e for e in result.excluded_packets if e.packet_id == "PKT-B")
        assert excluded_b.reason == "file_conflict"


def test_select_safe_batch_cost_exclusion():
    """Test batch selection excludes packets exceeding cost limit."""
    with patch("prefect_grace.platform.nightly_batch_selection.load_project_adapter") as mock_load, \
         patch("prefect_grace.platform.nightly_batch_selection.generate_nightly_preflight_risk_report") as mock_preflight, \
         patch("prefect_grace.platform.nightly_batch_selection.PacketRegistryStore") as mock_registry_cls:

        mock_project = MagicMock()
        mock_project.project_key = "test-project"
        mock_project.repo_root = "/test/repo"
        mock_project.runtime_state_root = "/test/state"
        mock_load.return_value = mock_project

        mock_registry = MagicMock()
        mock_registry.load_packet.return_value = {
            "depends_on": [],
            "registry_status": RegistryStatus.READY.value,
        }
        mock_registry_cls.return_value = mock_registry

        summary_cheap = PacketRiskSummary(
            packet_id="PKT-CHEAP",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="unit",
            allowed_write_scope=["/test/cheap.py"],
        )
        summary_expensive = PacketRiskSummary(
            packet_id="PKT-EXPENSIVE",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=PacketRiskFlags(),
            cost_estimate="live_required",
            allowed_write_scope=["/test/expensive.py"],
        )

        mock_report = MagicMock()
        mock_report.ok = True
        mock_report.safe_candidates = ["PKT-CHEAP", "PKT-EXPENSIVE"]
        mock_report.risky_candidates = []
        mock_report.blocked_candidates = []
        mock_report.approval_required_candidates = []
        mock_report.packet_summaries = [summary_cheap, summary_expensive]
        mock_report.conflict_groups_total = 0
        mock_preflight.return_value = mock_report

        result = select_safe_batch(
            project_config="/test/project.yaml",
            max_cost="backend_quick",
        )

        assert result.ok
        assert result.selected_total == 1
        assert "PKT-CHEAP" in result.selected_packets
        assert "PKT-EXPENSIVE" not in result.selected_packets
        excluded_ids = [e.packet_id for e in result.excluded_packets]
        assert "PKT-EXPENSIVE" in excluded_ids
        excluded_exp = next(e for e in result.excluded_packets if e.packet_id == "PKT-EXPENSIVE")
        assert excluded_exp.reason == "test_cost_too_high"


def test_select_safe_batch_max_packets_limit():
    """Test batch selection respects max packets limit."""
    with patch("prefect_grace.platform.nightly_batch_selection.load_project_adapter") as mock_load, \
         patch("prefect_grace.platform.nightly_batch_selection.generate_nightly_preflight_risk_report") as mock_preflight, \
         patch("prefect_grace.platform.nightly_batch_selection.PacketRegistryStore") as mock_registry_cls:

        mock_project = MagicMock()
        mock_project.project_key = "test-project"
        mock_project.repo_root = "/test/repo"
        mock_project.runtime_state_root = "/test/state"
        mock_load.return_value = mock_project

        mock_registry = MagicMock()
        mock_registry.load_packet.return_value = {
            "depends_on": [],
            "registry_status": RegistryStatus.READY.value,
        }
        mock_registry_cls.return_value = mock_registry

        # Create 5 safe candidates
        summaries = []
        safe_ids = []
        for i in range(5):
            pid = f"PKT-{i}"
            safe_ids.append(pid)
            summaries.append(PacketRiskSummary(
                packet_id=pid,
                registry_status=RegistryStatus.READY.value,
                source_status="ready",
                risk_flags=PacketRiskFlags(),
                cost_estimate="unit",
                allowed_write_scope=[f"/test/file_{i}.py"],
            ))

        mock_report = MagicMock()
        mock_report.ok = True
        mock_report.safe_candidates = safe_ids
        mock_report.risky_candidates = []
        mock_report.blocked_candidates = []
        mock_report.approval_required_candidates = []
        mock_report.packet_summaries = summaries
        mock_report.conflict_groups_total = 0
        mock_preflight.return_value = mock_report

        result = select_safe_batch(project_config="/test/project.yaml", max_packets=3)

        assert result.ok
        assert result.selected_total == 3
        assert result.stop_reason == "batch_limit_reached"
        # Should have 2 excluded due to batch limit
        batch_limit_excluded = [e for e in result.excluded_packets if e.reason == "batch_limit_reached"]
        assert len(batch_limit_excluded) == 2


def test_select_safe_batch_approval_required_exclusion():
    """Test batch selection excludes packets requiring approval."""
    with patch("prefect_grace.platform.nightly_batch_selection.load_project_adapter") as mock_load, \
         patch("prefect_grace.platform.nightly_batch_selection.generate_nightly_preflight_risk_report") as mock_preflight, \
         patch("prefect_grace.platform.nightly_batch_selection.PacketRegistryStore") as mock_registry_cls:

        mock_project = MagicMock()
        mock_project.project_key = "test-project"
        mock_project.repo_root = "/test/repo"
        mock_project.runtime_state_root = "/test/state"
        mock_load.return_value = mock_project

        mock_registry = MagicMock()
        mock_registry.load_packet.return_value = {
            "depends_on": [],
            "registry_status": RegistryStatus.READY.value,
        }
        mock_registry_cls.return_value = mock_registry

        flags_approval = PacketRiskFlags(operator_approval_required=True)
        summary_approval = PacketRiskSummary(
            packet_id="PKT-APPROVAL",
            registry_status=RegistryStatus.READY.value,
            source_status="ready",
            risk_flags=flags_approval,
            cost_estimate="unit",
            allowed_write_scope=["/test/approval.py"],
        )

        mock_report = MagicMock()
        mock_report.ok = True
        mock_report.safe_candidates = []
        mock_report.risky_candidates = []
        mock_report.blocked_candidates = []
        mock_report.approval_required_candidates = ["PKT-APPROVAL"]
        mock_report.packet_summaries = [summary_approval]
        mock_report.conflict_groups_total = 0
        mock_preflight.return_value = mock_report

        result = select_safe_batch(project_config="/test/project.yaml")

        assert result.ok
        assert result.selected_total == 0
        excluded_ids = [e.packet_id for e in result.excluded_packets]
        assert "PKT-APPROVAL" in excluded_ids
        excluded_approval = next(e for e in result.excluded_packets if e.packet_id == "PKT-APPROVAL")
        assert excluded_approval.reason == "approval_required"


def test_select_safe_batch_to_dict_bounded():
    """Test BatchSelectionResult.to_dict() bounds output lists."""
    result = BatchSelectionResult(
        ok=True,
        project_key="test-project",
        selected_packets=[f"PKT-{i}" for i in range(30)],
        selected_total=30,
        excluded_packets=[ExcludedPacket(f"PKT-EX-{i}", "test") for i in range(30)],
        excluded_total=30,
    )

    data = result.to_dict()
    assert len(data["selected_packets"]) == 25  # MAX_ITEMS
    assert len(data["excluded_packets"]) == 25  # MAX_ITEMS
    assert data["selected_total"] == 30
    assert data["excluded_total"] == 30
