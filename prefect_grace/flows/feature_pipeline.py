from __future__ import annotations

import json
from pathlib import Path

from prefect_grace.models import (
    FeatureStatus,
    FrontendVisualVerdict,
    ObservabilityVerdict,
    PacketStatus,
    ReasoningProfile,
    ReviewVerdict,
    TestVerdict,
    WaveVerdict,
)
from prefect_grace.prefect_compat import flow, get_run_logger, tags, task
from prefect_grace.flows.pipeline_helpers.evidence_collector import (
    append_evidence_path as _append_evidence_path,
    artifact_glob_matches as _artifact_glob_matches,
    candidate_file_path as _candidate_file_path,
    collect_candidate_commit_files as _collect_candidate_commit_files,
    collect_candidate_commit_files_from_payload as _collect_candidate_commit_files_from_payload,
    collect_verifier_supplemental_evidence as _collect_verifier_supplemental_evidence,
    enrich_verifier_evidence_paths as _enrich_verifier_evidence_paths,
    existing_file_path as _existing_file_path,
    feature_line_records as _feature_line_records,
    find_commit_marker as _find_commit_marker,
    normalize_commit_marker as _normalize_commit_marker,
    normalize_evidence_path as _normalize_evidence_path,
    path_candidates_from_text as _path_candidates_from_text,
    verifier_packet_for_run as _verifier_packet_for_run,
)
from prefect_grace.flows.pipeline_helpers.normalizers import (
    normalize_observability_scope as _normalize_observability_scope,
)
from prefect_grace.flows.pipeline_helpers.rework_routing import (
    REWORK_MODE_BOUNDED_FRESH,
    REWORK_MODE_DECISION_REQUIRED,
    REWORK_MODE_LIGHT_RESUME,
    REWORK_ROUTE_REQUIRES_PLANNER,
    REWORK_ROUTE_REQUIRES_USER_DECISION,
    REWORK_ROUTE_SELF_RESOLVABLE,
    REWORK_ROUTING_ARCHITECT_FIRST,
    REWORK_ROUTING_AUTO_BUNDLE,
    classify_rework_mode as _classify_rework_mode,
    classify_rework_route as _classify_rework_route,
    classify_rework_route_from_reasons as _classify_rework_route_from_reasons,
    escalate_repeated_observability_rework_for_pipeline as _escalate_repeated_observability_rework_for_pipeline,
    normalize_reviewer_decision_for_pipeline as _normalize_reviewer_decision_for_pipeline,
    normalize_rework_mode as _normalize_rework_mode,
    normalize_rework_route_classification as _normalize_rework_route_classification,
    packet_execution_contract as _packet_execution_contract,
    string_command_list as _string_command_list,
    uses_today_week_observability as _uses_today_week_observability,
)
from prefect_grace.flows.pipeline_helpers.status_formatter import (
    failure_status_for_category as _failure_status_for_category,
    final_user_summary as _final_user_summary,
    short_reason as _short_reason,
    status_label_ru as _status_label_ru,
)
from prefect_grace.flows.pipeline_helpers.wave_progression import (
    all_required_waves_accepted as _all_required_waves_accepted,
    architect_wave_gate_packet_id_for_wave as _architect_wave_gate_packet_id_for_wave,
    build_wave_progression as _build_wave_progression,
    is_execution_wave_id as _is_execution_wave_id,
    next_required_wave_id as _next_required_wave_id,
    normalize_wave_progression_entry as _normalize_wave_progression_entry,
    plan_wave_sequence as _plan_wave_sequence,
    required_wave_progression_issues as _required_wave_progression_issues,
    wave_id_from_issue as _wave_id_from_issue,
    wave_packets_by_wave_id as _wave_packets_by_wave_id,
    wave_required as _wave_required,
)
from prefect_grace.tasks.agent_output_parser import (
    parse_architect_artifact_plan_message,
    parse_direct_rework_packet_message,
    parse_planner_wave_plan_message,
    read_agent_message,
    resolve_reviewer_decision,
    resolve_verifier_result,
    resolve_wave_decision,
)
from prefect_grace.tasks.architect_artifacts import default_architect_artifact_plan, write_architect_artifacts
from prefect_grace.tasks.codex_launcher import launch_codex_for_packet
from prefect_grace.tasks.feature_bootstrap import bootstrap_feature, create_packet, mark_feature_status, seed_test_feature, sync_packet_file
from prefect_grace.tasks.planner_contract import (
    default_wave_plan_contract,
    find_architect_wave_gate_packet_id,
    find_first_packet_id,
    materialize_planner_contract,
    normalize_wave_plan_contract,
)
from prefect_grace.tasks.prefect_artifacts import publish_feature_artifacts, publish_packet_task_artifacts
from prefect_grace.tasks.review_router import (
    create_architect_decision_from_review,
    create_architect_rework_packet_from_review,
    create_direct_rework_from_architect,
    create_rework_bundle_from_review,
    create_rework_from_review,
    record_review,
    record_wave_review,
)
from prefect_grace.tasks.state_store import find_record, load_state, update_record
from prefect_grace.tasks.telegram_notify import notify_feature_event, notify_packet_event
from prefect_grace.tasks.verification_router import record_verification
from prefect_grace.tasks.wave_executor import (
    append_unique_packet,
    missing_internal_dependencies,
    order_packets_for_wave,
    packet_has_downstream_reviewer,
    packet_map,
    packet_result_key,
    reviewer_target_packet_id,
)
def _final_failure(
    *,
    feature_id: str,
    category: str,
    next_action: str,
    reasons: list[str] | None = None,
    next_wave_id: str | None = None,
) -> dict:
    feature = mark_feature_status(
        feature_id,
        _failure_status_for_category(category),
        blocker_reasons=list(reasons or []),
    )
    failure_updates: dict[str, object] = {}
    if next_wave_id is not None:
        failure_updates["next_wave_id"] = str(next_wave_id)
    if failure_updates:
        feature = update_record("features", "features", "feature_id", feature_id, failure_updates)
    return {
        "feature": feature,
        "has_failures": True,
        "final_outcome": "blocked",
        "user_facing_status": str(feature.get("status") or _failure_status_for_category(category).value),
        "user_summary": _final_user_summary(
            outcome="blocked",
            status=str(feature.get("status") or _failure_status_for_category(category).value),
            summary=str(feature.get("summary") or ""),
            next_action=next_action,
            reasons=list(reasons or []),
        ),
        "next_action": next_action,
        "failure_category": category,
        "reasons": list(reasons or []),
        "wave_progression": [dict(item) for item in list(feature.get("wave_progression") or [])],
        "next_wave_id": str(feature.get("next_wave_id") or ""),
        "all_required_waves_accepted": bool(feature.get("all_required_waves_accepted")),
    }


POST_ACCEPTANCE_NEXT_ACTION = "commit-feature-changes"


def _post_acceptance_final_status(
    *,
    feature_id: str,
    accepted_feature: dict,
    summary: str,
    packet_results: dict,
    verification_records: list[dict],
    review_routes: list[dict],
    wave_routes: list[dict],
    commit_hash: str | None,
    wave_progression: list[dict[str, object]] | None = None,
) -> dict:
    detected_commit = _normalize_commit_marker(commit_hash) or _find_commit_marker(accepted_feature) or _find_commit_marker(packet_results)
    candidate_commit_files = _collect_candidate_commit_files(
        feature_id=feature_id,
        feature=accepted_feature,
        packet_results=packet_results,
        verification_records=verification_records,
        review_routes=review_routes,
        wave_routes=wave_routes,
    )
    if detected_commit:
        resolved_wave_progression = [dict(item) for item in wave_progression or accepted_feature.get("wave_progression") or []]
        feature_updates = {
            "commit_status": "committed",
            "commit_hash": detected_commit,
            "candidate_commit_files": candidate_commit_files,
            "wave_progression": resolved_wave_progression,
            "next_wave_id": "",
            "all_required_waves_accepted": True,
        }
        committed_feature = update_record("features", "features", "feature_id", feature_id, feature_updates)
        return {
            "feature": committed_feature,
            "has_failures": False,
            "final_outcome": "accepted",
            "user_facing_status": FeatureStatus.ACCEPTED.value,
            "user_summary": _final_user_summary(
                outcome="accepted",
                status=FeatureStatus.ACCEPTED.value,
                summary=str(committed_feature.get("summary") or summary),
                next_action="feature-complete",
                reasons=[],
            ),
            "next_action": "feature-complete",
            "commit_status": "committed",
            "commit_hash": detected_commit,
            "candidate_commit_files": candidate_commit_files,
            "wave_progression": resolved_wave_progression,
            "next_wave_id": "",
            "all_required_waves_accepted": True,
            "reasons": [],
        }

    awaiting_feature = mark_feature_status(feature_id, FeatureStatus.AWAITING_COMMIT)
    resolved_wave_progression = [dict(item) for item in wave_progression or awaiting_feature.get("wave_progression") or []]
    awaiting_feature = update_record(
        "features",
        "features",
        "feature_id",
        feature_id,
        {
            "commit_status": "awaiting_commit",
            "candidate_commit_files": candidate_commit_files,
            "wave_progression": resolved_wave_progression,
            "next_wave_id": "",
            "all_required_waves_accepted": True,
        },
    )
    return {
        "feature": awaiting_feature,
        "has_failures": False,
        "final_outcome": "awaiting_commit",
        "user_facing_status": FeatureStatus.AWAITING_COMMIT.value,
        "user_summary": _final_user_summary(
            outcome="awaiting_commit",
            status=FeatureStatus.AWAITING_COMMIT.value,
            summary=str(awaiting_feature.get("summary") or summary),
            next_action=POST_ACCEPTANCE_NEXT_ACTION,
            reasons=[],
        ),
        "next_action": POST_ACCEPTANCE_NEXT_ACTION,
        "commit_status": "awaiting_commit",
        "commit_hash": "",
        "candidate_commit_files": candidate_commit_files,
        "wave_progression": resolved_wave_progression,
        "next_wave_id": "",
        "all_required_waves_accepted": True,
        "reasons": [],
    }


def _load_architect_manifest(feature_id: str) -> dict:
    try:
        feature = find_record("features", "features", "feature_id", feature_id)
    except KeyError:
        return {}
    manifest_path = str(feature.get("architect_manifest_path") or "").strip()
    if not manifest_path:
        return {}
    path = Path(manifest_path)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _architect_wave_contract(architect_manifest: dict, wave_id: str) -> dict:
    target_wave_id = str(wave_id or "").strip().upper()
    for wave in architect_manifest.get("waves") or []:
        if not isinstance(wave, dict):
            continue
        if str(wave.get("wave_id") or "").strip().upper() == target_wave_id:
            return dict(wave)
    return {}


def _persist_wave_progression(feature_id: str, wave_progression: list[dict[str, object]]) -> dict:
    return update_record(
        "features",
        "features",
        "feature_id",
        feature_id,
        {
            "wave_progression": [dict(item) for item in wave_progression],
            "next_wave_id": _next_required_wave_id(wave_progression),
            "all_required_waves_accepted": _all_required_waves_accepted(wave_progression),
        },
    )


def _set_wave_progression_status(
    *,
    feature_id: str,
    wave_progression: list[dict[str, object]],
    wave_id: str,
    status: str,
    reasons: list[str] | None = None,
) -> dict[str, object]:
    updated_wave: dict[str, object] | None = None
    for item in wave_progression:
        if str(item.get("wave_id") or "") != str(wave_id):
            continue
        item["status"] = status
        if reasons is not None:
            item["reasons"] = [str(reason).strip() for reason in reasons if str(reason).strip()]
        elif status in {"running", "accepted"}:
            item["reasons"] = []
        updated_wave = dict(item)
        break
    _persist_wave_progression(feature_id, wave_progression)
    return updated_wave or {}


def _build_direct_rework_followup_packets(
    *,
    source_reviewer_packet: dict,
    direct_rework_packet: dict,
    target_packet_id: str,
    packets_by_id: dict[str, dict],
) -> tuple[list[dict], str]:
    rework_packets = [direct_rework_packet]
    rework_reviewer_packet_id = ""
    verifier_source_packet_id = next(
        (
            dependency
            for dependency in source_reviewer_packet.get("dependencies") or []
            if str(packets_by_id.get(str(dependency), {}).get("role") or "") == "verifier"
        ),
        "",
    )
    origin_reviewer_packet_id = str(direct_rework_packet.get("origin_reviewer_packet_id") or source_reviewer_packet["packet_id"])
    verifier_source_packet = dict(packets_by_id.get(verifier_source_packet_id) or {})
    verifier_hints = dict(direct_rework_packet.get("execution_hints") or {})
    verifier_profile = {}
    if verifier_source_packet_id:
        verifier_hints = {**verifier_hints, **dict(verifier_source_packet.get("execution_hints") or {})}
        verifier_profile = dict(verifier_source_packet.get("verification_profile") or {})

    direct_verifier_packet = create_packet(
        feature_id=direct_rework_packet["feature_id"],
        wave_id=direct_rework_packet["wave_id"],
        title=f"Verifier Rework {direct_rework_packet['title']}",
        role="verifier",
        reasoning=ReasoningProfile.MEDIUM,
        summary=f"Validate the architect-bounded direct rework for `{target_packet_id}` and capture fresh evidence.",
        write_scope=["Verification notes and evidence references only."],
        inputs=[direct_rework_packet["packet_id"], origin_reviewer_packet_id],
        acceptance_criteria=[
            "Commands run are recorded for the direct rework packet.",
            "Evidence paths are refreshed for the reworked scope.",
            "Observability verdict is explicit for the direct rework.",
        ],
        verification_profile=verifier_profile
        or {
            "backend": "rerun minimally sufficient backend checks for the reworked scope",
            "frontend": "rerun targeted frontend checks if UI changed",
            "observability": "repeat post-test digest, trace, and replay review",
        },
        reviewer_gate=[
            "Evidence must correspond to the direct rework packet, not the original attempt.",
            "Missing visual proof remains a blocker for UI work.",
        ],
        dependencies=[direct_rework_packet["packet_id"]],
        packet_type="rework",
        notes=["This verifier packet was created for architect-bounded direct rework."],
        parent_packet_id=target_packet_id,
        execution_hints=verifier_hints,
        status=PacketStatus.READY,
    )
    direct_reviewer_packet = create_packet(
        feature_id=direct_rework_packet["feature_id"],
        wave_id=direct_rework_packet["wave_id"],
        title=f"Reviewer Rework {direct_rework_packet['title']}",
        role="reviewer",
        reasoning=ReasoningProfile.XHIGH,
        summary=f"Review whether the architect-bounded direct rework for `{target_packet_id}` addressed the reviewer blockers.",
        write_scope=["Review verdict and blocker notes only."],
        inputs=[direct_rework_packet["packet_id"], direct_verifier_packet["packet_id"]],
        acceptance_criteria=[
            "Exactly one verdict is returned.",
            "The original blockers are either resolved or explicitly remain.",
            "No unrelated scope expansion is accepted.",
        ],
        verification_profile={
            "backend": "consume verifier evidence",
            "frontend": "consume verifier evidence",
            "observability": "consume verifier evidence",
        },
        reviewer_gate=[
            "Assess only the original blocker scope.",
            "Escalate only if blockers imply decomposition or business changes.",
        ],
        dependencies=[direct_rework_packet["packet_id"], direct_verifier_packet["packet_id"]],
        packet_type="gate_decision",
        notes=["This reviewer packet was created for architect-bounded direct rework."],
        parent_packet_id=target_packet_id,
        status=PacketStatus.READY,
    )
    direct_reviewer_packet = update_record(
        "packets",
        "packets",
        "packet_id",
        direct_reviewer_packet["packet_id"],
        {
            "review_target_packet_id": direct_rework_packet["packet_id"],
            "execution_hints": dict(direct_rework_packet.get("execution_hints") or {}),
        },
    )
    direct_reviewer_packet = sync_packet_file(direct_reviewer_packet)
    rework_packets.extend([direct_verifier_packet, direct_reviewer_packet])
    rework_reviewer_packet_id = str(direct_reviewer_packet.get("packet_id") or "")
    return rework_packets, rework_reviewer_packet_id


def _should_run_planner(*, run_planner: bool | None, planner_contract: dict | None) -> bool:
    if run_planner is not None:
        return bool(run_planner)
    return False


def _architect_plan_next_action(payload: dict | None) -> str:
    action = str((payload or {}).get("next_action") or "materialize_packets").strip().lower().replace("-", "_")
    if action in {"materialize_packets", "requires_planner", "requires_user_decision"}:
        return action
    return "materialize_packets"


def _architect_packet_candidates_to_contract(payload: dict | None) -> dict | None:
    if not isinstance(payload, dict):
        return None
    raw_packets = payload.get("packet_candidates")
    if not isinstance(raw_packets, list) or not raw_packets:
        return None
    packets = [dict(packet) for packet in raw_packets if isinstance(packet, dict)]
    if not packets:
        return None
    raw_waves = payload.get("waves")
    waves = [dict(wave) for wave in raw_waves if isinstance(wave, dict)] if isinstance(raw_waves, list) else []
    return {"waves": waves, "packets": packets}


def _sync_architect_manifest_packets(
    *,
    feature_id: str,
    generated_packets: list[dict],
    architect_packet_id: str,
) -> None:
    try:
        feature = find_record("features", "features", "feature_id", feature_id)
    except KeyError:
        return
    manifest_path = Path(str(feature.get("architect_manifest_path") or "").strip())
    if not manifest_path.is_file():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(manifest, dict):
        return
    manifest["packet_candidates"] = [
        {
            "key": str(packet.get("packet_id") or ""),
            "wave_id": str(packet.get("wave_id") or ""),
            "title": str(packet.get("title") or ""),
            "role": str(packet.get("role") or ""),
            "reasoning": str(packet.get("reasoning") or ""),
            "packet_type": str(packet.get("packet_type") or ""),
            "summary": str(packet.get("summary") or ""),
            "write_scope": list(packet.get("write_scope") or []),
            "inputs": list(packet.get("inputs") or []),
            "acceptance_criteria": list(packet.get("acceptance_criteria") or []),
            "verification_profile": dict(packet.get("verification_profile") or {}),
            "reviewer_gate": list(packet.get("reviewer_gate") or []),
            "dependencies": [
                "architect formalization" if str(dependency) == architect_packet_id else str(dependency)
                for dependency in list(packet.get("dependencies") or [])
            ],
            "notes": list(packet.get("notes") or []),
            "review_target_key": str(packet.get("review_target_packet_id") or ""),
        }
        for packet in generated_packets
    ]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def _architect_direct_rework_packet_spec_from_run(architect_run: dict) -> dict | None:
    try:
        return parse_direct_rework_packet_message(
            read_agent_message(architect_run.get("last_message_path"), architect_run.get("stdout_path"))
        )
    except ValueError:
        return None


def _build_architect_direct_rework(
    *,
    coder_packet_id: str,
    reviewer_packet_id: str,
    reasons: list[str],
    architect_run: dict | None,
    route_classification: str,
    rework_mode: str,
) -> dict:
    packet_spec = _architect_direct_rework_packet_spec_from_run(architect_run or {}) if architect_run else None
    if packet_spec and packet_spec.get("route_classification") != route_classification:
        raise ValueError("Architect direct rework packet classification does not match reviewer route")
    if route_classification != REWORK_ROUTE_SELF_RESOLVABLE:
        raise ValueError("Architect direct rework builder only supports self-resolvable routing")
    title = str(packet_spec.get("title") or "").strip() if packet_spec else ""
    summary = str(packet_spec.get("summary") or "").strip() if packet_spec else ""
    resolved_rework_mode = _normalize_rework_mode(packet_spec.get("rework_mode") if packet_spec else rework_mode)
    return create_direct_rework_from_architect(
        coder_packet_id,
        reasons,
        reviewer_packet_id=reviewer_packet_id,
        rework_mode=resolved_rework_mode,
        title=title or None,
        summary=summary or None,
        write_scope=list(packet_spec.get("write_scope") or []) or None if packet_spec else None,
        inputs=list(packet_spec.get("inputs") or []) or None if packet_spec else None,
        acceptance_criteria=list(packet_spec.get("acceptance_criteria") or []) or None if packet_spec else None,
        verification_profile=dict(packet_spec.get("verification_profile") or {}) or None if packet_spec else None,
        reviewer_gate=list(packet_spec.get("reviewer_gate") or []) or None if packet_spec else None,
        notes=list(packet_spec.get("notes") or []) or None if packet_spec else None,
    )


def _build_light_resume_followup(
    *,
    source_reviewer_packet: dict,
    resumed_packet: dict,
    reasons: list[str],
    reviewer_packet_id: str,
    packets_by_id: dict[str, dict],
) -> dict:
    rework_packet = update_record(
        "packets",
        "packets",
        "packet_id",
        str(resumed_packet["packet_id"]),
        {
            "review_target_packet_id": str(resumed_packet["packet_id"]),
            "origin_reviewer_packet_id": str(reviewer_packet_id),
            "route_classification": REWORK_ROUTE_SELF_RESOLVABLE,
            "requested_rework_mode": REWORK_MODE_LIGHT_RESUME,
            "rework_mode": REWORK_MODE_LIGHT_RESUME,
            "status": PacketStatus.READY.value,
            "light_resume_stage": True,
            "light_resume_source_packet_id": str(resumed_packet["packet_id"]),
            "light_resume_attempt": int(resumed_packet.get("light_resume_attempt") or 0) + 1,
            "light_resume_max_attempts": 1,
        },
    )
    rework_packet["execution_hints"] = {
        **dict(rework_packet.get("execution_hints") or {}),
        "resume_strategy": "packet_parent",
        "resume_parent_packet_id": str(resumed_packet["packet_id"]),
        "rework_mode": REWORK_MODE_LIGHT_RESUME,
        "light_resume_stage": True,
        "light_resume_scope": "packet_local",
        "light_resume_source_packet_id": str(resumed_packet["packet_id"]),
        "light_resume_attempt": rework_packet["light_resume_attempt"],
        "light_resume_max_attempts": 1,
        "light_resume_reviewer_packet_id": str(reviewer_packet_id),
        "light_resume_reasons": [str(reason).strip() for reason in reasons if str(reason).strip()],
    }
    rework_packet = update_record(
        "packets",
        "packets",
        "packet_id",
        str(resumed_packet["packet_id"]),
        {"execution_hints": rework_packet["execution_hints"]},
    )
    rework_packets, rework_reviewer_packet_id = _build_direct_rework_followup_packets(
        source_reviewer_packet=source_reviewer_packet,
        direct_rework_packet=rework_packet,
        target_packet_id=str(resumed_packet["packet_id"]),
        packets_by_id=packets_by_id,
    )
    return {
        "packet_id": rework_packet["packet_id"],
        "rework": rework_packet,
        "packets": rework_packets,
        "reviewer_packet_id": rework_reviewer_packet_id,
        "rework_mode": REWORK_MODE_LIGHT_RESUME,
        "light_resume_stage": True,
    }


@task(task_run_name="bootstrap:{feature_id}")
def bootstrap_task(feature_id: str, title: str, summary: str):
    logger = get_run_logger()
    record = bootstrap_feature(feature_id=feature_id, title=title, summary=summary)
    logger.info("Bootstrapped feature %s", feature_id)
    return record


@task(task_run_name="seed-packets:{feature_id}")
def seed_feature_packets_task(
    feature_id: str,
    title: str,
    summary: str,
    implementation_title: str,
    implementation_summary: str,
    verifier_backend_profile: str | None,
    verifier_frontend_profile: str | None,
    verifier_frontend_commands: list[str] | None,
    verifier_observability_profile: str | None,
    verifier_observability_commands: list[str] | None,
    verifier_artifact_globs: list[str] | None,
    verifier_touches_frontend: bool,
    verifier_requires_frontend_visual: bool,
    verifier_include_day_live_canary: bool,
    agent_workdir: str | None,
    agent_sandbox: str | None,
    business_context: dict | None = None,
    planner_contract: dict | None = None,
    include_planner_packet: bool = False,
    materialize_execution_packets: bool = True,
):
    logger = get_run_logger()
    logger.info("Seeding role packets for %s", feature_id)
    return seed_test_feature(
        feature_id=feature_id,
        title=title,
        summary=summary,
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
        agent_workdir=agent_workdir,
        agent_sandbox=agent_sandbox,
        business_context=business_context,
        planner_contract=planner_contract,
        include_planner_packet=include_planner_packet,
        materialize_execution_packets=materialize_execution_packets,
    )


@task(task_run_name="packet-graph:resolve")
def resolve_planner_contract_task(
    planner_run: dict,
    *,
    planner_packet_id: str,
    architect_packet_id: str,
    feature_id: str,
    implementation_title: str,
    implementation_summary: str,
    verifier_backend_profile: str | None,
    verifier_frontend_profile: str | None,
    verifier_frontend_commands: list[str] | None,
    verifier_observability_profile: str | None,
    verifier_observability_commands: list[str] | None,
    verifier_artifact_globs: list[str] | None,
    verifier_touches_frontend: bool,
    verifier_requires_frontend_visual: bool,
    verifier_include_day_live_canary: bool,
    planner_contract_override: dict | None,
    prefer_agent_output: bool,
) -> dict:
    logger = get_run_logger()
    parser_error = None
    contract = None
    if prefer_agent_output:
        try:
            payload = parse_planner_wave_plan_message(
                read_agent_message(planner_run.get('last_message_path'), planner_run.get('stdout_path'))
            )
            contract = normalize_wave_plan_contract(
                payload,
                external_dependency_refs={
                    str(planner_packet_id).strip(),
                    str(architect_packet_id).strip(),
                    "planner output",
                    "architect formalization",
                },
            )
        except ValueError as exc:
            parser_error = str(exc)
    if contract is None and planner_contract_override:
        contract = normalize_wave_plan_contract(
            planner_contract_override,
            external_dependency_refs={
                str(planner_packet_id).strip(),
                str(architect_packet_id).strip(),
                "planner output",
                "architect formalization",
            },
        )
        source = 'explicit_input'
    elif contract is None:
        contract = default_wave_plan_contract(
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
        source = 'fallback'
    elif contract is not None:
        source = 'agent_output'
    logger.info('Resolved packet graph contract source=%s parser_error=%s', source, parser_error)
    return {'contract': contract, 'source': source, 'parser_error': parser_error}


@task(task_run_name="architect-artifacts:resolve:{feature_id}")
def resolve_architect_artifact_plan_task(
    architect_run: dict,
    *,
    feature_id: str,
    title: str,
    summary: str,
    business_context: dict | None,
    prefer_agent_output: bool,
) -> dict:
    logger = get_run_logger()
    parser_error = None
    payload = None
    if prefer_agent_output:
        try:
            payload = parse_architect_artifact_plan_message(
                read_agent_message(architect_run.get("last_message_path"), architect_run.get("stdout_path"))
            )
            source = "agent_output"
        except ValueError as exc:
            parser_error = str(exc)
    if payload is None:
        payload = default_architect_artifact_plan(
            feature_id=feature_id,
            title=title,
            summary=summary,
            business_context=business_context,
        )
        source = "fallback"
    logger.info("Resolved architect artifact plan source=%s parser_error=%s", source, parser_error)
    return {"payload": payload, "source": source, "parser_error": parser_error}


@task(task_run_name="architect-artifacts:write:{feature_id}")
def write_architect_artifacts_task(
    feature_id: str,
    architect_artifact_plan: dict,
) -> dict:
    logger = get_run_logger()
    written = write_architect_artifacts(
        feature_id=feature_id,
        architect_payload=architect_artifact_plan["payload"],
    )
    logger.info("Wrote architect slice docs for %s at %s", feature_id, written.get("slice_dir"))
    return written


@task(task_run_name="packet-graph:materialize:{feature_id}")
def materialize_planner_contract_task(
    feature_id: str,
    planner_packet_id: str,
    architect_packet_id: str,
    planner_contract_result: dict,
    agent_workdir: str | None,
    agent_sandbox: str | None,
    verifier_backend_profile: str | None,
    verifier_frontend_profile: str | None,
    verifier_frontend_commands: list[str] | None,
    verifier_observability_profile: str | None,
    verifier_observability_commands: list[str] | None,
    verifier_artifact_globs: list[str] | None,
    verifier_touches_frontend: bool,
    verifier_requires_frontend_visual: bool,
    verifier_include_day_live_canary: bool,
):
    logger = get_run_logger()
    base_execution_hints = {
        key: value
        for key, value in {
            'workdir': agent_workdir,
            'sandbox': agent_sandbox,
        }.items()
        if value not in (None, '')
    }
    materialized = materialize_planner_contract(
        feature_id=feature_id,
        planner_packet_id=planner_packet_id,
        architect_packet_id=architect_packet_id,
        contract=planner_contract_result['contract'],
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
    logger.info('Materialized packet graph with %s packets for %s', len(materialized['packets']), feature_id)
    return materialized


@task(task_run_name="packet-graph:validate:{feature_id}")
def validate_planner_contract_task(
    feature_id: str,
    materialized_contract: dict,
):
    logger = get_run_logger()
    packets = list(materialized_contract.get("packets") or [])
    packets_by_id = packet_map(packets)
    issues: list[str] = []
    architect_manifest = _load_architect_manifest(feature_id)

    for packet in packets:
        packet_id = str(packet.get("packet_id") or "")
        role = str(packet.get("role") or "")
        execution = _packet_execution_contract(packet)
        if role == "reviewer":
            explicit_target = str(packet.get("review_target_packet_id") or "").strip()
            if not explicit_target:
                issues.append(f"{packet_id}: reviewer packet is missing explicit review_target_packet_id")
            elif explicit_target not in packets_by_id:
                issues.append(f"{packet_id}: explicit review target does not resolve to a generated packet")
        if role == "verifier":
            hints = dict(packet.get("execution_hints") or {})
            for key in ("backend_commands", "frontend_commands", "observability_commands"):
                value = hints.get(key)
                if value is None:
                    continue
                if not isinstance(value, list):
                    issues.append(f"{packet_id}: {key} must be a list")
                    continue
                for item in value:
                    if not isinstance(item, str) or not item.strip():
                        issues.append(f"{packet_id}: {key} contains empty/non-string command")
                    elif item.strip().startswith("{") or item.strip().startswith("["):
                        issues.append(f"{packet_id}: {key} contains structured text instead of shell command")
        if _uses_today_week_observability(packet):
            if role != "verifier":
                issues.append(
                    f"{packet_id}: today-week canonical observability gate is allowed only on verifier packets"
                )
            observability_scope = _normalize_observability_scope(execution.get("observability_scope"))
            if observability_scope != "wave_final":
                issues.append(
                    f"{packet_id}: today-week canonical observability gate must declare execution.observability_scope=wave_final"
                )
            canonical_flow_commands = _string_command_list(execution.get("canonical_flow_commands"))
            include_day_live_canary = bool(execution.get("include_day_live_canary"))
            if not canonical_flow_commands and not include_day_live_canary:
                issues.append(
                    f"{packet_id}: today-week canonical observability gate must provide execution.canonical_flow_commands or include_day_live_canary"
                )
            architect_wave = _architect_wave_contract(architect_manifest, str(packet.get("wave_id") or ""))
            if not architect_wave:
                issues.append(
                    f"{packet_id}: architect manifest does not define wave {packet.get('wave_id')} required to authorize today-week evidence ownership"
                )
            else:
                architect_scope = _normalize_observability_scope(architect_wave.get("observability_scope"))
                architect_canonical = _string_command_list(architect_wave.get("canonical_flow_commands"))
                architect_live_canary = bool(architect_wave.get("include_day_live_canary"))
                if architect_scope != "wave_final":
                    issues.append(
                        f"{packet_id}: architect manifest wave {packet.get('wave_id')} does not authorize today-week wave_final ownership"
                    )
                if not architect_canonical and not architect_live_canary:
                    issues.append(
                        f"{packet_id}: architect manifest wave {packet.get('wave_id')} lacks canonical_flow_commands/include_day_live_canary for today-week gate"
                    )
                missing_architect_commands = [
                    command for command in architect_canonical if command not in canonical_flow_commands
                ]
                unexpected_planner_commands = [
                    command for command in canonical_flow_commands if command not in architect_canonical
                ]
                if missing_architect_commands:
                    issues.append(
                        f"{packet_id}: planner canonical_flow_commands are missing architect-authorized commands {missing_architect_commands}"
                    )
                if architect_canonical and unexpected_planner_commands:
                    issues.append(
                        f"{packet_id}: planner canonical_flow_commands widen architect scope with unexpected commands {unexpected_planner_commands}"
                    )
        if execution:
            observability_scope = _normalize_observability_scope(execution.get("observability_scope"))
            if observability_scope and observability_scope not in {"none", "packet_local", "wave_final"}:
                issues.append(f"{packet_id}: unsupported execution.observability_scope={execution.get('observability_scope')}")
            canonical_flow_commands = execution.get("canonical_flow_commands")
            if canonical_flow_commands is not None and not isinstance(canonical_flow_commands, list):
                issues.append(f"{packet_id}: execution.canonical_flow_commands must be a list")
            elif isinstance(canonical_flow_commands, list):
                for item in canonical_flow_commands:
                    if not isinstance(item, str) or not item.strip():
                        issues.append(f"{packet_id}: execution.canonical_flow_commands contains empty/non-string command")

    logger.info("Packet graph validation for %s issues=%s", feature_id, len(issues))
    return {"valid": not issues, "issues": issues}


@task(task_run_name="feature-status:{feature_id}:in-progress")
def mark_feature_in_progress_task(feature_id: str):
    logger = get_run_logger()
    logger.info("Marking feature %s as in progress", feature_id)
    record = mark_feature_status(feature_id, FeatureStatus.IN_PROGRESS)
    notify_feature_event(
        feature_id=feature_id,
        title=str(record.get("title") or ""),
        status=FeatureStatus.IN_PROGRESS.value,
        summary=str(record.get("summary") or ""),
    )
    return record


@task(task_run_name="packet:{packet_id}")
def run_packet_task(packet_id: str, dry_run: bool, timeout_seconds: int):
    logger = get_run_logger()
    logger.info("Running packet %s dry_run=%s", packet_id, dry_run)
    return launch_codex_for_packet(packet_id, dry_run=dry_run, timeout_seconds=timeout_seconds, logger=logger)


@task(task_run_name="verifier:{packet_id}")
def run_verifier_packet_task(packet_id: str, dry_run: bool, timeout_seconds: int):
    logger = get_run_logger()
    logger.info("Running verifier packet %s dry_run=%s", packet_id, dry_run)
    return launch_codex_for_packet(packet_id, dry_run=dry_run, timeout_seconds=timeout_seconds, logger=logger)


@task(task_run_name="packet-status:{packet_id}:{status}")
def mark_packet_status_task(packet_id: str, status: str):
    logger = get_run_logger()
    PacketStatus(status)
    logger.info("Packet %s status=%s", packet_id, status)
    record = update_record("packets", "packets", "packet_id", packet_id, {"status": status})
    notify_packet_event(
        feature_id=str(record.get("feature_id") or ""),
        packet_id=packet_id,
        role=str(record.get("role") or ""),
        status=status,
        wave_id=str(record.get("wave_id") or ""),
        title=str(record.get("title") or ""),
    )
    return record


@task(task_run_name="canon-digest:record:{feature_id}")
def record_canon_digest_task(feature_id: str, canon_digest_run: dict):
    try:
        logger = get_run_logger()
    except Exception:
        logger = None
    feature = find_record("features", "features", "feature_id", feature_id)
    feature_dir = Path(str(feature.get("feature_dir") or (Path("prefect_grace/packets") / feature_id)))
    output_path = feature_dir / "canon-digest.md"
    output_text = read_agent_message(canon_digest_run.get("last_message_path"), canon_digest_run.get("stdout_path")).strip()
    if not output_text:
        output_text = "# Canon Digest\n\nNo canon digest output was captured.\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_text + "\n", encoding="utf-8")
    if logger is not None:
        logger.info("Recorded canon digest for %s at %s", feature_id, output_path)
    return update_record("features", "features", "feature_id", feature_id, {"canon_digest_path": str(output_path)})


@task(task_run_name="review-route:{coder_packet_id}")
def route_reviewer_verdict_task(
    coder_packet_id: str,
    reviewer_packet_id: str,
    reviewer_decision: dict,
    create_rework: bool,
    rework_routing_policy: str = REWORK_ROUTING_ARCHITECT_FIRST,
    architect_rework_packet: dict | None = None,
):
    logger = get_run_logger()
    verdict = ReviewVerdict(reviewer_decision["packet_verdict"])
    review_reasons = list(reviewer_decision.get("reasons") or [])
    follow_up_action = str(reviewer_decision.get("follow_up_action") or "none")
    try:
        packet_record = find_record("packets", "packets", "packet_id", coder_packet_id)
    except KeyError:
        packet_record = {}
        logger.warning(
            "Reviewer route could not find packet record for %s during notify payload build",
            coder_packet_id,
        )
    rework = None
    decision = None
    route_classification = _classify_rework_route(reviewer_decision)
    review = record_review(
        packet_id=coder_packet_id,
        verdict=verdict,
        reasons=review_reasons,
        follow_up_action=follow_up_action,
    )
    if verdict == ReviewVerdict.ACCEPTED:
        mark_packet_status_task(reviewer_packet_id, PacketStatus.ACCEPTED.value)
        mark_packet_status_task(coder_packet_id, PacketStatus.ACCEPTED.value)
    elif verdict == ReviewVerdict.REWORK_REQUIRED:
        mark_packet_status_task(reviewer_packet_id, PacketStatus.ACCEPTED.value)
        if create_rework:
            if route_classification == REWORK_ROUTE_SELF_RESOLVABLE:
                if rework_routing_policy == REWORK_ROUTING_AUTO_BUNDLE:
                    rework = create_rework_bundle_from_review(
                        packet_id=coder_packet_id,
                        reviewer_packet_id=reviewer_packet_id,
                        reasons=review_reasons,
                    )
                else:
                    rework = architect_rework_packet
                    if rework is None:
                        decision = create_architect_decision_from_review(
                            coder_packet_id,
                            review_reasons,
                            route_classification=route_classification,
                            requested_action=(
                                "Architect rework packet did not produce a bounded direct coder packet; "
                                "inspect architect routing output before continuing."
                            ),
                        )
            elif route_classification in {REWORK_ROUTE_REQUIRES_USER_DECISION, REWORK_ROUTE_REQUIRES_PLANNER}:
                decision = create_architect_decision_from_review(
                    coder_packet_id,
                    review_reasons,
                    route_classification=route_classification,
                )
        mark_packet_status_task(coder_packet_id, PacketStatus.REWORK_REQUIRED.value)
    elif verdict == ReviewVerdict.ESCALATE_TO_ARCHITECT:
        mark_packet_status_task(reviewer_packet_id, PacketStatus.ACCEPTED.value)
        decision = create_architect_decision_from_review(
            coder_packet_id,
            review_reasons,
            route_classification=REWORK_ROUTE_REQUIRES_USER_DECISION,
        )
        mark_packet_status_task(coder_packet_id, PacketStatus.ESCALATE_TO_ARCHITECT.value)
    else:
        mark_packet_status_task(reviewer_packet_id, PacketStatus.BLOCKED.value)
        mark_packet_status_task(coder_packet_id, PacketStatus.BLOCKED.value)
    logger.info("Reviewer routed verdict=%s for packet %s", verdict.value, coder_packet_id)
    notify_packet_event(
        feature_id=str(packet_record.get("feature_id") or ""),
        packet_id=coder_packet_id,
        role=str(packet_record.get("role") or ""),
        status=verdict.value,
        wave_id=str(packet_record.get("wave_id") or ""),
        title=str(packet_record.get("title") or ""),
        reasons=review_reasons,
    )
    return {
        "review": review,
        "rework": rework,
        "decision": decision,
        "reviewer_verdict": verdict.value,
        "route_classification": route_classification,
        "rework_routing_policy": rework_routing_policy,
        "decision_source": reviewer_decision.get("source"),
        "parser_error": reviewer_decision.get("parser_error"),
    }


@task(task_run_name="wave-route:{feature_id}:{wave_id}")
def route_architect_wave_verdict_task(
    feature_id: str,
    wave_id: str,
    architect_packet_id: str,
    wave_decision: dict,
):
    logger = get_run_logger()
    verdict = WaveVerdict(wave_decision["wave_verdict"])
    wave_reasons = list(wave_decision.get("reasons") or [])
    review = record_wave_review(
        feature_id=feature_id,
        wave_id=wave_id,
        architect_packet_id=architect_packet_id,
        verdict=verdict,
        reasons=wave_reasons,
    )
    if verdict == WaveVerdict.ACCEPTED:
        mark_packet_status_task(architect_packet_id, PacketStatus.ACCEPTED.value)
    elif verdict == WaveVerdict.REWORK_REQUIRED:
        mark_packet_status_task(architect_packet_id, PacketStatus.REWORK_REQUIRED.value)
    else:
        mark_packet_status_task(architect_packet_id, PacketStatus.BLOCKED.value)
    logger.info("Architect wave gate routed verdict=%s for %s/%s", verdict.value, feature_id, wave_id)
    return {
        "wave_review": review,
        "wave_verdict": verdict.value,
        "decision_source": wave_decision.get("source"),
        "parser_error": wave_decision.get("parser_error"),
    }


@task(task_run_name="verifier-result:resolve")
def resolve_verifier_result_task(
    verifier_run: dict,
    verifier_test_verdict: str | None,
    verifier_observability_verdict: str | None,
    verifier_frontend_visual_verdict: str | None,
    verifier_commands_run: list[str] | None,
    verifier_evidence_paths: list[str] | None,
    verifier_blocking_issues: list[str] | None,
    prefer_agent_output: bool,
):
    logger = get_run_logger()
    try:
        result = resolve_verifier_result(
            verifier_run,
            fallback_test_verdict=verifier_test_verdict,
            fallback_observability_verdict=verifier_observability_verdict,
            fallback_frontend_visual_verdict=verifier_frontend_visual_verdict,
            fallback_commands_run=verifier_commands_run,
            fallback_evidence_paths=verifier_evidence_paths,
            fallback_blocking_issues=verifier_blocking_issues,
            prefer_agent_output=prefer_agent_output,
        )
        result = _enrich_verifier_evidence_paths(verifier_run, result)
    except ValueError as exc:
        result = {
            "test_verdict": TestVerdict.FAILED.value,
            "observability_verdict": ObservabilityVerdict.NO_EVIDENCE_BLOCKER.value,
            "frontend_visual_verdict": FrontendVisualVerdict.NOT_APPLICABLE.value,
            "commands_run": [],
            "evidence_paths": [],
            "blocking_issues": [f"Verifier output parse failed: {exc}"],
            "source": "parse_error",
            "parser_error": str(exc),
            "raw_message": "",
        }
    logger.info(
        "Resolved verifier result source=%s test=%s obs=%s",
        result.get("source"),
        result.get("test_verdict"),
        result.get("observability_verdict"),
    )
    return result


@task(task_run_name="record-verifier:{verifier_packet_id}")
def record_verifier_result_task(
    verifier_packet_id: str,
    verifier_result: dict,
):
    logger = get_run_logger()
    record = record_verification(
        packet_id=verifier_packet_id,
        test_verdict=verifier_result["test_verdict"],
        observability_verdict=verifier_result["observability_verdict"],
        frontend_visual_verdict=verifier_result["frontend_visual_verdict"],
        commands_run=list(verifier_result.get("commands_run") or []),
        evidence_paths=list(verifier_result.get("evidence_paths") or []),
        blocking_issues=list(verifier_result.get("blocking_issues") or []),
    )
    logger.info("Recorded verifier evidence for %s", verifier_packet_id)
    artifact_ids = publish_packet_task_artifacts(verification=record)
    if artifact_ids:
        logger.info("Published %s verifier task artifacts for %s", len(artifact_ids), verifier_packet_id)
    return record


@task(task_run_name="packet-review-artifacts:{review_route[review][packet_id]}")
def publish_packet_review_artifacts_task(review_route: dict):
    logger = get_run_logger()
    artifact_ids = publish_packet_task_artifacts(review_route=review_route)
    logger.info("Published %s packet review artifacts", len(artifact_ids))
    return artifact_ids


@task(task_run_name="feature-artifacts:{feature[feature_id]}")
def publish_feature_artifacts_task(
    feature: dict,
    packet_results: dict,
    verification: dict | None,
    review_route: dict | None,
    wave_route: dict | None,
    final_status: dict | None,
):
    logger = get_run_logger()
    current_feature = feature
    feature_id = str(feature.get("feature_id") or "").strip()
    if feature_id:
        try:
            current_feature = find_record("features", "features", "feature_id", feature_id)
        except KeyError:
            current_feature = feature
    artifact_ids = publish_feature_artifacts(
        feature=current_feature,
        packet_results=packet_results,
        verification=verification,
        review_route=review_route,
        wave_route=wave_route,
        final_status=final_status,
    )
    logger.info("Published %s feature artifacts", len(artifact_ids))
    return artifact_ids


@task(task_run_name="review-decision:resolve")
def resolve_reviewer_decision_task(
    reviewer_run: dict,
    reviewer_verdict: str | None,
    review_reasons: list[str] | None,
    prefer_agent_output: bool,
):
    logger = get_run_logger()
    try:
        decision = resolve_reviewer_decision(
            reviewer_run,
            fallback_verdict=reviewer_verdict,
            fallback_reasons=review_reasons,
            prefer_agent_output=prefer_agent_output,
        )
    except ValueError as exc:
        decision = {
            "packet_verdict": ReviewVerdict.BLOCKED.value,
            "follow_up_action": "none",
            "reasons": [f"Reviewer output parse failed: {exc}"],
            "source": "parse_error",
            "parser_error": str(exc),
            "raw_message": "",
        }
    logger.info("Resolved reviewer decision source=%s verdict=%s", decision.get("source"), decision.get("packet_verdict"))
    return decision


@task(task_run_name="wave-decision:resolve")
def resolve_wave_decision_task(
    architect_wave_run: dict,
    wave_verdict: str | None,
    wave_reasons: list[str] | None,
    prefer_agent_output: bool,
):
    logger = get_run_logger()
    try:
        decision = resolve_wave_decision(
            architect_wave_run,
            fallback_verdict=wave_verdict,
            fallback_reasons=wave_reasons,
            prefer_agent_output=prefer_agent_output,
        )
    except ValueError as exc:
        decision = {
            "wave_verdict": WaveVerdict.BLOCKED.value,
            "reasons": [f"Architect wave output parse failed: {exc}"],
            "source": "parse_error",
            "parser_error": str(exc),
            "raw_message": "",
        }
    logger.info("Resolved architect wave decision source=%s verdict=%s", decision.get("source"), decision.get("wave_verdict"))
    return decision


@flow(name="prefect-grace-feature-pipeline", flow_run_name="feature:{feature_id}")
def feature_pipeline(
    feature_id: str,
    title: str,
    summary: str,
    implementation_title: str = "Test Implementation Packet",
    implementation_summary: str = "Run a bounded end-to-end test feature through architect, planner, coder, verifier, and reviewer packets.",
    dry_run: bool = True,
    timeout_seconds: int = 3600,
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
    business_context: dict | None = None,
    planner_contract: dict | None = None,
    reviewer_verdict: str | None = ReviewVerdict.ACCEPTED.value,
    review_reasons: list[str] | None = None,
    verifier_test_verdict: str | None = TestVerdict.PASSED.value,
    verifier_observability_verdict: str | None = ObservabilityVerdict.CLEAN.value,
    verifier_frontend_visual_verdict: str | None = FrontendVisualVerdict.NOT_APPLICABLE.value,
    verifier_commands_run: list[str] | None = None,
    verifier_evidence_paths: list[str] | None = None,
    verifier_blocking_issues: list[str] | None = None,
    wave_verdict: str | None = WaveVerdict.ACCEPTED.value,
    wave_reasons: list[str] | None = None,
    create_rework: bool = True,
    prefer_agent_output: bool = False,
    run_architect: bool = True,
    run_planner: bool | None = None,
    commit_hash: str | None = None,
    rework_routing_policy: str = REWORK_ROUTING_ARCHITECT_FIRST,
    reviewer_verdict_script: list[str] | None = None,
    review_reasons_script: list[list[str]] | None = None,
    wave_verdict_script: list[str] | None = None,
    wave_reasons_script: list[list[str]] | None = None,
):
    with tags(f"feature:{feature_id}", "flow:feature-pipeline"):
        seeded = seed_feature_packets_task(
            feature_id=feature_id,
            title=title,
            summary=summary,
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
            agent_workdir=agent_workdir,
            agent_sandbox=agent_sandbox,
            business_context=business_context,
            planner_contract=planner_contract,
            include_planner_packet=bool(run_planner),
            materialize_execution_packets=False,
        )
        mark_feature_in_progress_task(feature_id)

        packet_results: dict[str, dict] = {}
        review_route = None

        canon_digest_packet_id = str((seeded["packets"].get("canon_digest") or {}).get("packet_id") or "")
        architect_packet_id = seeded["packets"]["architect"]["packet_id"]
        should_run_planner = _should_run_planner(run_planner=run_planner, planner_contract=planner_contract)
        planner_packet = seeded["packets"].get("planner")
        planner_packet_id = str((planner_packet or {}).get("packet_id") or "")

        if canon_digest_packet_id:
            with tags("wave:W00", "role:canon_digest"):
                canon_digest_run = run_packet_task(canon_digest_packet_id, dry_run, timeout_seconds)
            packet_results["canon_digest"] = canon_digest_run
            if canon_digest_run.get("returncode") == 0:
                record_canon_digest_task(feature_id, canon_digest_run)
                mark_packet_status_task(canon_digest_packet_id, PacketStatus.ACCEPTED.value)
            else:
                mark_packet_status_task(canon_digest_packet_id, PacketStatus.BLOCKED.value)
                final_status = _final_failure(
                    feature_id=feature_id,
                    category="environment_blocked",
                    next_action="inspect-failed-canon-digest",
                    reasons=["canon_digest preflight failed before architect formalization"],
                )
                publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, final_status)
                return {"feature": seeded["feature"], "seeded": seeded, "runs": packet_results, "review_route": review_route, "final_status": final_status}

        if run_architect:
            with tags("wave:W00", "role:architect"):
                architect_run = run_packet_task(architect_packet_id, dry_run, timeout_seconds)
        else:
            architect_run = {
                "packet_id": architect_packet_id,
                "returncode": 0,
                "launcher": "skipped",
                "stdout_path": "",
                "stderr_path": "",
                "last_message_path": "",
            }
        packet_results["architect"] = architect_run
        if architect_run.get("returncode") != 0:
            final_status = _final_failure(
                feature_id=feature_id,
                category="environment_blocked",
                next_action="inspect-failed-architect",
            )
            publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, final_status)
            return {"feature": seeded["feature"], "seeded": seeded, "runs": packet_results, "review_route": review_route, "final_status": final_status}
        with tags("wave:W00", "role:architect"):
            mark_packet_status_task(architect_packet_id, PacketStatus.ACCEPTED.value)

        architect_artifact_plan = resolve_architect_artifact_plan_task(
            architect_run,
            feature_id=feature_id,
            title=title,
            summary=summary,
            business_context=business_context,
            prefer_agent_output=prefer_agent_output,
        )
        packet_results["architect_artifact_plan"] = architect_artifact_plan
        architect_artifacts = write_architect_artifacts_task(feature_id, architect_artifact_plan)
        packet_results["architect_artifacts"] = architect_artifacts
        publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, None)

        architect_payload = dict(architect_artifact_plan.get("payload") or {})
        architect_next_action = _architect_plan_next_action(architect_payload)
        architect_contract = _architect_packet_candidates_to_contract(architect_payload)
        planner_required = should_run_planner or architect_next_action == "requires_planner"

        if architect_next_action == "requires_user_decision":
            reasons = list(architect_payload.get("open_decisions") or [])
            feature_record = mark_feature_status(feature_id, FeatureStatus.ARCHITECT_READY)
            final_status = {
                "feature": feature_record,
                "has_failures": False,
                "final_outcome": "awaiting_architect",
                "user_facing_status": FeatureStatus.ARCHITECT_READY.value,
                "user_summary": _final_user_summary(
                    outcome="awaiting_architect",
                    status=FeatureStatus.ARCHITECT_READY.value,
                    summary=str(feature_record.get("summary") or summary),
                    next_action="architect-user-decision-required",
                    reasons=reasons,
                ),
                "next_action": "architect-user-decision-required",
                "reasons": reasons,
            }
            publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, final_status)
            return {"feature": seeded["feature"], "seeded": seeded, "runs": packet_results, "review_route": review_route, "final_status": final_status}

        if planner_required and planner_packet_id:
            with tags("wave:W00", "role:planner"):
                planner_run = run_packet_task(planner_packet_id, dry_run, timeout_seconds)
        else:
            planner_run = {
                "packet_id": planner_packet_id,
                "returncode": 0,
                "launcher": "skipped",
                "stdout_path": "",
                "stderr_path": "",
                "last_message_path": "",
            }
        packet_results["planner"] = planner_run
        if planner_required and planner_run.get("returncode") != 0:
            final_status = _final_failure(
                feature_id=feature_id,
                category="environment_blocked",
                next_action="inspect-failed-planner",
            )
            publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, final_status)
            return {"feature": seeded["feature"], "seeded": seeded, "runs": packet_results, "review_route": review_route, "final_status": final_status}
        if planner_required and planner_packet_id:
            with tags("wave:W00", "role:planner"):
                mark_packet_status_task(planner_packet_id, PacketStatus.ACCEPTED.value)
        elif planner_packet_id:
            try:
                update_record("packets", "packets", "packet_id", planner_packet_id, {"status": PacketStatus.DRAFT.value})
            except KeyError:
                pass

        planner_contract_result = resolve_planner_contract_task(
            planner_run,
            planner_packet_id=planner_packet_id,
            architect_packet_id=architect_packet_id,
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
            planner_contract_override=planner_contract if planner_required else (architect_contract or planner_contract),
            prefer_agent_output=prefer_agent_output and planner_required,
        )
        packet_results["planner_contract"] = planner_contract_result
        if planner_required and prefer_agent_output and planner_contract_result.get("parser_error") and planner_contract_result.get("source") != "agent_output":
            final_status = _final_failure(
                feature_id=feature_id,
                category="pipeline_invalid",
                next_action="fix-planner-agent-output",
                reasons=[str(planner_contract_result["parser_error"])],
            )
            publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, final_status)
            return {"feature": seeded["feature"], "seeded": seeded, "runs": packet_results, "review_route": review_route, "final_status": final_status}
        materialized_contract = materialize_planner_contract_task(
            feature_id,
            planner_packet_id,
            architect_packet_id,
            planner_contract_result,
            agent_workdir,
            agent_sandbox,
            verifier_backend_profile,
            verifier_frontend_profile,
            verifier_frontend_commands,
            verifier_observability_profile,
            verifier_observability_commands,
            verifier_artifact_globs,
            verifier_touches_frontend,
            verifier_requires_frontend_visual,
            verifier_include_day_live_canary,
        )
        packet_results["planner_materialized"] = materialized_contract
        _sync_architect_manifest_packets(
            feature_id=feature_id,
            generated_packets=list(materialized_contract.get("packets") or []),
            architect_packet_id=architect_packet_id,
        )
        planner_validation = validate_planner_contract_task(feature_id, materialized_contract)
        packet_results["planner_validation"] = planner_validation
        publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, None)
        if not planner_validation["valid"]:
            final_status = _final_failure(
                feature_id=feature_id,
                category="pipeline_invalid",
                next_action="fix-packet-graph-contract",
                reasons=list(planner_validation.get("issues") or []),
            )
            publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, final_status)
            return {"feature": seeded["feature"], "seeded": seeded, "runs": packet_results, "review_route": review_route, "final_status": final_status}

        generated_packets = list(materialized_contract["packets"])
        packets_by_id = packet_map(generated_packets)
        wave_packets_by_id = _wave_packets_by_wave_id(generated_packets)
        architect_manifest = _load_architect_manifest(feature_id)
        wave_progression = _build_wave_progression(
            architect_manifest=architect_manifest,
            planner_waves=list(materialized_contract.get("waves") or []),
            generated_packets=generated_packets,
        )
        packet_results["wave_progression"] = [dict(item) for item in wave_progression]
        _persist_wave_progression(feature_id, wave_progression)
        wave_progression_issues = _required_wave_progression_issues(wave_progression)
        if wave_progression_issues:
            for issue in wave_progression_issues:
                issue_wave_id = _wave_id_from_issue(issue)
                if issue_wave_id:
                    _set_wave_progression_status(
                        feature_id=feature_id,
                        wave_progression=wave_progression,
                        wave_id=issue_wave_id,
                        status="blocked",
                        reasons=[issue],
                    )
            packet_results["wave_progression"] = [dict(item) for item in wave_progression]
            final_status = _final_failure(
                feature_id=feature_id,
                category="pipeline_invalid",
                next_action="fix-wave-plan-continuation",
                reasons=wave_progression_issues,
                next_wave_id=_wave_id_from_issue(wave_progression_issues[0]) or _next_required_wave_id(wave_progression),
            )
            _persist_wave_progression(feature_id, wave_progression)
            publish_feature_artifacts_task(seeded["feature"], packet_results, None, review_route, None, final_status)
            return {"feature": seeded["feature"], "seeded": seeded, "runs": packet_results, "review_route": review_route, "final_status": final_status}

        verification_records: list[dict] = []
        review_routes: list[dict] = []
        wave_routes: list[dict] = []
        wave_packet_sets: dict[str, set[str]] = {
            wave_id: {str(packet["packet_id"]) for packet in packets}
            for wave_id, packets in wave_packets_by_id.items()
        }
        completed_packet_ids: set[str] = {architect_packet_id}
        if planner_required and planner_packet_id:
            completed_packet_ids.add(planner_packet_id)
        reviewer_decision_index = 0
        wave_decision_index = 0

        for wave_entry in wave_progression:
            wave_id = str(wave_entry.get("wave_id") or "")
            wave_packets = list(wave_packets_by_id.get(wave_id) or [])
            if not wave_packets:
                continue
            _set_wave_progression_status(
                feature_id=feature_id,
                wave_progression=wave_progression,
                wave_id=wave_id,
                status="running",
            )
            packet_results["wave_progression"] = [dict(item) for item in wave_progression]
            ordered_packets = order_packets_for_wave(wave_packets)
            queue_packets = list(ordered_packets)
            queue_ids = {str(packet["packet_id"]) for packet in queue_packets}
            wave_route = None
            idle_steps = 0

            while queue_packets:
                packet = queue_packets.pop(0)
                packet_id = str(packet["packet_id"])
                role = str(packet.get("role") or "")
                queue_ids.discard(packet_id)

                missing_dependencies = missing_internal_dependencies(
                    packet,
                    known_packet_ids=set(packets_by_id),
                    completed_packet_ids=completed_packet_ids,
                )
                if missing_dependencies:
                    append_unique_packet(queue_packets, packet)
                    queue_ids.add(packet_id)
                    idle_steps += 1
                    if idle_steps > max(len(queue_packets), 1) + 1:
                        final_status = _final_failure(
                            feature_id=feature_id,
                            category="pipeline_invalid",
                            next_action=f"dependency-deadlock:{packet_id}",
                            reasons=list(missing_dependencies),
                        )
                        packet_results[packet_result_key("dependency_error", packet_id)] = {
                            "packet_id": packet_id,
                            "missing_dependencies": missing_dependencies,
                        }
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_routes[-1] if review_routes else None,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    continue

                idle_steps = 0

                if role in {"coder", "planner", "architect", "reviewer"}:
                    with tags(f"wave:{wave_id}", f"role:{role}"):
                        packet_run = run_packet_task(packet_id, dry_run, timeout_seconds)
                    packet_results[packet_result_key("run", packet_id)] = packet_run
                    if packet_run.get("returncode") != 0:
                        final_status = _final_failure(
                            feature_id=feature_id,
                            category="environment_blocked",
                            next_action=f"inspect-failed-packet:{packet_id}",
                        )
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_routes[-1] if review_routes else None,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }

                if role == "coder":
                    with tags(f"wave:{wave_id}", "role:coder"):
                        mark_packet_status_task(packet_id, PacketStatus.REVIEW.value)
                    completed_packet_ids.add(packet_id)
                    if not packet_has_downstream_reviewer(packet_id, wave_packets):
                        with tags(f"wave:{wave_id}", "role:coder"):
                            mark_packet_status_task(packet_id, PacketStatus.ACCEPTED.value)
                    continue

                if role == "verifier":
                    with tags(f"wave:{wave_id}", "role:verifier"):
                        verifier_run = run_verifier_packet_task(packet_id, dry_run, timeout_seconds)
                    packet_results[packet_result_key("verifier-run", packet_id)] = verifier_run
                    if verifier_run.get("returncode") != 0:
                        final_status = _final_failure(
                            feature_id=feature_id,
                            category="environment_blocked",
                            next_action=f"inspect-failed-verifier:{packet_id}",
                        )
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_routes[-1] if review_routes else None,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    verifier_result = resolve_verifier_result_task(
                        verifier_run,
                        verifier_test_verdict,
                        verifier_observability_verdict,
                        verifier_frontend_visual_verdict,
                        verifier_commands_run,
                        verifier_evidence_paths,
                        verifier_blocking_issues,
                        prefer_agent_output,
                    )
                    packet_results[packet_result_key("verifier-result", packet_id)] = verifier_result
                    if verifier_result.get("source") == "parse_error":
                        with tags(f"wave:{wave_id}", "role:verifier"):
                            mark_packet_status_task(packet_id, PacketStatus.BLOCKED.value)
                        final_status = _final_failure(
                            feature_id=feature_id,
                            category="pipeline_invalid",
                            next_action=f"inspect-verifier-parse-error:{packet_id}",
                            reasons=list(verifier_result.get("blocking_issues") or []),
                        )
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_routes[-1] if review_routes else None,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    with tags(f"wave:{wave_id}", "role:verifier"):
                        verification_record = record_verifier_result_task(packet_id, verifier_result)
                        mark_packet_status_task(packet_id, PacketStatus.ACCEPTED.value)
                    verification_records.append(verification_record)
                    packet_results[packet_result_key("verification", packet_id)] = verification_record
                    publish_feature_artifacts_task(
                        seeded["feature"],
                        packet_results,
                        verification_record,
                        review_routes[-1] if review_routes else None,
                        wave_routes[-1] if wave_routes else None,
                        None,
                    )
                    completed_packet_ids.add(packet_id)
                    continue

                if role == "reviewer":
                    target_packet_id = reviewer_target_packet_id(packet, packets_by_id)
                    current_review_reasons = (
                        review_reasons_script[reviewer_decision_index]
                        if review_reasons_script and reviewer_decision_index < len(review_reasons_script)
                        else review_reasons
                    )
                    current_reviewer_verdict = (
                        reviewer_verdict_script[reviewer_decision_index]
                        if reviewer_verdict_script and reviewer_decision_index < len(reviewer_verdict_script)
                        else reviewer_verdict
                    )
                    reviewer_decision = resolve_reviewer_decision_task(
                        packet_run,
                        current_reviewer_verdict,
                        current_review_reasons,
                        prefer_agent_output,
                    )
                    reviewer_decision = _normalize_reviewer_decision_for_pipeline(reviewer_decision)
                    reviewer_decision = _escalate_repeated_observability_rework_for_pipeline(
                        reviewer_decision,
                        target_packet_id=target_packet_id,
                        packets_by_id=packets_by_id,
                    )
                    route_classification = _classify_rework_route(reviewer_decision)
                    rework_mode = _classify_rework_mode(
                        decision=reviewer_decision,
                        route_classification=route_classification,
                        target_packet=packets_by_id.get(target_packet_id),
                    )
                    architect_rework_packet = None
                    architect_rework_router_packet = None
                    if (
                        reviewer_decision.get("packet_verdict") == ReviewVerdict.REWORK_REQUIRED.value
                        and create_rework
                        and rework_routing_policy == REWORK_ROUTING_ARCHITECT_FIRST
                        and route_classification == REWORK_ROUTE_SELF_RESOLVABLE
                    ):
                        architect_rework_router_packet = create_architect_rework_packet_from_review(
                            target_packet_id,
                            packet_id,
                            list(reviewer_decision.get("reasons") or []),
                            route_classification=route_classification,
                        )
                        packets_by_id[str(architect_rework_router_packet["packet_id"])] = architect_rework_router_packet
                        packet_results[packet_result_key("architect_rework_packet", packet_id)] = architect_rework_router_packet
                        with tags(f"wave:{wave_id}", "role:architect"):
                            mark_packet_status_task(
                                str(architect_rework_router_packet["packet_id"]),
                                PacketStatus.CODING.value,
                            )
                            architect_rework_run = run_packet_task(
                                str(architect_rework_router_packet["packet_id"]),
                                dry_run,
                                timeout_seconds,
                            )
                        packet_results[packet_result_key("architect_rework_run", packet_id)] = architect_rework_run
                        if architect_rework_run.get("returncode") != 0:
                            final_status = _final_failure(
                                feature_id=feature_id,
                                category="environment_blocked",
                                next_action=f"inspect-failed-architect-rework:{architect_rework_router_packet['packet_id']}",
                            )
                            publish_feature_artifacts_task(
                                seeded["feature"],
                                packet_results,
                                verification_records[-1] if verification_records else None,
                                review_route,
                                wave_routes[-1] if wave_routes else None,
                                final_status,
                            )
                            return {
                                "feature": seeded["feature"],
                                "seeded": seeded,
                                "runs": packet_results,
                                "verification_records": verification_records,
                                "review_routes": review_routes,
                                "wave_routes": wave_routes,
                                "final_status": final_status,
                            }
                        with tags(f"wave:{wave_id}", "role:architect"):
                            mark_packet_status_task(
                                str(architect_rework_router_packet["packet_id"]),
                                PacketStatus.ACCEPTED.value,
                            )
                        architect_rework_packet = _build_architect_direct_rework(
                            coder_packet_id=target_packet_id,
                            reviewer_packet_id=packet_id,
                            reasons=list(reviewer_decision.get("reasons") or []),
                            architect_run=architect_rework_run,
                            route_classification=route_classification,
                            rework_mode=rework_mode,
                        )
                    reviewer_decision_index += 1
                    with tags(f"wave:{wave_id}", "role:reviewer"):
                        review_route = route_reviewer_verdict_task(
                            target_packet_id,
                            packet_id,
                            reviewer_decision,
                            create_rework,
                            rework_routing_policy=rework_routing_policy,
                            architect_rework_packet=architect_rework_packet,
                        )
                    review_routes.append(review_route)
                    packet_results[packet_result_key("review", packet_id)] = review_route
                    with tags(f"wave:{wave_id}", "role:reviewer", "artifact:packet"):
                        publish_packet_review_artifacts_task(review_route)
                    publish_feature_artifacts_task(
                        seeded["feature"],
                        packet_results,
                        verification_records[-1] if verification_records else None,
                        review_route,
                        wave_routes[-1] if wave_routes else None,
                        None,
                    )
                    completed_packet_ids.add(packet_id)

                    if review_route["reviewer_verdict"] == ReviewVerdict.REWORK_REQUIRED.value:
                        rework_object = review_route.get("rework")
                        _set_wave_progression_status(
                            feature_id=feature_id,
                            wave_progression=wave_progression,
                            wave_id=wave_id,
                            status="blocked",
                            reasons=list((review_route.get("review") or {}).get("reasons") or []),
                        )
                        packet_results["wave_progression"] = [dict(item) for item in wave_progression]
                        if (
                            review_route.get("route_classification") == REWORK_ROUTE_SELF_RESOLVABLE
                            and rework_routing_policy == REWORK_ROUTING_ARCHITECT_FIRST
                            and not (isinstance(rework_object, dict) and rework_object.get("packet_id"))
                        ):
                            final_status = _final_failure(
                                feature_id=feature_id,
                                category="pipeline_invalid",
                                next_action=f"missing-architect-direct-rework:{packet_id}",
                                reasons=[
                                    f"Architect-first rework for {packet_id} did not yield a bounded direct coder packet."
                                ],
                            )
                            publish_feature_artifacts_task(
                                seeded["feature"],
                                packet_results,
                                verification_records[-1] if verification_records else None,
                                review_route,
                                wave_routes[-1] if wave_routes else None,
                                final_status,
                            )
                            return {
                                "feature": seeded["feature"],
                                "seeded": seeded,
                                "runs": packet_results,
                                "verification_records": verification_records,
                                "review_routes": review_routes,
                                "wave_routes": wave_routes,
                                "final_status": final_status,
                            }
                        if isinstance(rework_object, dict) and rework_object.get("packet_id"):
                            direct_rework_packet = dict(rework_object)
                            if (
                                str(direct_rework_packet.get("rework_mode") or "") == REWORK_MODE_LIGHT_RESUME
                                and str(direct_rework_packet.get("review_target_packet_id") or "") == str(target_packet_id)
                            ):
                                light_resume_followup = _build_light_resume_followup(
                                    source_reviewer_packet=packet,
                                    resumed_packet=dict(packets_by_id.get(target_packet_id) or {}),
                                    reasons=list((review_route.get("review") or {}).get("reasons") or reviewer_decision.get("reasons") or []),
                                    reviewer_packet_id=packet_id,
                                    packets_by_id=packets_by_id,
                                )
                                review_route["rework"] = light_resume_followup["rework"]
                                review_route["light_resume_stage"] = True
                                rework_packets = list(light_resume_followup["packets"])
                                rework_reviewer_packet_id = str(light_resume_followup["reviewer_packet_id"] or "")
                            else:
                                rework_packets, rework_reviewer_packet_id = _build_direct_rework_followup_packets(
                                    source_reviewer_packet=packet,
                                    direct_rework_packet=direct_rework_packet,
                                    target_packet_id=target_packet_id,
                                    packets_by_id=packets_by_id,
                                )
                        else:
                            rework_bundle = rework_object or {}
                            rework_packets = [
                                packet_obj
                                for packet_obj in [
                                    rework_bundle.get("rework"),
                                    rework_bundle.get("verifier"),
                                    rework_bundle.get("reviewer"),
                                ]
                                if isinstance(packet_obj, dict) and packet_obj.get("packet_id")
                            ]
                            rework_reviewer_packet_id = str(rework_bundle.get("reviewer", {}).get("packet_id") or "")
                        if rework_packets:
                            for rework_packet in rework_packets:
                                rework_packet_id = str(rework_packet["packet_id"])
                                packets_by_id[rework_packet_id] = rework_packet
                                wave_packet_sets.setdefault(wave_id, set()).add(rework_packet_id)
                                if (
                                    review_route.get("light_resume_stage") is True
                                    and rework_packet_id == str(target_packet_id)
                                ):
                                    completed_packet_ids.discard(rework_packet_id)
                                if rework_packet_id not in queue_ids and rework_packet_id not in completed_packet_ids:
                                    append_unique_packet(queue_packets, rework_packet)
                                    queue_ids.add(rework_packet_id)
                            if rework_reviewer_packet_id:
                                for queued_packet in queue_packets:
                                    if str(queued_packet.get("role") or "") != "architect":
                                        continue
                                    if str(queued_packet.get("wave_id") or "") != wave_id:
                                        continue
                                    dependencies = list(queued_packet.get("dependencies") or [])
                                    if packet_id in dependencies and rework_reviewer_packet_id and rework_reviewer_packet_id not in dependencies:
                                        queued_packet["dependencies"] = [*dependencies, rework_reviewer_packet_id]
                                        update_record(
                                            "packets",
                                            "packets",
                                            "packet_id",
                                            str(queued_packet["packet_id"]),
                                            {"dependencies": queued_packet["dependencies"]},
                                        )
                            _set_wave_progression_status(
                                feature_id=feature_id,
                                wave_progression=wave_progression,
                                wave_id=wave_id,
                                status="running",
                            )
                            packet_results["wave_progression"] = [dict(item) for item in wave_progression]
                            continue
                        if review_route.get("decision"):
                            next_action = (
                                "architect-user-decision-required"
                                if review_route.get("route_classification") == REWORK_ROUTE_REQUIRES_USER_DECISION
                                else "architect-planner-decomposition-required"
                            )
                            reasons = list((review_route.get("review") or {}).get("reasons") or [])
                            _set_wave_progression_status(
                                feature_id=feature_id,
                                wave_progression=wave_progression,
                                wave_id=wave_id,
                                status="blocked",
                                reasons=reasons,
                            )
                            packet_results["wave_progression"] = [dict(item) for item in wave_progression]
                            feature_record = mark_feature_status(feature_id, FeatureStatus.ARCHITECT_READY)
                            final_status = {
                                "feature": feature_record,
                                "has_failures": False,
                                "final_outcome": "awaiting_architect",
                                "user_facing_status": FeatureStatus.ARCHITECT_READY.value,
                                "user_summary": _final_user_summary(
                                    outcome="awaiting_architect",
                                    status=FeatureStatus.ARCHITECT_READY.value,
                                    summary=str(feature_record.get("summary") or summary),
                                    next_action=next_action,
                                    reasons=reasons,
                                ),
                                "next_action": next_action,
                                "reasons": reasons,
                                "wave_progression": [dict(item) for item in wave_progression],
                            }
                            notify_feature_event(
                                feature_id=feature_id,
                                title=str(seeded["feature"].get("title") or title),
                                status=FeatureStatus.ARCHITECT_READY.value,
                                summary=final_status["user_summary"],
                                blockers=reasons,
                                next_action=next_action,
                            )
                            publish_feature_artifacts_task(
                                seeded["feature"],
                                packet_results,
                                verification_records[-1] if verification_records else None,
                                review_route,
                                wave_routes[-1] if wave_routes else None,
                                final_status,
                            )
                            return {
                                "feature": seeded["feature"],
                                "seeded": seeded,
                                "runs": packet_results,
                                "verification_records": verification_records,
                                "review_routes": review_routes,
                                "wave_routes": wave_routes,
                                "final_status": final_status,
                            }
                        final_status = _final_failure(
                            feature_id=feature_id,
                            category="pipeline_invalid",
                            next_action=f"missing-rework-packet:{packet_id}",
                        )
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_route,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    if review_route["reviewer_verdict"] == ReviewVerdict.ESCALATE_TO_ARCHITECT.value:
                        reasons = list((review_route.get("review") or {}).get("reasons") or [])
                        _set_wave_progression_status(
                            feature_id=feature_id,
                            wave_progression=wave_progression,
                            wave_id=wave_id,
                            status="blocked",
                            reasons=reasons,
                        )
                        packet_results["wave_progression"] = [dict(item) for item in wave_progression]
                        feature_record = mark_feature_status(feature_id, FeatureStatus.ARCHITECT_READY)
                        final_status = {
                            "feature": feature_record,
                            "has_failures": False,
                            "final_outcome": "awaiting_architect",
                            "user_facing_status": FeatureStatus.ARCHITECT_READY.value,
                            "user_summary": _final_user_summary(
                                outcome="awaiting_architect",
                                status=FeatureStatus.ARCHITECT_READY.value,
                                summary=str(feature_record.get("summary") or summary),
                                next_action="architect-decision-required",
                                reasons=reasons,
                            ),
                            "next_action": "architect-decision-required",
                            "reasons": reasons,
                            "wave_progression": [dict(item) for item in wave_progression],
                        }
                        notify_feature_event(
                            feature_id=feature_id,
                            title=str(seeded["feature"].get("title") or title),
                            status=FeatureStatus.ARCHITECT_READY.value,
                            summary=final_status["user_summary"],
                            blockers=reasons,
                            next_action="architect-decision-required",
                        )
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_route,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    if review_route["reviewer_verdict"] == ReviewVerdict.BLOCKED.value:
                        reasons = list((review_route.get("review") or {}).get("reasons") or [])
                        _set_wave_progression_status(
                            feature_id=feature_id,
                            wave_progression=wave_progression,
                            wave_id=wave_id,
                            status="blocked",
                            reasons=reasons,
                        )
                        packet_results["wave_progression"] = [dict(item) for item in wave_progression]
                        category = "verification_blocked"
                        if any(
                            "pipeline" in reason.lower() or "verifier packet is missing" in reason.lower() or "structured text" in reason.lower()
                            for reason in reasons
                        ):
                            category = "pipeline_invalid"
                        final_status = _final_failure(
                            feature_id=feature_id,
                            category=category,
                            next_action=f"inspect-review-blockers:{packet_id}",
                            reasons=reasons,
                        )
                        publish_feature_artifacts_task(
                            seeded["feature"],
                            packet_results,
                            verification_records[-1] if verification_records else None,
                            review_route,
                            wave_routes[-1] if wave_routes else None,
                            final_status,
                        )
                        return {
                            "feature": seeded["feature"],
                            "seeded": seeded,
                            "runs": packet_results,
                            "verification_records": verification_records,
                            "review_routes": review_routes,
                            "wave_routes": wave_routes,
                            "final_status": final_status,
                        }
                    continue

                if role == "architect":
                    current_wave_reasons = (
                        wave_reasons_script[wave_decision_index]
                        if wave_reasons_script and wave_decision_index < len(wave_reasons_script)
                        else wave_reasons
                    )
                    current_wave_verdict = (
                        wave_verdict_script[wave_decision_index]
                        if wave_verdict_script and wave_decision_index < len(wave_verdict_script)
                        else wave_verdict
                    )
                    wave_decision = resolve_wave_decision_task(
                        packet_run,
                        current_wave_verdict,
                        current_wave_reasons,
                        prefer_agent_output,
                    )
                    wave_decision_index += 1
                    with tags(f"wave:{wave_id}", "role:architect"):
                        wave_route = route_architect_wave_verdict_task(
                            feature_id,
                            wave_id,
                            packet_id,
                            wave_decision,
                        )
                    wave_route["wave_progress"] = next(
                        (dict(item) for item in wave_progression if str(item.get("wave_id") or "") == wave_id),
                        {},
                    )
                    wave_routes.append(wave_route)
                    packet_results[packet_result_key("wave", packet_id)] = wave_route
                    publish_feature_artifacts_task(
                        seeded["feature"],
                        packet_results,
                        verification_records[-1] if verification_records else None,
                        review_routes[-1] if review_routes else None,
                        wave_route,
                        None,
                    )
                    completed_packet_ids.add(packet_id)
                    if wave_route["wave_verdict"] == WaveVerdict.ACCEPTED.value:
                        _set_wave_progression_status(
                            feature_id=feature_id,
                            wave_progression=wave_progression,
                            wave_id=wave_id,
                            status="accepted",
                        )
                        wave_route["wave_progress"] = next(
                            (dict(item) for item in wave_progression if str(item.get("wave_id") or "") == wave_id),
                            {},
                        )
                        packet_results["wave_progression"] = [dict(item) for item in wave_progression]
                        continue
                    if wave_route["wave_verdict"] == WaveVerdict.REWORK_REQUIRED.value:
                        reasons = list((wave_route.get("wave_review") or {}).get("reasons") or [])
                        _set_wave_progression_status(
                            feature_id=feature_id,
                            wave_progression=wave_progression,
                            wave_id=wave_id,
                            status="blocked",
                            reasons=reasons,
                        )
                        wave_route["wave_progress"] = next(
                            (dict(item) for item in wave_progression if str(item.get("wave_id") or "") == wave_id),
                            {},
                        )
                        packet_results["wave_progression"] = [dict(item) for item in wave_progression]
                        feature_record = mark_feature_status(
                            feature_id,
                            FeatureStatus.IN_PROGRESS,
                            blocker_reasons=reasons,
                        )
                        final_status = {
                            "feature": feature_record,
                            "has_failures": False,
                            "final_outcome": "rework_required",
                            "user_facing_status": FeatureStatus.IN_PROGRESS.value,
                            "user_summary": _final_user_summary(
                                outcome="rework_required",
                                status=FeatureStatus.IN_PROGRESS.value,
                                summary=str(feature_record.get("summary") or summary),
                                next_action=f"architect-wave-rework-required:{wave_id}",
                                reasons=reasons,
                            ),
                            "next_action": f"architect-wave-rework-required:{wave_id}",
                            "reasons": reasons,
                            "wave_progression": [dict(item) for item in wave_progression],
                        }
                        notify_feature_event(
                            feature_id=feature_id,
                            title=str(seeded["feature"].get("title") or title),
                            status=FeatureStatus.IN_PROGRESS.value,
                            summary=final_status["user_summary"],
                            wave_id=wave_id,
                            blockers=reasons,
                            next_action=final_status["next_action"],
                        )
                    else:
                        reasons = list((wave_route.get("wave_review") or {}).get("reasons") or [])
                        _set_wave_progression_status(
                            feature_id=feature_id,
                            wave_progression=wave_progression,
                            wave_id=wave_id,
                            status="blocked",
                            reasons=reasons,
                        )
                        wave_route["wave_progress"] = next(
                            (dict(item) for item in wave_progression if str(item.get("wave_id") or "") == wave_id),
                            {},
                        )
                        packet_results["wave_progression"] = [dict(item) for item in wave_progression]
                        final_status = _final_failure(
                            feature_id=feature_id,
                            category="product_blocked",
                            next_action=f"architect-wave-blocked:{wave_id}",
                            reasons=reasons,
                        )
                    publish_feature_artifacts_task(
                        seeded["feature"],
                        packet_results,
                        verification_records[-1] if verification_records else None,
                        review_routes[-1] if review_routes else None,
                        wave_route,
                        final_status,
                    )
                    return {
                        "feature": seeded["feature"],
                        "seeded": seeded,
                        "runs": packet_results,
                        "verification_records": verification_records,
                        "review_routes": review_routes,
                        "wave_routes": wave_routes,
                        "final_status": final_status,
                    }

            if wave_route is None:
                _set_wave_progression_status(
                    feature_id=feature_id,
                    wave_progression=wave_progression,
                    wave_id=wave_id,
                    status="blocked",
                    reasons=[f"Missing architect wave gate for {wave_id}"],
                )
                packet_results["wave_progression"] = [dict(item) for item in wave_progression]
                final_status = _final_failure(
                    feature_id=feature_id,
                    category="pipeline_invalid",
                    next_action=f"missing-architect-wave-gate:{wave_id}",
                )
                publish_feature_artifacts_task(
                    seeded["feature"],
                    packet_results,
                    verification_records[-1] if verification_records else None,
                    review_routes[-1] if review_routes else None,
                    wave_routes[-1] if wave_routes else None,
                    final_status,
                )
                return {
                    "feature": seeded["feature"],
                    "seeded": seeded,
                    "runs": packet_results,
                    "verification_records": verification_records,
                    "review_routes": review_routes,
                    "wave_routes": wave_routes,
                    "final_status": final_status,
                }

        if not _all_required_waves_accepted(wave_progression):
            next_wave_id = _next_required_wave_id(wave_progression)
            reasons = (
                [f"Feature cannot be accepted until required wave {next_wave_id} is accepted."]
                if next_wave_id
                else ["Feature cannot be accepted because not all required waves are accepted."]
            )
            final_status = _final_failure(
                feature_id=feature_id,
                category="pipeline_invalid",
                next_action=f"incomplete-required-waves:{next_wave_id or 'unknown'}",
                reasons=reasons,
            )
            publish_feature_artifacts_task(
                seeded["feature"],
                packet_results,
                verification_records[-1] if verification_records else None,
                review_routes[-1] if review_routes else None,
                wave_routes[-1] if wave_routes else None,
                final_status,
            )
            return {
                "feature": seeded["feature"],
                "seeded": seeded,
                "runs": packet_results,
                "verification_records": verification_records,
                "review_routes": review_routes,
                "wave_routes": wave_routes,
                "final_status": final_status,
            }

        accepted_feature = mark_feature_status(feature_id, FeatureStatus.ACCEPTED)
        accepted_feature = update_record(
            "features",
            "features",
            "feature_id",
            feature_id,
            {
                "wave_progression": [dict(item) for item in wave_progression],
                "next_wave_id": "",
                "all_required_waves_accepted": True,
            },
        )
        final_status = _post_acceptance_final_status(
            feature_id=feature_id,
            accepted_feature=accepted_feature,
            summary=summary,
            packet_results=packet_results,
            verification_records=verification_records,
            review_routes=review_routes,
            wave_routes=wave_routes,
            commit_hash=commit_hash,
            wave_progression=wave_progression,
        )
        notify_feature_event(
            feature_id=feature_id,
            title=str(seeded["feature"].get("title") or title),
            status=str(final_status["user_facing_status"]),
            summary=final_status["user_summary"],
            next_action=str(final_status["next_action"]),
        )
        publish_feature_artifacts_task(
            seeded["feature"],
            packet_results,
            verification_records[-1] if verification_records else None,
            review_routes[-1] if review_routes else None,
            wave_routes[-1] if wave_routes else None,
            final_status,
        )
        return {
            "feature": seeded["feature"],
            "seeded": seeded,
            "runs": packet_results,
            "verification_records": verification_records,
            "review_routes": review_routes,
            "wave_routes": wave_routes,
            "verification": verification_records[-1] if verification_records else None,
            "review_route": review_routes[-1] if review_routes else None,
            "wave_route": wave_routes[-1] if wave_routes else None,
            "final_status": final_status,
        }


@task(task_run_name="review-record:{packet_id}:{verdict}")
def review_task(packet_id: str, verdict: str, reasons: list[str], create_rework: bool):
    review = record_review(
        packet_id=packet_id,
        verdict=ReviewVerdict(verdict),
        reasons=reasons,
        follow_up_action="localized_rework" if create_rework else "none",
    )
    rework = None
    if verdict == ReviewVerdict.REWORK_REQUIRED.value and create_rework:
        rework = create_rework_from_review(packet_id, reasons)
    return {"review": review, "rework": rework}


@flow(name="prefect-grace-review-router", flow_run_name="review:{packet_id}:{verdict}")
def review_router_flow(
    packet_id: str,
    verdict: str,
    reasons: list[str] | None = None,
    create_rework: bool = True,
):
    return review_task(
        packet_id=packet_id,
        verdict=verdict,
        reasons=reasons or [],
        create_rework=create_rework,
    )


if __name__ == "__main__":
    feature_pipeline(
        feature_id="FEAT-PREFECT-GRACE-SCAFFOLD",
        title="Prefect Grace Scaffold",
        summary="Bootstrap file-backed Prefect orchestration for strict GRACE workflows.",
        dry_run=True,
    )
