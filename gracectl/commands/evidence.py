from __future__ import annotations

import subprocess
import time
import json
from pathlib import Path

import typer

from ..config import load_config
from ..reporters.failure_packet import FailurePacketWriter
from ..reporters.result_store import ResultStore
from ..types import CheckResult, CommandSummary

evidence_app = typer.Typer(help="Evidence generation and review commands")


def _safe_log_name(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-") or "evidence"


def _run_capture(command: str, *, cwd: Path, log_path: Path) -> tuple[int, float, str]:
    start = time.time()
    completed = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    duration = time.time() - start
    output = completed.stdout or ""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(output, encoding="utf-8")
    return completed.returncode, duration, output


def _record_result(
    *,
    command_name: str,
    target: str,
    command: str,
    config_path: str | None,
    log_suffix: str,
) -> tuple[int, str]:
    config = load_config(Path(config_path)) if config_path else load_config()
    reporter = ResultStore(config.defaults.report_path, config.defaults.log_dir)
    failure_writer = FailurePacketWriter(config.defaults.log_dir / "failures")
    log_path = reporter.log_dir / f"evidence-{log_suffix}.log"
    code, duration, output = _run_capture(command, cwd=config.defaults.repo_root, log_path=log_path)
    result = CheckResult(
        id=log_suffix,
        label=command,
        status="passed" if code == 0 else "failed",
        duration_ms=int(duration * 1000),
        exit_code=code,
        stdout_path=log_path,
    )
    if code != 0:
        result.failure_packet = failure_writer.write(target, log_suffix, {"command": command})
    reporter.write(
        CommandSummary(
            command=command_name,
            target=target,
            status=result.status,
            passed=1 if code == 0 else 0,
            failed=0 if code == 0 else 1,
            checks=[result],
        )
    )
    return code, output


def _json_tail(output: str) -> str:
    for index in range(len(output)):
        if output[index] != "{":
            continue
        candidate = output[index:].strip()
        try:
            json.loads(candidate)
        except json.JSONDecodeError:
            continue
        return candidate + "\n"
    return output


@evidence_app.command("generate")
def evidence_generate(
    flows: str = typer.Option("today,week,admin,catalog", "--flows", help="Comma-separated canonical flows to emit."),
    window_minutes: int = typer.Option(30, "--window-minutes", min=1),
    config_path: str = typer.Option(None, "--config", help="Path to gracectl.yaml"),
) -> None:
    command = (
        "PYTHONPATH=. python3 scripts/generate_canonical_evidence.py "
        f"--flows {flows} --window-minutes {window_minutes}"
    )
    code, output = _record_result(
        command_name="evidence generate",
        target=flows,
        command=command,
        config_path=config_path,
        log_suffix=f"generate-{_safe_log_name(flows)}",
    )
    typer.echo(_json_tail(output), nl=False)
    if code != 0:
        raise typer.Exit(code=code)


@evidence_app.command("review")
def evidence_review(
    profile: str = typer.Argument(..., help="post_test_review profile, e.g. today-week or read-only"),
    since: str = typer.Option("30m", "--since", help="Freshness window passed to post_test_review.py"),
    report_format: str = typer.Option("json", "--report-format", help="json or md"),
    config_path: str = typer.Option(None, "--config", help="Path to gracectl.yaml"),
) -> None:
    command = (
        "PYTHONPATH=. python3 tools/post_test_review.py "
        f"--profile {profile} --since {since} --report-format {report_format}"
    )
    code, output = _record_result(
        command_name="evidence review",
        target=profile,
        command=command,
        config_path=config_path,
        log_suffix=f"review-{_safe_log_name(profile)}",
    )
    typer.echo(output, nl=False)
    if code != 0:
        raise typer.Exit(code=code)
