"""
Tests for prefect_grace.platform.prefect_worker_binding module.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from prefect_grace.platform.prefect_worker_binding import (
    run_prefect_worker_binding_preflight,
    PrefectWorkerBindingResult,
    _check_prefect_available,
    _check_server_health,
    _check_work_pool,
    _check_queues,
    _check_deployment,
)


class TestPrefectAvailability:
    """Test Prefect availability checks."""

    def test_prefect_unavailable(self, monkeypatch):
        """Test fail-closed when Prefect is not installed."""
        # Mock import to fail
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "prefect":
                raise ImportError("No module named 'prefect'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        available, version, errors = _check_prefect_available()
        assert not available
        assert version is None
        assert len(errors) == 1
        assert errors[0]["type"] == "PREFECT_UNAVAILABLE"


class TestServerHealth:
    """Test Prefect server health checks."""

    def test_server_healthy(self):
        """Test healthy server check."""
        mock_client = Mock()
        mock_client.api_healthcheck = Mock()

        healthy, errors = _check_server_health(mock_client, "http://localhost:4200/api")
        assert healthy
        assert len(errors) == 0

    def test_server_unreachable(self):
        """Test unreachable server."""
        mock_client = Mock()
        mock_client.api_healthcheck = Mock(side_effect=Exception("Connection refused"))

        healthy, errors = _check_server_health(mock_client, "http://localhost:4200/api")
        assert not healthy
        assert len(errors) == 1
        assert errors[0]["type"] == "PREFECT_API_UNREACHABLE"


class TestWorkPool:
    """Test work pool validation."""

    def test_work_pool_ready(self):
        """Test work pool exists and is ready."""
        mock_client = Mock()
        mock_pool = Mock()
        mock_pool.type = "process"
        mock_pool.is_paused = False
        mock_client.read_work_pool = Mock(return_value=mock_pool)

        status, pool_type, errors = _check_work_pool(mock_client, "astro-process")
        assert status == "READY"
        assert pool_type == "process"
        assert len(errors) == 0

    def test_work_pool_not_found(self):
        """Test missing work pool."""
        mock_client = Mock()
        mock_client.read_work_pool = Mock(return_value=None)

        status, pool_type, errors = _check_work_pool(mock_client, "astro-process")
        assert status is None
        assert pool_type is None
        assert len(errors) == 1
        assert errors[0]["type"] == "WORK_POOL_NOT_FOUND"

    def test_work_pool_wrong_type(self):
        """Test work pool with wrong type."""
        mock_client = Mock()
        mock_pool = Mock()
        mock_pool.type = "kubernetes"
        mock_pool.is_paused = False
        mock_client.read_work_pool = Mock(return_value=mock_pool)

        status, pool_type, errors = _check_work_pool(mock_client, "astro-process")
        assert status is None
        assert pool_type == "kubernetes"
        assert len(errors) == 1
        assert errors[0]["type"] == "WORK_POOL_WRONG_TYPE"

    def test_work_pool_paused(self):
        """Test paused work pool."""
        mock_client = Mock()
        mock_pool = Mock()
        mock_pool.type = "process"
        mock_pool.is_paused = True
        mock_client.read_work_pool = Mock(return_value=mock_pool)

        status, pool_type, errors = _check_work_pool(mock_client, "astro-process")
        assert status == "PAUSED"
        assert pool_type == "process"
        assert len(errors) == 1
        assert errors[0]["type"] == "WORK_POOL_PAUSED"


class TestQueues:
    """Test queue validation."""

    def test_queues_ready(self):
        """Test all required queues exist and are ready."""
        mock_client = Mock()
        mock_queue = Mock()
        mock_queue.is_paused = False
        mock_client.read_work_queue_by_name = Mock(return_value=mock_queue)

        statuses, errors = _check_queues(mock_client, "astro-process", ["grace-live", "grace-monitoring"])
        assert len(statuses) == 2
        assert statuses["grace-live"]["exists"]
        assert statuses["grace-live"]["status"] == "READY"
        assert statuses["grace-monitoring"]["exists"]
        assert statuses["grace-monitoring"]["status"] == "READY"
        assert len(errors) == 0

    def test_queue_not_found(self):
        """Test missing queue."""
        mock_client = Mock()
        mock_client.read_work_queue_by_name = Mock(return_value=None)

        statuses, errors = _check_queues(mock_client, "astro-process", ["grace-live"])
        assert not statuses["grace-live"]["exists"]
        assert len(errors) == 1
        assert errors[0]["type"] == "QUEUE_NOT_FOUND"

    def test_queue_paused(self):
        """Test paused queue."""
        mock_client = Mock()
        mock_queue = Mock()
        mock_queue.is_paused = True
        mock_client.read_work_queue_by_name = Mock(return_value=mock_queue)

        statuses, errors = _check_queues(mock_client, "astro-process", ["grace-live"])
        assert statuses["grace-live"]["exists"]
        assert statuses["grace-live"]["status"] == "PAUSED"
        assert len(errors) == 1
        assert errors[0]["type"] == "QUEUE_PAUSED"


class TestDeployment:
    """Test deployment validation."""

    def test_deployment_exists_and_valid(self):
        """Test deployment exists with correct routing."""
        mock_client = Mock()
        mock_deployment = Mock()
        mock_deployment.work_pool_name = "astro-process"
        mock_deployment.work_queue_name = "grace-live"
        mock_client.read_deployment_by_name = Mock(return_value=mock_deployment)

        exists, work_pool, work_queue, valid, errors = _check_deployment(
            mock_client, "prefect-grace-managed-packet-runner/live-managed-packet-runner",
            "astro-process", "grace-live"
        )
        assert exists
        assert work_pool == "astro-process"
        assert work_queue == "grace-live"
        assert valid
        assert len(errors) == 0

    def test_deployment_not_found(self):
        """Test missing deployment."""
        mock_client = Mock()
        mock_client.read_deployment_by_name = Mock(side_effect=Exception("Not found"))

        exists, work_pool, work_queue, valid, errors = _check_deployment(
            mock_client, "prefect-grace-managed-packet-runner/live-managed-packet-runner",
            "astro-process", "grace-live"
        )
        assert not exists
        assert work_pool is None
        assert work_queue is None
        assert not valid
        assert len(errors) == 1
        assert errors[0]["type"] == "DEPLOYMENT_NOT_FOUND"

    def test_deployment_wrong_work_pool(self):
        """Test deployment with wrong work pool."""
        mock_client = Mock()
        mock_deployment = Mock()
        mock_deployment.work_pool_name = "wrong-pool"
        mock_deployment.work_queue_name = "grace-live"
        mock_client.read_deployment_by_name = Mock(return_value=mock_deployment)

        exists, work_pool, work_queue, valid, errors = _check_deployment(
            mock_client, "prefect-grace-managed-packet-runner/live-managed-packet-runner",
            "astro-process", "grace-live"
        )
        assert exists
        assert work_pool == "wrong-pool"
        assert not valid
        assert len(errors) == 1
        assert errors[0]["type"] == "DEPLOYMENT_WRONG_WORK_POOL"

    def test_deployment_wrong_queue(self):
        """Test deployment with wrong queue."""
        mock_client = Mock()
        mock_deployment = Mock()
        mock_deployment.work_pool_name = "astro-process"
        mock_deployment.work_queue_name = "wrong-queue"
        mock_client.read_deployment_by_name = Mock(return_value=mock_deployment)

        exists, work_pool, work_queue, valid, errors = _check_deployment(
            mock_client, "prefect-grace-managed-packet-runner/live-managed-packet-runner",
            "astro-process", "grace-live"
        )
        assert exists
        assert work_queue == "wrong-queue"
        assert not valid
        assert len(errors) == 1
        assert errors[0]["type"] == "DEPLOYMENT_WRONG_QUEUE"
