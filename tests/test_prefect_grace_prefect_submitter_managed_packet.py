"""
Tests for prefect_submitter managed packet submission request building.

Validates that build_managed_packet_submission_request() creates correct
submission requests without making Prefect API calls.
"""

from datetime import datetime, timezone
from prefect_grace.tasks.prefect_submitter import (
    build_managed_packet_submission_request,
    managed_packet_flow_parameters,
    managed_packet_flow_run_name,
    MANAGED_PACKET_DEPLOYMENT_NAME,
)


def test_managed_packet_flow_run_name_with_title():
    """Verify flow run name format with title."""
    name = managed_packet_flow_run_name("TEST-PACKET-001", "Test Packet Title")
    assert name == "packet:TEST-PACKET-001:Test Packet Title"


def test_managed_packet_flow_run_name_without_title():
    """Verify flow run name format without title."""
    name = managed_packet_flow_run_name("TEST-PACKET-001", None)
    assert name == "packet:TEST-PACKET-001"


def test_managed_packet_flow_parameters():
    """Verify managed packet flow parameters structure."""
    params = managed_packet_flow_parameters(
        packet_file="/repo/packets/P1.md",
        repo_root="/repo",
        worktree_root="/worktrees",
        project_key="test-project",
        packet_id="P1",
        attempt=1,
        base_ref="HEAD",
        dry_run=False,
        execute_agent=True,
        timeout_seconds=3600,
    )

    assert params["packet_file"] == "/repo/packets/P1.md"
    assert params["repo_root"] == "/repo"
    assert params["worktree_root"] == "/worktrees"
    assert params["project_key"] == "test-project"
    assert params["packet_id"] == "P1"
    assert params["attempt"] == 1
    assert params["base_ref"] == "HEAD"
    assert params["dry_run"] is False
    assert params["execute_agent"] is True
    assert params["timeout_seconds"] == 3600


def test_build_managed_packet_submission_request_structure():
    """Verify submission request structure without Prefect calls."""
    params = managed_packet_flow_parameters(
        packet_file="/repo/packets/P1.md",
        repo_root="/repo",
        worktree_root="/worktrees",
        project_key="test-project",
        packet_id="P1",
        attempt=1,
    )

    request = build_managed_packet_submission_request(
        parameters=params,
        scheduled_for=None,
        tags=["custom-tag"],
        idempotency_key="test-key-123",
    )

    assert request["deployment_name"] == MANAGED_PACKET_DEPLOYMENT_NAME
    assert request["parameters"] == params
    assert request["flow_run_name"] == "packet:P1"
    assert request["idempotency_key"] == "test-key-123"
    assert "grace" in request["tags"]
    assert "packet" in request["tags"]
    assert "managed-runner" in request["tags"]
    assert "packet:P1" in request["tags"]
    assert "project:test-project" in request["tags"]
    assert "custom-tag" in request["tags"]
    assert request["labels"]["grace.packet_id"] == "P1"
    assert request["labels"]["grace.project_key"] == "test-project"
    assert "api_url" in request
    assert "work_queue_name" in request


def test_build_managed_packet_submission_request_auto_idempotency_key():
    """Verify auto-generated idempotency key format."""
    params = managed_packet_flow_parameters(
        packet_file="/repo/packets/P1.md",
        repo_root="/repo",
        worktree_root="/worktrees",
        project_key="test-project",
        packet_id="P1",
        attempt=1,
    )

    request = build_managed_packet_submission_request(
        parameters=params,
        scheduled_for=None,
        tags=[],
        idempotency_key=None,
    )

    # Auto-generated key should contain project, packet, and timestamp
    assert request["idempotency_key"].startswith("grace-packet:test-project:P1:")
    assert isinstance(request["scheduled_time"], datetime)


def test_build_managed_packet_submission_request_scheduled_time():
    """Verify scheduled time parsing."""
    params = managed_packet_flow_parameters(
        packet_file="/repo/packets/P1.md",
        repo_root="/repo",
        worktree_root="/worktrees",
        project_key="test-project",
        packet_id="P1",
        attempt=1,
    )

    request = build_managed_packet_submission_request(
        parameters=params,
        scheduled_for="2026-05-26T12:00:00Z",
        tags=[],
        idempotency_key="test-key",
    )

    assert request["scheduled_time"].year == 2026
    assert request["scheduled_time"].month == 5
    assert request["scheduled_time"].day == 26
    assert request["scheduled_time"].hour == 12
    assert request["scheduled_time"].tzinfo == timezone.utc
