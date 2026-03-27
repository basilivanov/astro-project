from __future__ import annotations

from pathlib import Path

import typer

from ..config import load_config
from ..reporters.failure_packet import FailurePacketWriter
from ..reporters.result_store import ResultStore
from ..runners.process import ProcessRunner
from ..slice_registry import SliceRegistry
from ..types import CheckResult, CommandSummary

env_app = typer.Typer(help="Environment diagnostics")


@env_app.command("check")
def env_check(config_path: str = typer.Option(None, "--config", help="Path to gracectl.yaml")) -> None:
    registry = SliceRegistry(load_config(Path(config_path)) if config_path else None)
    defaults = registry.config.defaults
    reporter = ResultStore(defaults.report_path, defaults.log_dir)
    failure_writer = FailurePacketWriter(defaults.log_dir / "failures")
    runner = ProcessRunner()
    checks: list[CheckResult] = []

    def run_check(check_id: str, label: str, command: str) -> CheckResult:
        log_path = reporter.log_dir / f"{check_id}.log"
        code, duration = runner.run(command, log_path)
        result = CheckResult(
            id=check_id,
            label=label,
            status="passed" if code == 0 else "failed",
            duration_ms=int(duration * 1000),
            exit_code=code,
            stdout_path=log_path,
        )
        if code != 0:
            packet = failure_writer.write("ENV", check_id, {"command": command})
            result.failure_packet = packet
        return result

    checks.append(run_check("docker.ps", "docker ps", "docker ps"))
    checks.append(
        run_check(
            "backend.health",
            "backend /health",
            f"docker exec {defaults.backend_container} curl -fsS --max-time 5 http://localhost:8000/health",
        )
    )

    frontend_probe = run_check(
        "frontend.reports",
        "frontend /reports",
        f"docker exec {defaults.frontend_container} curl -fsS --max-time 5 http://localhost:3000/reports",
    )
    checks.append(frontend_probe)

    if frontend_probe.status == "failed":
        restart = run_check(
            "frontend.restart",
            "restart frontend",
            f"docker restart {defaults.frontend_container}",
        )
        checks.append(restart)
        if restart.status == "passed":
            checks.append(
                run_check(
                    "frontend.reports.retry",
                    "frontend /reports (retry)",
                    f"docker exec {defaults.frontend_container} curl -fsS --max-time 5 http://localhost:3000/reports",
                )
            )

    passed = sum(1 for c in checks if c.status == "passed")
    failed = sum(1 for c in checks if c.status == "failed")
    summary = CommandSummary(
        command="env check",
        target="environment",
        status="passed" if failed == 0 else "failed",
        passed=passed,
        failed=failed,
        checks=checks,
    )
    reporter.write(summary)

    if failed:
        raise typer.Exit(code=1)
