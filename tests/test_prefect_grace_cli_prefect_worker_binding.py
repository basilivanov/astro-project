"""
Tests for prefect_grace CLI prefect-worker-binding command.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from prefect_grace.platform.prefect_worker_binding import PrefectWorkerBindingResult


class TestPrefectWorkerBindingCLI:
    """Test CLI command for prefect-worker-binding."""

    def test_cli_dry_run_json_output(self, tmp_path, capsys):
        """Test CLI dry-run with JSON output."""
        # Create mock project config
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Mock the preflight function
        mock_result = PrefectWorkerBindingResult(
            ok=True,
            project_key="test-project",
            mode="prefect_worker_binding",
            dry_run=True,
            prefect_api_url="http://localhost:4200/api",
            prefect_version="3.6.25",
            server_healthy=True,
            work_pool_name="astro-process",
            work_pool_status="READY",
            work_pool_type="process",
            required_queues=["grace-live", "grace-monitoring"],
            queue_statuses={
                "grace-live": {"exists": True, "status": "READY"},
                "grace-monitoring": {"exists": True, "status": "READY"},
            },
            deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
            deployment_exists=True,
            deployment_work_pool_name="astro-process",
            deployment_work_queue_name="grace-live",
            deployment_parameters_valid=True,
            worker_runtime_smoke={"smoke_ran": False, "ok": None},
            deployment_mutation="none",
            deployment_apply_result=None,
            prefect_runs_created=0,
            live_agents_started=0,
            warnings=[],
            errors=[],
        )

        with patch("prefect_grace.platform.prefect_worker_binding.run_prefect_worker_binding_preflight", return_value=mock_result):
            from prefect_grace.cli_commands.prefect_worker_binding import _cmd_prefect_worker_binding

            # Create mock args
            args = Mock()
            args.project = project_config
            args.dry_run = True
            args.apply_deployment = False
            args.i_understand_prefect_mutation = False
            args.run_worker_smoke = False
            args.json = True

            with pytest.raises(SystemExit) as exc_info:
                _cmd_prefect_worker_binding(args)

            assert exc_info.value.code == 0

            captured = capsys.readouterr()
            output = json.loads(captured.out)

            assert output["ok"] is True
            assert output["command"] == "prefect-worker-binding"
            assert output["result"]["prefect_runs_created"] == 0
            assert output["result"]["live_agents_started"] == 0

    def test_cli_apply_without_approval_blocked(self, tmp_path, capsys):
        """Test that apply-deployment without approval is blocked."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        from prefect_grace.cli_commands.prefect_worker_binding import _cmd_prefect_worker_binding

        args = Mock()
        args.project = project_config
        args.dry_run = True
        args.apply_deployment = True
        args.i_understand_prefect_mutation = False
        args.run_worker_smoke = False
        args.json = False

        with pytest.raises(SystemExit) as exc_info:
            _cmd_prefect_worker_binding(args)

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "--i-understand-prefect-mutation" in captured.err

    def test_cli_apply_without_env_approval_blocked(self, tmp_path, capsys, monkeypatch):
        """Test that apply-deployment without env approval is blocked."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Ensure env var is not set
        monkeypatch.delenv("GRACE_PREFECT_BINDING_APPROVED", raising=False)

        from prefect_grace.cli_commands.prefect_worker_binding import _cmd_prefect_worker_binding

        args = Mock()
        args.project = project_config
        args.dry_run = True
        args.apply_deployment = True
        args.i_understand_prefect_mutation = True
        args.run_worker_smoke = False
        args.json = False

        with pytest.raises(SystemExit) as exc_info:
            _cmd_prefect_worker_binding(args)

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "GRACE_PREFECT_BINDING_APPROVED=deployment" in captured.err

    def test_cli_prefect_unavailable_fails_closed(self, tmp_path, capsys):
        """Test that CLI fails closed when Prefect is unavailable."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        mock_result = PrefectWorkerBindingResult(
            ok=False,
            project_key="test-project",
            mode="prefect_worker_binding",
            dry_run=True,
            prefect_api_url="",
            prefect_version=None,
            server_healthy=False,
            work_pool_name="astro-process",
            work_pool_status=None,
            work_pool_type=None,
            required_queues=["grace-live", "grace-monitoring"],
            queue_statuses={},
            deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
            deployment_exists=False,
            deployment_work_pool_name=None,
            deployment_work_queue_name=None,
            deployment_parameters_valid=False,
            worker_runtime_smoke={"smoke_ran": False, "ok": None},
            deployment_mutation="none",
            deployment_apply_result=None,
            prefect_runs_created=0,
            live_agents_started=0,
            warnings=[],
            errors=[{"type": "PREFECT_UNAVAILABLE", "message": "Prefect is not installed"}],
        )

        with patch("prefect_grace.platform.prefect_worker_binding.run_prefect_worker_binding_preflight", return_value=mock_result):
            from prefect_grace.cli_commands.prefect_worker_binding import _cmd_prefect_worker_binding

            args = Mock()
            args.project = project_config
            args.dry_run = True
            args.apply_deployment = False
            args.i_understand_prefect_mutation = False
            args.run_worker_smoke = False
            args.json = True

            with pytest.raises(SystemExit) as exc_info:
                _cmd_prefect_worker_binding(args)

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            output = json.loads(captured.out)

            assert output["ok"] is False
            assert len(output["errors"]) > 0
            assert output["result"]["prefect_runs_created"] == 0

    def test_cli_deployment_not_found_reports_would_register(self, tmp_path, capsys):
        """Test that missing deployment reports dry_run_would_register."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        mock_result = PrefectWorkerBindingResult(
            ok=False,
            project_key="test-project",
            mode="prefect_worker_binding",
            dry_run=True,
            prefect_api_url="http://localhost:4200/api",
            prefect_version="3.6.25",
            server_healthy=True,
            work_pool_name="astro-process",
            work_pool_status="READY",
            work_pool_type="process",
            required_queues=["grace-live", "grace-monitoring"],
            queue_statuses={
                "grace-live": {"exists": True, "status": "READY"},
                "grace-monitoring": {"exists": True, "status": "READY"},
            },
            deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
            deployment_exists=False,
            deployment_work_pool_name=None,
            deployment_work_queue_name=None,
            deployment_parameters_valid=False,
            worker_runtime_smoke={"smoke_ran": False, "ok": None},
            deployment_mutation="dry_run_would_register",
            deployment_apply_result=None,
            prefect_runs_created=0,
            live_agents_started=0,
            warnings=[],
            errors=[{"type": "DEPLOYMENT_NOT_FOUND", "message": "Deployment not found"}],
        )

        with patch("prefect_grace.platform.prefect_worker_binding.run_prefect_worker_binding_preflight", return_value=mock_result):
            from prefect_grace.cli_commands.prefect_worker_binding import _cmd_prefect_worker_binding

            args = Mock()
            args.project = project_config
            args.dry_run = True
            args.apply_deployment = False
            args.i_understand_prefect_mutation = False
            args.run_worker_smoke = False
            args.json = True

            with pytest.raises(SystemExit) as exc_info:
                _cmd_prefect_worker_binding(args)

            assert exc_info.value.code == 1

            captured = capsys.readouterr()
            output = json.loads(captured.out)

            assert output["result"]["deployment_mutation"] == "dry_run_would_register"
            assert output["result"]["prefect_runs_created"] == 0

    def test_cli_approved_apply_propagates_args(self, tmp_path, capsys, monkeypatch):
        """Test that CLI propagates --apply flag to preflight correctly."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Set approval env var
        monkeypatch.setenv("GRACE_PREFECT_BINDING_APPROVED", "deployment")

        mock_result = PrefectWorkerBindingResult(
            ok=True,
            project_key="test-project",
            mode="prefect_worker_binding",
            dry_run=False,
            prefect_api_url="http://localhost:4200/api",
            prefect_version="3.6.25",
            server_healthy=True,
            work_pool_name="astro-process",
            work_pool_status="READY",
            work_pool_type="process",
            required_queues=["grace-live", "grace-monitoring"],
            queue_statuses={
                "grace-live": {"exists": True, "status": "READY"},
                "grace-monitoring": {"exists": True, "status": "READY"},
            },
            deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
            deployment_exists=True,
            deployment_work_pool_name="astro-process",
            deployment_work_queue_name="grace-live",
            deployment_parameters_valid=True,
            worker_runtime_smoke={"smoke_ran": False, "ok": None},
            deployment_mutation="applied",
            deployment_apply_result=None,
            prefect_runs_created=0,
            live_agents_started=0,
            warnings=["Deployment applied: test-deployment-id"],
            errors=[],
        )

        with patch("prefect_grace.platform.prefect_worker_binding.run_prefect_worker_binding_preflight", return_value=mock_result) as mock_preflight:
            from prefect_grace.cli_commands.prefect_worker_binding import _cmd_prefect_worker_binding

            args = Mock()
            args.project = project_config
            args.apply = True  # --apply flag
            args.dry_run = False
            args.apply_deployment = True
            args.i_understand_prefect_mutation = True
            args.run_worker_smoke = False
            args.json = True

            with pytest.raises(SystemExit) as exc_info:
                _cmd_prefect_worker_binding(args)

            assert exc_info.value.code == 0

            # Verify preflight was called with dry_run=False
            assert mock_preflight.called
            call_kwargs = mock_preflight.call_args[1]
            assert call_kwargs["dry_run"] is False
            assert call_kwargs["apply_deployment"] is True

            captured = capsys.readouterr()
            output = json.loads(captured.out)

            assert output["ok"] is True
            assert output["result"]["dry_run"] is False
            assert output["result"]["deployment_mutation"] == "applied"
            assert output["result"]["prefect_runs_created"] == 0
            assert output["result"]["live_agents_started"] == 0

    def test_cli_plain_apply_deployment_produces_dry_run_plan(self, tmp_path, capsys, monkeypatch):
        """Test that plain --apply-deployment without --apply produces dry-run plan."""
        project_config = tmp_path / "grace.yaml"
        project_config.write_text("project_key: test-project\n")

        # Set approval env var
        monkeypatch.setenv("GRACE_PREFECT_BINDING_APPROVED", "deployment")

        mock_result = PrefectWorkerBindingResult(
            ok=False,
            project_key="test-project",
            mode="prefect_worker_binding",
            dry_run=True,
            prefect_api_url="http://localhost:4200/api",
            prefect_version="3.6.25",
            server_healthy=True,
            work_pool_name="astro-process",
            work_pool_status="READY",
            work_pool_type="process",
            required_queues=["grace-live", "grace-monitoring"],
            queue_statuses={
                "grace-live": {"exists": True, "status": "READY"},
                "grace-monitoring": {"exists": True, "status": "READY"},
            },
            deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
            deployment_exists=False,
            deployment_work_pool_name=None,
            deployment_work_queue_name=None,
            deployment_parameters_valid=False,
            worker_runtime_smoke={"smoke_ran": False, "ok": None},
            deployment_mutation="dry_run_would_apply",
            deployment_apply_result=None,
            prefect_runs_created=0,
            live_agents_started=0,
            warnings=[],
            errors=[{"type": "DEPLOYMENT_NOT_FOUND", "message": "Deployment not found"}],
        )

        with patch("prefect_grace.platform.prefect_worker_binding.run_prefect_worker_binding_preflight", return_value=mock_result) as mock_preflight:
            from prefect_grace.cli_commands.prefect_worker_binding import _cmd_prefect_worker_binding

            args = Mock()
            args.project = project_config
            args.apply = False  # No --apply flag
            args.dry_run = True
            args.apply_deployment = True
            args.i_understand_prefect_mutation = True
            args.run_worker_smoke = False
            args.json = True

            with pytest.raises(SystemExit) as exc_info:
                _cmd_prefect_worker_binding(args)

            assert exc_info.value.code == 1

            # Verify preflight was called with dry_run=True
            assert mock_preflight.called
            call_kwargs = mock_preflight.call_args[1]
            assert call_kwargs["dry_run"] is True
            assert call_kwargs["apply_deployment"] is True

            captured = capsys.readouterr()
            output = json.loads(captured.out)

            assert output["ok"] is False
            assert output["result"]["dry_run"] is True
            assert output["result"]["deployment_mutation"] == "dry_run_would_apply"
            assert output["result"]["prefect_runs_created"] == 0
            assert output["result"]["live_agents_started"] == 0
