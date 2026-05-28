from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

import pytest

from prefect_grace.platform.single_live_prefect_packet_pilot import (
    PACKET_ID,
    SingleLivePrefectPacketPilotResult,
)


def _args(tmp_path: Path) -> Namespace:
    return Namespace(
        project=Path("prefect_grace/project.yaml"),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packet-root",
        dry_run=True,
        execute_agent=False,
        i_understand_live_agent=False,
        timeout_seconds=1800,
        json=True,
    )


def _result(*, ok: bool = True, dry_run: bool = True) -> SingleLivePrefectPacketPilotResult:
    return SingleLivePrefectPacketPilotResult(
        ok=ok,
        project_key="astro-project",
        mode="single_live_prefect_packet_pilot",
        dry_run=dry_run,
        opt_in_confirmed=dry_run,
        state_root="/tmp/grace/state",
        worktree_root="/tmp/grace/worktrees",
        packet_root="/tmp/grace/packet-root",
        selected_packet_id=PACKET_ID,
        registry_before={},
        registry_after={},
        submit_plan={"packets_to_submit": [PACKET_ID]},
        deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
        work_queue_name=None,
        flow_run_id=None,
        flow_run_name="packet:SINGLE-LIVE-PREFECT-PACKET-PILOT-W01-SCRATCH",
        flow_run_url=None,
        prefect_runs_created=0,
        live_agents_started=0,
        domain_status=None,
        scope_verdict=None,
        changed_files=[],
        writes_outside_temp_roots=[],
        poll_events=[],
        warnings=[],
        errors=[] if ok else [{"code": "BLOCKED", "message": "blocked"}],
        bootstrap_apply_count=1,
        sync_plan={},
    )


def test_cli_json_dry_run_contract(tmp_path, capsys):
    """CLI returns the standard JSON envelope and preserves result == data."""
    args = _args(tmp_path)

    with patch(
        "prefect_grace.platform.single_live_prefect_packet_pilot.run_single_live_prefect_packet_pilot",
        return_value=_result(),
    ) as run_pilot:
        from prefect_grace.cli_commands.packet_execution import _cmd_run_single_live_prefect_packet_pilot

        with pytest.raises(SystemExit) as exc_info:
            _cmd_run_single_live_prefect_packet_pilot(args)

    assert exc_info.value.code == 0
    assert run_pilot.called
    call_kwargs = run_pilot.call_args[1]
    assert call_kwargs["dry_run"] is True
    assert call_kwargs["execute_agent"] is False

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["command"] == "run-single-live-prefect-packet-pilot"
    assert payload["result"] == payload["data"]
    assert payload["data"]["prefect_runs_created"] == 0
    assert payload["data"]["live_agents_started"] == 0


def test_cli_execute_agent_requires_no_dry_run(tmp_path, capsys):
    """Live agent flag without explicit --no-dry-run fails before platform call."""
    args = _args(tmp_path)
    args.execute_agent = True

    with patch(
        "prefect_grace.platform.single_live_prefect_packet_pilot.run_single_live_prefect_packet_pilot",
        return_value=_result(),
    ) as run_pilot:
        from prefect_grace.cli_commands.packet_execution import _cmd_run_single_live_prefect_packet_pilot

        with pytest.raises(SystemExit) as exc_info:
            _cmd_run_single_live_prefect_packet_pilot(args)

    assert exc_info.value.code == 2
    assert not run_pilot.called
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "MISSING_EXPLICIT_NO_DRY_RUN"


def test_cli_live_mode_passes_env_token(tmp_path, capsys, monkeypatch):
    """CLI passes the explicit env token only after --no-dry-run was acknowledged."""
    args = _args(tmp_path)
    args.dry_run = False
    args.execute_agent = True
    args.i_understand_live_agent = True
    setattr(args, "_no_dry_run_explicit", True)
    monkeypatch.setenv("GRACE_LIVE_PREFECT_PACKET_OPT_IN", "single-live-prefect")

    with patch(
        "prefect_grace.platform.single_live_prefect_packet_pilot.run_single_live_prefect_packet_pilot",
        return_value=_result(dry_run=False),
    ) as run_pilot:
        from prefect_grace.cli_commands.packet_execution import _cmd_run_single_live_prefect_packet_pilot

        with pytest.raises(SystemExit) as exc_info:
            _cmd_run_single_live_prefect_packet_pilot(args)

    assert exc_info.value.code == 0
    call_kwargs = run_pilot.call_args[1]
    assert call_kwargs["dry_run"] is False
    assert call_kwargs["execute_agent"] is True
    assert call_kwargs["acknowledge_live_agent"] is True
    assert call_kwargs["opt_in_token"] == "single-live-prefect"
    payload = json.loads(capsys.readouterr().out)
    assert payload["result"] == payload["data"]
