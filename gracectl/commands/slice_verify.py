from __future__ import annotations

from pathlib import Path

import typer

from ..config import load_config
from ..reporters.failure_packet import FailurePacketWriter
from ..reporters.result_store import ResultStore
from ..runners.process import ProcessRunner
from ..slice_registry import SliceRegistry
from ..types import CheckResult, CommandSummary

slice_app = typer.Typer(help="Slice-level operations")


def _run_commands(
    runner: ProcessRunner,
    failure_writer: FailurePacketWriter,
    reporter: ResultStore,
    slice_key: str,
    commands: list[str],
    prefix: str,
) -> list[CheckResult]:
    results: list[CheckResult] = []
    for idx, command in enumerate(commands, start=1):
        check_id = f"{prefix}.{idx}"
        log_path = reporter.log_dir / f"{slice_key.lower()}-{check_id}.log"
        code, duration = runner.run(command, log_path)
        result = CheckResult(
            id=check_id,
            label=command,
            status="passed" if code == 0 else "failed",
            duration_ms=int(duration * 1000),
            exit_code=code,
            stdout_path=log_path,
        )
        if code != 0:
            packet = failure_writer.write(slice_key, check_id, {"command": command})
            result.failure_packet = packet
        results.append(result)
    return results


@slice_app.command("verify")
def slice_verify(
    slice_key: str = typer.Argument(..., help="Slice identifier (e.g. M-NATAL-SUMMARY-LAYER)"),
    run_backend: bool = typer.Option(True, "--backend/--no-backend"),
    run_frontend: bool = typer.Option(True, "--frontend/--no-frontend"),
    run_replay: bool = typer.Option(True, "--replay/--no-replay"),
    config_path: str = typer.Option(None, "--config", help="Path to gracectl.yaml"),
) -> None:
    registry = SliceRegistry(load_config(Path(config_path)) if config_path else None)
    profile = registry.get(slice_key)
    defaults = registry.config.defaults
    reporter = ResultStore(defaults.report_path, defaults.log_dir)
    failure_writer = FailurePacketWriter(defaults.log_dir / "failures")
    runner = ProcessRunner(defaults.repo_root)

    checks: list[CheckResult] = []
    if run_backend and profile.commands.backend:
        checks.extend(
            _run_commands(runner, failure_writer, reporter, profile.key, profile.commands.backend, "backend")
        )
    if run_frontend and profile.commands.frontend:
        checks.extend(
            _run_commands(runner, failure_writer, reporter, profile.key, profile.commands.frontend, "frontend")
        )
    if run_replay and profile.commands.replay:
        checks.extend(
            _run_commands(runner, failure_writer, reporter, profile.key, profile.commands.replay, "replay")
        )

    passed = sum(1 for c in checks if c.status == "passed")
    failed = sum(1 for c in checks if c.status == "failed")
    summary = CommandSummary(
        command="slice verify",
        target=profile.key,
        status="passed" if failed == 0 else "failed",
        passed=passed,
        failed=failed,
        checks=checks,
    )
    reporter.write(summary)

    if failed:
        raise typer.Exit(code=1)



@slice_app.command("plan")
def slice_plan(
    slice_key: str = typer.Argument(..., help="Slice identifier"),
    config_path: str = typer.Option(None, "--config", help="Path to gracectl.yaml"),
) -> None:
    registry = SliceRegistry(load_config(Path(config_path)) if config_path else None)
    profile = registry.get(slice_key)

    typer.echo(f"Slice: {profile.key}")
    typer.echo(f"Title: {profile.title}")
    typer.echo(f"Description: {profile.description}")
    typer.echo(f"Gate: {profile.gate}")
    typer.echo("VM IDs:")
    for vm in profile.vm_ids:
        typer.echo(f"  - {vm}")
    typer.echo("Docs:")
    for doc in profile.docs:
        typer.echo(f"  - {doc}")
    typer.echo("Evidence:")
    for ev in profile.evidence:
        typer.echo(f"  - {ev}")
    typer.echo("Backend commands:")
    for cmd in profile.commands.backend:
        typer.echo(f"  - {cmd}")
    typer.echo("Frontend commands:")
    for cmd in profile.commands.frontend:
        typer.echo(f"  - {cmd}")
    typer.echo("Replay commands:")
    for cmd in profile.commands.replay:
        typer.echo(f"  - {cmd}")
    typer.echo("Watch flows: refer to top-level watch.flows config.")
