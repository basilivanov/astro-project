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

    def test_deployment_entrypoint_exists(self):
        """Test that the managed packet runner flow entrypoint exists."""
        from pathlib import Path
        import importlib.util

        # Check file exists
        flow_file = Path("prefect_grace/flows/managed_packet_runner_flow.py")
        assert flow_file.exists(), f"Flow file not found: {flow_file}"

        # Check module can be imported
        spec = importlib.util.spec_from_file_location("managed_packet_runner_flow", flow_file)
        assert spec is not None, "Could not load module spec"
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Check function exists
        assert hasattr(module, "managed_packet_runner_flow"), "Flow function not found in module"
        assert callable(module.managed_packet_runner_flow), "managed_packet_runner_flow is not callable"


class TestPreflightApplyPath:
    """Test platform-level preflight apply path with injected mocks."""

    def test_preflight_dry_run_would_apply(self, tmp_path):
        """Test dry-run mode with --apply-deployment reports would-apply plan."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Mock Prefect client
        mock_client = Mock()
        mock_client.api_healthcheck = Mock()

        # Mock work pool
        mock_pool = Mock()
        mock_pool.type = "process"
        mock_pool.is_paused = False
        mock_client.read_work_pool = Mock(return_value=mock_pool)

        # Mock queues
        mock_queue = Mock()
        mock_queue.is_paused = False
        mock_client.read_work_queue_by_name = Mock(return_value=mock_queue)

        # Mock deployment - not found
        mock_client.read_deployment_by_name = Mock(return_value=None)

        # Run preflight in dry-run mode with apply_deployment=True
        result = run_prefect_worker_binding_preflight(
            project_config=project_config,
            dry_run=True,
            apply_deployment=True,
            acknowledge_prefect_mutation=True,
            approval_token="deployment",
            run_worker_smoke=False,
            prefect_client=mock_client,
        )

        # Should report dry_run_would_apply
        assert result.dry_run is True
        assert result.deployment_mutation == "dry_run_would_apply"
        assert result.prefect_runs_created == 0
        assert result.live_agents_started == 0

        # Should not call apply helper in dry-run mode
        # (no way to verify this without patching, but zero runs proves it)

    def test_preflight_apply_success_rereads_deployment(self, tmp_path, monkeypatch):
        """Test successful apply re-reads deployment and returns consistent state."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Mock Prefect client
        mock_client = Mock()
        mock_client.api_healthcheck = Mock()

        # Mock work pool
        mock_pool = Mock()
        mock_pool.type = "process"
        mock_pool.is_paused = False
        mock_client.read_work_pool = Mock(return_value=mock_pool)

        # Mock queues
        mock_queue = Mock()
        mock_queue.is_paused = False
        mock_client.read_work_queue_by_name = Mock(return_value=mock_queue)

        # Mock deployment - first call returns None (not found), second call returns deployment
        mock_deployment = Mock()
        mock_deployment.work_pool_name = "astro-process"
        mock_deployment.work_queue_name = "grace-live"
        mock_client.read_deployment_by_name = Mock(side_effect=[None, mock_deployment])

        # Mock apply helper to succeed
        from unittest.mock import patch
        from prefect_grace.platform.runtime_adapter import DeploymentApplyResult

        mock_apply_result = DeploymentApplyResult(
            success=True,
            deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
            deployment_id="dep-123",
            work_pool_name="astro-process",
            work_queue_name="grace-live",
            entrypoint="prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow",
            working_directory="/opt/astro-project",
            created=True,
            prefect_runs_created=0,
            live_agents_started=0,
            errors=[],
        )

        with patch("prefect_grace.platform.prefect_worker_binding._apply_managed_packet_deployment") as mock_apply:
            mock_apply.return_value = mock_apply_result

            # Run preflight in apply mode
            result = run_prefect_worker_binding_preflight(
                project_config=project_config,
                dry_run=False,
                apply_deployment=True,
                acknowledge_prefect_mutation=True,
                approval_token="deployment",
                run_worker_smoke=False,
                prefect_client=mock_client,
            )

        # Should report applied
        assert result.dry_run is False
        assert result.deployment_mutation == "applied"
        assert result.prefect_runs_created == 0
        assert result.live_agents_started == 0

        # Should have re-read deployment (2 calls total)
        assert mock_client.read_deployment_by_name.call_count == 2

        # After-state should be consistent
        assert result.deployment_exists is True
        assert result.deployment_work_pool_name == "astro-process"
        assert result.deployment_work_queue_name == "grace-live"
        assert result.deployment_parameters_valid is True

        # Should not have DEPLOYMENT_NOT_FOUND error
        assert not any(e["type"] == "DEPLOYMENT_NOT_FOUND" for e in result.errors)

        # Should have deployment_apply_result
        assert result.deployment_apply_result is not None
        assert result.deployment_apply_result["success"] is True
        assert result.deployment_apply_result["deployment_id"] == "dep-123"
        assert result.deployment_apply_result["created"] is True
        assert result.deployment_apply_result["prefect_runs_created"] == 0
        assert result.deployment_apply_result["live_agents_started"] == 0

        # Should be ok
        assert result.ok is True

    def test_preflight_apply_failure(self, tmp_path, monkeypatch):
        """Test failed apply reports apply_failed and preserves errors."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Mock Prefect client
        mock_client = Mock()
        mock_client.api_healthcheck = Mock()

        # Mock work pool
        mock_pool = Mock()
        mock_pool.type = "process"
        mock_pool.is_paused = False
        mock_client.read_work_pool = Mock(return_value=mock_pool)

        # Mock queues
        mock_queue = Mock()
        mock_queue.is_paused = False
        mock_client.read_work_queue_by_name = Mock(return_value=mock_queue)

        # Mock deployment - not found
        mock_client.read_deployment_by_name = Mock(return_value=None)

        # Mock apply helper to fail
        from unittest.mock import patch
        from prefect_grace.platform.runtime_adapter import DeploymentApplyResult

        mock_apply_result = DeploymentApplyResult(
            success=False,
            deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
            deployment_id=None,
            work_pool_name="astro-process",
            work_queue_name="grace-live",
            entrypoint="prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow",
            working_directory="/opt/astro-project",
            created=False,
            prefect_runs_created=0,
            live_agents_started=0,
            errors=[{"type": "DEPLOYMENT_APPLY_FAILED", "message": "Apply failed"}],
        )

        with patch("prefect_grace.platform.prefect_worker_binding._apply_managed_packet_deployment") as mock_apply:
            mock_apply.return_value = mock_apply_result

            # Run preflight in apply mode
            result = run_prefect_worker_binding_preflight(
                project_config=project_config,
                dry_run=False,
                apply_deployment=True,
                acknowledge_prefect_mutation=True,
                approval_token="deployment",
                run_worker_smoke=False,
                prefect_client=mock_client,
            )

        # Should report apply_failed
        assert result.dry_run is False
        assert result.deployment_mutation == "apply_failed"
        assert result.prefect_runs_created == 0
        assert result.live_agents_started == 0

        # Should have apply failure error
        assert any(e["type"] == "DEPLOYMENT_APPLY_FAILED" for e in result.errors)

        # Should have deployment_apply_result
        assert result.deployment_apply_result is not None
        assert result.deployment_apply_result["success"] is False
        assert result.deployment_apply_result["deployment_id"] is None

        # Should not be ok
        assert result.ok is False

    def test_preflight_invalid_entrypoint_blocks_apply(self, tmp_path, monkeypatch):
        """Test invalid entrypoint fails closed before apply."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Mock Prefect client
        mock_client = Mock()
        mock_client.api_healthcheck = Mock()

        # Mock work pool
        mock_pool = Mock()
        mock_pool.type = "process"
        mock_pool.is_paused = False
        mock_client.read_work_pool = Mock(return_value=mock_pool)

        # Mock queues
        mock_queue = Mock()
        mock_queue.is_paused = False
        mock_client.read_work_queue_by_name = Mock(return_value=mock_queue)

        # Mock deployment - not found
        mock_client.read_deployment_by_name = Mock(return_value=None)

        # Mock the apply helper to return invalid entrypoint error
        from unittest.mock import patch
        from prefect_grace.platform.runtime_adapter import DeploymentApplyResult

        mock_apply_result = DeploymentApplyResult(
            success=False,
            deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
            deployment_id=None,
            work_pool_name="astro-process",
            work_queue_name="grace-live",
            entrypoint="prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow",
            working_directory="/opt/astro-project",
            created=False,
            prefect_runs_created=0,
            live_agents_started=0,
            errors=[{"type": "INVALID_ENTRYPOINT", "message": "Entrypoint file not found: prefect_grace/flows/managed_packet_runner_flow.py"}],
        )

        with patch("prefect_grace.platform.prefect_worker_binding._apply_managed_packet_deployment") as mock_apply:
            mock_apply.return_value = mock_apply_result

            # Run preflight in apply mode
            result = run_prefect_worker_binding_preflight(
                project_config=project_config,
                dry_run=False,
                apply_deployment=True,
                acknowledge_prefect_mutation=True,
                approval_token="deployment",
                run_worker_smoke=False,
                prefect_client=mock_client,
            )

        # Should report apply_failed (not applied)
        assert result.dry_run is False
        assert result.deployment_mutation == "apply_failed"
        assert result.prefect_runs_created == 0
        assert result.live_agents_started == 0

        # Should have INVALID_ENTRYPOINT error
        assert any(e["type"] == "INVALID_ENTRYPOINT" for e in result.errors)

        # Should have deployment_apply_result showing failure
        assert result.deployment_apply_result is not None
        assert result.deployment_apply_result["success"] is False
        assert result.deployment_apply_result["deployment_id"] is None

        # Should not be ok
        assert result.ok is False

    def test_preflight_apply_created_vs_updated(self, tmp_path, monkeypatch):
        """Test apply correctly reports created vs updated."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Mock Prefect client
        mock_client = Mock()
        mock_client.api_healthcheck = Mock()

        # Mock work pool
        mock_pool = Mock()
        mock_pool.type = "process"
        mock_pool.is_paused = False
        mock_client.read_work_pool = Mock(return_value=mock_pool)

        # Mock queues
        mock_queue = Mock()
        mock_queue.is_paused = False
        mock_client.read_work_queue_by_name = Mock(return_value=mock_queue)

        from unittest.mock import patch
        from prefect_grace.platform.runtime_adapter import DeploymentApplyResult

        # Test case 1: deployment doesn't exist -> created=True
        mock_deployment = Mock()
        mock_deployment.work_pool_name = "astro-process"
        mock_deployment.work_queue_name = "grace-live"
        mock_client.read_deployment_by_name = Mock(side_effect=[None, mock_deployment])

        mock_apply_result_created = DeploymentApplyResult(
            success=True,
            deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
            deployment_id="dep-123",
            work_pool_name="astro-process",
            work_queue_name="grace-live",
            entrypoint="prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow",
            working_directory="/opt/astro-project",
            created=True,
            prefect_runs_created=0,
            live_agents_started=0,
            errors=[],
        )

        with patch("prefect_grace.platform.prefect_worker_binding._apply_managed_packet_deployment") as mock_apply:
            mock_apply.return_value = mock_apply_result_created

            result = run_prefect_worker_binding_preflight(
                project_config=project_config,
                dry_run=False,
                apply_deployment=True,
                acknowledge_prefect_mutation=True,
                approval_token="deployment",
                run_worker_smoke=False,
                prefect_client=mock_client,
            )

        assert result.deployment_mutation == "applied"
        assert result.deployment_apply_result["created"] is True
        assert "created" in result.warnings[0].lower()

        # Test case 2: deployment exists -> created=False (updated)
        mock_client.read_deployment_by_name = Mock(side_effect=[mock_deployment, mock_deployment])

        mock_apply_result_updated = DeploymentApplyResult(
            success=True,
            deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
            deployment_id="dep-456",
            work_pool_name="astro-process",
            work_queue_name="grace-live",
            entrypoint="prefect_grace/flows/managed_packet_runner_flow.py:managed_packet_runner_flow",
            working_directory="/opt/astro-project",
            created=False,
            prefect_runs_created=0,
            live_agents_started=0,
            errors=[],
        )

        with patch("prefect_grace.platform.prefect_worker_binding._apply_managed_packet_deployment") as mock_apply:
            mock_apply.return_value = mock_apply_result_updated

            result = run_prefect_worker_binding_preflight(
                project_config=project_config,
                dry_run=False,
                apply_deployment=True,
                acknowledge_prefect_mutation=True,
                approval_token="deployment",
                run_worker_smoke=False,
                prefect_client=mock_client,
            )

        assert result.deployment_mutation == "applied"
        assert result.deployment_apply_result["created"] is False
        assert "updated" in result.warnings[0].lower()

    def test_preflight_missing_approval_gates(self, tmp_path):
        """Test apply without approval gates is blocked."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Mock Prefect client
        mock_client = Mock()
        mock_client.api_healthcheck = Mock()

        # Mock work pool
        mock_pool = Mock()
        mock_pool.type = "process"
        mock_pool.is_paused = False
        mock_client.read_work_pool = Mock(return_value=mock_pool)

        # Mock queues
        mock_queue = Mock()
        mock_queue.is_paused = False
        mock_client.read_work_queue_by_name = Mock(return_value=mock_queue)

        # Mock deployment - not found
        mock_client.read_deployment_by_name = Mock(return_value=None)

        # Run preflight without acknowledgement
        result = run_prefect_worker_binding_preflight(
            project_config=project_config,
            dry_run=False,
            apply_deployment=True,
            acknowledge_prefect_mutation=False,  # Missing gate
            approval_token="deployment",
            run_worker_smoke=False,
            prefect_client=mock_client,
        )

        # Should be blocked
        assert result.ok is False
        assert result.deployment_mutation == "none"
        assert result.prefect_runs_created == 0
        assert result.live_agents_started == 0
        assert any(e["type"] == "DEPLOYMENT_APPLY_NOT_ACKNOWLEDGED" for e in result.errors)

        # Run preflight without approval token
        result = run_prefect_worker_binding_preflight(
            project_config=project_config,
            dry_run=False,
            apply_deployment=True,
            acknowledge_prefect_mutation=True,
            approval_token=None,  # Missing gate
            run_worker_smoke=False,
            prefect_client=mock_client,
        )

        # Should be blocked
        assert result.ok is False
        assert result.deployment_mutation == "none"
        assert result.prefect_runs_created == 0
        assert result.live_agents_started == 0
        assert any(e["type"] == "DEPLOYMENT_APPLY_NOT_APPROVED" for e in result.errors)

    def test_preflight_missing_approval_gates_with_valid_deployment(self, tmp_path):
        """Test apply without approval gates is blocked even when deployment exists and is valid."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Mock Prefect client
        mock_client = Mock()
        mock_client.api_healthcheck = Mock()

        # Mock work pool
        mock_pool = Mock()
        mock_pool.type = "process"
        mock_pool.is_paused = False
        mock_client.read_work_pool = Mock(return_value=mock_pool)

        # Mock queues
        mock_queue = Mock()
        mock_queue.is_paused = False
        mock_client.read_work_queue_by_name = Mock(return_value=mock_queue)

        # Mock deployment - exists and is valid
        mock_deployment = Mock()
        mock_deployment.work_pool_name = "astro-process"
        mock_deployment.work_queue_name = "grace-live"
        mock_client.read_deployment_by_name = Mock(return_value=mock_deployment)

        # Run preflight without acknowledgement (deployment exists and is valid)
        result = run_prefect_worker_binding_preflight(
            project_config=project_config,
            dry_run=False,
            apply_deployment=True,
            acknowledge_prefect_mutation=False,  # Missing gate
            approval_token="deployment",
            run_worker_smoke=False,
            prefect_client=mock_client,
        )

        # Should be blocked even though deployment is valid
        assert result.ok is False
        assert result.deployment_mutation == "none"
        assert result.prefect_runs_created == 0
        assert result.live_agents_started == 0
        assert any(e["type"] == "DEPLOYMENT_APPLY_NOT_ACKNOWLEDGED" for e in result.errors)

        # Run preflight without approval token (deployment exists and is valid)
        result = run_prefect_worker_binding_preflight(
            project_config=project_config,
            dry_run=False,
            apply_deployment=True,
            acknowledge_prefect_mutation=True,
            approval_token=None,  # Missing gate
            run_worker_smoke=False,
            prefect_client=mock_client,
        )

        # Should be blocked even though deployment is valid
        assert result.ok is False
        assert result.deployment_mutation == "none"
        assert result.prefect_runs_created == 0
        assert result.live_agents_started == 0
        assert any(e["type"] == "DEPLOYMENT_APPLY_NOT_APPROVED" for e in result.errors)

