"""Tests for PrefectRuntimeAdapter.submit_packet_run() public API."""

from unittest.mock import patch

import pytest

from prefect_grace.platform.runtime_adapter import PrefectRuntimeAdapter
from prefect_grace.tasks.prefect_submitter import E2E_PACKET_DEPLOYMENT_NAME


def test_prefect_runtime_adapter_submit_packet_run():
    """Verify PrefectRuntimeAdapter.submit_packet_run() uses E2E submission."""
    with patch("prefect_grace.tasks.prefect_submitter.submit_e2e_packet_flow_run") as mock_submit, \
         patch("prefect_grace.tasks.prefect_submitter.e2e_packet_flow_parameters") as mock_params:

        mock_params.return_value = {
            "project_root": "/repo",
            "packet_path": "/repo/prefect_grace/packets/P1/EXECUTION_PACKET.md",
            "state_root": "/state",
            "worktree_root": "/worktrees",
            "project_key": "test-project",
            "packet_id": "P1",
            "attempt": 1,
            "base_ref": "HEAD",
            "dry_run": True,
            "execute_agent": False,
            "timeout_seconds": 3600,
            "keep_worktree": True,
        }
        mock_submit.return_value = {
            "flow_run_id": "flow-run-123",
            "flow_run_name": "e2e-packet:P1:attempt-1",
            "deployment_id": "deployment-456",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "packet_id": "P1",
            "project_key": "test-project",
            "runner_kind": "e2e",
            "status": "Scheduled",
            "scheduled_for": "2026-05-26T12:00:00Z",
            "work_pool_name": "test-pool",
            "work_queue_name": "test-queue",
            "tags": ["grace", "packet", "e2e"],
            "url": "http://prefect.local/flow-runs/flow-run-123",
        }

        adapter = PrefectRuntimeAdapter(work_pool="test-pool", queue="test-queue")
        packet = {"packet_id": "P1", "feature_id": "F1", "project_key": "test-project"}
        parameters = {
            "project_root": "/repo",
            "packet_path": "/repo/prefect_grace/packets/P1/EXECUTION_PACKET.md",
            "state_root": "/state",
            "worktree_root": "/worktrees",
            "title": "Test Packet",
            "summary": "Test summary",
        }

        result = adapter.submit_packet_run(packet, parameters)

        mock_params.assert_called_once()
        call_kwargs = mock_params.call_args.kwargs
        assert call_kwargs["project_root"] == "/repo"
        assert call_kwargs["packet_path"] == "/repo/prefect_grace/packets/P1/EXECUTION_PACKET.md"
        assert call_kwargs["project_key"] == "test-project"
        assert call_kwargs["packet_id"] == "P1"
        assert call_kwargs["attempt"] == 1
        assert call_kwargs["dry_run"] is True
        assert call_kwargs["execute_agent"] is False

        mock_submit.assert_called_once_with(
            parameters=mock_params.return_value,
            scheduled_for=None,
            tags=["grace", "packet", "e2e", "packet:P1", "feature:F1"],
            idempotency_key=None,
        )

        assert result["run_id"] == "flow-run-123"
        assert result["runtime"] == "prefect"
        assert result["packet_id"] == "P1"
        assert result["feature_id"] == "F1"
        assert result["runner_kind"] == "e2e"
        assert result["deployment_name"] == E2E_PACKET_DEPLOYMENT_NAME
        assert result["state"] == "Scheduled"
        assert "flow-run-123" in result["url"]


def test_prefect_runtime_adapter_submit_packet_run_missing_feature_id():
    """Verify adapter raises ValueError when feature_id is missing."""
    adapter = PrefectRuntimeAdapter()
    packet = {"packet_id": "P1"}
    parameters = {}

    with pytest.raises(ValueError, match="packet_id and feature_id are required"):
        adapter.submit_packet_run(packet, parameters)


def test_prefect_runtime_adapter_submit_packet_run_missing_packet_id():
    """Verify adapter raises ValueError when packet_id is missing."""
    adapter = PrefectRuntimeAdapter()
    packet = {"feature_id": "F1"}
    parameters = {}

    with pytest.raises(ValueError, match="packet_id and feature_id are required"):
        adapter.submit_packet_run(packet, parameters)


def test_prefect_runtime_adapter_submit_packet_run_import_error():
    """Verify adapter raises RuntimeError when Prefect unavailable."""
    import sys

    original_module = sys.modules.get("prefect_grace.tasks.prefect_submitter")

    try:
        if "prefect_grace.tasks.prefect_submitter" in sys.modules:
            del sys.modules["prefect_grace.tasks.prefect_submitter"]

        with patch.dict(sys.modules, {"prefect_grace.tasks.prefect_submitter": None}):
            adapter = PrefectRuntimeAdapter()
            packet = {"packet_id": "P1", "feature_id": "F1"}
            parameters = {}

            with pytest.raises(RuntimeError, match="Prefect runtime unavailable"):
                adapter.submit_packet_run(packet, parameters)
    finally:
        if original_module is not None:
            sys.modules["prefect_grace.tasks.prefect_submitter"] = original_module


def test_prefect_runtime_adapter_submit_packet_run_unknown_parameters():
    """Verify adapter ignores unknown parameters without raising TypeError."""
    with patch("prefect_grace.tasks.prefect_submitter.submit_e2e_packet_flow_run") as mock_submit, \
         patch("prefect_grace.tasks.prefect_submitter.e2e_packet_flow_parameters") as mock_params:

        mock_params.return_value = {
            "project_root": "/repo",
            "packet_path": "/repo/prefect_grace/packets/P1/EXECUTION_PACKET.md",
            "state_root": "/state",
            "worktree_root": "/worktrees",
            "project_key": "test-project",
            "packet_id": "P1",
            "attempt": 1,
            "base_ref": "HEAD",
            "dry_run": True,
            "execute_agent": False,
            "timeout_seconds": 3600,
            "keep_worktree": True,
        }
        mock_submit.return_value = {
            "flow_run_id": "flow-run-123",
            "deployment_id": "deployment-456",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "packet_id": "P1",
            "project_key": "test-project",
            "runner_kind": "e2e",
            "status": "Scheduled",
            "scheduled_for": "2026-05-26T12:00:00Z",
            "work_queue_name": "test-queue",
            "tags": ["grace", "packet", "e2e"],
        }

        adapter = PrefectRuntimeAdapter(work_pool="test-pool", queue="test-queue")
        packet = {"packet_id": "P1", "feature_id": "F1", "project_key": "test-project"}
        parameters = {
            "project_root": "/repo",
            "packet_path": "/repo/prefect_grace/packets/P1/EXECUTION_PACKET.md",
            "state_root": "/state",
            "worktree_root": "/worktrees",
            "title": "Test Feature",
            "summary": "Test summary",
            "unknown_param": "should be ignored",
            "another_unknown": 123,
        }

        result = adapter.submit_packet_run(packet, parameters)

        mock_params.assert_called_once()
        call_kwargs = mock_params.call_args.kwargs
        assert call_kwargs["project_root"] == "/repo"
        assert call_kwargs["packet_path"] == "/repo/prefect_grace/packets/P1/EXECUTION_PACKET.md"
        assert call_kwargs["project_key"] == "test-project"
        assert "unknown_param" not in call_kwargs
        assert "another_unknown" not in call_kwargs
        assert result["runner_kind"] == "e2e"


def test_prefect_runtime_adapter_submit_packet_run_missing_title_summary():
    """Verify adapter provides defaults for missing runtime packet inputs."""
    with patch("prefect_grace.tasks.prefect_submitter.submit_e2e_packet_flow_run") as mock_submit, \
         patch("prefect_grace.tasks.prefect_submitter.e2e_packet_flow_parameters") as mock_params:

        mock_params.return_value = {
            "project_root": ".",
            "packet_path": "",
            "state_root": ".grace/state",
            "worktree_root": ".grace/worktrees",
            "project_key": "test-project",
            "packet_id": "P1",
            "attempt": 1,
            "base_ref": "HEAD",
            "dry_run": True,
            "execute_agent": False,
            "timeout_seconds": 3600,
            "keep_worktree": True,
        }
        mock_submit.return_value = {
            "flow_run_id": "flow-run-123",
            "deployment_id": "deployment-456",
            "deployment_name": E2E_PACKET_DEPLOYMENT_NAME,
            "packet_id": "P1",
            "project_key": "test-project",
            "runner_kind": "e2e",
            "status": "Scheduled",
            "scheduled_for": "2026-05-26T12:00:00Z",
            "work_queue_name": "test-queue",
            "tags": ["grace", "packet", "e2e"],
        }

        adapter = PrefectRuntimeAdapter(work_pool="test-pool", queue="test-queue")
        packet = {"packet_id": "P1", "feature_id": "F1", "project_key": "test-project"}
        parameters = {}

        result = adapter.submit_packet_run(packet, parameters)

        mock_params.assert_called_once()
        call_kwargs = mock_params.call_args.kwargs
        assert call_kwargs["project_root"] == "."
        assert call_kwargs["packet_path"] == ""
        assert call_kwargs["project_key"] == "test-project"
        assert call_kwargs["dry_run"] is True
        assert result["runner_kind"] == "e2e"
