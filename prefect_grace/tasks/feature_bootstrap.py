from __future__ import annotations

from pathlib import Path
from typing import Any

from prefect_grace.models import FeatureRecord, FeatureStatus, PacketRecord, PacketStatus, ReasoningProfile, slugify
from prefect_grace.tasks.architect_artifacts import default_architect_artifact_plan
from prefect_grace.tasks.planner_contract import default_wave_plan_contract, materialize_planner_contract
from prefect_grace.tasks.state_store import append_record, find_record, update_record

FEATURES_DIR = Path(__file__).resolve().parents[1] / "packets"
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"


def _render_template(template_name: str, replacements: dict[str, str]) -> str:
    template = (TEMPLATE_DIR / template_name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        template = template.replace("{{ " + key + " }}", value)
    return template


def _bullet_lines(items: list[str] | None) -> str:
    cleaned = [item.strip() for item in items or [] if item and item.strip()]
    return "\n".join(f"- {item}" for item in cleaned) if cleaned else "-"


def _numbered_lines(items: list[str] | None) -> str:
    cleaned = [item.strip() for item in items or [] if item and item.strip()]
    return "\n".join(f"{index}. {item}" for index, item in enumerate(cleaned, start=1)) if cleaned else "1."


def _verification_lines(profile: dict[str, str] | None) -> str:
    merged = {
        "backend": "not required",
        "frontend": "not required",
        "observability": "artifact review only",
    }
    merged.update(profile or {})
    return "\n".join(f"- {key}: {value}" for key, value in merged.items())


def _execution_hint_lines(hints: dict[str, Any] | None) -> str:
    if not hints:
        return "-"
    lines: list[str] = []
    for key, value in hints.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            if not value:
                continue
            lines.append(f"- {key}:")
            lines.extend(f"  - {item}" for item in value)
        else:
            lines.append(f"- {key}: {value}")
    return "\n".join(lines) if lines else "-"


def _write_wave_plan(feature_dir: Path, feature_id: str, title: str, packets: list[dict[str, Any]]) -> str:
    packet_registry = [
        f"`{packet['packet_id']}` — role `{packet['role']}` — {packet['title']}"
        for packet in packets
    ]
    dependency_rules = [
        f"`{packet['packet_id']}` depends on {', '.join(packet.get('dependencies') or ['nothing'])}"
        for packet in packets
    ]
    wave_plan_path = feature_dir / "wave-plan.md"
    wave_plan_path.write_text(
        _render_template(
            "wave_plan.md",
            {
                "feature_id": feature_id,
                "objective": title,
                "waves": _numbered_lines(
                    [
                        "W00 — architect formalization and planner slicing.",
                        "W01 — implementation, verifier evidence, reviewer technical gate, architect wave gate.",
                    ]
                ),
                "packet_registry": _bullet_lines(packet_registry),
                "dependency_rules": _bullet_lines(dependency_rules),
                "exit_conditions": _bullet_lines(
                    [
                        "Architect packet produced feature-local artifact deltas.",
                        "Planner packet defined bounded execution packets.",
                        "Implementation, verifier, reviewer, and architect wave gate completed in order.",
                    ]
                ),
            },
        ),
        encoding="utf-8",
    )
    return str(wave_plan_path)


def bootstrap_feature(
    feature_id: str,
    title: str,
    summary: str,
    business_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    feature_dir = FEATURES_DIR / feature_id
    feature_dir.mkdir(parents=True, exist_ok=True)
    (feature_dir / "packets").mkdir(exist_ok=True)
    (feature_dir / "reviews").mkdir(exist_ok=True)
    (feature_dir / "decisions").mkdir(exist_ok=True)
    (feature_dir / "evidence").mkdir(exist_ok=True)

    brief_path = feature_dir / "feature-brief.md"
    brief_text = _render_template(
        "feature_brief.md",
        {
            "feature_id": feature_id,
            "business_intent": summary,
            "desired_outcome": title,
            "in_scope": _bullet_lines(
                list((business_context or {}).get("scope") or [
                    "Formalize the feature into GRACE artifacts.",
                    "Slice the feature into bounded execution packets.",
                    "Prepare implementation, verification, and review flow.",
                ])
            ),
            "out_of_scope": _bullet_lines(
                list((business_context or {}).get("non_goals") or [
                    "Full production rollout of the feature.",
                    "Unbounded refactors outside the packet scopes.",
                ])
            ),
            "impacted_surfaces": _bullet_lines(
                list((business_context or {}).get("impacted_surfaces") or [
                    "backend: packet orchestration and state tracking.",
                    "frontend: define visual verification requirements when UI is touched.",
                    "automation: Prefect flows and Codex launcher integration.",
                    "observability: logs, evidence, and reviewer verdict routing.",
                ])
            ),
            "impacted_grace_artifacts": _bullet_lines(
                list((business_context or {}).get("impacted_grace_artifacts") or [
                    "requirements.xml: feature scope and invariants if they change.",
                    "technology.xml: runtime or toolchain updates if they change.",
                    "development-plan.xml: execution topology and packet model.",
                    "knowledge-graph.xml: impacted modules and flow links.",
                    "verification-matrix.md: required tests and evidence gates.",
                ])
            ),
            "wave_proposal": _numbered_lines(
                list((business_context or {}).get("wave_proposal") or [
                    "Architect formalizes the feature and impacted GRACE deltas.",
                    "Planner slices execution into waves and packets.",
                    "Coder, verifier, reviewer, and architect execute W01.",
                ])
            ),
            "open_decisions": _bullet_lines(
                list((business_context or {}).get("open_decisions") or [
                    "Confirm whether the feature needs frontend visual proof.",
                    "Confirm whether the first execution should stay dry-run or use real Codex runs.",
                ])
            ),
            "acceptance_criteria": _bullet_lines(list((business_context or {}).get("acceptance_criteria") or [])),
            "visual_expectations": _bullet_lines(list((business_context or {}).get("visual_expectations") or [])),
        },
    )
    if not brief_path.exists() or business_context:
        brief_path.write_text(brief_text, encoding="utf-8")

    try:
        find_record("features", "features", "feature_id", feature_id)
        return update_record(
            "features",
            "features",
            "feature_id",
            feature_id,
            {
                "title": title,
                "summary": summary,
                "feature_dir": str(feature_dir),
                "business_context": business_context or {},
            },
        )
    except KeyError:
        record = FeatureRecord(
            feature_id=feature_id,
            title=title,
            summary=summary,
            status=FeatureStatus.DRAFT,
            feature_dir=str(feature_dir),
            business_context=business_context or {},
        ).to_dict()
        append_record("features", "features", record)
        return record


def mark_feature_status(feature_id: str, status: FeatureStatus) -> dict[str, Any]:
    return update_record("features", "features", "feature_id", feature_id, {"status": status.value})


def create_packet(
    *,
    feature_id: str,
    wave_id: str,
    title: str,
    role: str,
    reasoning: ReasoningProfile,
    summary: str,
    write_scope: list[str] | None = None,
    inputs: list[str] | None = None,
    acceptance_criteria: list[str] | None = None,
    verification_profile: dict[str, str] | None = None,
    reviewer_gate: list[str] | None = None,
    dependencies: list[str] | None = None,
    notes: list[str] | None = None,
    parent_packet_id: str | None = None,
    execution_hints: dict[str, Any] | None = None,
    status: PacketStatus = PacketStatus.READY,
) -> dict[str, Any]:
    packet_slug = slugify(title)
    packet_id = f"{feature_id}-{wave_id}-{packet_slug}".upper()
    feature_dir = FEATURES_DIR / feature_id
    packet_dir = feature_dir / "packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    packet_path = packet_dir / f"{packet_id}.md"
    packet_path.write_text(
        _render_template(
            "packet.md",
            {
                "packet_id": packet_id,
                "summary": summary,
                "wave_id": wave_id,
                "role": role,
                "reasoning": reasoning.value,
                "write_scope": _bullet_lines(write_scope),
                "inputs": _bullet_lines(inputs),
                "acceptance_criteria": _bullet_lines(acceptance_criteria),
                "verification_profile": _verification_lines(verification_profile),
                "execution_hints": _execution_hint_lines(execution_hints),
                "reviewer_gate": _bullet_lines(reviewer_gate),
                "dependencies": _bullet_lines(dependencies),
                "notes": _bullet_lines(notes),
            },
        ),
        encoding="utf-8",
    )
    record = PacketRecord(
        packet_id=packet_id,
        feature_id=feature_id,
        wave_id=wave_id,
        title=title,
        summary=summary,
        role=role,
        reasoning=reasoning,
        status=status,
        dependencies=dependencies or [],
        parent_packet_id=parent_packet_id,
        execution_hints=execution_hints or {},
        packet_path=str(packet_path),
    ).to_dict()
    try:
        find_record("packets", "packets", "packet_id", packet_id)
        return update_record("packets", "packets", "packet_id", packet_id, record)
    except KeyError:
        append_record("packets", "packets", record)
        return record


def seed_test_feature(
    *,
    feature_id: str,
    title: str,
    summary: str,
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
    agent_workdir: str | None = None,
    agent_sandbox: str | None = None,
    business_context: dict[str, Any] | None = None,
    planner_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    feature = bootstrap_feature(feature_id=feature_id, title=title, summary=summary, business_context=business_context)
    business_context = dict(business_context or {})
    architect_artifact_plan = default_architect_artifact_plan(
        feature_id=feature_id,
        title=title,
        summary=summary,
        business_context=business_context,
    )
    base_execution_hints = {
        key: value
        for key, value in {
            "workdir": agent_workdir,
            "sandbox": agent_sandbox,
        }.items()
        if value not in (None, "")
    }

    architect_packet = create_packet(
        feature_id=feature_id,
        wave_id="W00",
        title="Architect Formalization",
        role="architect",
        reasoning=ReasoningProfile.XHIGH,
        summary="Formalize the business feature into incremental GRACE artifact deltas and define execution boundaries.",
        write_scope=[
            "Feature-local GRACE artifacts for this feature.",
            "Impacted sections of core GRACE documents if required.",
        ],
        inputs=[
            f"Feature brief `{feature_id}/feature-brief.md`.",
            "Current repository GRACE baseline.",
        ],
        acceptance_criteria=[
            "Impacted artifacts are explicitly identified.",
            "Architect produces slice-local GRACE docs before planning.",
            "Open decisions are separated from execution-ready facts.",
            "Wave boundaries are concrete enough for planner handoff.",
        ],
        verification_profile={
            "backend": "not required",
            "frontend": "not required",
            "observability": "artifact review and consistency check",
        },
        reviewer_gate=[
            "No missing artifact delta for impacted surfaces.",
            "No silent scope expansion.",
        ],
        notes=[
            "Patch existing GRACE files incrementally.",
            "Write slice-local GRACE docs and architect manifest before planner handoff.",
            "Keep frontend verification explicit if UI is touched.",
            "Return FINAL_ARCHITECT_ARTIFACT_PLAN_JSON markers.",
        ],
        execution_hints=base_execution_hints,
    )

    planner_packet = create_packet(
        feature_id=feature_id,
        wave_id="W00",
        title="Planner Slicing",
        role="planner",
        reasoning=ReasoningProfile.XHIGH,
        summary="Slice the feature into waves and execution packets with explicit dependencies and acceptance gates.",
        write_scope=[
            "Feature-local wave plan.",
            "Packet definitions for execution waves.",
        ],
        inputs=[
            architect_packet["packet_id"],
            "Architect manifest and handoff.",
            f"Feature brief `{feature_id}/feature-brief.md`.",
        ],
        acceptance_criteria=[
            "Every packet has one primary write scope.",
            "Verification and reviewer gates are explicit.",
            "Dependencies allow deterministic execution order.",
            "Planner returns parseable JSON wave contract.",
        ],
        verification_profile={
            "backend": "not required",
            "frontend": "not required",
            "observability": "artifact dependency review",
        },
        reviewer_gate=[
            "No oversized packets.",
            "No packet without verification expectations.",
        ],
        dependencies=[architect_packet["packet_id"]],
        notes=[
            "Prefer smaller packets over broad scopes.",
            "Flag architect escalation when decomposition is ambiguous.",
            "Return FINAL_GRACE_WAVE_PLAN_JSON markers.",
        ],
        execution_hints=base_execution_hints,
    )

    contract = planner_contract or default_wave_plan_contract(
        feature_id=feature_id,
        implementation_title=implementation_title,
        implementation_summary=implementation_summary,
        verifier_backend_profile=verifier_backend_profile,
        verifier_frontend_profile=verifier_frontend_profile,
        verifier_frontend_commands=verifier_frontend_commands,
        verifier_observability_profile=verifier_observability_profile,
        verifier_observability_commands=verifier_observability_commands,
        verifier_artifact_globs=verifier_artifact_globs,
        verifier_touches_frontend=verifier_touches_frontend,
        verifier_requires_frontend_visual=verifier_requires_frontend_visual,
        verifier_include_day_live_canary=verifier_include_day_live_canary,
    )
    materialized = materialize_planner_contract(
        feature_id=feature_id,
        planner_packet_id=planner_packet["packet_id"],
        architect_packet_id=architect_packet["packet_id"],
        contract=contract,
        base_execution_hints=base_execution_hints,
        default_verifier_execution_hints={
            "runner": "verifier",
            "backend_profile": verifier_backend_profile,
            "frontend_profile": verifier_frontend_profile,
            "frontend_commands": verifier_frontend_commands or [],
            "observability_profile": verifier_observability_profile,
            "observability_commands": verifier_observability_commands or [],
            "artifact_globs": verifier_artifact_globs or [],
            "touches_frontend": verifier_touches_frontend,
            "requires_frontend_visual": verifier_requires_frontend_visual,
            "include_day_live_canary": verifier_include_day_live_canary,
        },
    )

    packets = [architect_packet, planner_packet, *materialized["packets"]]
    return {
        "feature": {
            **find_record("features", "features", "feature_id", feature_id),
            "wave_plan_path": materialized["wave_plan_path"],
        },
        "packets": {
            "architect": architect_packet,
            "planner": planner_packet,
            "generated": materialized["packets"],
            "packets_by_key": materialized["packets_by_key"],
        },
        "planner_contract": materialized,
    }
