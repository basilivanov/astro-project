from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest

from prefect_grace.platform.single_astro_packet_pilot import SingleAstroPacketPilotResult


def _args(tmp_path: Path) -> Namespace:
    return Namespace(
        project=Path("prefect_grace/project.yaml"),
        state_root=tmp_path / "state",
        worktree_root=tmp_path / "worktrees",
        packet_root=tmp_path / "packet-root",
        packet="FEAT-ASTRO-SAFE-PILOT-W01-NARROW",
        dry_run=True,
        execute_agent=False,
        i_understand_live_agent=False,
        timeout_seconds=1800,
        json=True,
    )


def _result(*, ok: bool = True, dry_run: bool = True) -> SingleAstroPacketPilotResult:
    return SingleAstroPacketPilotResult(
        ok=ok,
        project_key="astro-project",
        mode="single_astro_packet_pilot",
        dry_run=dry_run,
        opt_in_confirmed=dry_run,
        state_root="/tmp/grace/state",
        worktree_root="/tmp/grace/worktrees",
        packet_root="/tmp/grace/packet-root",
        selected_packet_id="FEAT-ASTRO-SAFE-PILOT-W01-NARROW",
        registry_before={},
        registry_after={},
        submit_plan={"packets_to_submit": ["FEAT-ASTRO-SAFE-PILOT-W01-NARROW"]},
        deployment_name="prefect-grace-managed-packet-runner/live-managed-packet-runner",
        work_queue_name=None,
        flow_run_id=None,
        flow_run_name="packet:FEAT-ASTRO-SAFE-PILOT-W01-NARROW",
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
    )


def test_cli_json_dry_run_contract(tmp_path, capsys):
    """CLI returns the standard JSON envelope and preserves result == data."""
    args = _args(tmp_path)

    with patch(
        "prefect_grace.platform.single_astro_packet_pilot.run_single_astro_packet_pilot",
        return_value=_result(),
    ) as run_pilot:
        from prefect_grace.cli_commands.packet_execution import _cmd_run_single_astro_packet_pilot

        with pytest.raises(SystemExit) as exc_info:
            _cmd_run_single_astro_packet_pilot(args)

    assert exc_info.value.code == 0
    assert run_pilot.called
    call_kwargs = run_pilot.call_args[1]
    assert call_kwargs["dry_run"] is True
    assert call_kwargs["execute_agent"] is False
    assert call_kwargs["packet_id"] == "FEAT-ASTRO-SAFE-PILOT-W01-NARROW"

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["command"] == "run-single-astro-packet-pilot"
    assert payload["result"] == payload["data"]
    assert payload["data"]["prefect_runs_created"] == 0
    assert payload["data"]["live_agents_started"] == 0


def test_cli_execute_agent_requires_no_dry_run(tmp_path, capsys):
    """Live agent flag without explicit --no-dry-run fails before platform call."""
    args = _args(tmp_path)
    args.execute_agent = True

    with patch(
        "prefect_grace.platform.single_astro_packet_pilot.run_single_astro_packet_pilot",
        return_value=_result(),
    ) as run_pilot:
        from prefect_grace.cli_commands.packet_execution import _cmd_run_single_astro_packet_pilot

        with pytest.raises(SystemExit) as exc_info:
            _cmd_run_single_astro_packet_pilot(args)

    assert exc_info.value.code == 2
    assert not run_pilot.called
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "MISSING_EXPLICIT_NO_DRY_RUN"


def test_cli_live_mode_passes_env_token(tmp_path, capsys, monkeypatch):
    """CLI passes the Astro env token only after --no-dry-run was acknowledged."""
    args = _args(tmp_path)
    args.dry_run = False
    args.execute_agent = True
    args.i_understand_live_agent = True
    setattr(args, "_no_dry_run_explicit", True)
    monkeypatch.setenv("GRACE_ASTRO_PACKET_OPT_IN", "single-astro-packet")

    with patch(
        "prefect_grace.platform.single_astro_packet_pilot.run_single_astro_packet_pilot",
        return_value=_result(dry_run=False),
    ) as run_pilot:
        from prefect_grace.cli_commands.packet_execution import _cmd_run_single_astro_packet_pilot

        with pytest.raises(SystemExit) as exc_info:
            _cmd_run_single_astro_packet_pilot(args)

    assert exc_info.value.code == 0
    call_kwargs = run_pilot.call_args[1]
    assert call_kwargs["dry_run"] is False
    assert call_kwargs["execute_agent"] is True
    assert call_kwargs["acknowledge_live_agent"] is True
    assert call_kwargs["opt_in_token"] == "single-astro-packet"
    payload = json.loads(capsys.readouterr().out)
    assert payload["result"] == payload["data"]


def test_real_project_cli_dry_run_output_is_bounded(tmp_path):
    """Real project dry-run emits bounded registry summaries, not full registry maps."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "prefect_grace.cli",
            "run-single-astro-packet-pilot",
            "--project",
            "prefect_grace/project.yaml",
            "--state-root",
            str(tmp_path / "state-root"),
            "--worktree-root",
            str(tmp_path / "worktrees"),
            "--packet-root",
            str(tmp_path / "packet-root"),
            "--dry-run",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    assert len(result.stdout.splitlines()) < 500
    assert len(result.stdout.encode("utf-8")) < 40000
    assert "allowed_write_scope" not in result.stdout

    payload = json.loads(result.stdout)
    data = payload["data"]
    assert payload["result"] == data
    assert payload["ok"] is True
    assert data["selected_packet_id"]
    assert data["prefect_runs_created"] == 0
    assert data["live_agents_started"] == 0
    assert data["registry_before"]["records_included"] is False
    assert data["registry_after"]["records_included"] is False
    assert "total_packets" in data["registry_before"]
    assert "status_counts" in data["registry_before"]
    assert data["registry_before"]["selected_packet"]["packet_id"] == data["selected_packet_id"]
    assert data["registry_before"]["selected_packet"]["allowed_scope_count"] > 0
    assert data["plan_count"] == 1
