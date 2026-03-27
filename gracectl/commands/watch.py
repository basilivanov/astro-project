from __future__ import annotations

from pathlib import Path

import typer

from ..config import load_config
from ..reporters.failure_packet import FailurePacketWriter
from ..reporters.result_store import ResultStore
from ..runners.process import ProcessRunner
from ..slice_registry import SliceRegistry
from ..types import CheckResult, CommandSummary, WatchFlow

watch_app = typer.Typer(help="Watcher commands")


@watch_app.command("run")
def watch_run(
    slice_key: str = typer.Argument(..., help="Slice identifier"),
    config_path: str = typer.Option(None, "--config", help="Path to gracectl.yaml"),
) -> None:
    registry = SliceRegistry(load_config(Path(config_path)) if config_path else None)
    defaults = registry.config.defaults
    reporter = ResultStore(defaults.report_path, defaults.log_dir)
    failure_writer = FailurePacketWriter(defaults.log_dir / "failures")
    runner = ProcessRunner(defaults.repo_root)

    flows = _select_flows(registry.watch_flows, slice_key)
    if not flows:
        typer.echo(f"Slice {slice_key} has no watch flows configured.")
        raise typer.Exit(code=0)

    checks: list[CheckResult] = []
    for idx, flow in enumerate(flows, start=1):
        check_id = f"watcher.{idx}"
        command = _build_command(flow)
        log_path = reporter.log_dir / f"{slice_key.lower()}-{check_id}.log"
        code, duration = runner.run(command, log_path)
        result = CheckResult(
            id=check_id,
            label=f"{flow.id}: {command}",
            status="passed" if code == 0 else "failed",
            duration_ms=int(duration * 1000),
            exit_code=code,
            stdout_path=log_path,
        )
        if code != 0:
            packet = failure_writer.write(slice_key, check_id, {"command": command, "flow": flow.id})
            result.failure_packet = packet
        checks.append(result)

    passed = sum(1 for c in checks if c.status == "passed")
    failed = sum(1 for c in checks if c.status == "failed")
    summary = CommandSummary(
        command="watch run",
        target=slice_key,
        status="passed" if failed == 0 else "failed",
        passed=passed,
        failed=failed,
        checks=checks,
    )
    reporter.write(summary)

    if failed:
        raise typer.Exit(code=1)


def _select_flows(flows: list[WatchFlow], slice_key: str) -> list[WatchFlow]:
    if not flows:
        return []
    lookup = slice_key.upper()
    return [flow for flow in flows if not flow.slices or lookup in (s.upper() for s in flow.slices)]


def _build_command(flow: WatchFlow) -> str:
    parts = [flow.script]
    for key, value in flow.args.items():
        flag = str(key)
        if not flag.startswith("-"):
            flag = f"--{flag}"
        if isinstance(value, bool):
            if value:
                parts.append(flag)
        else:
            parts.append(f"{flag} {value}")
    return " ".join(parts)
