from __future__ import annotations

import json
import os
import re
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import yaml

from prefect_grace.models import ReasoningProfile
from prefect_grace.tasks.agent_output_parser import read_agent_message
from prefect_grace.tasks.state_store import find_record, update_record

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).resolve().parents[1] / "agent_profiles.yaml"
RUNS_DIR = Path(__file__).resolve().parents[1] / "state" / "runs"
FEATURES_DIR = Path(__file__).resolve().parents[1] / "packets"


@dataclass(frozen=True)
class CodexLaunchResult:
    packet_id: str
    returncode: int
    launcher: str
    command: list[str]
    stdout_path: str
    stderr_path: str
    last_message_path: str
    started_at: str
    finished_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "returncode": self.returncode,
            "launcher": self.launcher,
            "command": self.command,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "last_message_path": self.last_message_path,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


def load_agent_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}


def _role_defaults(config: dict[str, Any], role: str) -> dict[str, Any]:
    return dict(config.get("codex", {}).get("roles", {}).get(role, {}))


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.strip())
    return cleaned.strip("-") or "packet"


def _read_text(path: str | Path | None) -> str:
    if not path:
        return ""
    file_path = Path(path)
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8").strip()


def _artifact_block(tag: str, path: str | Path | None, **attrs: str) -> str:
    text = _read_text(path)
    if not text:
        return ""
    attr_text = " ".join(f'{key}="{value}"' for key, value in attrs.items() if value)
    prefix = f" {attr_text}" if attr_text else ""
    return f"<{tag}{prefix}>\n{text}\n</{tag}>"


def _feature_context_blocks(packet: dict[str, Any]) -> list[str]:
    feature_dir = FEATURES_DIR / str(packet.get("feature_id"))
    blocks: list[str] = []
    for tag, path in (
        ("feature_brief", feature_dir / "feature-brief.md"),
        ("wave_plan", feature_dir / "wave-plan.md"),
    ):
        text = _read_text(path)
        if text:
            blocks.append(f"<{tag} path=\"{path}\">\n{text}\n</{tag}>")
    return blocks


def _dependency_context_blocks(packet: dict[str, Any]) -> list[str]:
    blocks: list[str] = []
    related_packet_ids = list(packet.get("dependencies") or [])
    parent_packet_id = packet.get("parent_packet_id")
    if parent_packet_id:
        related_packet_ids.append(parent_packet_id)
    seen: set[str] = set()
    for related_packet_id in related_packet_ids:
        if related_packet_id in seen:
            continue
        seen.add(related_packet_id)
        try:
            related_packet = find_record("packets", "packets", "packet_id", related_packet_id)
        except KeyError:
            continue
        related_packet_text = _read_text(related_packet.get("packet_path"))
        if related_packet_text:
            blocks.append(
                f"<dependency_packet packet_id=\"{related_packet_id}\" role=\"{related_packet.get('role', '')}\">\n"
                f"{related_packet_text}\n"
                f"</dependency_packet>"
            )
        related_run = related_packet.get("last_execution_run") or related_packet.get("last_verifier_run") or related_packet.get("last_codex_run") or {}
        related_message = read_agent_message(related_run.get("last_message_path"), related_run.get("stdout_path"))
        if related_message:
            blocks.append(
                f"<dependency_output packet_id=\"{related_packet_id}\" role=\"{related_packet.get('role', '')}\">\n"
                f"{related_message}\n"
                f"</dependency_output>"
            )
        last_verification = related_packet.get("last_verification") or {}
        verification_path = last_verification.get("verification_path")
        verification_block = _artifact_block(
            "dependency_verification",
            verification_path,
            packet_id=related_packet_id,
            role=str(related_packet.get("role", "")),
        )
        if verification_block:
            blocks.append(verification_block)
        last_review = related_packet.get("last_review") or {}
        review_path = last_review.get("review_path")
        review_block = _artifact_block(
            "dependency_review",
            review_path,
            packet_id=related_packet_id,
            role=str(related_packet.get("role", "")),
        )
        if review_block:
            blocks.append(review_block)
        last_wave_review = related_packet.get("last_wave_review") or {}
        wave_review_path = last_wave_review.get("review_path")
        wave_review_block = _artifact_block(
            "dependency_wave_review",
            wave_review_path,
            packet_id=related_packet_id,
            role=str(related_packet.get("role", "")),
        )
        if wave_review_block:
            blocks.append(wave_review_block)
    return blocks


def build_packet_prompt(packet: dict[str, Any], role_prompt: str) -> str:
    packet_path = packet.get("packet_path") or ""
    packet_text = _read_text(packet_path)
    context_blocks = _feature_context_blocks(packet) + _dependency_context_blocks(packet)
    context_text = "\n\n".join(context_blocks)
    prompt_parts = [
        role_prompt.strip(),
        "\n".join(
            [
                f"You are running as role: {packet.get('role')}",
                f"Packet ID: {packet.get('packet_id')}",
                f"Feature ID: {packet.get('feature_id')}",
                f"Wave ID: {packet.get('wave_id')}",
                f"Packet file: {packet_path}",
            ]
        ),
    ]
    if context_text:
        prompt_parts.append(context_text)
    prompt_parts.append(f"<packet>\n{packet_text}\n</packet>")
    return "\n\n".join(prompt_parts) + "\n"


def role_prompt_for(role: str) -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / f"{role}_prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return "You are a strict-GRACE agent. Follow the assigned packet exactly."


def _pump_stream(stream: TextIO | None, sink_path: Path) -> None:
    if stream is None:
        sink_path.write_text("", encoding="utf-8")
        return
    with sink_path.open("w", encoding="utf-8") as sink:
        for chunk in iter(stream.readline, ""):
            sink.write(chunk)
            sink.flush()


def _run_codex_process(
    command: list[str],
    *,
    prompt: str,
    workdir: str,
    env: dict[str, str],
    timeout_seconds: int,
    stdout_path: Path,
    stderr_path: Path,
) -> int:
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=workdir,
        env=env,
        bufsize=1,
    )
    stdout_thread = threading.Thread(target=_pump_stream, args=(process.stdout, stdout_path), daemon=True)
    stderr_thread = threading.Thread(target=_pump_stream, args=(process.stderr, stderr_path), daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    try:
        assert process.stdin is not None
        process.stdin.write(prompt)
        process.stdin.close()
        returncode = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
        returncode = 124
        with stderr_path.open("a", encoding="utf-8") as sink:
            sink.write(f"\nTimed out after {timeout_seconds} seconds.\n")
            sink.flush()
    finally:
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
    return returncode


def launch_codex_for_packet(packet_id: str, *, dry_run: bool = False, timeout_seconds: int = 3600) -> dict[str, Any]:
    config = load_agent_config()
    packet = find_record("packets", "packets", "packet_id", packet_id)
    role = str(packet.get("role") or "coder")
    role_defaults = _role_defaults(config, role)
    execution_hints = dict(packet.get("execution_hints") or {})
    reasoning = str(packet.get("reasoning") or role_defaults.get("reasoning") or ReasoningProfile.HIGH.value)
    sandbox = str(execution_hints.get("sandbox") or role_defaults.get("sandbox") or "workspace-write")
    approval = str(role_defaults.get("approval") or "never")
    codex_binary = str(config.get("codex", {}).get("binary") or "codex1")
    shared_model = str(config.get("codex", {}).get("shared_model") or "gpt-5.4")
    workdir = str(execution_hints.get("workdir") or config.get("codex", {}).get("workdir") or ROOT_DIR)
    role_prompt = role_prompt_for(role)
    prompt = build_packet_prompt(packet, role_prompt)

    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{_sanitize_filename(packet_id)}"
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = run_dir / "prompt.md"
    stdout_path = run_dir / "stdout.jsonl"
    stderr_path = run_dir / "stderr.log"
    last_message_path = run_dir / "last-message.md"
    prompt_path.write_text(prompt, encoding="utf-8")

    command = [
        codex_binary,
        "exec",
        "-C",
        workdir,
        "-m",
        shared_model,
        "--json",
        "--output-last-message",
        str(last_message_path),
        "--sandbox",
        sandbox,
        "-c",
        f'model_reasoning_effort="{reasoning}"',
        "-",
    ]
    if approval != "never":
        command.extend(["--profile", approval])
    env = os.environ.copy()
    env.pop("CODEX_FORCE_PROFILE_MODEL_PREFIX", None)

    started_at = datetime.now(timezone.utc).isoformat()
    if dry_run:
        stdout_path.write_text(json.dumps({"dry_run": True, "command": command, "launcher": codex_binary, "routing": "cliproxy-via-wrapper"}) + "\n", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        last_message_path.write_text("DRY RUN: Codex was not launched.\n", encoding="utf-8")
        returncode = 0
    else:
        returncode = _run_codex_process(
            command,
            prompt=prompt,
            workdir=workdir,
            env=env,
            timeout_seconds=timeout_seconds,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
        )
    finished_at = datetime.now(timezone.utc).isoformat()

    result = CodexLaunchResult(
        packet_id=packet_id,
        returncode=returncode,
        launcher=codex_binary,
        command=command,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        last_message_path=str(last_message_path),
        started_at=started_at,
        finished_at=finished_at,
    ).to_dict()
    update_record(
        "packets",
        "packets",
        "packet_id",
        packet_id,
        {
            "last_codex_run": result,
            "last_execution_run": result,
            "status": "review" if returncode == 0 else "blocked",
        },
    )
    return result
