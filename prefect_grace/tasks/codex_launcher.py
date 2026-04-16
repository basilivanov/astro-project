from __future__ import annotations

import json
import hashlib
import logging
import os
import re
import subprocess
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

import yaml

from prefect_grace.models import ReasoningProfile
from prefect_grace.tasks.agent_output_parser import (
    ARCHITECT_ARTIFACT_PLAN_END,
    PACKET_DECISION_END,
    PACKET_DECISION_START,
    PLANNER_WAVE_PLAN_END,
    VERIFIER_EVIDENCE_END,
    WAVE_DECISION_END,
    read_agent_message,
)
from prefect_grace.tasks.state_store import find_record, update_record
from prefect_grace.tasks.workdir import resolve_execution_workdir

ROOT_DIR = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).resolve().parents[1] / "agent_profiles.yaml"
RUNS_DIR = Path(__file__).resolve().parents[1] / "state" / "runs"
FEATURES_DIR = Path(__file__).resolve().parents[1] / "packets"
DEFAULT_HEARTBEAT_INTERVAL_SECONDS = 15.0
DEFAULT_STALL_TIMEOUT_SECONDS = 900.0
DEFAULT_FINAL_OUTPUT_GRACE_SECONDS = 60.0
DEFAULT_POST_TURN_COMPLETION_GRACE_SECONDS = 30.0
DEFAULT_PROMPT_DIGEST_MAX_CHARS = 4000
AUTO_RESUME_TERMINATION_REASONS = {"stall_killed", "timeout"}
PACKET_CONTRACT_START = "FINAL_PACKET_CONTRACT_JSON"
PACKET_CONTRACT_END = "END_FINAL_PACKET_CONTRACT_JSON"
ARCHITECT_CONTEXT_FULL = "full"
ARCHITECT_CONTEXT_REWORK = "rework"
ARCHITECT_CONTEXT_GATE_DECISION = "gate_decision"
FINAL_OUTPUT_MARKERS = (
    ARCHITECT_ARTIFACT_PLAN_END,
    PLANNER_WAVE_PLAN_END,
    VERIFIER_EVIDENCE_END,
    PACKET_DECISION_END,
    WAVE_DECISION_END,
)
SEMANTIC_ITEM_TYPES = {"agent_message", "file_change", "command_execution"}


@dataclass(frozen=True)
class CodexLaunchResult:
    packet_id: str
    returncode: int
    launcher: str
    command: list[str]
    session_mode: str
    resume_strategy: str
    thread_id: str | None
    resumed_from_thread_id: str | None
    stdout_path: str
    stderr_path: str
    last_message_path: str
    started_at: str
    finished_at: str
    termination_reason: str | None = None
    attempt: int = 1
    attempt_count: int = 1
    attempts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "returncode": self.returncode,
            "launcher": self.launcher,
            "command": self.command,
            "session_mode": self.session_mode,
            "resume_strategy": self.resume_strategy,
            "thread_id": self.thread_id,
            "resumed_from_thread_id": self.resumed_from_thread_id,
            "stdout_path": self.stdout_path,
            "stderr_path": self.stderr_path,
            "last_message_path": self.last_message_path,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "termination_reason": self.termination_reason,
            "attempt": self.attempt,
            "attempt_count": self.attempt_count,
            "attempts": list(self.attempts),
        }


@dataclass(frozen=True)
class CodexProcessResult:
    returncode: int
    termination_reason: str


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


def _compact_text(text: str, *, limit: int = DEFAULT_PROMPT_DIGEST_MAX_CHARS) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    head = int(limit * 0.7)
    tail = max(0, limit - head - 64)
    return (
        stripped[:head].rstrip()
        + "\n\n...[prompt digest truncated for size]...\n\n"
        + stripped[-tail:].lstrip()
    )


def _bullet_digest(text: str, *, max_lines: int = 24, max_chars: int = DEFAULT_PROMPT_DIGEST_MAX_CHARS) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    selected: list[str] = []
    for line in lines:
        keep = False
        stripped = line.lstrip()
        if stripped.startswith(("#", "- ", "* ", "##", "###")):
            keep = True
        if ":" in stripped and len(stripped) < 220:
            keep = True
        if keep:
            selected.append(line)
        if len(selected) >= max_lines:
            break
    if not selected:
        return _compact_text(text, limit=max_chars)
    return _compact_text("\n".join(selected), limit=max_chars)


def _extract_packet_contract_block(text: str) -> str:
    if not text:
        return ""
    pattern = re.compile(
        rf"{re.escape(PACKET_CONTRACT_START)}\s*(\{{.*?\}})\s*{re.escape(PACKET_CONTRACT_END)}",
        re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ""
    return match.group(0).strip()


def _architect_context_mode(packet: dict[str, Any], *, role: str | None = None) -> str:
    normalized_role = str(role or packet.get("role") or "").strip().lower()
    if normalized_role != "architect":
        return ARCHITECT_CONTEXT_FULL
    packet_type = str(packet.get("packet_type") or "").strip().lower().replace("-", "_")
    if packet_type == "rework" or str(packet.get("parent_packet_id") or "").strip():
        return ARCHITECT_CONTEXT_REWORK
    if packet_type == "gate_decision" or str(packet.get("wave_id") or "").strip().upper() != "W00":
        return ARCHITECT_CONTEXT_GATE_DECISION
    return ARCHITECT_CONTEXT_FULL


def _architect_packet_tags(packet: dict[str, Any], *, role: str) -> set[str]:
    if str(role or "").strip().lower() != "architect":
        return set()
    tags = {_architect_context_mode(packet, role=role)}
    tags.add("architect")
    return tags


def _context_text_for_role(*, role: str, tag: str, text: str) -> str:
    strict_digest_roles = {"architect", "planner"}
    if role not in strict_digest_roles:
        return text
    digest_tags = {
        "feature_brief",
        "wave_plan",
        "architect_handoff",
        "execution_packet",
        "requirements_slice",
        "development_plan_slice",
        "verification_matrix_slice",
        "knowledge_graph_slice",
        "dependency_packet",
        "dependency_output",
        "dependency_verification",
        "dependency_review",
        "dependency_wave_review",
    }
    if tag == "dependency_packet":
        contract_only = _extract_packet_contract_block(text)
        if contract_only:
            return contract_only
    if tag == "architect_manifest":
        return _compact_text(text, limit=2500)
    if tag in digest_tags:
        return _bullet_digest(text)
    return _compact_text(text)


def _feature_context_blocks(packet: dict[str, Any], *, role: str, context_mode: str = ARCHITECT_CONTEXT_FULL) -> list[str]:
    feature_dir = FEATURES_DIR / str(packet.get("feature_id"))
    blocks: list[str] = []
    feature_files = [
        ("feature_brief", feature_dir / "feature-brief.md"),
        ("wave_plan", feature_dir / "wave-plan.md"),
    ]
    if role == "architect" and context_mode in {ARCHITECT_CONTEXT_REWORK, ARCHITECT_CONTEXT_GATE_DECISION}:
        feature_files = feature_files[:1]
    for tag, path in feature_files:
        text = _read_text(path)
        if text:
            blocks.append(f"<{tag} path=\"{path}\">\n{_context_text_for_role(role=role, tag=tag, text=text)}\n</{tag}>")
    try:
        feature = find_record("features", "features", "feature_id", str(packet.get("feature_id")))
    except KeyError:
        feature = {}
    artifact_specs = [
        ("architect_manifest", "architect_manifest_path"),
        ("architect_handoff", "architect_handoff_path"),
        ("execution_packet", "execution_packet_path"),
        ("requirements_slice", "requirements_slice_path"),
        ("development_plan_slice", "development_plan_slice_path"),
        ("verification_matrix_slice", "verification_matrix_slice_path"),
        ("knowledge_graph_slice", "knowledge_graph_slice_path"),
    ]
    if role == "architect" and context_mode == ARCHITECT_CONTEXT_REWORK:
        artifact_specs = [
            ("architect_manifest", "architect_manifest_path"),
            ("execution_packet", "execution_packet_path"),
            ("verification_matrix_slice", "verification_matrix_slice_path"),
        ]
    elif role == "architect" and context_mode == ARCHITECT_CONTEXT_GATE_DECISION:
        artifact_specs = [
            ("architect_manifest", "architect_manifest_path"),
            ("execution_packet", "execution_packet_path"),
        ]
    for tag, key in artifact_specs:
        path = feature.get(key)
        text = _read_text(path)
        if text:
            blocks.append(f"<{tag} path=\"{path}\">\n{_context_text_for_role(role=role, tag=tag, text=text)}\n</{tag}>")
    return blocks


def _dependency_context_blocks(packet: dict[str, Any], *, role: str) -> list[str]:
    blocks: list[str] = []
    related_packet_ids = list(packet.get("dependencies") or [])
    parent_packet_id = packet.get("parent_packet_id")
    if parent_packet_id:
        related_packet_ids.append(parent_packet_id)
    architect_context_mode = _architect_context_mode(packet, role=role)
    if role == "architect" and architect_context_mode == ARCHITECT_CONTEXT_GATE_DECISION:
        related_packet_ids = [
            packet_id
            for packet_id in related_packet_ids
            if _related_packet_role(packet_id) in {"reviewer", "verifier", "coder"}
        ][-3:]
    elif role == "architect" and architect_context_mode == ARCHITECT_CONTEXT_REWORK:
        target_packet_id = str(packet.get("review_target_packet_id") or parent_packet_id or "").strip()
        preferred_ids = [target_packet_id, *list(packet.get("dependencies") or []), parent_packet_id]
        related_packet_ids = [packet_id for packet_id in preferred_ids if str(packet_id or "").strip()]
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
                f"{_context_text_for_role(role=role, tag='dependency_packet', text=related_packet_text)}\n"
                f"</dependency_packet>"
            )
        related_run = related_packet.get("last_execution_run") or related_packet.get("last_verifier_run") or related_packet.get("last_codex_run") or {}
        related_message = read_agent_message(related_run.get("last_message_path"), related_run.get("stdout_path"))
        include_dependency_output = not (
            role == "architect"
            and architect_context_mode in {ARCHITECT_CONTEXT_REWORK, ARCHITECT_CONTEXT_GATE_DECISION}
            and str(related_packet.get("role") or "").strip().lower() not in {"reviewer", "verifier"}
        )
        if related_message and include_dependency_output:
            blocks.append(
                f"<dependency_output packet_id=\"{related_packet_id}\" role=\"{related_packet.get('role', '')}\">\n"
                f"{_context_text_for_role(role=role, tag='dependency_output', text=related_message)}\n"
                f"</dependency_output>"
            )
        last_verification = related_packet.get("last_verification") or {}
        verification_path = last_verification.get("verification_path")
        verification_block = ""
        if not (role == "architect" and architect_context_mode == ARCHITECT_CONTEXT_REWORK and str(related_packet.get("role") or "") not in {"verifier"}):
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
        review_block = ""
        if not (role == "architect" and architect_context_mode == ARCHITECT_CONTEXT_REWORK and str(related_packet.get("role") or "") not in {"reviewer", "coder"}):
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
        wave_review_block = ""
        if not (role == "architect" and architect_context_mode in {ARCHITECT_CONTEXT_REWORK, ARCHITECT_CONTEXT_GATE_DECISION}):
            wave_review_block = _artifact_block(
                "dependency_wave_review",
                wave_review_path,
                packet_id=related_packet_id,
                role=str(related_packet.get("role", "")),
            )
        if wave_review_block:
            blocks.append(wave_review_block)
    return blocks


def _related_packet_role(packet_id: str) -> str:
    try:
        return str(find_record("packets", "packets", "packet_id", str(packet_id)).get("role") or "").strip().lower()
    except KeyError:
        return ""


def _architect_mode_preamble(context_mode: str) -> str:
    if context_mode == ARCHITECT_CONTEXT_REWORK:
        return "\n".join(
            [
                "ARCHITECT MODE: rework",
                "Resume the existing architectural context. Do not repeat feature formalization or reslice unless the blocker explicitly requires it.",
                "Use only the local blocker, target packet contract, reviewer blockers, and latest relevant verifier evidence.",
                "Return FINAL_DIRECT_REWORK_PACKET_JSON with packet_type semantics: execution, rework, or gate_decision. Do not introduce light/basic packet semantics.",
            ]
        )
    if context_mode == ARCHITECT_CONTEXT_GATE_DECISION:
        return "\n".join(
            [
                "ARCHITECT MODE: gate-decision",
                "Issue a lightweight wave verdict only: accepted, rework_required, blocked, or next-step reasons.",
                "Do not perform start/formalize work and do not pull unrelated feature history into the verdict.",
                "Return FINAL_WAVE_DECISION_JSON.",
            ]
        )
    return "\n".join(
        [
            "ARCHITECT MODE: start/formalize",
            "Formalize the business feature, update only impacted GRACE canon, define waves, and produce small execution packets.",
            "Keep packet.md as the primary execution contract. Machine JSON must stay as a compact embedded final block.",
        ]
    )


def build_packet_prompt(packet: dict[str, Any], role_prompt: str) -> str:
    role = str(packet.get("role") or "")
    packet_path = packet.get("packet_path") or ""
    packet_text = _read_text(packet_path)
    execution_hints = dict(packet.get("execution_hints") or {})
    packet_type = str(packet.get("packet_type") or "").strip().lower().replace("-", "_")
    parent_packet_id = str(packet.get("parent_packet_id") or "").strip()
    architect_context_mode = _architect_context_mode(packet, role=role)
    if role == "coder" and execution_hints.get("light_resume_stage"):
        original_title = str(packet.get("title") or "").strip() or str(packet.get("packet_id") or "").strip()
        summary = str(execution_hints.get("light_resume_summary") or packet.get("summary") or "").strip()
        write_scope = [str(item).strip() for item in list(execution_hints.get("light_resume_write_scope") or []) if str(item).strip()]
        inputs = [str(item).strip() for item in list(execution_hints.get("light_resume_inputs") or []) if str(item).strip()]
        acceptance = [
            str(item).strip()
            for item in list(execution_hints.get("light_resume_acceptance_criteria") or [])
            if str(item).strip()
        ]
        reviewer_gate = [
            str(item).strip()
            for item in list(execution_hints.get("light_resume_reviewer_gate") or [])
            if str(item).strip()
        ]
        notes = [str(item).strip() for item in list(execution_hints.get("light_resume_notes") or []) if str(item).strip()]
        reasons = [str(item).strip() for item in list(execution_hints.get("light_resume_reasons") or []) if str(item).strip()]
        light_resume_lines = [
            f"# Packet\n{original_title} (light resume stage)",
            "",
            f"## Summary\n{summary or f'Resume the existing coder context for `{original_title}`.'}",
            "",
            "## Light Resume Routing",
            f"- source_packet_id: {execution_hints.get('light_resume_source_packet_id') or packet.get('packet_id')}",
            f"- attempt: {execution_hints.get('light_resume_attempt') or 1}",
            f"- max_attempts: {execution_hints.get('light_resume_max_attempts') or 1}",
            "- scope: packet_local small fix only",
            "- resume_strategy: packet_parent",
        ]
        if reasons:
            light_resume_lines.extend(["", "## Reviewer Blockers", *[f"- {reason}" for reason in reasons]])
        if write_scope:
            light_resume_lines.extend(["", "## Write Scope", *[f"- {item}" for item in write_scope]])
        if inputs:
            light_resume_lines.extend(["", "## Inputs", *[f"- {item}" for item in inputs]])
        if acceptance:
            light_resume_lines.extend(["", "## Acceptance Criteria", *[f"- {item}" for item in acceptance]])
        if reviewer_gate:
            light_resume_lines.extend(["", "## Reviewer Gate", *[f"- {item}" for item in reviewer_gate]])
        if notes:
            light_resume_lines.extend(["", "## Notes", *[f"- {item}" for item in notes]])
        packet_text = "\n".join(light_resume_lines).strip() + "\n"
    if role == "architect":
        if packet_type == "rework" or parent_packet_id:
            role_prompt = role_prompt.replace(
                "Your job is to either:\n- transform a business feature request into incremental GRACE canon updates, explicit slice boundaries, and an execution-ready wave / packet graph; or\n- accept or reject a completed wave as the architect gate.",
                "Your job is to issue a bounded architect rework packet or escalation decision for the current blocker.",
            )
        elif packet_type == "gate_decision":
            role_prompt = role_prompt.replace(
                "Your job is to either:\n- transform a business feature request into incremental GRACE canon updates, explicit slice boundaries, and an execution-ready wave / packet graph; or\n- accept or reject a completed wave as the architect gate.",
                "Your job is to accept or reject the completed wave as a lightweight architect gate.",
            )
    context_blocks = _feature_context_blocks(
        packet,
        role=role,
        context_mode=architect_context_mode,
    ) + _dependency_context_blocks(packet, role=role)
    context_text = "\n\n".join(context_blocks)
    prompt_parts = [
        role_prompt.strip(),
        "\n".join(
            [
                f"You are running as role: {packet.get('role')}",
                f"Packet ID: {packet.get('packet_id')}",
                f"Feature ID: {packet.get('feature_id')}",
                f"Wave ID: {packet.get('wave_id')}",
                f"Packet type: {packet.get('packet_type') or 'execution'}",
                f"Packet file: {packet_path}",
            ]
        ),
    ]
    if role == "architect":
        prompt_parts.append(_architect_mode_preamble(architect_context_mode))
    if context_text:
        prompt_parts.append(context_text)
    prompt_parts.append(f"<packet>\n{packet_text}\n</packet>")
    return "\n\n".join(prompt_parts) + "\n"


def role_prompt_for(role: str) -> str:
    prompt_path = Path(__file__).resolve().parents[1] / "prompts" / f"{role}_prompt.md"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8")
    return "You are a strict-GRACE agent. Follow the assigned packet exactly."


def _normalize_resume_strategy(value: Any) -> str:
    strategy = str(value or "none").strip().lower().replace("-", "_")
    if strategy not in {"none", "feature_role", "packet_parent"}:
        return "none"
    return strategy


def _normalize_non_negative_int(value: Any, *, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, 0)


def _normalize_positive_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed <= 0:
        return None
    return parsed


def _resolve_resume_strategy(packet: dict[str, Any], role_defaults: dict[str, Any]) -> str:
    execution_hints = dict(packet.get("execution_hints") or {})
    return _normalize_resume_strategy(execution_hints.get("resume_strategy") or role_defaults.get("resume_strategy"))


def _resolve_stall_timeout_seconds(
    packet: dict[str, Any],
    role_defaults: dict[str, Any],
    explicit_timeout: float | None,
) -> float | None:
    if explicit_timeout is not None:
        return explicit_timeout
    execution_hints = dict(packet.get("execution_hints") or {})
    resolved = _normalize_positive_float(
        execution_hints.get("stall_timeout_seconds", role_defaults.get("stall_timeout_seconds"))
    )
    if resolved is not None:
        return resolved
    return DEFAULT_STALL_TIMEOUT_SECONDS


def _resolve_max_auto_resume_attempts(packet: dict[str, Any], role_defaults: dict[str, Any]) -> int:
    execution_hints = dict(packet.get("execution_hints") or {})
    return _normalize_non_negative_int(
        execution_hints.get("max_auto_resume_attempts", role_defaults.get("max_auto_resume_attempts")),
        default=0,
    )


def _feature_role_session(feature_id: str, role: str) -> dict[str, Any] | None:
    try:
        feature = find_record("features", "features", "feature_id", feature_id)
    except KeyError:
        return None
    role_threads = feature.get("role_threads") or {}
    session = role_threads.get(role)
    if isinstance(session, dict):
        return dict(session)
    return None


def _packet_parent_session(packet: dict[str, Any]) -> dict[str, Any] | None:
    execution_hints = dict(packet.get("execution_hints") or {})
    parent_packet_id = str(
        execution_hints.get("resume_parent_packet_id") or packet.get("parent_packet_id") or ""
    ).strip()
    if not parent_packet_id:
        return None
    try:
        parent_packet = find_record("packets", "packets", "packet_id", parent_packet_id)
    except KeyError:
        return None
    thread_id = str(parent_packet.get("last_thread_id") or "").strip()
    if not thread_id:
        last_run = (
            parent_packet.get("last_execution_run")
            or parent_packet.get("last_codex_run")
            or {}
        )
        thread_id = str(last_run.get("thread_id") or "").strip()
    if not thread_id:
        return None
    return {
        "thread_id": thread_id,
        "packet_id": parent_packet_id,
    }


def _store_feature_role_session(
    *,
    feature_id: str,
    role: str,
    thread_id: str,
    launcher: str,
    packet_id: str,
    reasoning: str,
    sandbox: str,
    approval: str,
    model: str,
    session_mode: str,
    run_dir: Path,
    resumed_from_thread_id: str | None,
) -> dict[str, Any] | None:
    try:
        feature = find_record("features", "features", "feature_id", feature_id)
    except KeyError:
        return None
    role_threads = dict(feature.get("role_threads") or {})
    previous = role_threads.get(role) if isinstance(role_threads.get(role), dict) else {}
    session = {
        **previous,
        "thread_id": thread_id,
        "launcher": launcher,
        "packet_id": packet_id,
        "reasoning": reasoning,
        "sandbox": sandbox,
        "approval": approval,
        "model": model,
        "session_mode": session_mode,
        "resumed_from_thread_id": resumed_from_thread_id,
        "run_dir": str(run_dir),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    role_threads[role] = session
    update_record(
        "features",
        "features",
        "feature_id",
        feature_id,
        {"role_threads": role_threads},
    )
    return session


def _extract_thread_id(stdout_path: Path) -> str | None:
    if not stdout_path.exists():
        return None
    with stdout_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if str(payload.get("type") or "").strip() != "thread.started":
                continue
            thread_id = str(payload.get("thread_id") or "").strip()
            if thread_id:
                return thread_id
    return None


def _config_override_args(*, reasoning: str, approval: str, sandbox: str | None = None) -> list[str]:
    args = ["-c", f'model_reasoning_effort="{reasoning}"']
    if approval:
        args.extend(["-c", f'approval_policy="{approval}"'])
    if sandbox:
        args.extend(["-c", f'sandbox_mode="{sandbox}"'])
    return args


def _uses_bypass_sandbox(sandbox: str, approval: str) -> bool:
    return sandbox == "danger-full-access" and approval == "never"


def _build_exec_command(
    *,
    codex_binary: str,
    workdir: str,
    shared_model: str,
    reasoning: str,
    approval: str,
    sandbox: str,
    last_message_path: Path,
) -> list[str]:
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
        *_config_override_args(reasoning=reasoning, approval=approval),
    ]
    if _uses_bypass_sandbox(sandbox, approval):
        command.append("--dangerously-bypass-approvals-and-sandbox")
    else:
        command.extend(["--sandbox", sandbox])
    command.append("-")
    return command


def _build_resume_command(
    *,
    codex_binary: str,
    workdir: str,
    shared_model: str,
    reasoning: str,
    approval: str,
    sandbox: str,
    thread_id: str,
    last_message_path: Path,
) -> list[str]:
    command = [
        codex_binary,
        "exec",
        "-C",
        workdir,
        "resume",
        "--json",
        "--output-last-message",
        str(last_message_path),
        "-m",
        shared_model,
        *_config_override_args(reasoning=reasoning, approval=approval, sandbox=sandbox),
    ]
    if _uses_bypass_sandbox(sandbox, approval):
        command.append("--dangerously-bypass-approvals-and-sandbox")
    command.extend([thread_id, "-"])
    return command


def _pump_stream(stream: TextIO | None, sink_path: Path) -> None:
    if stream is None:
        sink_path.write_text("", encoding="utf-8")
        return
    with sink_path.open("w", encoding="utf-8") as sink:
        for chunk in iter(stream.readline, ""):
            sink.write(chunk)
            sink.flush()


def _extract_last_stdout_event(stdout_path: Path, *, max_bytes: int = 16384) -> dict[str, str] | None:
    if not stdout_path.exists() or stdout_path.stat().st_size == 0:
        return None
    with stdout_path.open("rb") as handle:
        size = handle.seek(0, os.SEEK_END)
        read_size = min(size, max_bytes)
        handle.seek(-read_size, os.SEEK_END)
        tail = handle.read(read_size).decode("utf-8", errors="replace")
    lines = [line.strip() for line in tail.splitlines() if line.strip()]
    for line in reversed(lines):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        event_type = str(payload.get("type") or "").strip()
        item = payload.get("item") if isinstance(payload.get("item"), dict) else {}
        status = str(item.get("status") or "").strip()
        if event_type or status:
            return {
                "event_type": event_type or "unknown",
                "status": status or "unknown",
            }
    return None


def _run_progress_class(stdout_path: Path) -> str:
    progress = _extract_stdout_progress(stdout_path)
    if progress.get("turn_completed_signature"):
        return "completed_turn"
    semantic_reason = str(progress.get("semantic_reason") or "")
    if semantic_reason.startswith("item."):
        return "semantic_progress"
    if semantic_reason == "thread.started" or progress.get("event_type") in {"turn.started", "thread.started"}:
        return "startup_only"
    return "no_output"


def _text_signature(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def _iter_stdout_payloads(stdout_path: Path, *, max_bytes: int = 262144) -> list[dict[str, Any]]:
    if not stdout_path.exists() or stdout_path.stat().st_size == 0:
        return []
    with stdout_path.open("rb") as handle:
        size = handle.seek(0, os.SEEK_END)
        read_size = min(size, max_bytes)
        handle.seek(-read_size, os.SEEK_END)
        tail = handle.read(read_size).decode("utf-8", errors="replace")
    payloads: list[dict[str, Any]] = []
    for line in tail.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _payload_text(payload: dict[str, Any]) -> str:
    item = payload.get("item") if isinstance(payload.get("item"), dict) else {}
    for value in (item.get("text"), payload.get("text"), item.get("message"), payload.get("message")):
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _detect_final_marker(text: str) -> str | None:
    for marker in FINAL_OUTPUT_MARKERS:
        if marker in text:
            return marker
    return None


def _semantic_signature_from_payload(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    event_type = str(payload.get("type") or "").strip()
    if event_type == "thread.started":
        thread_id = str(payload.get("thread_id") or "").strip()
        if thread_id:
            return (f"thread.started:{thread_id}", "thread.started")
        return ("thread.started", "thread.started")

    item = payload.get("item") if isinstance(payload.get("item"), dict) else {}
    item_type = str(item.get("type") or "").strip()
    if item_type not in SEMANTIC_ITEM_TYPES:
        return (None, None)
    item_id = str(item.get("id") or "").strip()
    status = str(item.get("status") or "").strip()
    if item_type == "agent_message":
        text = _payload_text(payload)
        if not text:
            return (None, None)
        return (
            f"{event_type}:{item_type}:{item_id}:{_text_signature(text)}",
            f"{event_type}:{item_type}",
        )
    exit_code = item.get("exit_code")
    exit_code_part = f":{exit_code}" if exit_code is not None else ""
    return (
        f"{event_type}:{item_type}:{item_id}:{status}{exit_code_part}",
        f"{event_type}:{item_type}",
    )


def _extract_stdout_progress(stdout_path: Path, *, max_bytes: int = 262144) -> dict[str, Any]:
    payloads = _iter_stdout_payloads(stdout_path, max_bytes=max_bytes)
    latest_event: dict[str, Any] = {
        "event_type": "none",
        "status": "none",
        "item_type": "none",
        "semantic_signature": None,
        "semantic_reason": None,
        "final_signature": None,
        "final_marker": None,
        "turn_completed_signature": None,
    }
    for payload in reversed(payloads):
        if latest_event["event_type"] == "none":
            event_type = str(payload.get("type") or "").strip()
            item = payload.get("item") if isinstance(payload.get("item"), dict) else {}
            status = str(item.get("status") or "").strip()
            item_type = str(item.get("type") or "").strip()
            if event_type or status or item_type:
                latest_event["event_type"] = event_type or "unknown"
                latest_event["status"] = status or "unknown"
                latest_event["item_type"] = item_type or "unknown"
        if latest_event["semantic_signature"] is None:
            semantic_signature, semantic_reason = _semantic_signature_from_payload(payload)
            if semantic_signature is not None:
                latest_event["semantic_signature"] = semantic_signature
                latest_event["semantic_reason"] = semantic_reason
        if latest_event["final_signature"] is None:
            item = payload.get("item") if isinstance(payload.get("item"), dict) else {}
            item_type = str(item.get("type") or "").strip()
            if item_type == "agent_message":
                text = _payload_text(payload)
                marker = _detect_final_marker(text)
                if marker:
                    item_id = str(item.get("id") or "").strip()
                    latest_event["final_signature"] = f"agent_message:{item_id}:{marker}:{_text_signature(text)}"
                    latest_event["final_marker"] = marker
        if latest_event["turn_completed_signature"] is None and str(payload.get("type") or "").strip() == "turn.completed":
            usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
            latest_event["turn_completed_signature"] = (
                f"turn.completed:{usage.get('input_tokens')}:{usage.get('output_tokens')}:{usage.get('reasoning_tokens')}"
            )
        if (
            latest_event["semantic_signature"] is not None
            and latest_event["final_signature"] is not None
            and latest_event["turn_completed_signature"] is not None
        ):
            break
    return latest_event


def _last_message_progress(last_message_path: Path | None) -> dict[str, Any]:
    if last_message_path is None or not last_message_path.exists():
        return {
            "last_message_bytes": 0,
            "last_message_signature": None,
            "final_signature": None,
            "final_marker": None,
        }
    text = last_message_path.read_text(encoding="utf-8").strip()
    if not text:
        return {
            "last_message_bytes": 0,
            "last_message_signature": None,
            "final_signature": None,
            "final_marker": None,
        }
    marker = _detect_final_marker(text)
    signature = f"last_message:{_text_signature(text)}"
    return {
        "last_message_bytes": len(text.encode("utf-8")),
        "last_message_signature": signature,
        "final_signature": f"{signature}:{marker}" if marker else None,
        "final_marker": marker,
    }


def _heartbeat_payload(
    *,
    run_dir: Path,
    stdout_path: Path,
    process: subprocess.Popen[str],
    last_message_path: Path | None = None,
) -> dict[str, Any]:
    progress = _extract_stdout_progress(stdout_path)
    last_message = _last_message_progress(last_message_path)
    stdout_bytes = stdout_path.stat().st_size if stdout_path.exists() else 0
    semantic_signature = last_message["last_message_signature"] or progress["semantic_signature"]
    semantic_reason = "last_message" if last_message["last_message_signature"] else progress["semantic_reason"]
    final_signature = last_message["final_signature"] or progress["final_signature"]
    final_marker = last_message["final_marker"] or progress["final_marker"]
    return {
        "run_dir": str(run_dir),
        "stdout_path": str(stdout_path),
        "stdout_bytes": stdout_bytes,
        "pid": process.pid,
        "event_type": progress.get("event_type", "none"),
        "event_status": progress.get("status", "none"),
        "event_item_type": progress.get("item_type", "none"),
        "semantic_signature": semantic_signature,
        "semantic_reason": semantic_reason or "none",
        "final_signature": final_signature,
        "final_marker": final_marker or "none",
        "last_message_bytes": last_message["last_message_bytes"],
        "last_message_path": str(last_message_path) if last_message_path else "",
    }


def _format_heartbeat_message(packet_id: str, payload: dict[str, Any]) -> str:
    return (
        "Codex heartbeat packet=%s pid=%s run_dir=%s stdout_bytes=%s last_event=%s/%s/%s last_semantic=%s final=%s stdout=%s last_message=%s"
        % (
            packet_id,
            payload.get("pid"),
            payload.get("run_dir"),
            payload.get("stdout_bytes"),
            payload.get("event_type"),
            payload.get("event_status"),
            payload.get("event_item_type"),
            payload.get("semantic_reason"),
            payload.get("final_marker"),
            payload.get("stdout_path"),
            payload.get("last_message_path"),
        )
    )


def _heartbeat_loop(
    process: subprocess.Popen[str],
    *,
    packet_id: str,
    run_dir: Path,
    stdout_path: Path,
    logger: logging.Logger,
    interval_seconds: float,
    stop_event: threading.Event,
    stall_state: dict[str, Any] | None = None,
    stall_timeout_seconds: float | None = DEFAULT_STALL_TIMEOUT_SECONDS,
    last_message_path: Path | None = None,
    final_output_grace_seconds: float = DEFAULT_FINAL_OUTPUT_GRACE_SECONDS,
    post_turn_completion_grace_seconds: float = DEFAULT_POST_TURN_COMPLETION_GRACE_SECONDS,
) -> None:
    last_progress_at = datetime.now(timezone.utc)
    payload = _heartbeat_payload(
        run_dir=run_dir,
        stdout_path=stdout_path,
        process=process,
        last_message_path=last_message_path,
    )
    last_semantic_signature = payload.get("semantic_signature")
    last_final_signature = payload.get("final_signature")
    final_seen_at = datetime.now(timezone.utc) if last_final_signature else None
    last_turn_completed_signature = payload.get("turn_completed_signature")
    turn_completed_seen_at = datetime.now(timezone.utc) if last_turn_completed_signature else None
    while not stop_event.wait(interval_seconds):
        if process.poll() is not None:
            break
        payload = _heartbeat_payload(
            run_dir=run_dir,
            stdout_path=stdout_path,
            process=process,
            last_message_path=last_message_path,
        )
        semantic_signature = payload.get("semantic_signature")
        if semantic_signature and semantic_signature != last_semantic_signature:
            last_semantic_signature = semantic_signature
            last_progress_at = datetime.now(timezone.utc)
        final_signature = payload.get("final_signature")
        if final_signature:
            if final_signature != last_final_signature:
                last_final_signature = final_signature
                final_seen_at = datetime.now(timezone.utc)
        else:
            last_final_signature = None
            final_seen_at = None
        turn_completed_signature = payload.get("turn_completed_signature")
        if turn_completed_signature:
            if turn_completed_signature != last_turn_completed_signature:
                last_turn_completed_signature = turn_completed_signature
                turn_completed_seen_at = datetime.now(timezone.utc)
        else:
            last_turn_completed_signature = None
            turn_completed_seen_at = None
        idle_seconds = max(0.0, (datetime.now(timezone.utc) - last_progress_at).total_seconds())
        logger.info("%s idle_seconds=%.1f", _format_heartbeat_message(packet_id, payload), idle_seconds)
        if (
            final_seen_at is not None
            and final_output_grace_seconds > 0
            and (datetime.now(timezone.utc) - final_seen_at).total_seconds() >= final_output_grace_seconds
            and process.poll() is None
        ):
            if stall_state is not None:
                stall_state["final_output_collected"] = True
                stall_state["final_marker"] = payload.get("final_marker")
                stall_state["idle_seconds"] = idle_seconds
            logger.warning(
                "Codex final output collected packet=%s pid=%s final_marker=%s run_dir=%s stdout=%s; terminating hung process",
                packet_id,
                process.pid,
                payload.get("final_marker"),
                run_dir,
                stdout_path,
            )
            process.kill()
            break
        if (
            turn_completed_seen_at is not None
            and post_turn_completion_grace_seconds > 0
            and (datetime.now(timezone.utc) - turn_completed_seen_at).total_seconds() >= post_turn_completion_grace_seconds
            and process.poll() is None
        ):
            if stall_state is not None:
                stall_state["post_turn_completion_collected"] = True
                stall_state["turn_completed_signature"] = last_turn_completed_signature
                stall_state["idle_seconds"] = idle_seconds
            logger.warning(
                "Codex post-turn completion collected packet=%s pid=%s run_dir=%s stdout=%s; terminating hung process after completed turn",
                packet_id,
                process.pid,
                run_dir,
                stdout_path,
            )
            process.kill()
            break
        if stall_timeout_seconds and idle_seconds >= stall_timeout_seconds and process.poll() is None:
            if stall_state is not None:
                stall_state["detected"] = True
                stall_state["idle_seconds"] = idle_seconds
            logger.warning(
                "Codex stall detected packet=%s pid=%s idle_seconds=%.1f run_dir=%s stdout=%s; terminating process",
                packet_id,
                process.pid,
                idle_seconds,
                run_dir,
                stdout_path,
            )
            process.kill()
            break


def _run_codex_process(
    command: list[str],
    *,
    packet_id: str,
    prompt: str,
    workdir: str,
    env: dict[str, str],
    timeout_seconds: int,
    stdout_path: Path,
    stderr_path: Path,
    run_dir: Path,
    logger: logging.Logger | None = None,
    heartbeat_interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    stall_timeout_seconds: float | None = DEFAULT_STALL_TIMEOUT_SECONDS,
) -> CodexProcessResult:
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
    heartbeat_stop = threading.Event()
    heartbeat_thread: threading.Thread | None = None
    stall_state: dict[str, Any] = {
        "detected": False,
        "idle_seconds": 0.0,
        "final_output_collected": False,
        "post_turn_completion_collected": False,
    }
    returncode = -1
    heartbeat_logger = logger or (logging.getLogger(__name__) if stall_timeout_seconds else None)
    last_message_path = run_dir / "last-message.md"
    if heartbeat_logger is not None:
        heartbeat_logger.info(
            "Launching Codex packet=%s pid=%s run_dir=%s stdout=%s stderr=%s",
            packet_id,
            process.pid,
            run_dir,
            stdout_path,
            stderr_path,
        )
        heartbeat_thread = threading.Thread(
            target=_heartbeat_loop,
            args=(process,),
            kwargs={
                "packet_id": packet_id,
                "run_dir": run_dir,
                "stdout_path": stdout_path,
                "logger": heartbeat_logger,
                "interval_seconds": heartbeat_interval_seconds,
                "stop_event": heartbeat_stop,
                "stall_state": stall_state,
                "stall_timeout_seconds": stall_timeout_seconds,
                "last_message_path": last_message_path,
            },
            daemon=True,
        )
        heartbeat_thread.start()
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
        termination_reason = "completed"
        if stall_state.get("final_output_collected"):
            returncode = 0
            termination_reason = "final_output_collected"
            with stderr_path.open("a", encoding="utf-8") as sink:
                sink.write(
                    f"\nCodex final output collected ({stall_state.get('final_marker') or 'unknown-marker'})"
                    f" after {float(stall_state.get('idle_seconds') or 0.0):.1f} idle seconds; process terminated.\n"
                )
                sink.flush()
        elif stall_state.get("post_turn_completion_collected"):
            returncode = 0
            termination_reason = "post_turn_hung_killed"
            with stderr_path.open("a", encoding="utf-8") as sink:
                sink.write(
                    f"\nCodex post-turn completion collected after {float(stall_state.get('idle_seconds') or 0.0):.1f} idle seconds; process terminated after completed turn.\n"
                )
                sink.flush()
        elif stall_state.get("detected"):
            termination_reason = "stall_killed"
            with stderr_path.open("a", encoding="utf-8") as sink:
                sink.write(
                    f"\nCodex stall detected after {float(stall_state.get('idle_seconds') or 0.0):.1f} idle seconds.\n"
                )
                sink.flush()
        elif returncode == 124:
            termination_reason = "timeout"
        elif returncode != 0:
            termination_reason = "nonzero_exit"
        heartbeat_stop.set()
        if heartbeat_thread is not None:
            heartbeat_thread.join(timeout=5)
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        if process.stdout is not None:
            process.stdout.close()
        if process.stderr is not None:
            process.stderr.close()
        if logger is not None:
            logger.info(
                "Codex finished packet=%s pid=%s rc=%s reason=%s stdout_bytes=%s run_dir=%s last_message=%s",
                packet_id,
                process.pid,
                returncode,
                termination_reason,
                stdout_path.stat().st_size if stdout_path.exists() else 0,
                run_dir,
                run_dir / "last-message.md",
            )
    return CodexProcessResult(returncode=returncode, termination_reason=termination_reason)


def launch_codex_for_packet(
    packet_id: str,
    *,
    dry_run: bool = False,
    timeout_seconds: int = 3600,
    logger: logging.Logger | None = None,
    heartbeat_interval_seconds: float = DEFAULT_HEARTBEAT_INTERVAL_SECONDS,
    stall_timeout_seconds: float | None = None,
) -> dict[str, Any]:
    config = load_agent_config()
    packet = find_record("packets", "packets", "packet_id", packet_id)
    role = str(packet.get("role") or "coder")
    role_defaults = _role_defaults(config, role)
    execution_hints = dict(packet.get("execution_hints") or {})
    reasoning = str(packet.get("reasoning") or role_defaults.get("reasoning") or ReasoningProfile.HIGH.value)
    sandbox = str(execution_hints.get("sandbox") or role_defaults.get("sandbox") or "workspace-write")
    approval = str(role_defaults.get("approval") or "never")
    resume_strategy = _resolve_resume_strategy(packet, role_defaults)
    effective_stall_timeout_seconds = _resolve_stall_timeout_seconds(packet, role_defaults, stall_timeout_seconds)
    max_auto_resume_attempts = _resolve_max_auto_resume_attempts(packet, role_defaults)
    codex_binary = str(config.get("codex", {}).get("binary") or "codex1")
    shared_model = str(config.get("codex", {}).get("shared_model") or "gpt-5.4")
    configured_workdir = str(execution_hints.get("workdir") or config.get("codex", {}).get("workdir") or ROOT_DIR)
    workdir = str(resolve_execution_workdir(configured_workdir))
    role_prompt = role_prompt_for(role)
    prompt = build_packet_prompt(packet, role_prompt)

    if resume_strategy == "feature_role":
        existing_session = _feature_role_session(str(packet.get("feature_id")), role)
    elif resume_strategy == "packet_parent":
        existing_session = _packet_parent_session(packet)
    else:
        existing_session = None
    env = os.environ.copy()
    env.pop("CODEX_FORCE_PROFILE_MODEL_PREFIX", None)

    attempts: list[dict[str, Any]] = []
    resume_thread_id = (
        str(existing_session.get("thread_id") or "").strip()
        if existing_session and str(existing_session.get("thread_id") or "").strip()
        else None
    )
    attempt = 0
    while True:
        attempt += 1
        run_id = (
            f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
            f"-{_sanitize_filename(packet_id)}-try{attempt}"
        )
        run_dir = RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = run_dir / "prompt.md"
        stdout_path = run_dir / "stdout.jsonl"
        stderr_path = run_dir / "stderr.log"
        last_message_path = run_dir / "last-message.md"
        prompt_path.write_text(prompt, encoding="utf-8")

        resumed_from_thread_id = resume_thread_id or None
        session_mode = "resume" if resumed_from_thread_id else "exec"
        if resumed_from_thread_id:
            command = _build_resume_command(
                codex_binary=codex_binary,
                workdir=workdir,
                shared_model=shared_model,
                reasoning=reasoning,
                approval=approval,
                sandbox=sandbox,
                thread_id=resumed_from_thread_id,
                last_message_path=last_message_path,
            )
        else:
            command = _build_exec_command(
                codex_binary=codex_binary,
                workdir=workdir,
                shared_model=shared_model,
                reasoning=reasoning,
                approval=approval,
                sandbox=sandbox,
                last_message_path=last_message_path,
            )

        started_at = datetime.now(timezone.utc).isoformat()
        termination_reason = "dry_run"
        if dry_run:
            stdout_path.write_text(
                json.dumps(
                    {"dry_run": True, "command": command, "launcher": codex_binary, "routing": "cliproxy-via-wrapper"}
                )
                + "\n",
                encoding="utf-8",
            )
            stderr_path.write_text("", encoding="utf-8")
            last_message_path.write_text("DRY RUN: Codex was not launched.\n", encoding="utf-8")
            returncode = 0
            if logger is not None:
                logger.info(
                    "Codex dry-run packet=%s attempt=%s run_dir=%s stdout=%s stderr=%s last_message=%s",
                    packet_id,
                    attempt,
                    run_dir,
                    stdout_path,
                    stderr_path,
                    last_message_path,
                )
            thread_id = resumed_from_thread_id
        else:
            process_result = _run_codex_process(
                command,
                packet_id=packet_id,
                prompt=prompt,
                workdir=workdir,
                env=env,
                timeout_seconds=timeout_seconds,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                run_dir=run_dir,
                logger=logger,
                heartbeat_interval_seconds=heartbeat_interval_seconds,
                stall_timeout_seconds=effective_stall_timeout_seconds,
            )
            if isinstance(process_result, CodexProcessResult):
                returncode = process_result.returncode
                termination_reason = process_result.termination_reason
            else:
                returncode = int(process_result)
                termination_reason = "timeout" if returncode == 124 else ("completed" if returncode == 0 else "nonzero_exit")
            thread_id = _extract_thread_id(stdout_path) or resumed_from_thread_id
        finished_at = datetime.now(timezone.utc).isoformat()

        if resume_strategy == "feature_role" and thread_id:
            _store_feature_role_session(
                feature_id=str(packet.get("feature_id")),
                role=role,
                thread_id=thread_id,
                launcher=codex_binary,
                packet_id=packet_id,
                reasoning=reasoning,
                sandbox=sandbox,
                approval=approval,
                model=shared_model,
                session_mode=session_mode,
                run_dir=run_dir,
                resumed_from_thread_id=resumed_from_thread_id,
            )

        attempt_result = CodexLaunchResult(
            packet_id=packet_id,
            returncode=returncode,
            launcher=codex_binary,
            command=command,
            session_mode=session_mode,
            resume_strategy=resume_strategy,
            thread_id=thread_id,
            resumed_from_thread_id=resumed_from_thread_id,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            last_message_path=str(last_message_path),
            started_at=started_at,
            finished_at=finished_at,
            termination_reason=termination_reason,
            attempt=attempt,
            attempt_count=attempt,
            attempts=[],
        ).to_dict()
        attempts.append(attempt_result)

        progress_class = _run_progress_class(stdout_path)

        should_auto_resume = (
            not dry_run
            and returncode != 0
            and bool(thread_id)
            and termination_reason in AUTO_RESUME_TERMINATION_REASONS
            and progress_class not in {"startup_only", "no_output"}
            and attempt <= max_auto_resume_attempts
        )
        if should_auto_resume:
            resume_thread_id = str(thread_id)
            if logger is not None:
                logger.warning(
                    "Codex packet=%s attempt=%s rc=%s reason=%s thread=%s; scheduling automatic resume",
                    packet_id,
                    attempt,
                    returncode,
                    termination_reason,
                    resume_thread_id,
                )
            continue

        should_retry_fresh = (
            not dry_run
            and returncode != 0
            and termination_reason in AUTO_RESUME_TERMINATION_REASONS
            and attempt <= max_auto_resume_attempts
            and progress_class in {"startup_only", "no_output"}
        )
        if should_retry_fresh:
            resume_thread_id = None
            if logger is not None:
                logger.warning(
                    "Codex packet=%s attempt=%s rc=%s reason=%s progress=%s; retrying with fresh exec instead of resume",
                    packet_id,
                    attempt,
                    returncode,
                    termination_reason,
                    progress_class,
                )
            continue

        result = CodexLaunchResult(
            packet_id=packet_id,
            returncode=returncode,
            launcher=codex_binary,
            command=command,
            session_mode=session_mode,
            resume_strategy=resume_strategy,
            thread_id=thread_id,
            resumed_from_thread_id=resumed_from_thread_id,
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            last_message_path=str(last_message_path),
            started_at=started_at,
            finished_at=finished_at,
            termination_reason=termination_reason,
            attempt=attempt,
            attempt_count=len(attempts),
            attempts=attempts,
        ).to_dict()
        break
    update_record(
        "packets",
        "packets",
        "packet_id",
        packet_id,
        {
            "last_codex_run": result,
            "last_execution_run": result,
            "last_thread_id": thread_id,
            "last_session_mode": session_mode,
            "last_resume_strategy": resume_strategy,
            "status": "review" if returncode == 0 else "blocked",
        },
    )
    return result
