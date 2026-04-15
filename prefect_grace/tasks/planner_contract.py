from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from prefect_grace.models import PacketStatus, ReasoningProfile
from prefect_grace.tasks.state_store import find_record, update_record

WAVE_PLAN_MARKER_START = "FINAL_GRACE_WAVE_PLAN_JSON"
WAVE_PLAN_MARKER_END = "END_FINAL_GRACE_WAVE_PLAN_JSON"

FEATURES_DIR = Path(__file__).resolve().parents[1] / "packets"


def default_wave_plan_contract(
    *,
    feature_id: str,
    implementation_title: str,
    implementation_summary: str,
    verifier_backend_profile: str | None = "backend_quick",
    verifier_frontend_profile: str | None = None,
    verifier_frontend_commands: list[str] | None = None,
    verifier_observability_profile: str | None = None,
    verifier_observability_commands: list[str] | None = None,
    verifier_artifact_globs: list[str] | None = None,
    verifier_touches_frontend: bool = False,
    verifier_requires_frontend_visual: bool = False,
    verifier_include_day_live_canary: bool = False,
) -> dict[str, Any]:
    coder_key = "coder_main"
    verifier_key = "verifier_main"
    reviewer_key = "reviewer_main"
    architect_key = "architect_wave_gate"
    return {
        "waves": [
            {
                "wave_id": "W01",
                "title": "Implementation and acceptance wave",
                "objective": "Implement, verify, review, and architect-accept the first bounded feature slice.",
                "exit_conditions": [
                    "Coder packet is completed within scope.",
                    "Verifier evidence is recorded.",
                    "Reviewer technical gate is accepted or routed to rework.",
                    "Architect wave gate accepts or blocks the wave.",
                ],
            }
        ],
        "packets": [
            {
                "key": coder_key,
                "wave_id": "W01",
                "title": implementation_title,
                "role": "coder",
                "reasoning": ReasoningProfile.HIGH.value,
                "summary": implementation_summary,
                "write_scope": [
                    "Only files required by the packet.",
                    "Bounded implementation/refactor required by the feature brief.",
                ],
                "inputs": ["planner output", "architect formalization", "feature brief"],
                "acceptance_criteria": [
                    "Requested code change is implemented within scope.",
                    "Targeted tests are added or updated if needed.",
                    "Implementation notes are left for verifier and reviewer.",
                ],
                "verification_profile": {
                    "backend": "backend:quick or targeted tests as required by the packet",
                    "frontend": "targeted Playwright run if the packet touches UI",
                    "observability": "post-test log, digest, and trace review",
                },
                "reviewer_gate": ["Packet scope respected.", "Verification handoff notes included."],
                "dependencies": [],
                "notes": ["Prefer root-cause fixes.", "Strengthen logs if the packet touches runtime flow."],
            },
            {
                "key": verifier_key,
                "wave_id": "W01",
                "title": "Verifier Evidence",
                "role": "verifier",
                "reasoning": ReasoningProfile.HIGH.value,
                "summary": "Validate the coder packet with the required test profile and observability gate.",
                "write_scope": ["Verification notes and evidence references only."],
                "inputs": [coder_key, "coder packet file"],
                "acceptance_criteria": [
                    "Commands run are recorded.",
                    "Evidence paths are recorded.",
                    "Observability verdict is explicit.",
                    "Frontend visual verdict is explicit when UI is touched.",
                ],
                "verification_profile": {
                    "backend": "execute minimally sufficient backend profile",
                    "frontend": "execute minimally sufficient frontend profile if UI is touched",
                    "observability": "mandatory log, replay, digest, and trace review",
                },
                "reviewer_gate": [
                    "No green-only pass without evidence review.",
                    "Blocking issues are explicit when evidence is missing.",
                ],
                "dependencies": [coder_key],
                "notes": ["Fail the packet if evidence is missing."],
                "execution_hints": {
                    "runner": "verifier",
                    "backend_profile": verifier_backend_profile,
                    "frontend_profile": verifier_frontend_profile,
                    "frontend_commands": verifier_frontend_commands or [],
                    "observability_profile": verifier_observability_profile,
                    "observability_commands": verifier_observability_commands or [],
                    "touches_frontend": verifier_touches_frontend,
                    "requires_frontend_visual": verifier_requires_frontend_visual,
                    "artifact_globs": verifier_artifact_globs or [],
                    "include_day_live_canary": verifier_include_day_live_canary,
                },
            },
            {
                "key": reviewer_key,
                "wave_id": "W01",
                "title": "Reviewer Verdict",
                "role": "reviewer",
                "reasoning": ReasoningProfile.XHIGH.value,
                "summary": "Judge the packet outcome and decide accepted, rework_required, blocked, or escalate_to_architect.",
                "write_scope": ["Review verdict and blocker notes only."],
                "inputs": [coder_key, verifier_key],
                "acceptance_criteria": [
                    "Exactly one verdict is returned.",
                    "Blockers are actionable.",
                    "Follow-up action is explicit.",
                ],
                "verification_profile": {
                    "backend": "not required",
                    "frontend": "not required",
                    "observability": "consume verifier evidence and notes",
                },
                "reviewer_gate": ["Do not invent new scope.", "Do not accept missing evidence."],
                "dependencies": [coder_key, verifier_key],
                "notes": ["Escalate to architect when the blocker changes decomposition or business semantics."],
                "review_target_key": coder_key,
            },
            {
                "key": architect_key,
                "wave_id": "W01",
                "title": "Architect Wave Gate",
                "role": "architect",
                "reasoning": ReasoningProfile.XHIGH.value,
                "summary": "Accept or reject the completed wave based on business fit, UX, visual proof, and overall feature intent.",
                "write_scope": ["Wave acceptance note only.", "No direct implementation changes in this gate packet."],
                "inputs": [reviewer_key, verifier_key, coder_key, "wave plan"],
                "acceptance_criteria": [
                    "Wave result matches business intent.",
                    "Frontend visual proof is sufficient when UI is touched.",
                    "Technical acceptance is backed by verifier and reviewer evidence.",
                ],
                "verification_profile": {
                    "backend": "consume verifier evidence",
                    "frontend": "review screenshots, Playwright evidence, and expected UI states if UI is touched",
                    "observability": "review verifier observability verdict for the wave",
                },
                "reviewer_gate": ["Architect confirms wave acceptance or rejects it with explicit reasons."],
                "dependencies": [reviewer_key],
                "notes": [
                    "This is the wave-level acceptance gate.",
                    "Frontend visual review belongs here when the wave touches UI.",
                ],
            },
        ],
    }


def normalize_wave_plan_contract(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Planner contract must be a JSON object")
    packets = payload.get("packets")
    if not isinstance(packets, list) or not packets:
        raise ValueError("Planner contract must contain non-empty packets list")
    waves = payload.get("waves")
    if waves is not None and not isinstance(waves, list):
        raise ValueError("Planner contract waves must be a list")

    normalized_packets: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    for index, packet in enumerate(packets):
        if not isinstance(packet, dict):
            raise ValueError(f"Packet #{index + 1} must be an object")
        key = str(packet.get("key") or packet.get("title") or f"packet_{index + 1}").strip()
        if not key:
            raise ValueError(f"Packet #{index + 1} key is empty")
        if key in seen_keys:
            raise ValueError(f"Duplicate packet key: {key}")
        seen_keys.add(key)
        role = str(packet.get("role") or "coder").strip().lower()
        if role not in {"coder", "verifier", "reviewer", "architect", "planner"}:
            raise ValueError(f"Unsupported packet role for {key}: {role}")
        reasoning = str(packet.get("reasoning") or _default_reasoning_for_role(role)).strip().lower()
        ReasoningProfile(reasoning)
        normalized_packets.append(
            {
                "key": key,
                "wave_id": str(packet.get("wave_id") or "W01").strip().upper(),
                "title": str(packet.get("title") or key).strip(),
                "role": role,
                "reasoning": reasoning,
                "summary": str(packet.get("summary") or packet.get("title") or key).strip(),
                "write_scope": _string_list(packet.get("write_scope")),
                "inputs": _string_list(packet.get("inputs")),
                "acceptance_criteria": _string_list(packet.get("acceptance_criteria")),
                "verification_profile": dict(packet.get("verification_profile") or {}),
                "reviewer_gate": _string_list(packet.get("reviewer_gate")),
                "dependencies": _string_list(packet.get("dependencies")),
                "notes": _string_list(packet.get("notes")),
                "execution_hints": dict(packet.get("execution_hints") or {}),
                "review_target_key": str(packet.get("review_target_key") or "").strip(),
            }
        )

    known_keys = {packet["key"] for packet in normalized_packets}
    for packet in normalized_packets:
        unknown_dependencies = [dependency for dependency in packet["dependencies"] if dependency not in known_keys]
        if unknown_dependencies:
            raise ValueError(f"Packet {packet['key']} has unknown dependencies: {unknown_dependencies}")

    return {
        "waves": [dict(wave) for wave in waves or [] if isinstance(wave, dict)],
        "packets": normalized_packets,
    }


def materialize_planner_contract(
    *,
    feature_id: str,
    planner_packet_id: str,
    architect_packet_id: str,
    contract: dict[str, Any],
    base_execution_hints: dict[str, Any] | None = None,
    default_verifier_execution_hints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = normalize_wave_plan_contract(contract)
    key_to_packet_id: dict[str, str] = {}
    materialized: list[dict[str, Any]] = []
    base_hints = dict(base_execution_hints or {})

    for packet_spec in normalized["packets"]:
        dependencies = [key_to_packet_id[key] for key in packet_spec["dependencies"]]
        if packet_spec["role"] == "coder" and not dependencies:
            dependencies = [planner_packet_id]
        execution_hints = _resolve_execution_hints(
            packet_spec,
            base_execution_hints=base_hints,
            default_verifier_execution_hints=default_verifier_execution_hints,
        )
        from prefect_grace.tasks.feature_bootstrap import create_packet

        packet = create_packet(
            feature_id=feature_id,
            wave_id=packet_spec["wave_id"],
            title=packet_spec["title"],
            role=packet_spec["role"],
            reasoning=ReasoningProfile(packet_spec["reasoning"]),
            summary=packet_spec["summary"],
            write_scope=packet_spec["write_scope"],
            inputs=_resolve_inputs(packet_spec["inputs"], key_to_packet_id, planner_packet_id, architect_packet_id),
            acceptance_criteria=packet_spec["acceptance_criteria"],
            verification_profile=packet_spec["verification_profile"],
            reviewer_gate=packet_spec["reviewer_gate"],
            dependencies=dependencies,
            notes=packet_spec["notes"],
            execution_hints=execution_hints,
            status=PacketStatus.READY,
        )
        review_target_key = str(packet_spec.get("review_target_key") or "").strip()
        if review_target_key:
            packet = update_record(
                "packets",
                "packets",
                "packet_id",
                packet["packet_id"],
                {"review_target_packet_id": key_to_packet_id.get(review_target_key, "")},
            )
        key_to_packet_id[packet_spec["key"]] = packet["packet_id"]
        materialized.append(packet)

    wave_plan_path = _write_dynamic_wave_plan(feature_id, normalized["waves"], materialized)
    update_record(
        "features",
        "features",
        "feature_id",
        feature_id,
        {
            "status": "planned",
            "wave_plan_path": wave_plan_path,
            "planner_contract": normalized,
        },
    )
    return {
        "waves": normalized["waves"],
        "packets": materialized,
        "packets_by_key": key_to_packet_id,
        "wave_plan_path": wave_plan_path,
    }


def find_first_packet_id(packets: list[dict[str, Any]], *, role: str) -> str:
    for packet in packets:
        if str(packet.get("role") or "") == role:
            return str(packet["packet_id"])
    raise ValueError(f"Planner contract did not produce a {role} packet")


def find_architect_wave_gate_packet_id(packets: list[dict[str, Any]]) -> str:
    for packet in packets:
        if str(packet.get("role") or "") == "architect" and str(packet.get("wave_id") or "").upper() != "W00":
            return str(packet["packet_id"])
    return find_first_packet_id(packets, role="architect")


def _default_reasoning_for_role(role: str) -> str:
    if role in {"architect", "planner", "reviewer"}:
        return ReasoningProfile.XHIGH.value
    return ReasoningProfile.HIGH.value


def _string_list(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _resolve_inputs(
    inputs: list[str],
    key_to_packet_id: dict[str, str],
    planner_packet_id: str,
    architect_packet_id: str,
) -> list[str]:
    resolved: list[str] = []
    for item in inputs:
        if item in key_to_packet_id:
            resolved.append(key_to_packet_id[item])
        elif item == "planner output":
            resolved.append(planner_packet_id)
        elif item == "architect formalization":
            resolved.append(architect_packet_id)
        else:
            resolved.append(item)
    return resolved


def _write_dynamic_wave_plan(feature_id: str, waves: list[dict[str, Any]], packets: list[dict[str, Any]]) -> str:
    feature = find_record("features", "features", "feature_id", feature_id)
    feature_dir = Path(feature["feature_dir"])
    wave_lines = []
    for wave in waves:
        wave_id = str(wave.get("wave_id") or "W01")
        title = str(wave.get("title") or "Untitled wave")
        objective = str(wave.get("objective") or "")
        wave_lines.append(f"{wave_id} — {title}: {objective}".strip())
    if not wave_lines:
        wave_lines = sorted({f"{packet['wave_id']} — generated execution wave" for packet in packets})

    packet_lines = [
        f"`{packet['packet_id']}` — role `{packet['role']}` — {packet['title']}"
        for packet in packets
    ]
    dependency_lines = [
        f"`{packet['packet_id']}` depends on {', '.join(packet.get('dependencies') or ['nothing'])}"
        for packet in packets
    ]
    exit_conditions: list[str] = []
    for wave in waves:
        exit_conditions.extend(_string_list(wave.get("exit_conditions")))
    if not exit_conditions:
        exit_conditions = [
            "All generated coder packets are implemented.",
            "Verifier evidence is recorded for the wave.",
            "Reviewer and architect gates are resolved.",
        ]

    wave_plan_path = feature_dir / "wave-plan.md"
    wave_plan_path.write_text(
        "\n".join(
            [
                f"# Wave Plan: {feature_id}",
                "",
                "## Objective",
                str(feature.get("title") or feature_id),
                "",
                "## Waves",
                _markdown_numbered(wave_lines),
                "",
                "## Packet Registry",
                _markdown_bullets(packet_lines),
                "",
                "## Dependency Rules",
                _markdown_bullets(dependency_lines),
                "",
                "## Exit Conditions",
                _markdown_bullets(exit_conditions),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return str(wave_plan_path)


def _markdown_bullets(items: list[str]) -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    return "\n".join(f"- {item}" for item in cleaned) if cleaned else "-"


def _markdown_numbered(items: list[str]) -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    return "\n".join(f"{index}. {item}" for index, item in enumerate(cleaned, start=1)) if cleaned else "1."


COMMAND_PATTERN = re.compile(r"`([^`\n]+)`")


def _resolve_execution_hints(
    packet_spec: dict[str, Any],
    *,
    base_execution_hints: dict[str, Any],
    default_verifier_execution_hints: dict[str, Any] | None,
) -> dict[str, Any]:
    packet_hints = dict(packet_spec.get("execution_hints") or {})
    if packet_spec["role"] != "verifier":
        return {**base_execution_hints, **packet_hints}

    verifier_defaults = dict(default_verifier_execution_hints or {})
    hints: dict[str, Any] = {**base_execution_hints, **verifier_defaults, **packet_hints}
    hints.setdefault("runner", "verifier")

    verifier_execution = dict(packet_spec.get("verification_profile") or {}).get("execution")
    if isinstance(verifier_execution, dict):
        backend_commands = _extract_commands(verifier_execution.get("backend_commands"))
        frontend_commands = _extract_commands(verifier_execution.get("frontend_commands"))
        observability_commands = _extract_commands(verifier_execution.get("observability_commands"))
        if backend_commands:
            hints["backend_commands"] = backend_commands
            hints.pop("backend_profile", None)
        if frontend_commands:
            hints["frontend_commands"] = frontend_commands
            hints.pop("frontend_profile", None)
        if observability_commands:
            hints["observability_commands"] = observability_commands
            hints.pop("observability_profile", None)
        if "touches_frontend" not in packet_hints and "touches_frontend" in verifier_execution:
            hints["touches_frontend"] = bool(verifier_execution.get("touches_frontend"))
        if "requires_frontend_visual" not in packet_hints and "requires_frontend_visual" in verifier_execution:
            hints["requires_frontend_visual"] = bool(verifier_execution.get("requires_frontend_visual"))
        if "artifact_globs" not in packet_hints and verifier_execution.get("artifact_globs") is not None:
            hints["artifact_globs"] = _string_list(verifier_execution.get("artifact_globs"))
        if "include_day_live_canary" not in packet_hints and "include_day_live_canary" in verifier_execution:
            hints["include_day_live_canary"] = bool(verifier_execution.get("include_day_live_canary"))

    return hints


def _extract_commands(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, list):
        commands: list[str] = []
        for item in value:
            commands.extend(_extract_commands(item))
        return commands
    text = str(value)
    commands = [match.strip() for match in COMMAND_PATTERN.findall(text) if match.strip()]
    if commands:
        return commands
    stripped = text.strip()
    if not stripped or "not required" in stripped.lower():
        return []
    if any(token in stripped for token in ("./", "python", "pnpm", "npm", "docker ", "docker exec", "bash ", "corepack ")):
        return [stripped]
    return []
