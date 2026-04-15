from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Any

import yaml

from prefect_grace.models import FrontendVisualVerdict, ObservabilityVerdict, TestVerdict
from prefect_grace.tasks.agent_output_parser import read_agent_message
from prefect_grace.tasks.state_store import find_record, update_record
from prefect_grace.tasks.workdir import resolve_execution_workdir

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).resolve().parents[1] / "agent_profiles.yaml"
RUNS_DIR = Path(__file__).resolve().parents[1] / "state" / "runs"

POST_TEST_REVIEW_MAP = {
    "PASS_CLEAN": ObservabilityVerdict.CLEAN.value,
    "PASS_WITH_EXPECTED_DEGRADATION": ObservabilityVerdict.DEGRADED_BUT_EXPECTED.value,
    "PASS_PRIMARY_LIVE_CLEAN_WRAPPER_NOISE": ObservabilityVerdict.DEGRADED_BUT_EXPECTED.value,
    "FAIL_OBSERVABILITY_GATE": ObservabilityVerdict.UNEXPECTED_DEGRADATION.value,
    "FAIL_NO_EVIDENCE": ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value,
    "FAIL_PRIMARY_LIVE_SESSION_MISMATCH": ObservabilityVerdict.UNEXPECTED_DEGRADATION.value,
}
VISUAL_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".html"}


@dataclass(frozen=True)
class PlannedVerifierStep:
    phase: str
    command: str


def load_agent_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def build_verifier_plan(packet: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    hints = dict(packet.get("execution_hints") or {})
    verification_cfg = dict(config.get("verification") or {})
    backend_profiles = dict(verification_cfg.get("backend_profiles") or {})
    frontend_profiles = dict(verification_cfg.get("frontend_profiles") or {})
    observability_profiles = dict(verification_cfg.get("observability_profiles") or {})

    backend_commands = list(hints.get("backend_commands") or [])
    backend_profile = hints.get("backend_profile")
    if backend_profile and not backend_commands:
        command = backend_profiles.get(str(backend_profile))
        if command:
            backend_commands.append(str(command))

    frontend_commands = list(hints.get("frontend_commands") or [])
    frontend_profile = hints.get("frontend_profile")
    if frontend_profile and not frontend_commands:
        command = frontend_profiles.get(str(frontend_profile))
        if command:
            frontend_commands.append(str(command))

    observability_commands = list(hints.get("observability_commands") or [])
    observability_profile = hints.get("observability_profile")
    if observability_profile and not observability_commands:
        command = str(observability_profiles.get(str(observability_profile)) or "").strip()
        if command:
            if hints.get("include_day_live_canary"):
                command = f"{command} --include-day-live-canary"
            observability_commands.append(command)

    artifact_globs = list(hints.get("artifact_globs") or verification_cfg.get("default_artifact_globs") or [])
    touches_frontend = bool(hints.get("touches_frontend"))
    requires_frontend_visual = bool(hints.get("requires_frontend_visual") or touches_frontend)

    steps = [
        *[PlannedVerifierStep("backend", command) for command in backend_commands],
        *[PlannedVerifierStep("frontend", command) for command in frontend_commands],
        *[PlannedVerifierStep("observability", command) for command in observability_commands],
    ]
    return {
        "steps": steps,
        "touches_frontend": touches_frontend,
        "requires_frontend_visual": requires_frontend_visual,
        "artifact_globs": artifact_globs,
        "observability_profile": observability_profile,
    }


def validate_verifier_plan(packet: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    hints = dict(packet.get("execution_hints") or {})

    for key in ("backend_commands", "frontend_commands", "observability_commands"):
        value = hints.get(key)
        if value is None:
            continue
        if not isinstance(value, list):
            issues.append(f"{key} must be a list of shell commands.")
            continue
        for item in value:
            if not isinstance(item, str) or not item.strip():
                issues.append(f"{key} contains an empty or non-string command.")
            elif item.strip().startswith("{") or item.strip().startswith("["):
                issues.append(f"{key} contains non-executable structured text instead of a shell command.")

    if plan["touches_frontend"] and not any(step.phase == "frontend" for step in plan["steps"]):
        issues.append("Frontend-touching verifier packet is missing explicit frontend commands.")
    if plan["requires_frontend_visual"] and not plan.get("artifact_globs"):
        issues.append("Frontend visual verification requires artifact globs for screenshot/video evidence.")
    if not any(step.phase == "observability" for step in plan["steps"]):
        issues.append("Verifier packet is missing explicit observability commands.")

    return issues


def build_verifier_message(
    *,
    commands_run: list[str],
    test_verdict: str,
    observability_verdict: str,
    frontend_visual_verdict: str,
    evidence_paths: list[str],
    blocking_issues: list[str],
) -> str:
    commands_text = "\n".join(f"- {command}" for command in commands_run) or "- none"
    evidence_text = "\n".join(f"- {path}" for path in evidence_paths) or "- none"
    issues_text = "\n".join(f"- {issue}" for issue in blocking_issues) or "- none"
    payload = {
        "test_verdict": test_verdict,
        "observability_verdict": observability_verdict,
        "frontend_visual_verdict": frontend_visual_verdict,
        "commands_run": commands_run,
        "evidence_paths": evidence_paths,
        "blocking_issues": blocking_issues,
    }
    return (
        "## Commands Run\n"
        f"{commands_text}\n\n"
        "## Test Verdict\n"
        f"{test_verdict}\n\n"
        "## Evidence Reviewed\n"
        f"{evidence_text}\n\n"
        "## Observability Verdict\n"
        f"{observability_verdict}\n\n"
        "## Frontend Visual Verdict\n"
        f"{frontend_visual_verdict}\n\n"
        "## Blocking Issues\n"
        f"{issues_text}\n\n"
        "FINAL_VERIFIER_EVIDENCE_JSON\n"
        f"{json.dumps(payload, ensure_ascii=False)}\n"
        "END_FINAL_VERIFIER_EVIDENCE_JSON\n"
    )


def _sanitize_filename(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in value).strip("-") or "packet"


def _run_shell_command(command: str, *, cwd: str, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-lc", command],
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )


def _collect_artifacts(globs: list[str], *, root_dir: Path, started_at: datetime) -> tuple[list[str], list[str]]:
    evidence_paths: list[str] = []
    visual_paths: list[str] = []
    threshold = started_at.timestamp() - 1
    for pattern in globs:
        iterator = root_dir.glob(pattern) if not Path(pattern).is_absolute() else [Path(pattern)]
        for path in iterator:
            if not path.exists() or not path.is_file():
                continue
            try:
                if path.stat().st_mtime < threshold:
                    continue
            except OSError:
                continue
            resolved = str(path.resolve())
            if resolved not in evidence_paths:
                evidence_paths.append(resolved)
            if path.suffix.lower() in VISUAL_EXTENSIONS and resolved not in visual_paths:
                visual_paths.append(resolved)
    return evidence_paths, visual_paths


def _observability_from_stdout(stdout_text: str) -> tuple[str, list[str], list[str]]:
    text = stdout_text.strip()
    if not text:
        return ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value, [], ["Observability review produced no output."]
    if text.startswith("# Post-test observability gate"):
        verdict = ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value
        issues: list[str] = []
        evidence: list[str] = []
        first_line = text.splitlines()[0].strip()
        if "PASS_CLEAN" in first_line:
            verdict = ObservabilityVerdict.CLEAN.value
        elif "PASS_WITH_EXPECTED_DEGRADATION" in first_line or "PASS_PRIMARY_LIVE_CLEAN_WRAPPER_NOISE" in first_line:
            verdict = ObservabilityVerdict.DEGRADED_BUT_EXPECTED.value
        elif "FAIL_OBSERVABILITY_GATE" in first_line or "FAIL_PRIMARY_LIVE_SESSION_MISMATCH" in first_line:
            verdict = ObservabilityVerdict.UNEXPECTED_DEGRADATION.value
        elif "FAIL_NO_EVIDENCE" in first_line:
            verdict = ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value
        current_flow = ""
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if line.startswith('## FLOW-'):
                current_flow = line.replace('## ', '').strip()
                evidence.append(current_flow)
            elif line.startswith('- alerts:'):
                alert = line.removeprefix('- alerts:').strip()
                if alert and alert != '-':
                    issues.append(f"{current_flow or 'observability'}: {alert}")
            elif line.startswith('- sample_trace_id:') or line.startswith('- sample_request_id:') or line.startswith('- sample_report_id:'):
                value = line.split(':', 1)[1].strip().strip('`')
                if value and value != 'None':
                    evidence.append(f"{current_flow or 'observability'}:{line[2:]}")
        return verdict, evidence, issues
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value, [], ["Observability review output is not valid JSON or markdown gate summary."]
    verdict = POST_TEST_REVIEW_MAP.get(str(payload.get("verdict") or "").strip(), ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value)
    evidence: list[str] = []
    issues: list[str] = []
    for flow in payload.get("flows") or []:
        flow_id = str(flow.get("flow_id") or "").strip()
        status = str(flow.get("status") or "").strip()
        trace_id = str(flow.get("sample_trace_id") or "").strip()
        request_id = str(flow.get("sample_request_id") or "").strip()
        report_id = str(flow.get("sample_report_id") or "").strip()
        if flow_id:
            evidence.append(f"{flow_id}:status={status}")
        if trace_id:
            evidence.append(f"{flow_id}:trace_id={trace_id}")
        if request_id:
            evidence.append(f"{flow_id}:request_id={request_id}")
        if report_id and report_id != "None":
            evidence.append(f"{flow_id}:report_id={report_id}")
        for alert in flow.get("alerts") or []:
            if alert:
                issues.append(f"{flow_id}: {alert}")
    return verdict, evidence, issues


def _message_evidence_paths(packet: dict[str, Any]) -> list[str]:
    related_runs: list[dict[str, Any]] = []
    if isinstance(packet.get("last_execution_run"), dict):
        related_runs.append(dict(packet.get("last_execution_run") or {}))
    if isinstance(packet.get("last_codex_run"), dict):
        related_runs.append(dict(packet.get("last_codex_run") or {}))
    paths: list[str] = []
    for run in related_runs:
        message = read_agent_message(run.get("last_message_path"), run.get("stdout_path"))
        if not message:
            continue
        for match in re.findall(r"\(([^)]+\.(?:png|jpg|jpeg|webp|html))\)", message):
            if Path(match).exists() and match not in paths:
                paths.append(match)
        for match in re.findall(r"(/[^\s]+\.(?:png|jpg|jpeg|webp|html))", message):
            clean = match.rstrip('.,')
            if Path(clean).exists() and clean not in paths:
                paths.append(clean)
    return paths


def run_verifier_for_packet(packet_id: str, *, dry_run: bool = False, timeout_seconds: int = 3600) -> dict[str, Any]:
    packet = find_record("packets", "packets", "packet_id", packet_id)
    if str(packet.get("role") or "") != "verifier":
        raise ValueError(f"Packet {packet_id} is not a verifier packet")
    config = load_agent_config()
    plan = build_verifier_plan(packet, config)
    plan_issues = validate_verifier_plan(packet, plan)
    execution_hints = dict(packet.get("execution_hints") or {})
    configured_workdir = str(execution_hints.get("workdir") or ROOT_DIR)
    workdir = resolve_execution_workdir(configured_workdir)

    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{_sanitize_filename(packet_id)}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = run_dir / "stdout.jsonl"
    stderr_path = run_dir / "stderr.log"
    last_message_path = run_dir / "last-message.md"
    plan_path = run_dir / "verifier-plan.json"

    plan_payload = {
        "packet_id": packet_id,
        "workdir": str(workdir),
        "steps": [{"phase": step.phase, "command": step.command} for step in plan["steps"]],
        "touches_frontend": plan["touches_frontend"],
        "requires_frontend_visual": plan["requires_frontend_visual"],
        "artifact_globs": plan["artifact_globs"],
        "observability_profile": plan["observability_profile"],
    }
    plan_path.write_text(json.dumps(plan_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if plan_issues:
        message = build_verifier_message(
            commands_run=[],
            test_verdict=TestVerdict.FAILED.value,
            observability_verdict=ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value,
            frontend_visual_verdict=FrontendVisualVerdict.NOT_APPLICABLE.value,
            evidence_paths=[str(plan_path)],
            blocking_issues=plan_issues,
        )
        last_message_path.write_text(message, encoding="utf-8")
        result = {
            "packet_id": packet_id,
            "returncode": 0,
            "runner": "verifier",
            "command": [],
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "last_message_path": str(last_message_path),
            "started_at": datetime.now(timezone.utc).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "steps": [],
            "pipeline_invalid": True,
            "pipeline_invalid_reasons": plan_issues,
        }
        stdout_path.write_text(json.dumps({"packet_id": packet_id, "pipeline_invalid": plan_issues}, ensure_ascii=False), encoding="utf-8")
        stderr_path.write_text("\n".join(plan_issues), encoding="utf-8")
        update_record(
            "packets",
            "packets",
            "packet_id",
            packet_id,
            {
                "last_verifier_run": result,
                "last_execution_run": result,
                "status": "blocked",
            },
        )
        return result

    started_at = datetime.now(timezone.utc)
    command_results: list[dict[str, Any]] = []
    commands_run: list[str] = []
    blocking_issues: list[str] = []
    evidence_paths: list[str] = [str(plan_path)]
    visual_paths: list[str] = []
    observability_verdict = ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value
    observability_evidence: list[str] = []
    infrastructure_error: str | None = None

    try:
        if dry_run:
            stdout_path.write_text(
                json.dumps({"dry_run": True, "packet_id": packet_id, "steps": plan_payload["steps"]}, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            stderr_path.write_text("", encoding="utf-8")
            last_message_path.write_text("DRY RUN: verifier runner was not launched.\n", encoding="utf-8")
            returncode = 0
        else:
            stderr_chunks: list[str] = []
            for index, step in enumerate(plan["steps"], start=1):
                commands_run.append(step.command)
                completed = _run_shell_command(step.command, cwd=str(workdir), timeout_seconds=timeout_seconds)
                step_stdout = run_dir / f"{index:02d}-{step.phase}.stdout.log"
                step_stderr = run_dir / f"{index:02d}-{step.phase}.stderr.log"
                step_stdout.write_text(completed.stdout or "", encoding="utf-8")
                step_stderr.write_text(completed.stderr or "", encoding="utf-8")
                evidence_paths.extend([str(step_stdout), str(step_stderr)])
                command_results.append(
                    {
                        "phase": step.phase,
                        "command": step.command,
                        "returncode": completed.returncode,
                        "stdout_path": str(step_stdout),
                        "stderr_path": str(step_stderr),
                    }
                )
                if completed.stderr:
                    stderr_chunks.append(f"$ {step.command}\n{completed.stderr}")
                if step.phase in {"backend", "frontend"} and completed.returncode != 0:
                    blocking_issues.append(f"{step.phase} verification command failed: {step.command}")
                if step.phase == "observability":
                    parsed_verdict, parsed_evidence, parsed_issues = _observability_from_stdout(completed.stdout or "")
                    observability_verdict = parsed_verdict
                    observability_evidence.extend(parsed_evidence)
                    blocking_issues.extend(parsed_issues)
                    if completed.returncode != 0 and not parsed_issues:
                        blocking_issues.append(f"Observability command failed: {step.command}")
            stdout_path.write_text(json.dumps({"packet_id": packet_id, "steps": command_results}, ensure_ascii=False, indent=2), encoding="utf-8")
            stderr_path.write_text("\n\n".join(stderr_chunks), encoding="utf-8")
            returncode = 0
    except Exception as exc:
        infrastructure_error = str(exc)
        stdout_path.write_text(json.dumps({"packet_id": packet_id, "error": infrastructure_error}, ensure_ascii=False), encoding="utf-8")
        stderr_path.write_text(infrastructure_error, encoding="utf-8")
        returncode = 1

    test_commands = [item for item in command_results if item["phase"] in {"backend", "frontend"}]
    if infrastructure_error:
        test_verdict = TestVerdict.FAILED.value
        observability_verdict = ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value
        blocking_issues.append(f"Verifier runner infrastructure failure: {infrastructure_error}")
    elif any(item["returncode"] != 0 for item in test_commands):
        test_verdict = TestVerdict.FAILED.value
    elif test_commands:
        test_verdict = TestVerdict.PASSED.value
    else:
        test_verdict = TestVerdict.NOT_RUN.value

    artifact_evidence, collected_visual_paths = _collect_artifacts(
        plan["artifact_globs"],
        root_dir=workdir,
        started_at=started_at,
    )
    explicit_visual_paths = _message_evidence_paths(packet)
    for path in artifact_evidence:
        if path not in evidence_paths:
            evidence_paths.append(path)
    visual_paths.extend(path for path in collected_visual_paths if path not in visual_paths)
    visual_paths.extend(path for path in explicit_visual_paths if path not in visual_paths)
    for item in observability_evidence:
        if item not in evidence_paths:
            evidence_paths.append(item)
    for item in explicit_visual_paths:
        if item not in evidence_paths:
            evidence_paths.append(item)

    if plan["touches_frontend"]:
        if any(item["phase"] == "frontend" and item["returncode"] != 0 for item in command_results):
            frontend_visual_verdict = FrontendVisualVerdict.INSUFFICIENT.value
        elif visual_paths:
            frontend_visual_verdict = FrontendVisualVerdict.SUFFICIENT.value
        else:
            frontend_visual_verdict = FrontendVisualVerdict.INSUFFICIENT.value
            blocking_issues.append("Frontend packet requires visual proof, but no recent visual artifact was captured.")
    else:
        frontend_visual_verdict = FrontendVisualVerdict.NOT_APPLICABLE.value

    if not any(item["phase"] == "observability" for item in command_results):
        observability_verdict = ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value
        blocking_issues.append("No observability review command is configured for this verifier packet.")

    if observability_verdict in {
        ObservabilityVerdict.UNEXPECTED_DEGRADATION.value,
        ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value,
    }:
        issue = f"Observability verdict is {observability_verdict}."
        if issue not in blocking_issues:
            blocking_issues.append(issue)

    message = build_verifier_message(
        commands_run=commands_run,
        test_verdict=test_verdict,
        observability_verdict=observability_verdict,
        frontend_visual_verdict=frontend_visual_verdict,
        evidence_paths=evidence_paths,
        blocking_issues=blocking_issues,
    )
    last_message_path.write_text(message, encoding="utf-8")
    finished_at = datetime.now(timezone.utc).isoformat()

    result = {
        "packet_id": packet_id,
        "returncode": returncode,
        "runner": "verifier",
        "command": commands_run,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "last_message_path": str(last_message_path),
        "started_at": started_at.isoformat(),
        "finished_at": finished_at,
        "steps": command_results,
    }
    update_record(
        "packets",
        "packets",
        "packet_id",
        packet_id,
        {
            "last_verifier_run": result,
            "last_execution_run": result,
            "status": "review" if returncode == 0 else "blocked",
        },
    )
    return result
