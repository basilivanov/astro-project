"""
Tests for PrefectRuntimeAdapter.submit_packet_run() public API.

Validates that the adapter correctly calls submit_feature_flow_run with new signature.
"""

import pytest
from unittest.mock import Mock, patch
from prefect_grace.platform.runtime_adapter import PrefectRuntimeAdapter


def test_prefect_runtime_adapter_submit_packet_run():
    """Verify PrefectRuntimeAdapter.submit_packet_run() uses new signature."""
    with patch("prefect_grace.tasks.prefect_submitter.submit_feature_flow_run") as mock_submit, \
         patch("prefect_grace.tasks.prefect_submitter.feature_flow_parameters") as mock_params:

        # Mock feature_flow_parameters to return a dict
        mock_params.return_value = {
            "feature_id": "F1",
            "title": "Test Feature",
            "summary": "Test summary",
        }

        # Mock submit_feature_flow_run to return a result dict
        mock_submit.return_value = {
            "flow_run_id": "flow-run-123",
            "deployment_id": "deployment-456",
            "feature_id": "F1",
            "title": "Test Feature",
            "status": "Scheduled",
            "scheduled_for": "2026-05-26T12:00:00Z",
            "work_queue_name": "test-queue",
            "tags": ["grace", "live"],
        }

        # Create adapter and submit packet run
        adapter = PrefectRuntimeAdapter(work_pool="test-pool", queue="test-queue")
        packet = {
            "packet_id": "P1",
            "feature_id": "F1",
        }
        parameters = {
            "title": "Test Feature",
            "summary": "Test summary",
        }

        result = adapter.submit_packet_run(packet, parameters)

        # Verify feature_flow_parameters was called with correct args
        mock_params.assert_called_once()
        call_kwargs = mock_params.call_args.kwargs
        assert call_kwargs["feature_id"] == "F1"
        assert call_kwargs["title"] == "Test Feature"
        assert call_kwargs["summary"] == "Test summary"

        # Verify submit_feature_flow_run was called with new signature
        mock_submit.assert_called_once_with(
            parameters=mock_params.return_value,
            scheduled_for=None,
            tags=None,
            idempotency_key=None,
        )

        # Verify result structure
        assert result["run_id"] == "flow-run-123"
        assert result["runtime"] == "prefect"
        assert result["packet_id"] == "P1"
        assert result["feature_id"] == "F1"
        assert result["state"] == "Scheduled"
        assert "flow-run-123" in result["url"]


def test_prefect_runtime_adapter_submit_packet_run_missing_feature_id():
    """Verify adapter raises ValueError when feature_id is missing."""
    adapter = PrefectRuntimeAdapter()
    packet = {"packet_id": "P1"}  # Missing feature_id
    parameters = {}

    with pytest.raises(ValueError, match="packet_id and feature_id are required"):
        adapter.submit_packet_run(packet, parameters)


def test_prefect_runtime_adapter_submit_packet_run_missing_packet_id():
    """Verify adapter raises ValueError when packet_id is missing."""
    adapter = PrefectRuntimeAdapter()
    packet = {"feature_id": "F1"}  # Missing packet_id
    parameters = {}

    with pytest.raises(ValueError, match="packet_id and feature_id are required"):
        adapter.submit_packet_run(packet, parameters)


def test_prefect_runtime_adapter_submit_packet_run_import_error():
    """Verify adapter raises RuntimeError when Prefect unavailable."""
    # Temporarily hide the module to trigger ImportError
    import sys
    original_module = sys.modules.get("prefect_grace.tasks.prefect_submitter")

    try:
        # Remove module from sys.modules to force import failure
        if "prefect_grace.tasks.prefect_submitter" in sys.modules:
            del sys.modules["prefect_grace.tasks.prefect_submitter"]

        # Patch import to raise ImportError
        with patch.dict(sys.modules, {"prefect_grace.tasks.prefect_submitter": None}):
            adapter = PrefectRuntimeAdapter()
            packet = {"packet_id": "P1", "feature_id": "F1"}
            parameters = {}

            with pytest.raises(RuntimeError, match="Prefect runtime unavailable"):
                adapter.submit_packet_run(packet, parameters)
    finally:
        # Restore original module
        if original_module is not None:
            sys.modules["prefect_grace.tasks.prefect_submitter"] = original_module


def test_prefect_runtime_adapter_submit_packet_run_unknown_parameters():
    """Verify adapter ignores unknown parameters without raising TypeError."""
    with patch("prefect_grace.tasks.prefect_submitter.submit_feature_flow_run") as mock_submit, \
         patch("prefect_grace.tasks.prefect_submitter.feature_flow_parameters") as mock_params:

        # Mock feature_flow_parameters to return a dict
        mock_params.return_value = {
            "feature_id": "F1",
            "title": "Test Feature",
            "summary": "Test summary",
        }

        # Mock submit_feature_flow_run to return a result dict
        mock_submit.return_value = {
            "flow_run_id": "flow-run-123",
            "deployment_id": "deployment-456",
            "feature_id": "F1",
            "title": "Test Feature",
            "status": "Scheduled",
            "scheduled_for": "2026-05-26T12:00:00Z",
            "work_queue_name": "test-queue",
            "tags": ["grace", "live"],
        }

        # Create adapter and submit packet run with unknown parameters
        adapter = PrefectRuntimeAdapter(work_pool="test-pool", queue="test-queue")
        packet = {
            "packet_id": "P1",
            "feature_id": "F1",
        }
        parameters = {
            "title": "Test Feature",
            "summary": "Test summary",
            "unknown_param": "should be ignored",
            "another_unknown": 123,
        }

        # Should not raise TypeError
        result = adapter.submit_packet_run(packet, parameters)

        # Verify feature_flow_parameters was called with known fields only
        mock_params.assert_called_once()
        call_kwargs = mock_params.call_args.kwargs
        assert call_kwargs["feature_id"] == "F1"
        assert call_kwargs["title"] == "Test Feature"
        assert call_kwargs["summary"] == "Test summary"
        assert "unknown_param" not in call_kwargs
        assert "another_unknown" not in call_kwargs

        # Verify result structure
        assert result["run_id"] == "flow-run-123"
        assert result["runtime"] == "prefect"


def test_prefect_runtime_adapter_submit_packet_run_missing_title_summary():
    """Verify adapter provides defaults for missing title and summary."""
    with patch("prefect_grace.tasks.prefect_submitter.submit_feature_flow_run") as mock_submit, \
         patch("prefect_grace.tasks.prefect_submitter.feature_flow_parameters") as mock_params:

        # Mock feature_flow_parameters to return a dict
        mock_params.return_value = {
            "feature_id": "F1",
            "title": "Untitled Feature",
            "summary": "No summary provided",
        }

        # Mock submit_feature_flow_run to return a result dict
        mock_submit.return_value = {
            "flow_run_id": "flow-run-123",
            "deployment_id": "deployment-456",
            "feature_id": "F1",
            "title": "Untitled Feature",
            "status": "Scheduled",
            "scheduled_for": "2026-05-26T12:00:00Z",
            "work_queue_name": "test-queue",
            "tags": ["grace", "live"],
        }

        # Create adapter and submit packet run without title/summary
        adapter = PrefectRuntimeAdapter(work_pool="test-pool", queue="test-queue")
        packet = {
            "packet_id": "P1",
            "feature_id": "F1",
        }
        parameters = {}

        result = adapter.submit_packet_run(packet, parameters)

        # Verify feature_flow_parameters was called with defaults
        mock_params.assert_called_once()
        call_kwargs = mock_params.call_args.kwargs
        assert call_kwargs["feature_id"] == "F1"
        assert call_kwargs["title"] == "Untitled Feature"
        assert call_kwargs["summary"] == "No summary provided"

        # Verify result structure
        assert result["run_id"] == "flow-run-123"
        assert result["runtime"] == "prefect"
