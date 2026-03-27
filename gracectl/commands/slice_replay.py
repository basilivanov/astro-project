from __future__ import annotations

from pathlib import Path

import typer

from .slice_verify import slice_app
from ..config import load_config
from ..reporters.result_store import ResultStore
from ..runners.process import ProcessRunner
from ..slice_registry import SliceRegistry
from ..types import CheckResult, CommandSummary


@slice_app.command("replay")
def slice_replay(
    slice_key: str = typer.Argument(..., help="Slice identifier"),
    config_path: str = typer.Option(None, "--config", help="Path to gracectl.yaml"),
) -> None:
    registry = SliceRegistry(load_config(Path(config_path)) if config_path else None)
    profile = registry.get(slice_key)
    defaults = registry.config.defaults
    reporter = ResultStore(defaults.report_path, defaults.log_dir)
    runner = ProcessRunner(defaults.repo_root)

    if not profile.commands.replay:
        typer.echo(f"Slice {slice_key} has no replay helpers configured.")
        raise typer.Exit(code=0)

    checks: list[CheckResult] = []
    for idx, command in enumerate(profile.commands.replay, start=1):
        check_id = f"replay.{idx}"
        log_path = reporter.log_dir / f"{profile.key.lower()}-{check_id}.log"
        code, duration = runner.run(command, log_path)
        checks.append(
            CheckResult(
                id=check_id,
                label=command,
                status="passed" if code == 0 else "failed",
                duration_ms=int(duration * 1000),
                exit_code=code,
                stdout_path=log_path,
            )
        )

    passed = sum(1 for c in checks if c.status == "passed")
    failed = sum(1 for c in checks if c.status == "failed")
    summary = CommandSummary(
        command="slice replay",
        target=profile.key,
        status="passed" if failed == 0 else "failed",
        passed=passed,
        failed=failed,
        checks=checks,
    )
    reporter.write(summary)

    if failed:
        raise typer.Exit(code=1)
